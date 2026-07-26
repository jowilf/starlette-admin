from datetime import UTC, datetime
from typing import Any

import filetype
from models import Loan, LoanStatus, MembershipType
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin import (
    BooleanField,
    ColorField,
    DateTimeField,
    EmailField,
    EnumField,
    FileField,
    ImageField,
    IntegerField,
    StringField,
    TagsField,
    TextAreaField,
    action,
    flash,
    row_action,
)
from starlette_admin.contrib.beanie import InlineModelView, ModelView
from starlette_admin.contrib.beanie.filters import DateTimeBetweenFilter
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField
from starlette_admin.storage import LocalStorage

UPLOAD_DIR = "uploads"

covers_storage = LocalStorage(base_dir=f"{UPLOAD_DIR}/covers", name="covers")
samples_storage = LocalStorage(base_dir=f"{UPLOAD_DIR}/samples", name="samples")


def validate_pdf(request: Request, field: BaseField, upload: UploadFile) -> None:
    upload.file.seek(0)
    header = upload.file.read(2048)
    kind = filetype.guess(header)
    detected = kind.mime if kind else "application/octet-stream"
    upload.file.seek(0)
    if detected != "application/pdf":
        raise ValueError(f"Invalid file type '{detected}'. Only PDF is allowed.")
    return


# ── Inline ────────────────────────────────────────────────────────────────────


class LoanInline(InlineModelView):
    """Loans embedded inside the Member create/edit form."""

    document = Loan
    fields = [
        "id",
        "book",
        DateTimeField("loan_date"),
        DateTimeField("due_date"),
        DateTimeField("returned_at"),
        EnumField("status", enum=LoanStatus),
        TextAreaField("notes"),
    ]
    menu_label = "Loans"
    extra = 1


# ── Genre ─────────────────────────────────────────────────────────────────────


class GenreView(ModelView):
    fields = ["id", "name", ColorField("color"), TextAreaField("description")]
    searchable_fields = ["name"]
    sortable_fields = ["name"]


# ── Book ──────────────────────────────────────────────────────────────────────


class BookView(ModelView):
    fields = [
        "id",
        "title",
        "isbn",
        TextAreaField("synopsis"),
        IntegerField("published_year"),
        IntegerField("page_count"),
        IntegerField("total_copies"),
        BooleanField("featured"),
        TagsField("tags"),
        ImageField("cover", storage=covers_storage, upload_folder="covers"),
        FileField(
            "sample",
            storage=samples_storage,
            upload_folder="samples",
            accept=".pdf",
            max_size=10 * 1024 * 1024,
            validators=[validate_pdf],
        ),
        "genres",
        DateTimeField("created_at"),
    ]
    exclude_fields_from_list = ["synopsis", "sample"]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]

    exporters = ["csv", "xlsx"]
    searchable_fields = ["title", "isbn", "tags"]
    sortable_fields = [
        "title",
        "published_year",
        "page_count",
        "featured",
        "created_at",
    ]
    fields_default_sort = [("created_at", True)]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.created_at = datetime.now(UTC)


# ── Member ────────────────────────────────────────────────────────────────────


class MemberView(ModelView):
    fields = [
        "id",
        "full_name",
        EmailField("email"),
        StringField("phone"),
        EnumField("membership_type", enum=MembershipType),
        TextAreaField("notes"),
        DateTimeField("joined_at"),
    ]
    exclude_fields_from_create = ["joined_at"]
    exclude_fields_from_edit = ["joined_at"]

    inlines = [LoanInline]

    exporters = ["csv", "xlsx"]
    searchable_fields = ["full_name", "email"]
    sortable_fields = ["full_name", "membership_type", "joined_at"]
    fields_default_sort = [("joined_at", True)]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.joined_at = datetime.now(UTC)


# ── Loan ──────────────────────────────────────────────────────────────────────


class LoanView(ModelView):
    fields = [
        "id",
        "book",
        "member",
        DateTimeField("loan_date", filters=[DateTimeBetweenFilter]),
        DateTimeField("due_date"),
        DateTimeField("returned_at"),
        EnumField("status", enum=LoanStatus),
        TextAreaField("notes"),
    ]
    exclude_fields_from_list = ["notes"]

    exporters = ["csv", "xlsx"]
    sortable_fields = ["loan_date", "due_date", "status"]
    fields_default_sort = [("loan_date", True)]

    actions = ["mark_returned", "mark_overdue", "delete"]
    row_actions = ["view", "edit", "mark_returned", "delete"]

    # ── Batch actions ──────────────────────────────────────────────────────────

    @action(
        name="mark_returned",
        text="Mark as returned",
        confirmation="Mark the selected loans as returned?",
        submit_btn_text="Mark returned",
        submit_btn_class="btn btn-success",
    )
    async def mark_returned_action(self, request: Request, pks: list[Any]) -> None:
        count = 0
        for loan in await self.find_by_pks(request, pks):
            if loan.status != LoanStatus.RETURNED:
                loan.status = LoanStatus.RETURNED
                loan.returned_at = datetime.now(UTC)
                await loan.save()
                count += 1
        flash(request, f"{count} loan(s) marked as returned.", "success")

    @action(
        name="mark_overdue",
        text="Mark as overdue",
        confirmation="Mark the selected loans as overdue?",
        submit_btn_text="Mark overdue",
        submit_btn_class="btn btn-warning",
    )
    async def mark_overdue_action(self, request: Request, pks: list[Any]) -> None:
        count = 0
        for loan in await self.find_by_pks(request, pks):
            if loan.status == LoanStatus.ACTIVE:
                loan.status = LoanStatus.OVERDUE
                await loan.save()
                count += 1
        flash(request, f"{count} loan(s) marked as overdue.", "success")

    # ── Row action ─────────────────────────────────────────────────────────────

    @row_action(
        name="mark_returned",
        text="Return",
        confirmation="Mark this loan as returned?",
        icon_class="fas fa-check",
        submit_btn_text="Return",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
    )
    async def mark_returned_row_action(self, request: Request, pk: Any) -> None:
        loan = await self.find_by_pk(request, pk)
        if loan.status == LoanStatus.RETURNED:
            raise ActionFailed("Loan is already returned.")
        loan.status = LoanStatus.RETURNED
        loan.returned_at = datetime.now(UTC)
        await loan.save()
        flash(request, "Loan marked as returned.", "success")

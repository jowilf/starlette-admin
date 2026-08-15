from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any, Literal

from starlette.requests import Request
from starlette_admin.exceptions import ActionFailed
from starlette_admin.filters.base import FilterGroup
from starlette_admin.i18n import lazy_gettext as _

if TYPE_CHECKING:
    from starlette_admin.views import BaseModelView

ModalSize = Literal["sm", "md", "lg", "xl"]
_MODAL_SIZES: frozenset[str] = frozenset(("sm", "md", "lg", "xl"))


class ActionSelection:
    """The rows a batch action targets, resolved lazily.

    Behaves identically whether the user checked rows one by one or clicked
    "select all matching" in the banner: call `rows()`, `pks()`, or `count()`
    and the right query runs underneath.

    `is_select_all`, `filters`, and `q` are exposed for handlers that want to
    reason about *how* rows were selected, e.g. to push the whole operation
    down as a single bulk query instead of materializing rows.
    """

    def __init__(
        self,
        view: "BaseModelView",
        request: Request,
        pks: list[Any] | None,
        filters: FilterGroup | None,
        q: str | None,
    ) -> None:
        self._view = view
        self._request = request
        self._pks = pks
        self.is_select_all = pks is None
        self.filters = filters
        self.q = q
        self._rows: Sequence[Any] | None = None
        self._count: int | None = None

    async def rows(self) -> Sequence[Any]:
        """The target rows. Fetched once and cached across calls."""
        if self._rows is None:
            if self.is_select_all:
                await self._count_matching_within_limit()
                self._rows = await self._view.find_all(
                    self._request, skip=0, limit=-1, q=self.q, filters=self.filters
                )
            else:
                self._rows = await self._view.find_by_pks(
                    self._request, self._pks or []
                )
        return self._rows

    async def pks(self) -> list[Any]:
        """Primary keys of the target rows."""
        if not self.is_select_all:
            return list(self._pks or [])
        return [
            str(await self._view.get_pk_value(self._request, obj))
            for obj in await self.rows()
        ]

    async def count(self) -> int:
        """Number of rows the action targets.

        In select-all mode, this runs a `count()` query and enforces
        `action_select_all_limit`, raising `ActionFailed` when the current
        filter/search matches too many rows.
        """
        if self._count is not None:
            return self._count
        if self._rows is not None:
            self._count = len(self._rows)
        elif self.is_select_all:
            return await self._count_matching_within_limit()
        else:
            self._count = len(self._pks or [])
        return self._count

    async def _count_matching_within_limit(self) -> int:
        if self._count is None:
            count = await self._view.count(
                self._request, q=self.q, filters=self.filters
            )
            if count > self._view.action_select_all_limit:
                raise ActionFailed(
                    _(
                        "Too many rows match the current filter (%(count)s); "
                        "refine your filter (limit: %(limit)s)"
                    )
                    % {"count": count, "limit": self._view.action_select_all_limit}
                )
            self._count = count
        return self._count


def action(
    name: str,
    text: str,
    confirmation: str | None = None,
    header: str | None = None,
    submit_btn_class: str | None = None,
    submit_btn_text: str | None = _("Yes, Proceed"),
    icon_class: str | None = None,
    form: str | Callable[..., str | Awaitable[str]] | None = None,
    custom_response: bool | None = False,
    allow_empty_selection: bool = False,
    dedicated_button: bool = False,
    modal_size: ModalSize = "sm",
) -> Callable[[Callable[..., Awaitable[Any]]], Any]:
    """Decorator to add a custom batch action to a
    [ModelView][starlette_admin.views.BaseModelView].

    Args:
        name: Unique action name within the ModelView.
        text: Action text displayed to users.
        confirmation: Confirmation text. If not provided, the action executes
            unconditionally.
        header: Title shown in the confirmation modal header. If not provided,
            the modal renders without a header.
        submit_btn_text: Submit button text.
        submit_btn_class: Complete class string for the submit button
            (e.g. `btn btn-outline-danger`), or a class role the active theme
            maps. Defaults to the theme's `action.modal_confirm_button` role.
        icon_class: Icon class (e.g. `fa-lite fa-folder`, `fa-duotone fa-circle-right`).
        form: Custom form to collect data from the user. Either a static HTML
            string, or a callable that builds the form HTML per request —
            `(request) -> str`, or `(request, view) -> str` to also receive the
            `BaseModelView` instance. Sync or async either way.
        custom_response: Set to True when you want to return a custom Starlette response
            instead of `None`.
        allow_empty_selection: Set to True for actions that operate on the whole
            collection rather than on a row selection, such as a full sync or a
            bulk import. These actions render in a separate, always visible
            "Actions" dropdown on the list page and can be triggered without
            selecting any row, so `selection` may resolve to zero rows.
            Defaults to False, which requires at least one selected row.
        dedicated_button: Set to True to render this action as its own toolbar
            button instead of an entry in the grouped "Actions" dropdown.
            Requires `allow_empty_selection=True`; combining it with a
            selection-only action raises `ValueError` at startup.
        modal_size: Size of the confirmation modal: `sm`, `md`, `lg`, or `xl`.
            Defaults to `sm`. Only relevant when `confirmation` is set.

    !!! usage

        ```python
        class ArticleView(ModelView):
            actions = ['make_published', 'redirect']

            @action(
                name="make_published",
                text="Mark selected articles as published",
                confirmation="Are you sure you want to mark selected articles as published ?",
                submit_btn_text="Yes, proceed",
                submit_btn_class="btn btn-success",
                form='''
                <form>
                    <div class="mt-3">
                        <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
                    </div>
                </form>
                '''
            )
            async def make_published_action(
                self, request: Request, selection: ActionSelection
            ) -> None:
                # Retrieve form data submitted by the user
                data: FormData = await request.form()
                user_input = data.get("example-text-input")

                for article in await selection.rows():
                    # TODO: Implement database update logic here
                    pass

                if ...:
                    # Halt execution and display a descriptive error to the user
                    raise ActionFailed("Sorry, we cannot process this action right now.")

                # Confirm successful execution via a UI flash message
                flash(request, "{} articles were successfully marked as published".format(await selection.count()), "success")

            # Return a Starlette Response instead of None when custom_response=True
            @action(
                name="redirect",
                text="Redirect",
                custom_response=True,
                confirmation="Fill the form",
                form='''
                <form>
                    <div class="mt-3">
                        <input type="text" class="form-control" name="value" placeholder="Enter value">
                    </div>
                </form>
                '''
             )
            async def redirect_action(
                self, request: Request, selection: ActionSelection
            ) -> Response:
                data = await request.form()
                return RedirectResponse(f"https://example.com/?value={data['value']}")

            # `form` can also be a callable, to build the form HTML per request
            def build_export_form(request: Request) -> str:
                default_filename = request.query_params.get("q", "export")
                return f'''
                <form>
                    <div class="mt-3">
                        <input type="text" class="form-control" name="filename" value="{escape(default_filename)}">
                    </div>
                </form>
                '''

            @action(
                name="export",
                text="Export selected",
                confirmation="Choose a filename",
                form=build_export_form,
            )
            async def export_action(
                self, request: Request, selection: ActionSelection
            ) -> None:
                data = await request.form()
                filename = data["filename"]
                # TODO: Implement export logic here, e.g. via selection.rows()
        ```
    """

    if modal_size not in _MODAL_SIZES:
        raise ValueError(
            f"Action `{name}`: modal_size must be one of {sorted(_MODAL_SIZES)}, "
            f"got {modal_size!r}"
        )

    def wrap(f: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        f._action = {  # type: ignore
            "name": name,
            "text": text,
            "confirmation": confirmation,
            "header": header,
            "submit_btn_text": submit_btn_text,
            "submit_btn_class": submit_btn_class,
            "icon_class": icon_class,
            "form": form if form is not None else "",
            "custom_response": custom_response,
            "allow_empty_selection": allow_empty_selection,
            "dedicated_button": dedicated_button,
            "modal_size": modal_size,
        }
        return f

    return wrap


def row_action(
    name: str,
    text: str,
    confirmation: str | None = None,
    header: str | None = None,
    action_btn_class: str | None = None,
    submit_btn_class: str | None = None,
    submit_btn_text: str | None = _("Yes, Proceed"),
    icon_class: str | None = None,
    form: str | Callable[[Request, Any], str | Awaitable[str]] | None = None,
    custom_response: bool | None = False,
    exclude_from_list: bool = False,
    exclude_from_detail: bool = False,
    modal_size: ModalSize = "sm",
) -> Callable[[Callable[..., Awaitable[Any]]], Any]:
    """Decorator to add a custom row action to a
    [ModelView][starlette_admin.views.BaseModelView].

    Args:
        name: Unique row action name for the ModelView.
        text: Action text displayed to users.
        confirmation: Confirmation text. If provided, the action requires confirmation.
        header: Title shown in the confirmation modal header. If not provided,
            the modal renders without a header.
        action_btn_class: Complete class string for the action button on the
            detail page (e.g. `btn btn-info`), or a class role the active
            theme maps. Defaults to the theme's `action.row_item` role.
        submit_btn_class: Complete class string for the submit button
            (e.g. `btn btn-outline-danger`), or a class role the active theme
            maps. Defaults to the theme's `action.modal_confirm_button` role.
        submit_btn_text: Text for the submit button.
        icon_class: Icon class (e.g. `fa-lite fa-folder`, `fa-duotone fa-circle-right`).
        form: Custom HTML to collect data from the user. Either a static HTML
            string, or a callable `(request, obj) -> str` (sync or async) that
            builds the form HTML for that specific row.
        custom_response: Set to True when you want to return a custom Starlette response
            instead of `None`.
        exclude_from_list: Set to True to exclude the action from the list view.
        exclude_from_detail: Set to True to exclude the action from the detail view.
        modal_size: Size of the confirmation modal: `sm`, `md`, `lg`, or `xl`.
            Defaults to `sm`. Only relevant when `confirmation` is set.

    !!! usage

        ```python
        @row_action(
            name="make_published",
            text="Mark as published",
            confirmation="Are you sure you want to mark this article as published ?",
            icon_class="fas fa-check-circle",
            submit_btn_text="Yes, proceed",
            submit_btn_class="btn btn-success",
            action_btn_class="btn btn-info",
        )
        async def make_published_row_action(self, request: Request, pk: Any) -> None:
            session: Session = request.state.session
            article = await self.find_by_pk(request, pk)
            if article.status == Status.Published:
                raise ActionFailed("The article is already marked as published.")
            article.status = Status.Published
            session.add(article)
            session.flush()
            flash(request, "The article was successfully marked as published.", "success")

        # `form` can also be a callable, to build the form HTML per row
        def build_rename_form(request: Request, obj: Any) -> str:
            return f'''
            <form>
                <div class="mt-3">
                    <input type="text" class="form-control" name="title" value="{obj.title}">
                </div>
            </form>
            '''

        @row_action(
            name="rename",
            text="Rename",
            form=build_rename_form,
        )
        async def rename_row_action(self, request: Request, pk: Any) -> None:
            data = await request.form()
            article = await self.find_by_pk(request, pk)
            article.title = data["title"]
        ```
    """

    if modal_size not in _MODAL_SIZES:
        raise ValueError(
            f"Row action `{name}`: modal_size must be one of {sorted(_MODAL_SIZES)}, "
            f"got {modal_size!r}"
        )

    def wrap(f: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        f._row_action = {  # type: ignore
            "name": name,
            "text": text,
            "confirmation": confirmation,
            "header": header,
            "action_btn_class": action_btn_class,
            "submit_btn_text": submit_btn_text,
            "submit_btn_class": submit_btn_class,
            "icon_class": icon_class,
            "form": form if form is not None else "",
            "custom_response": custom_response,
            "exclude_from_list": exclude_from_list,
            "exclude_from_detail": exclude_from_detail,
            "modal_size": modal_size,
        }
        return f

    return wrap


def link_row_action(
    name: str,
    text: str,
    action_btn_class: str | None = None,
    icon_class: str | None = None,
    exclude_from_list: bool = False,
    exclude_from_detail: bool = False,
) -> Callable[[Callable[..., str]], Any]:
    """Decorator to add a custom row action that redirects to a URL instead of running
    server-side logic.

    !!! note

        Use this decorator when a row action should navigate users to a website or
        internal page rather than execute a handler and stay on the current page.

    Args:
        name: Unique row action name for the ModelView.
        text: Action text displayed to users.
        action_btn_class: Complete class string for the action button on the
            detail page (e.g. `btn btn-info`), or a class role the active
            theme maps. Defaults to the theme's `action.row_item` role.
        icon_class: Icon class (e.g. `fa-lite fa-folder`, `fa-duotone fa-circle-right`).
        exclude_from_list: Set to True to exclude the action from the list view.
        exclude_from_detail: Set to True to exclude the action from the detail view.

    !!! usage

        ```python
        @link_row_action(
            name="go_to_example",
            text="Go to example.com",
            icon_class="fas fa-arrow-up-right-from-square",
        )
        def go_to_example_row_action(self, request: Request, pk: Any) -> str:
            return f"https://example.com/?pk={pk}"
        ```

    """

    def wrap(f: Callable[..., str]) -> Callable[..., str]:
        f._row_action = {  # type: ignore
            "name": name,
            "text": text,
            "action_btn_class": action_btn_class,
            "icon_class": icon_class,
            "is_link": True,
            "exclude_from_list": exclude_from_list,
            "exclude_from_detail": exclude_from_detail,
        }
        return f

    return wrap

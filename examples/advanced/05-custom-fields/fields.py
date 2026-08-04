"""Custom fields for the employee directory example.

`StatusBadgeField` renders an enum-like value as a colored Tabler badge on the
list page. `AvatarNameField` renders a `name` column together with the row's
avatar image on the list page, while staying a plain text field everywhere
else (detail, create, edit, export).
"""

from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any

from starlette.requests import Request
from starlette_admin.fields import EnumField, StringField
from starlette_admin.storage.local import LocalStorage
from starlette_admin.types import RequestAction


@dataclass
class StatusBadgeField(EnumField):
    """Renders an enum-like status value as a colored badge on the list page.

    The badge color is looked up in `badge_class_by_value`; any value with no
    explicit mapping falls back to a plain `badge` class.
    """

    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    badge_class_by_value: dict[str, str] = dc_field(
        default_factory=lambda: {
            "Online": "badge bg-success-lt",
            "Busy": "badge bg-danger-lt",
            "Offline": "badge",
        }
    )


# You are free to not use dataclasses for your custom fields, but it makes it easier to define
class AvatarNameField(StringField):
    """Renders `name` together with a circular avatar image on the list page."""

    def __init__(
        self,
        avatars_storage: LocalStorage,
        **kwargs,
    ):
        super().__init__("name", list_template="employee/avatar_name.html", **kwargs)
        self.avatars_storage = avatars_storage

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        name = await super().parse_obj(request, obj)
        avatar_key = None
        if obj.avatar is not None:
            avatar_key = obj.avatar.get("key")
        return {
            "name": name,
            "avatar_key": avatar_key,
            "initials": self._initials(name),
        }

    async def serialize_value(self, request: Request, value: Any) -> Any:
        name, avatar_key = value.get("name"), value.get("avatar_key")  # from parse_obj
        if request.state.action != RequestAction.LIST:
            return name
        if avatar_key is not None:
            value["avatar_url"] = await self.avatars_storage.url(request, avatar_key)
        return value

    @staticmethod
    def _initials(name: str) -> str:
        """Fallback shown in the avatar circle when there is no uploaded image."""
        parts = name.split()
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

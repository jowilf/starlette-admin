from typing import Any


class StarletteAdminException(Exception):
    pass


class FormValidationError(StarletteAdminException):
    def __init__(
        self,
        errors: dict[str | int, Any],
    ) -> None:
        if not isinstance(errors, dict):
            raise TypeError(f"errors must be a dict, got {type(errors).__name__!r}")

        self.errors = errors

    def has(self, name: str) -> bool:
        return self.errors.get(name, None) is not None

    def msg(self, name: str) -> Any:
        return self.errors.get(name, None)


class LoginFailed(StarletteAdminException):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


class ActionFailed(StarletteAdminException):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)
        self.msg = msg


class NotSupportedAnnotation(StarletteAdminException):
    pass


class InvalidRelationFieldError(StarletteAdminException):
    """Raised when a RelationField (HasOne/HasMany) points to a key that
    has no matching view registered on the admin instance."""


class ExportError(StarletteAdminException):
    pass

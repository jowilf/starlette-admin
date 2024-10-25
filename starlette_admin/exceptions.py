from typing import Any, Union


class StarletteAdminException(Exception):
    pass


class FormValidationError(StarletteAdminException):
    def __init__(self, errors: dict[Union[str, int], Any]) -> None:
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

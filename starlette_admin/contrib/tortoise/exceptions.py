from starlette_admin.exceptions import StarletteAdminException


class InvalidModelError(StarletteAdminException):
    pass


class NotSupportedField(StarletteAdminException):
    pass

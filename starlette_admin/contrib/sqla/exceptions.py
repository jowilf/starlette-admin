from starlette_admin.exceptions import SFAdminException


class InvalidModelError(SFAdminException):
    pass


class InvalidQuery(SFAdminException):
    pass


class NotSupportedColumn(SFAdminException):
    pass

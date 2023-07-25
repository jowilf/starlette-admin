from starlette_admin.exceptions import StarletteAdminException


class NotSupportedAnnotation(StarletteAdminException):
    pass


class NotSupportedField(StarletteAdminException):
    pass


class NotSupportedExpression(StarletteAdminException):
    pass


class EmptyExpression(StarletteAdminException):
    pass

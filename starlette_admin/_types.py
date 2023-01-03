from enum import Enum


class RequestAction(str, Enum):
    API = "API"  # For select2 request
    LIST = "LIST"
    DETAIL = "DETAIL"
    CREATE = "CREATE"
    EDIT = "EDIT"

    def is_form(self) -> bool:
        return self.value in [self.CREATE, self.EDIT]


class ExportType(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PRINT = "print"

from enum import Enum


class RequestAction(str, Enum):
    API = "API"  # For select2 request
    LIST = "LIST"
    DETAIL = "DETAIL"
    CREATE = "CREATE"
    EDIT = "EDIT"


class ExportType(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    PRINT = "print"

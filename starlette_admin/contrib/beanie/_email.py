from typing import Any, Callable, Dict, Generator

from devtools import debug  # noqa: F401
from email_validator import EmailNotValidError, validate_email


class Email(str):
    @classmethod
    def __get_validators__(cls) -> Generator[Callable, None, None]:
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(type="string", format="string", examples="user@domain.com")

    @classmethod
    def validate(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("email(string) required")

        if len(v) == 0:
            return cls(v)

        try:
            # Validate.
            valid = validate_email(v)
            # Update with the normalized form.
            email = valid.email
        except EmailNotValidError as e:
            raise TypeError(str(e)) from e

        return cls(email)

    def __repr__(self) -> str:
        return f"Email({super().__repr__()})"

from typing import Union

from devtools import debug  # noqa: F401
from phonenumbers import (
    NumberParseException,
    PhoneNumber,
    PhoneNumberFormat,
    format_number,
    is_possible_number,
    parse,
)


class Telephone(PhoneNumber):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, PhoneNumber]):
        if isinstance(v, PhoneNumber):
            return format_number(v, PhoneNumberFormat.E164)
        # is a str...
        if len(v) == 0:
            return None
        try:
            # en el caso que se ingrese un numero valido, pero por ejemplo con un caracter(letra) de mas
            # se la elimina y lo da como valido
            # ejemplo: 541165661234a es valido aunque tenga la letra 'a'
            number = parse(v, None)

        except NumberParseException as ex:
            raise ValueError(f"Invalid phone number: {v}") from ex

        if not is_possible_number(number):
            raise ValueError(f"Invalid phone number: {v}")

        return format_number(number, PhoneNumberFormat.E164)

    @classmethod
    def __modify_schema__(cls, field_schema: dict) -> None:
        field_schema.update(
            type="string",
            examples=["+541165661234"],
        )

    def json_encode(self) -> str:
        return format_number(self, PhoneNumberFormat.E164)

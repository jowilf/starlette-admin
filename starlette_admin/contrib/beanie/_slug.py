from typing import Any, Callable, Dict, Generator

from slugify import slugify


class Slug(str):
    @classmethod
    def __get_validators__(cls) -> Generator[Callable, None, None]:
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type="string", format="string", examples="this-is-a-slug")

    @classmethod
    def validate(cls, v: str) -> str:
        if not isinstance(v, str):
            raise TypeError("string required")

        return cls(slugify(v))

    def __repr__(self) -> str:
        return f"Slug({super().__repr__()})"

from slugify import slugify


class Slug(str):
    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        field_schema.update(type="string", format="string", examples="this-is-a-slug")

    @classmethod
    def validate(cls, v: str) -> dict:
        if not isinstance(v, str):
            raise TypeError("string required")

        return cls(slugify(v))

    def __repr__(self):
        return f"Slug({super().__repr__()})"

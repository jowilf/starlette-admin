import json
from typing import Dict, Union, get_args

from devtools import debug  # noqa: F401


class MyJson(str):
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
        field_schema.update(type="string", format="json-string", examples='{"key": 10}')

    @classmethod
    # con fastapi necesitaba que el campo json sea un string, para poder enviarlo
    # pero para utilizar con starlette_admin necesito que sea dict
    def validate(cls, v: Union[str, Dict]) -> dict:
        # antes..
        # if not isinstance(v, str):
        if not isinstance(v, get_args(Union[str, Dict])):
            raise TypeError("string or dict required")

        # si es un dict...
        if isinstance(v, Dict):
            return v

        # si un str....
        # ....

        # validate
        # using json.loads()
        # convert dictionary string to dictionary

        # reemplazo '(single quote) por "(double quote)
        v = v.replace("'", '"')
        if len(v) > 0:
            # parse a valid JSON string and convert it into a Python Dictionary.
            res = json.loads(v)
            if not isinstance(res, dict):
                raise TypeError("invalid my json format")
        else:
            res = {}

        # pendiente validar

        # if not m:

        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly

        return cls(res)

    def __repr__(self):
        return f"MyJson({super().__repr__()})"

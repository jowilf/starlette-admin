import json
from typing import Any, Callable, Dict, Generator, Union

from devtools import debug  # noqa: F401


class MyJson(str):
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
        field_schema.update(type="string", format="json-string", examples='{"key": 10}')

    @classmethod
    # with fastapi, I needed the json field to be a string, in order to send it from /docs
    # but to use with starlette_admin I need it to be dict
    def validate(cls, v: Union[str, Dict]) -> Union[Dict, str]:
        if not isinstance(v, (str, Dict)):
            raise TypeError("string or dict required")

        if isinstance(v, Dict):
            return v

        # replace '(single quote) with "(double quote)
        v = v.replace("'", '"')
        if len(v) > 0:
            # parse a valid JSON string and convert it into a Python Dictionary.
            try:
                res = json.loads(v)
            except ValueError as e:
                raise TypeError("invalid my json format") from e
            if not isinstance(res, dict):
                raise TypeError("invalid my json format")
        else:
            res = {}

        return cls(res)

    def __repr__(self) -> str:
        return f"MyJson({super().__repr__()})"

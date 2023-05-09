from typing import Any, List, Mapping

from beanie.operators import And, Or
from bson.son import SON
from starlette_admin.contrib.beanie.exceptions import (
    EmptyExpression,
    NotSupportedExpression,
)


class Expr:
    def __init__(self, current_field=None):
        self.query = {}
        self.new_obj = {}
        self.current_field = current_field
        self.options = {}

    def add_and(self, expression):
        self.query.setdefault("$and", []).append(_get_query(expression))
        return self

    def add_or(self, expression):
        self.query.setdefault("$or", []).append(_get_query(expression))
        return self

    def add_many_to_set(self, values):
        self._requires_current_field()
        self.new_obj.setdefault("$addToSet", {})[self.current_field] = {"$each": values}
        return self

    def add_nor(self, expression):
        self.query.setdefault("$nor", []).append(_get_query(expression))

    def add_to_set(self, value_or_expression):
        self._requires_current_field()
        self.new_obj.setdefault("$addToSet", {})[self.current_field] = _get_query(
            value_or_expression
        )

    def all(self, values):
        return self.operator("$all", list(values))

    def operator(self, operator, value):
        self._wrap_equality_criteria()
        if self.current_field:
            self.query.setdefault(self.current_field, {})[operator] = value
        else:
            self.query[operator] = value
        return self

    def _bit(self, operator, value):
        self._requires_current_field()
        self.new_obj.setdefault("$bit", {}).setdefault(self.current_field, {})[
            operator
        ] = value
        return self

    def bit_and(self, value):
        return self._bit("and", value)

    def bit_or(self, value):
        return self._bit("or", value)

    def bits_all_clear(self, value):
        self._requires_current_field()
        return self.operator("$bitsAllClear", value)

    def bits_all_set(self, value):
        self._requires_current_field()
        return self.operator("$bitsAllSet", value)

    def case_sensitive(self, case_sensitive):
        if "$text" not in self.query:
            raise RuntimeError(
                "This method requires a $text operator (call text() first)"
            )

        if case_sensitive:
            self.query["$text"]["$caseSensitive"] = True
        elif "$caseSensitive" in self.query["$text"]:
            del self.query["$text"]["$caseSensitive"]

        return self

    def comment(self, comment):
        self.query["$comment"] = comment
        return self

    def current_date(self, type="date"):
        if type not in ("date", "timestamp"):
            raise ValueError(
                'Type for current_date operator must be "date" or "timestamp".'
            )
        self._requires_current_field()
        self.new_obj.setdefault("$currentDate", {}).setdefault(self.current_field, {})[
            "$type"
        ] = type

        return self

    def each(self, values):
        return self.operator("$each", values)

    def elem_match(self, expression):
        return self.operator("$elemMatch", _get_query(expression))

    def equals(self, value):
        if self.current_field:
            self.query[self.current_field] = value
        else:
            self.query = value

        return self

    def exists(self, value=True):
        return self.operator("$exists", bool(value))

    def field(self, field):
        self.current_field = str(field)
        return self

    def gt(self, value):
        return self.operator("$gt", value)

    def gte(self, value):
        return self.operator("$gte", value)

    def lt(self, value):
        return self.operator("$lt", value)

    def lte(self, value):
        return self.operator("$lte", value)

    def is_in(self, values):
        return self.operator(
            "$in", list(values.values()) if isinstance(values, dict) else values
        )

    def is_not_in(self, values):
        return self.operator(
            "$nin", list(values.values()) if isinstance(values, dict) else values
        )

    def inc(self, value):
        self._requires_current_field()
        self.new_obj.setdefault("$inc", {})[self.current_field] = value

        return self

    def max(self, value):
        self._requires_current_field()
        self.new_obj.setdefault("$max", {})[self.current_field] = value
        return self

    def min(self, value):
        self._requires_current_field()
        self.new_obj.setdefault("$min", {})[self.current_field] = value
        return self

    def mul(self, value):
        self._requires_current_field()
        self.new_obj.setdefault("$mul", {})[self.current_field] = value
        return self

    def is_not(self, expression):
        return self.operator("$not", _get_query(expression))

    def not_equals(self, value):
        return self.ne(value)

    def ne(self, value):
        return self.operator("$ne", value)

    def text(
        self, search, language=None, case_sensitive=False, diacritic_sensitive=False
    ):
        search_expression = {
            "$search": search,
            "$language": language,
            "$caseSensitive": bool(case_sensitive),
            "$diacriticSensitive": bool(diacritic_sensitive),
        }

        if search_expression["$language"] is None:
            # We need to exclude the property to force mongo to use it's default.
            del search_expression["$language"]

        return self.operator("$text", search_expression)

    def search(
        self, search, language=None, case_sensitive=False, diacritic_sensitive=False
    ):
        return self.text(
            search=search,
            language=language,
            case_sensitive=case_sensitive,
            diacritic_sensitive=diacritic_sensitive,
        )

    def null(self):
        return self.equals(None)

    def not_null(self):
        return self.ne(None)

    def pop_first(self):
        self._requires_current_field()
        self.new_obj.setdefault("$pop", {})[self.current_field] = 1
        return self

    def pop_last(self):
        self._requires_current_field()
        self.new_obj.setdefault("$pop", {})[self.current_field] = -1
        return self

    def position(self, position):
        return self.operator("$position", position)

    def pull(self, value_or_expression):
        self._requires_current_field()
        self.new_obj.setdefault("$pull", {})[self.current_field] = _get_query(
            value_or_expression
        )
        return self

    def pull_all(self, values):
        self._requires_current_field()
        self.new_obj.setdefault("$pullAll", {})[self.current_field] = values
        return self

    def push(self, value_or_expression):
        if isinstance(value_or_expression, Expr):
            value_or_expression = value_or_expression.get_query()
            value_or_expression.setdefault("$each", [])

        self._requires_current_field()
        self.new_obj.setdefault("$push", {})[self.current_field] = value_or_expression
        return self

    def push_all(self, values):
        self._requires_current_field()
        self.new_obj.setdefault("$pushAll", {})[self.current_field] = values
        return self

    def range(self, start, end):
        return self.operator("$gte", start).operator("$lt", end)

    def regex(self, pattern, options="i"):
        return self.operator("$regex", pattern).operator("$options", options)

    def rename(self, name):
        self._requires_current_field()
        self.new_obj.setdefault("$rename", {})[self.current_field] = name

        return self

    def set(self, value, atomic=True):
        self._requires_current_field()
        if atomic:
            self.new_obj.setdefault("$set", {})[self.current_field] = value
            return self

        if "." not in self.current_field:
            self.new_obj[self.current_field] = value
            return self

        keys = self.current_field.split(".")
        current = self.new_obj
        for key in keys[:-1]:
            current = current[key]
        current[keys[-1]] = value

        return self

    def set_on_insert(self, value):
        self._requires_current_field()
        self.new_obj.setdefault("$setOnInsert", {})[self.current_field] = value

        return self

    def size(self, size):
        return self.operator("$size", size)

    def slice(self, size):
        return self.operator("$slice", size)

    def is_type(self, type):
        if isinstance(type, str):
            type = type.lower()
            _map = {
                "double": 1,
                "string": 2,
                "object": 3,
                "array": 4,
                "binary": 5,
                "undefined": 6,
                "objectid": 7,
                "boolean": 8,
                "date": 9,
                "null": 10,
                "regex": 11,
                "jscode": 13,
                "symbol": 14,
                "jscodewithscope": 15,
                "integer32": 16,
                "timestamp": 17,
                "integer64": 18,
                "maxkey": 127,
                "minkey": 255,
            }

            type = _map[type] if type in _map else type

        return self.operator("$type", type)

    def unset_field(self):
        self._requires_current_field()
        self.new_obj.setdefault("$unset", {})[self.current_field] = 1

        return self

    def where(self, javascript):
        self.query["$where"] = javascript

        return self

    def get_query(self):
        return self.query

    def _requires_current_field(self):
        if not self.current_field:
            raise RuntimeError(
                "This method requires you set a current field using field()."
            )

    def _wrap_equality_criteria(self):
        if self.current_field and (
            self.current_field not in self.query or not self.query[self.current_field]
        ):
            # If the current field has no criteria yet, do nothing.
            # This ensures that we do not inadvertently inject {"$in": null} into the query.
            return

        query = self.query[self.current_field] if self.current_field else self.query

        if isinstance(query, (dict, SON)) and (
            not query or list(query.keys())[0][0] == "$"
        ):
            # Don't do anything if we already have a query dictionary
            # and it's either empty or already a "query" dictionary.
            # We can assume this when "$" is the first character of the first key.
            return

        if self.current_field:
            self.query[self.current_field] = {"$in": [self.query[self.current_field]]}
        else:
            self.query = {"$in": [self.query]}


def _get_query(expr):
    if isinstance(expr, Expr):
        return expr.get_query()
    return expr


class Expression:
    field_name: str
    exp: str
    value: str

    def __init__(self, field_name: str, exp: str, value: str):
        self.field_name = field_name
        self.exp = exp
        self.value = value


class Where:
    op: str
    expression: List[Expression] = []
    data: Any

    def __init__(self, data):
        self.data = data
        self.init()

    def init(self):
        self.expression = []
        for k, v in self.data.items():
            self.op = k
            for q in v:
                for field_name, expression in q.items():
                    for ke, ve in expression.items():
                        self.expression.append(
                            Expression(field_name=field_name, exp=ke, value=ve)
                        )

    def builder(self) -> Mapping[str, Any]:
        if len(self.expression) == 0:
            raise EmptyExpression("Expression empty")

        regex_map = {
            "contains": ("regex", "VALUE"),
            "not_contains": ("regex", r"^((?!{VALUE}).)*$"),
            "startswith": ("regex", r"^{VALUE}"),
            "not_startswith": ("regex", r"^(?!{VALUE})"),
            "not_endswith": ("regex", r"^(?!.*{VALUE}$).*"),
            "eq": ("equals", "VALUE"),
            "neq": ("not_equals", "VALUE"),
            "is_null": ("null", None),
            "is_not_null": ("not_null", None),
        }

        t = []
        for item in self.expression:
            k = globals()["Expr"](current_field=item.field_name)
            func = getattr(k, regex_map[item.exp][0])
            if regex_map[item.exp][1] is not None:
                args = str(regex_map[item.exp][1]).replace("VALUE", item.value)
                t.append(func(args).get_query())
            else:
                t.append(func().get_query())

        if self.op == "or":
            r = Or(*t)
        elif self.op == "and":
            r = And(*t)
        else:
            # raise
            raise NotSupportedExpression(f"Expression {self.op} is not supported")

        return r

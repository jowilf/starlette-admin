from typing import Any, Dict

comparison_map = {
    "eq": "$eq",
    "neq": "$ne",
    "ge": "$gte",
    "gt": "$gt",
    "le": "$lte",
    "lt": "$lt",
    "in": "$in",
    "not_in": "$nin",
}


def build_raw_query(dt_query: Dict[str, Any]) -> Dict[str, Any]:
    raw_query: Dict[str, Any] = dict()
    for key in dt_query:
        if key == "or":
            raw_query["$or"] = [build_raw_query(q) for q in dt_query[key]]
        elif key == "and":
            raw_query["$and"] = [build_raw_query(q) for q in dt_query[key]]
        elif key == "not":
            raw_query["$not"] = build_raw_query(dt_query[key])
        elif key == "between":
            values = dt_query[key]
            raw_query = {"$gte": values[0], "$lte": values[1]}
        elif key == "not_between":
            values = dt_query[key]
            raw_query = {"$not": {"$gte": values[0], "$lte": values[1]}}
        elif key == "contains":
            raw_query = {"$regex": dt_query[key], "$options": "mi"}
        elif key == "startsWith":
            raw_query = {"$regex": "^%s" % dt_query[key], "$options": "mi"}
        elif key == "endsWith":
            raw_query = {"$regex": "%s$" % dt_query[key], "$options": "mi"}
        elif key in comparison_map:
            raw_query[comparison_map[key]] = dt_query[key]
        else:
            raw_query[key] = build_raw_query(dt_query[key])
    return raw_query

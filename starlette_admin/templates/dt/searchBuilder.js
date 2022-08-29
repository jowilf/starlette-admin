function extractCriteria(c) {
console.log(c);
  var d = {};
  if ((c.logic && c.logic == "OR") || c.logic == "AND") {
    d[c.logic.toLowerCase()] = [];
    c.criteria.forEach((v) => {
      d[c.logic.toLowerCase()].push(extractCriteria(v));
    });
  } else {
    if (c.type.startsWith("moment-")) {
      search_format = columns[c.origData].search_format;
      if (!search_format) search_format = moment.defaultFormat;
      c.value = [];
      if (c.value1) {
        c.value1 = moment(c.value1).format(search_format);
        c.value.push(c.value1);
      }
      if (c.value2) {
        c.value2 = moment(c.value2).format(search_format);
        c.value.push(c.value2);
      }
    } else if (c.type == "num") {
      c.value = [];
      if (c.value1) {
        c.value1 = Number(c.value1);
        c.value.push(c.value1);
      }
      if (c.value2) {
        c.value2 = Number(c.value2);
        c.value.push(c.value2);
      }
    }
    cnd = {};
    c_map = {
      "=": "eq",
      "!=": "neq",
      ">": "gt",
      ">=": "ge",
      "<": "lt",
      "<=": "le",
      contains: "contains",
      starts: "startsWith",
      ends: "endsWith",
    };
    if (c.condition == "between") {
      cnd["between"] = c.value;
    } else if (c.condition == "!between") {
      cnd["not_between"] = c.value;
    } else if (c.condition == "!starts") {
      cnd["not"] = { startsWith: c.value1 };
    } else if (c.condition == "!ends") {
      cnd["not"] = { endsWith: c.value1 };
    } else if (c.condition == "!contains") {
      cnd["not"] = { contains: c.value1 };
    } else if (c.condition == "null") {
      cnd["eq"] = null;
    } else if (c.condition == "!null") {
      cnd["neq"] = null;
    } else if (c.condition == "false") {
      cnd["eq"] = false;
    } else if (c.condition == "true") {
      cnd["eq"] = true;
    } else if (c_map[c.condition]) {
      cnd[c_map[c.condition]] = c.value1;
    }
    d[c.origData] = cnd;
  }
  return d;
}

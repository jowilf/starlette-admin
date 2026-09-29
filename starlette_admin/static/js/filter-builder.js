/**
 * Drive the `_filter_builder.html` panel: build/edit a filter tree of leaf
 * rows and arbitrarily-nested AND/OR groups as plain DOM, pre-fill it from
 * the current `filter` query param when possible, and serialise the tree
 * into the hidden `filter-json` input as a human-readable filter string
 * (inspired by Django's field lookup syntax) such as
 * `name__contains=john AND (age__gte=25 OR verified__is_true)` before the
 * form submits — a standard GET navigation.
 *
 * Format rules:
 *   - Leaf (no value):  `field__op`
 *   - Leaf (value):     `field__op=value`
 *   - Between:          `field__op=val..val2`
 *   - Enum multi-val:   `field__op=v1,v2,v3`
 *   - Quoted value:     `field__op="value with spaces"` (mandatory when the
 *     value contains spaces, commas, parens, `..`, or `"`).
 *   - Group:            `(rule1 AND rule2)` — top-level group has no outer parens.
 *
 * @param {Object} config
 * @param {Array<Object>} config.fields - `[{name, label, choices?, filters: [{name, label, data_type, has_value2, choices?}]}]`,
 *   the fields that have at least one available filter and the filters available for each.
 *   `choices` (`[[value, label], ...]`) is present on a field for enum fields, and on an
 *   individual filter for filters that supply their own dropdown (e.g. an "is one of" filter
 *   over a relation); a filter's own `choices` take precedence over its field's.
 *   `relation` (`{url, pk}`) is present on relation fields (`HasOne`/`HasMany`): the foreign
 *   view's `relation-lookup` API URL and primary key attribute, used by `data_type: "relation"`
 *   filters to render a searchable Select2 record picker whose value is a list of primary keys.
 * @param {?string} config.initialFilter - the current `filter` query param value, or `null`.
 */
function initFilterBuilder(config) {
  if (!config.fields.length) return;

  let $rows = $('[data-sa-hook="filter-rows"]');
  let $rootLogic = $('[data-sa-hook="filter-root-logic"]');
  let rowTemplate = document.querySelector('[data-sa-hook="filter-row-template"]');
  let groupTemplate = document.querySelector('[data-sa-hook="filter-group-template"]');
  let $form = $('[data-sa-hook="filter-form"]');
  let $jsonInput = $('[data-sa-hook="filter-json"]');

  function fieldByName(name) {
    return config.fields.find(function (f) {
      return f.name === name;
    });
  }

  function filterByName(field, name) {
    return field
      ? field.filters.find(function (f) {
          return f.name === name;
        })
      : null;
  }

  function choicesFor(field, op) {
    if (op && Array.isArray(op.choices) && op.choices.length > 0) return op.choices;
    if (field && Array.isArray(field.choices) && field.choices.length > 0) return field.choices;
    return null;
  }

  function inputTypeFor(dataType) {
    return (
      { number: "number", date: "date", datetime: "datetime-local", time: "time" }[
        dataType
      ] || "text"
    );
  }

  function isGroupNode(node) {
    return (
      node &&
      typeof node === "object" &&
      !Array.isArray(node) &&
      ("logic" in node || "rules" in node)
    );
  }

  // ── Value quoting / unquoting ─────────────────────────────────────────────

  function quoteValue(v) {
    if (/[ ()\t,"]|\.\./.test(v)) {
      return '"' + v.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
    }
    return v;
  }

  function unquoteValue(v) {
    if (v.length >= 2 && v[0] === '"' && v[v.length - 1] === '"') {
      return v.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, "\\");
    }
    return v;
  }

  function findSepOutsideQuotes(s, sep) {
    let inQ = false;
    for (let i = 0; i < s.length; i++) {
      if (s[i] === '"') {
        inQ = !inQ;
        continue;
      }
      if (!inQ && s.slice(i, i + sep.length) === sep) return i;
    }
    return -1;
  }

  function splitCommasOutsideQuotes(s) {
    let parts = [],
      cur = "",
      inQ = false;
    for (let i = 0; i < s.length; i++) {
      if (s[i] === '"') {
        inQ = !inQ;
        cur += s[i];
        continue;
      }
      if (!inQ && s[i] === ",") {
        parts.push(cur);
        cur = "";
        continue;
      }
      cur += s[i];
    }
    parts.push(cur);
    return parts;
  }

  // ── Serialization: DOM tree → filter string ──────────────────────────────

  function serializeRow($row) {
    let field = fieldByName($row.find('[data-sa-hook="filter-row-field"]').val());
    let op = filterByName(field, $row.find('[data-sa-hook="filter-row-op"]').val());
    if (!field || !op) return null;

    let base = field.name + "__" + op.name;
    if (op.data_type === "none") return base;

    let hasChoices = !!choicesFor(field, op);
    if (op.data_type === "relation") {
      let vals = $row.find('[data-sa-hook="filter-row-value-relation"]').val() || [];
      if (!vals.length) return null;
      return base + "=" + vals.map(quoteValue).join(",");
    } else if (op.data_type === "array") {
      let vals = $row.find('[data-sa-hook="filter-row-value-tags"]').val() || [];
      if (!vals.length) return null;
      return base + "=" + vals.map(quoteValue).join(",");
    } else if (hasChoices) {
      if (op.data_type === "enum") {
        let selected = $row.find('[data-sa-hook="filter-row-value-select"]').val() || [];
        if (!selected.length) return null;
        return base + "=" + selected.map(quoteValue).join(",");
      } else {
        let selected = $row.find('[data-sa-hook="filter-row-value-select"]').val();
        if (!selected) return null;
        return base + "=" + quoteValue(selected);
      }
    } else {
      let raw = $row.find('[data-sa-hook="filter-row-value"]').val().trim();
      if (!raw) return null;
      if (op.has_value2) {
        let raw2 = $row.find('[data-sa-hook="filter-row-value2"]').val().trim();
        if (!raw2) return null;
        return base + "=" + quoteValue(raw) + ".." + quoteValue(raw2);
      }
      return base + "=" + quoteValue(raw);
    }
  }

  function serializeGroup($group) {
    let logic = $group.data("filterLogic").val().toUpperCase();
    let parts = serializeChildren($group.data("filterChildren"));
    return parts.length ? "(" + parts.join(" " + logic + " ") + ")" : null;
  }

  function serializeChildren($children) {
    let parts = [];
    $children.children().each(function () {
      let $el = $(this);
      let part = $el.is('[data-sa-hook="filter-group"]') ? serializeGroup($el) : serializeRow($el);
      if (part) parts.push(part);
    });
    return parts;
  }

  // ── Parsing: filter string → {logic,rules} / {field,filter,value,value2} ──

  function parseFilterString(str) {
    let pos = 0;

    function skipWS() {
      while (pos < str.length && /\s/.test(str[pos])) pos++;
    }

    function peekKeyword() {
      skipWS();
      let rest = str.slice(pos).toUpperCase();
      if (/^AND(?:\s|$|\))/.test(rest)) return "AND";
      if (/^OR(?:\s|$|\))/.test(rest)) return "OR";
      return null;
    }

    function readLeafToken() {
      skipWS();
      let result = "",
        inValue = false;
      while (pos < str.length) {
        let ch = str[pos];
        if (ch === "=") {
          result += ch;
          pos++;
          inValue = true;
          continue;
        }
        if (!inValue && /[\s()]/.test(ch)) break;
        if (inValue && /[\s)]/.test(ch)) break;
        if (inValue && ch === '"') {
          result += ch;
          pos++;
          while (pos < str.length && str[pos] !== '"') {
            if (str[pos] === "\\" && pos + 1 < str.length) result += str[pos++];
            result += str[pos++];
          }
          if (pos < str.length) {
            result += str[pos++];
          }
          continue;
        }
        result += ch;
        pos++;
      }
      return result;
    }

    function parseLeafToken(token) {
      let eqIdx = token.indexOf("=");
      let key = eqIdx === -1 ? token : token.slice(0, eqIdx);
      let valueStr = eqIdx === -1 ? null : token.slice(eqIdx + 1);

      let dunderIdx = key.lastIndexOf("__");
      if (dunderIdx === -1) return null;
      let fieldName = key.slice(0, dunderIdx);
      let opName = key.slice(dunderIdx + 2);

      let fieldDef = fieldByName(fieldName);
      if (!fieldDef) return null;
      let opDef = filterByName(fieldDef, opName);
      if (!opDef) return null;

      let rule = { field: fieldName, filter: opName };
      if (valueStr !== null && opDef.data_type !== "none") {
        if (opDef.has_value2) {
          let sepIdx = findSepOutsideQuotes(valueStr, "..");
          if (sepIdx !== -1) {
            rule.value = unquoteValue(valueStr.slice(0, sepIdx));
            rule.value2 = unquoteValue(valueStr.slice(sepIdx + 2));
          } else {
            rule.value = unquoteValue(valueStr);
          }
        } else if (
          opDef.data_type === "enum" ||
          opDef.data_type === "array" ||
          opDef.data_type === "relation"
        ) {
          rule.value = splitCommasOutsideQuotes(valueStr).map(unquoteValue);
        } else {
          rule.value = unquoteValue(valueStr);
        }
      }
      return rule;
    }

    function parseTerm() {
      skipWS();
      if (pos >= str.length) return null;
      if (str[pos] === "(") {
        pos++;
        let group = parseGroup();
        skipWS();
        if (pos < str.length && str[pos] === ")") pos++;
        return group;
      }
      if (peekKeyword()) return null;
      let token = readLeafToken();
      return token ? parseLeafToken(token) : null;
    }

    function parseGroup() {
      let terms = [],
        logic = "and";
      let term = parseTerm();
      if (!term) return { logic: "and", rules: [] };
      terms.push(term);
      while (true) {
        skipWS();
        let kw = peekKeyword();
        if (!kw) break;
        logic = kw.toLowerCase();
        pos += kw.length;
        let t = parseTerm();
        if (!t) break;
        terms.push(t);
      }
      return terms.length === 1 ? terms[0] : { logic: logic, rules: terms };
    }

    try {
      skipWS();
      let result = parseGroup();
      return result;
    } catch (e) {
      return null;
    }
  }

  // ── Select2 tags initialisation ───────────────────────────────────────────

  function maybeInitTagsInput($el) {
    if ($el.data("s2")) return;
    let prefill = $el.data("filterPrefill") || [];
    prefill.forEach(function (v) {
      $el.append(new Option(v, v, true, true));
    });
    $el.data("s2", true).select2({ tags: true, tokenSeparators: [","], width: "100%" });
  }

  // ── Select2 relation record picker ────────────────────────────────────────

  function relationSelectionHtml(item) {
    if (item._meta && item._meta.select2) return $(item._meta.select2.selection);
    let html = item.element ? $(item.element).data("selectionHtml") : null;
    if (html) return $(html);
    return item.text;
  }

  /**
   * Turn the row's relation `<select multiple>` into an AJAX Select2 backed
   * by the foreign view's `relation-lookup` API (same endpoint and response
   * format as the relation widget in forms, see `form.js`). Values are the
   * related records' primary keys. Keys prefilled from the URL are shown
   * raw first and then swapped for their rendered labels once resolved.
   */
  function maybeInitRelationInput($el, field) {
    if ($el.data("s2") || !field || !field.relation) return;
    let rel = field.relation;
    let $parent = $el.closest(".dropdown-menu");
    $el.data("s2", true).select2({
      width: "100%",
      dropdownParent: $parent.length ? $parent : $(document.body),
      ajax: {
        url: rel.url,
        dataType: "json",
        delay: 250,
        data: function (params) {
          return { skip: ((params.page || 1) - 1) * 20, limit: 20, q: params.term };
        },
        processResults: function (data, params) {
          return {
            results: $.map(data.items, function (obj) {
              obj.id = String(obj[rel.pk]);
              return obj;
            }),
            pagination: { more: (params.page || 1) * 20 < data.total },
          };
        },
        cache: true,
      },
      minimumInputLength: 0,
      templateResult: function (item) {
        if (item.loading || !item._meta) return item.text;
        return $(item._meta.select2.result);
      },
      templateSelection: relationSelectionHtml,
    });

    let prefill = ($el.data("filterPrefill") || []).map(String);
    if (!prefill.length) return;
    prefill.forEach(function (v) {
      $el.append(new Option(v, v, true, true));
    });
    $el.trigger("change");
    let sep = rel.url.indexOf("?") === -1 ? "?" : "&";
    $.ajax({ url: rel.url + sep + $.param({ pks: prefill }, true), dataType: "json" }).then(
      function (data) {
        (data.items || []).forEach(function (obj) {
          let id = String(obj[rel.pk]);
          $el.find("option").each(function () {
            if (this.value === id) {
              $(this).data("selectionHtml", obj._meta.select2.selection);
            }
          });
        });
        $el.trigger("change");
      }
    );
  }

  function destroyRelationInput($el) {
    if ($el.data("s2")) $el.select2("destroy").removeData("s2");
    $el.empty();
  }

  // ── DOM creation ──────────────────────────────────────────────────────────

  function createRow(initial) {
    let $row = $(rowTemplate.content.cloneNode(true)).find('[data-sa-hook="filter-row"]');
    let $field = $row.find('[data-sa-hook="filter-row-field"]');
    let $op = $row.find('[data-sa-hook="filter-row-op"]');
    let $value = $row.find('[data-sa-hook="filter-row-value"]');
    let $valueSelect = $row.find('[data-sa-hook="filter-row-value-select"]');
    let $valueTags = $row.find('[data-sa-hook="filter-row-value-tags"]');
    let $valueRelation = $row.find('[data-sa-hook="filter-row-value-relation"]');
    let $value2 = $row.find('[data-sa-hook="filter-row-value2"]');

    config.fields.forEach(function (f) {
      $field.append($("<option>").val(f.name).text(f.label));
    });

    function populateSelect(choices) {
      $valueSelect.empty();
      (choices || []).forEach(function (choice) {
        $valueSelect.append($("<option>").val(choice[0]).text(choice[1]));
      });
    }

    function syncValueInputs() {
      let field = fieldByName($field.val());
      let op = filterByName(field, $op.val());
      let dataType = op ? op.data_type : "string";
      let inputType = inputTypeFor(dataType);
      let choices = choicesFor(field, op);
      let hasChoices = !!choices;
      let isNone = op && dataType === "none";
      let isArray = dataType === "array";
      let isRelation = dataType === "relation" && !!(field && field.relation);
      let showSelect = hasChoices && !isNone && !isArray && !isRelation;
      let showTags = isArray && !isNone;
      // Different filters on the same field can carry different `choices`
      // (e.g. `department_contains` has none while `department_in` lists
      // every department), so the select must be repopulated on every op
      // change, not just when the field itself changes.
      populateSelect(choices);
      // `.toggleClass`, not `.toggle()`/`.show()`/`.hide()`: jQuery's
      // show/hide path dereferences `ownerDocument.documentElement`, which is
      // `null` for elements still inside cloned `<template>` content (its
      // owner is an inert "template contents" document with no <html>) — and
      // `createRow` may run this before the row is appended to the live DOM.
      $value
        .attr("type", inputType)
        .attr("step", inputType === "number" ? "any" : null)
        .toggleClass("d-none", showSelect || isNone || showTags || isRelation);
      $valueSelect
        .prop("multiple", dataType === "enum")
        .toggleClass("d-none", !showSelect);
      $valueTags.toggleClass("d-none", !showTags);
      $valueRelation.toggleClass("d-none", !isRelation);
      if (isRelation) {
        // Defer init so Select2 runs after the row is appended to the live DOM.
        setTimeout(function () {
          if (
            !$valueRelation.hasClass("d-none") &&
            document.body &&
            document.body.contains($valueRelation[0])
          ) {
            maybeInitRelationInput($valueRelation, fieldByName($field.val()));
          }
        }, 0);
      } else if ($valueRelation.data("s2")) {
        destroyRelationInput($valueRelation);
      }
      if (showTags) {
        // Defer init so Select2 runs after the row is appended to the live DOM.
        setTimeout(function () {
          if (!$valueTags.hasClass("d-none") && document.body && document.body.contains($valueTags[0])) {
            maybeInitTagsInput($valueTags);
          }
        }, 0);
      } else if ($valueTags.data("s2")) {
        // Tear down Select2 when the tags input is hidden; otherwise its
        // generated container stays in the DOM as a sibling of the hidden
        // <select> and keeps showing after the user switches field/op.
        $valueTags.select2("destroy").removeData("s2");
      }
      $value2
        .attr("type", inputType)
        .attr("step", inputType === "number" ? "any" : null)
        .toggleClass("d-none", !(op && op.has_value2));
    }

    function syncOps(selectedOp) {
      $op.empty();
      let field = fieldByName($field.val());
      (field || { filters: [] }).filters.forEach(function (op) {
        $op.append($("<option>").val(op.name).text(op.label));
      });
      if (selectedOp) $op.val(selectedOp);
      syncValueInputs();
    }

    $field.on("change", function () {
      // Each relation field looks up a different foreign view, so the
      // record picker must be rebuilt (not reused) for the new field.
      $valueRelation.removeData("filterPrefill");
      destroyRelationInput($valueRelation);
      syncOps(null);
      $value.val("");
      $valueSelect.val([]);
      // Clear the tags select so its state doesn't leak when the user
      // switches to another field. Use Select2's API when active.
      if ($valueTags.data("s2")) {
        $valueTags.val(null).trigger("change");
      } else {
        $valueTags.val([]).empty();
      }
      $value2.val("");
    });
    $op.on("change", syncValueInputs);
    $row.find('[data-sa-action="filter-row-remove"]').on("click", function () {
      $row.remove();
    });

    if (initial && typeof initial === "object") {
      $field.val(initial.field);
      syncOps(initial.filter);
      let field = fieldByName(initial.field);
      let op = filterByName(field, initial.filter);
      let dataType = op ? op.data_type : "string";
      let hasChoices = !!choicesFor(field, op);
      if (dataType === "relation") {
        let vals = initial.value == null ? [] : (Array.isArray(initial.value) ? initial.value : [initial.value]);
        $valueRelation.data("filterPrefill", vals);
      } else if (dataType === "array") {
        let vals = initial.value == null ? [] : (Array.isArray(initial.value) ? initial.value : [initial.value]);
        $valueTags.data("filterPrefill", vals);
      } else if (hasChoices) {
        $valueSelect.val(initial.value == null ? [] : initial.value);
      } else {
        $value.val(initial.value == null ? "" : initial.value);
      }
      $value2.val(initial.value2 == null ? "" : initial.value2);
    } else {
      syncOps(null);
    }

    return $row;
  }

  function createGroup(initial) {
    let $group = $(groupTemplate.content.cloneNode(true)).find('[data-sa-hook="filter-group"]');
    // Captured here, before any child group is appended, so these references
    // unambiguously stay this group's own — `.find()` would otherwise also
    // match nested groups' `filter-group-logic`/`filter-group-children` hooks.
    let $logic = $group.find('[data-sa-hook="filter-group-logic"]').first();
    let $children = $group.find('[data-sa-hook="filter-group-children"]').first();
    $group.data("filterLogic", $logic);
    $group.data("filterChildren", $children);

    $logic.val(initial && initial.logic === "or" ? "or" : "and");

    $group.find('[data-sa-action="filter-group-add-row"]').on("click", function () {
      $children.append(createRow(null));
    });
    $group.find('[data-sa-action="filter-group-add-group"]').on("click", function () {
      $children.append(createGroup(null));
    });
    $group.find('[data-sa-action="filter-group-remove"]').on("click", function () {
      $group.remove();
    });

    if (initial && Array.isArray(initial.rules)) {
      initial.rules.forEach(function (rule) {
        $children.append(isGroupNode(rule) ? createGroup(rule) : createRow(rule));
      });
    }

    return $group;
  }

  // ── Prefill from URL ──────────────────────────────────────────────────────

  /**
   * Rebuild the whole tree — leaf rows and arbitrarily-nested AND/OR groups —
   * from the current `filter` query param string, so editing a hand-built or
   * previously-applied nested filter works the same way a flat one always did.
   */
  function prefill() {
    if (!config.initialFilter) return false;

    let data = parseFilterString(config.initialFilter);
    if (!data) return false;

    let logic = "and";
    let rules;
    if (isGroupNode(data)) {
      logic = data.logic === "or" ? "or" : "and";
      rules = data.rules;
    } else {
      rules = [data];
    }
    if (!Array.isArray(rules) || !rules.length) return false;

    $rootLogic.val(logic);
    rules.forEach(function (rule) {
      $rows.append(isGroupNode(rule) ? createGroup(rule) : createRow(rule));
    });
    return true;
  }

  $('[data-sa-action="add-filter-row"]').on("click", function () {
    $rows.append(createRow(null));
  });
  $('[data-sa-action="add-filter-group"]').on("click", function () {
    $rows.append(createGroup(null));
  });

  if (!prefill()) $rows.append(createRow(null));

  // Init Select2 tags on any array-type rows that were built from the prefill
  // tree (their containers were not live during createRow, so syncValueInputs
  // couldn't init them inline).
  $rows.find('[data-sa-hook="filter-row-value-tags"]:not(.d-none)').each(function () {
    maybeInitTagsInput($(this));
  });

  $form.on("submit", function () {
    let parts = serializeChildren($rows);
    let logic = $rootLogic.val().toUpperCase();
    $jsonInput.prop("disabled", parts.length === 0);
    if (parts.length) {
      $jsonInput.val(parts.join(" " + logic + " "));
    }
  });
}

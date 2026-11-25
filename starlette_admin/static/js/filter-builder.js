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
  let $dropdown = $form.closest(".dropdown");
  let $dropdownMenu = $form.closest(".dropdown-menu");
  let s2Interacting = false;

  // Select2 dropdowns (for enum and tags filters) attach to document.body
  // so they are never clipped by `.dropdown-menu`'s `overflow-y: auto`.
  // Selecting an option or removing a chip can mutate/detach the target node
  // before Bootstrap's `autoClose="outside"` click handler runs, so track
  // mousedown inside Select2 and keep the filter dropdown open.
  function hasOpenSelect2() {
    return $rows.find(".select2-container--open").length > 0;
  }

  function closeOpenSelect2() {
    $rows.find("select.select2-hidden-accessible").each(function () {
      if ($(this).data("s2")) $(this).select2("close");
    });
  }

  function clearS2Interacting() {
    if (!s2Interacting) return;
    setTimeout(function () {
      s2Interacting = false;
    }, 0);
  }

  $(document)
    .off(".saFilterS2")
    .on(
      "mousedown.saFilterS2",
      "#filter-builder-dropdown .select2-container, .sa-filter-s2-dropdown",
      function (e) {
        if ((e.button && e.button !== 0) || !$dropdownMenu.hasClass("show")) return;
        s2Interacting = true;
      }
    )
    .on("mouseup.saFilterS2", clearS2Interacting);
  $(window).off(".saFilterS2").on("blur.saFilterS2", clearS2Interacting);

  // Intercept Escape on `window` in the capture phase (before Bootstrap 5's
  // `document` capture listener) so:
  // 1. Pressing Escape while a Select2 dropdown is open closes ONLY Select2
  //    (leaving the filter builder menu open, e.g. to click "Apply filters"),
  //    even when focus has moved to document.body after clicking an option.
  // 2. The matching Escape keyup never reaches Select2 4.1.0's inline-search
  //    `keyup.search` listener (which omits ESC from its ignore list and would
  //    otherwise immediately re-open the dropdown).
  if (window._saFilterS2Keydown) {
    window.removeEventListener("keydown", window._saFilterS2Keydown, true);
  }
  if (window._saFilterS2Keyup) {
    window.removeEventListener("keyup", window._saFilterS2Keyup, true);
  }
  window._saFilterS2Keydown = function (e) {
    if (e.key === "Escape" && $dropdownMenu.hasClass("show") && hasOpenSelect2()) {
      e.preventDefault();
      e.stopImmediatePropagation();
      closeOpenSelect2();
    }
  };
  window._saFilterS2Keyup = function (e) {
    if (
      e.key === "Escape" &&
      $dropdownMenu.hasClass("show") &&
      $(e.target).closest(".select2-search--inline").length
    ) {
      e.stopPropagation();
    }
  };
  window.addEventListener("keydown", window._saFilterS2Keydown, true);
  window.addEventListener("keyup", window._saFilterS2Keyup, true);

  $dropdown.on("hide.bs.dropdown", function (e) {
    if (
      s2Interacting ||
      (e.clickEvent &&
        $(e.clickEvent.target).closest(
          "#filter-builder-dropdown .select2-container, .sa-filter-s2-dropdown"
        ).length)
    ) {
      e.preventDefault();
      return;
    }
    closeOpenSelect2();
  });

  $dropdownMenu.on("scroll", closeOpenSelect2);

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
    if (op.data_type === "array") {
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
        } else if (opDef.data_type === "enum" || opDef.data_type === "array") {
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

  // ── Select2 helpers ───────────────────────────────────────────────────────

  function destroySelect2($el) {
    if ($el.data("s2")) {
      $el.select2("destroy").removeData("s2");
    }
  }

  function destroySelect2In($container) {
    $container.find("select.select2-hidden-accessible").each(function () {
      destroySelect2($(this));
    });
  }

  function maybeInitTagsInput($el) {
    if ($el.data("s2") || !$.fn.select2) return;
    let prefill = $el.data("filterPrefill") || [];
    $el.removeData("filterPrefill");
    prefill.forEach(function (v) {
      $el.append(new Option(v, v, true, true));
    });
    $el.data("s2", true).select2({
      tags: true,
      tokenSeparators: [","],
      width: "100%",
      dropdownParent: $(document.body),
      dropdownCssClass: "sa-filter-s2-dropdown",
    });
  }

  function maybeInitEnumSelect($el) {
    if ($el.data("s2") || !$.fn.select2) return;
    $el.data("s2", true).select2({
      width: "100%",
      dropdownParent: $(document.body),
      closeOnSelect: false,
      dropdownCssClass: "sa-filter-s2-dropdown sa-filter-enum-dropdown",
    });
  }

  function initSelect2In($container) {
    $container.find('[data-sa-hook="filter-row-value-tags"]:not(.d-none)').each(function () {
      maybeInitTagsInput($(this));
    });
    $container
      .find('[data-sa-hook="filter-row-value-select"]:not(.d-none)')
      .filter(function () {
        return this.multiple;
      })
      .each(function () {
        maybeInitEnumSelect($(this));
      });
  }

  // ── DOM creation ──────────────────────────────────────────────────────────

  function createRow(initial) {
    let $row = $(rowTemplate.content.cloneNode(true)).find('[data-sa-hook="filter-row"]');
    let $field = $row.find('[data-sa-hook="filter-row-field"]');
    let $op = $row.find('[data-sa-hook="filter-row-op"]');
    let $value = $row.find('[data-sa-hook="filter-row-value"]');
    let $valueSelect = $row.find('[data-sa-hook="filter-row-value-select"]');
    let $valueTags = $row.find('[data-sa-hook="filter-row-value-tags"]');
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
      let showSelect = hasChoices && !isNone && !isArray;
      let showMultiEnum = showSelect && dataType === "enum";
      let showTags = isArray && !isNone;
      let wasMultiEnum = $valueSelect.prop("multiple");
      let prevEnumVals = wasMultiEnum && showMultiEnum ? $valueSelect.val() || [] : [];

      if (!showMultiEnum) {
        // Tear down Select2 before flipping `multiple` or hiding the <select>;
        // otherwise its generated container stays visible as a sibling and
        // Select2 wouldn't switch cleanly back to single-select mode.
        destroySelect2($valueSelect);
      }

      // Set `multiple` before populating options: in non-multiple mode the
      // browser auto-selects option 0, which would otherwise leak as an
      // unwanted selection once `multiple` is enabled.
      $valueSelect.prop("multiple", showMultiEnum);

      // Different filters on the same field can carry different `choices`
      // (e.g. `department_contains` has none while `department_in` lists
      // every department), so the select must be repopulated on every op
      // change, not just when the field itself changes.
      populateSelect(choices);

      if (showMultiEnum && prevEnumVals.length) {
        let validValues = new Set(
          (choices || []).map(function (choice) {
            return String(choice[0]);
          })
        );
        let kept = prevEnumVals.filter(function (v) {
          return validValues.has(String(v));
        });
        $valueSelect.val(kept);
      }

      // `.toggleClass`, not `.toggle()`/`.show()`/`.hide()`: jQuery's
      // show/hide path dereferences `ownerDocument.documentElement`, which is
      // `null` for elements still inside cloned `<template>` content (its
      // owner is an inert "template contents" document with no <html>) — and
      // `createRow` may run this before the row is appended to the live DOM.
      $value
        .attr("type", inputType)
        .attr("step", inputType === "number" ? "any" : null)
        .toggleClass("d-none", showSelect || isNone || showTags);
      $valueSelect.toggleClass("d-none", !showSelect);
      if (showMultiEnum) {
        if ($valueSelect.data("s2")) {
          // Options were refreshed while Select2 was already active (e.g.
          // switching `in` -> `not_in` or `any_of` -> `all_of`); sync chips.
          $valueSelect.trigger("change");
        } else if (document.body && document.body.contains($valueSelect[0])) {
          maybeInitEnumSelect($valueSelect);
        } else {
          // Defer init so Select2 runs after the row is appended to the live DOM.
          setTimeout(function () {
            if (
              !$valueSelect.hasClass("d-none") &&
              $valueSelect.prop("multiple") &&
              document.body &&
              document.body.contains($valueSelect[0])
            ) {
              maybeInitEnumSelect($valueSelect);
            }
          }, 0);
        }
      }
      $valueTags.toggleClass("d-none", !showTags);
      if (showTags) {
        if (document.body && document.body.contains($valueTags[0])) {
          maybeInitTagsInput($valueTags);
        } else {
          // Defer init so Select2 runs after the row is appended to the live DOM.
          setTimeout(function () {
            if (!$valueTags.hasClass("d-none") && document.body && document.body.contains($valueTags[0])) {
              maybeInitTagsInput($valueTags);
            }
          }, 0);
        }
      } else {
        destroySelect2($valueTags);
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
      // Tear down and reset the choice select before `syncOps` rebuilds the
      // new field's options so previous selections never leak across fields.
      destroySelect2($valueSelect);
      $valueSelect.val([]);
      syncOps(null);
      $value.val("");
      // Clear the tags select so its state doesn't leak when the user
      // switches to another field. Use Select2's API when active.
      if ($valueTags.data("s2")) {
        $valueTags.val(null).trigger("change");
      } else {
        $valueTags.val([]).empty();
      }
      $value2.val("");
    });
    $op.on("change", function () {
      closeOpenSelect2();
      syncValueInputs();
    });
    $row.find('[data-sa-action="filter-row-remove"]').on("click", function () {
      destroySelect2In($row);
      $row.remove();
    });

    if (initial && typeof initial === "object") {
      $field.val(initial.field);
      syncOps(initial.filter);
      let field = fieldByName(initial.field);
      let op = filterByName(field, initial.filter);
      let dataType = op ? op.data_type : "string";
      let hasChoices = !!choicesFor(field, op);
      if (dataType === "array") {
        let vals = initial.value == null ? [] : (Array.isArray(initial.value) ? initial.value : [initial.value]);
        $valueTags.data("filterPrefill", vals);
      } else if (hasChoices) {
        let val =
          initial.value == null
            ? dataType === "enum"
              ? []
              : ""
            : dataType === "enum" && !Array.isArray(initial.value)
              ? [initial.value]
              : initial.value;
        $valueSelect.val(val);
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
      let $row = createRow(null);
      $children.append($row);
      initSelect2In($row);
    });
    $group.find('[data-sa-action="filter-group-add-group"]').on("click", function () {
      $children.append(createGroup(null));
    });
    $group.find('[data-sa-action="filter-group-remove"]').on("click", function () {
      destroySelect2In($group);
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
    let $row = createRow(null);
    $rows.append($row);
    initSelect2In($row);
  });
  $('[data-sa-action="add-filter-group"]').on("click", function () {
    $rows.append(createGroup(null));
  });

  if (!prefill()) $rows.append(createRow(null));

  // Init Select2 on any enum/array rows that were built while detached from
  // the live DOM (their containers were not live during createRow).
  initSelect2In($rows);

  $form.on("submit", function () {
    let parts = serializeChildren($rows);
    let logic = $rootLogic.val().toUpperCase();
    $jsonInput.prop("disabled", parts.length === 0);
    if (parts.length) {
      $jsonInput.val(parts.join(" " + logic + " "));
    }
  });
}

/**
 * Initialize the server-rendered list page: row selection + bulk/row actions
 * and tooltips.
 *
 * @param {Object} config
 * @param {string} config.actionUrl - Base URL for bulk actions.
 * @param {string} config.rowActionUrl - Base URL for row actions.
 * @param {boolean} [config.searchHighlight=true] - Highlight search term in table cells.
 * @param {boolean} [config.searchAutoSubmit=false] - Auto-submit search form on input.
 * @param {number} config.rowsTotal - Total rows matching the current filter/search,
 *   across all pages. Used by the "select all matching" banner.
 * @param {Object} [config.inlineEdit] - Inline-edit configuration, present
 *   only when the view has `inline_editable_fields` set and the current user
 *   can edit. See `initInlineEdit`.
 */
function initListPage(config) {
  $(function () {
    const selection = initRowSelection(config);
    initRowClickToDetail();
    initTooltips();
    initMultiSort();
    initJsonViewers();
    if (config.inlineEdit && config.inlineEdit.enabled) {
      initInlineEdit(config.inlineEdit, selection);
    }
    const q = document.querySelector('input[name="q"]');
    if (q) {
      q.focus();
      if (q.value) {
        const val = q.value;
        q.value = '';
        q.value = val;
      }
    }
    if (config.searchAutoSubmit !== false) initAutoSearch();
    if (config.searchHighlight !== false) {
      if (q && q.value) highlightSearchTerm(q.value);
    }
  });
}

/**
 * Shift+click on a sort column header appends/toggles that column in the
 * active sort instead of replacing all existing sorts.
 * The multi-sort URL is pre-computed server-side and stored in
 * data-multi-sort-href so no client-side URL manipulation is needed.
 */
function initMultiSort() {
  document.querySelectorAll(".sort-link").forEach(function (link) {
    link.addEventListener("click", function (e) {
      if (e.shiftKey) {
        var href = this.getAttribute("data-multi-sort-href");
        if (href) {
          e.preventDefault();
          window.location.href = href;
        }
      }
    });
  });
}

/**
 * Row selection and bulk/row actions. Checkbox and cell handlers are
 * delegated to the document and row checkboxes are looked up live, so a row
 * swapped in by inline edit participates without rebinding.
 *
 * @returns {{refresh: function(), rebindRow: function(HTMLElement)}} - Hooks
 *   for callers that replace a row: `rebindRow` rewires the per-element
 *   bindings a fresh row needs (no-confirmation row actions), `refresh`
 *   recomputes the selection state.
 */
function initRowSelection(config) {
  let selectedPks = [];
  let selectAllMatching = false;
  let selectAll = $("#select-all-rows");
  let actionsDropdown = $("#actions-dropdown");
  let banner = $("#select-all-banner");
  let bannerPage = $("#select-all-banner-page");
  let bannerAll = $("#select-all-banner-all");

  function rowCheckboxes() {
    return $(".row-checkbox");
  }

  function syncSelectAllState() {
    let boxes = rowCheckboxes();
    let total = boxes.length;
    let checked = boxes.filter(":checked").length;
    selectAll.prop("checked", total > 0 && checked === total);
    selectAll.prop("indeterminate", checked > 0 && checked < total);
  }

  function updateBanner() {
    if (!banner.length) return;
    let boxes = rowCheckboxes();
    let total = boxes.length;
    let checked = boxes.filter(":checked").length;
    if (selectAllMatching) {
      banner.removeClass("d-none");
      bannerPage.addClass("d-none");
      bannerAll.removeClass("d-none");
    } else if (total > 0 && checked === total) {
      banner.removeClass("d-none");
      bannerPage.removeClass("d-none");
      bannerAll.addClass("d-none");
    } else {
      banner.addClass("d-none");
    }
  }

  function onSelectionChange() {
    let boxes = rowCheckboxes();
    selectedPks = boxes
      .filter(":checked")
      .map(function () {
        return $(this).val();
      })
      .get();
    if (selectedPks.length !== boxes.length) selectAllMatching = false;
    actionsDropdown.toggle(selectedPks.length > 0);
    $(".actions-selected-counter").text(
      selectAllMatching ? config.rowsTotal : selectedPks.length
    );
    syncSelectAllState();
    updateBanner();
  }

  selectAll.on("change", function () {
    rowCheckboxes().prop("checked", $(this).is(":checked"));
    if (!$(this).is(":checked")) selectAllMatching = false;
    onSelectionChange();
  });
  $(document).on("change", ".row-checkbox", onSelectionChange);
  onSelectionChange();

  $("#select-all-matching-link").on("click", function (e) {
    e.preventDefault();
    selectAllMatching = true;
    $(".actions-selected-counter").text(config.rowsTotal);
    updateBanner();
  });
  $("#clear-select-all-link").on("click", function (e) {
    e.preventDefault();
    selectAllMatching = false;
    updateBanner();
    onSelectionChange();
  });

  // Clicking anywhere in the checkbox cell toggles its checkbox
  $(document).on("click", ".checkbox-cell", function (e) {
    if (e.target.type === "checkbox") return;
    $(this).find("input[type=checkbox]").prop("checked", function (_, checked) {
      return !checked;
    }).trigger("change");
  });

  let actionManager = new ActionManager(
    config.actionUrl,
    config.rowActionUrl,
    function (query, element) {
      // appendQueryParams
      if (element.data("is-row-action") === true) {
        query.append("pk", element.closest("tr").data("pk"));
      } else if (selectAllMatching) {
        query.append("all", "1");
      } else {
        selectedPks.forEach((pk) => query.append("pks", pk));
      }
    },
    function (actionName, element, msg) {
      // onSuccess
      successAlert(msg);
      window.location.reload();
    },
    function (actionName, element, error) {
      // onError
      dangerAlert(error);
    }
  );
  actionManager.initNoConfirmationActions();
  actionManager.initActionModal();
  initExportFormDefaults(function () {
    return { selectAllMatching: selectAllMatching, count: selectAllMatching ? config.rowsTotal : selectedPks.length };
  });

  return {
    refresh: onSelectionChange,
    rebindRow: function (row) {
      actionManager.initNoConfirmationActions(row);
    },
  };
}

/**
 * Fill in the built-in export action's scope radio (selected-rows count,
 * default choice, disabled when nothing is selected) each time the shared
 * action modal opens for a form marked `[data-export-scope]`. The form is
 * rendered once, server side, when the list page loads, so the selection
 * state living in `initRowSelection`'s closure has to be patched onto it
 * client side right before the modal is shown.
 *
 * @param {function(): {selectAllMatching: boolean, count: number}} getSelection
 */
function initExportFormDefaults(getSelection) {
  $("#modal-action").on("show.bs.modal", function () {
    const scopeForm = document.querySelector("#modal-form [data-export-scope]");
    if (!scopeForm) return;
    const selection = getSelection();
    const countEl = scopeForm.querySelector("[data-export-selected-count]");
    if (countEl) countEl.textContent = selection.count;
    const labelEl = scopeForm.querySelector("[data-export-selected-label]");
    if (labelEl) {
      labelEl.textContent = selection.selectAllMatching
        ? scopeForm.dataset.labelAll
        : scopeForm.dataset.labelSelected;
    }
    const selectedRadio = scopeForm.querySelector("[data-export-scope-selected]");
    const pageRadio = scopeForm.querySelector("[data-export-scope-page]");
    if (selectedRadio) {
      selectedRadio.disabled = selection.count === 0;
      if (selection.count > 0) {
        selectedRadio.checked = true;
        if (pageRadio) pageRadio.checked = false;
      }
    }
  });
}

/**
 * Clicking anywhere on a row with a data-href attribute navigates to the
 * detail page, unless the click originated on an interactive element
 * (checkbox, link, button, row action) or the user was selecting text.
 * Delegated to the document so rows swapped in by inline edit keep working.
 */
function initRowClickToDetail() {
  document.addEventListener("click", function (e) {
    var row = e.target.closest("tr[data-href]");
    if (!row) return;
    if (e.target.closest("a, button, input, label, .dropdown, .row-action-item, .checkbox-cell, [data-inline-editable]")) {
      return;
    }
    var selection = window.getSelection();
    if (selection && selection.toString().length > 0) {
      return;
    }
    var href = row.getAttribute("data-href");
    if (!href) return;
    if (e.ctrlKey || e.metaKey) {
      window.open(href, "_blank");
    } else {
      window.location.href = href;
    }
  });
}

function applyColumnVisibility() {
  let checked = [];
  let all = [];
  $(".column-visibility-toggle").each(function () {
    all.push($(this).val());
    if ($(this).is(":checked")) checked.push($(this).val());
  });

  let url = new URL(window.location.href);
  url.searchParams.delete("page");
  if (checked.length === 0 || checked.length === all.length) {
    url.searchParams.delete("cols");
  } else {
    url.searchParams.set("cols", checked.join(","));
  }
  window.location.href = url.toString();
}

function initAutoSearch(debounceMs) {
  const input = document.querySelector('input[name="q"]');
  if (!input) return;

  let timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () {
      input.closest('form').submit();
    }, debounceMs || 400);
  });
}

function highlightSearchTerm(term) {
  if (!term || !term.trim()) return;
  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp('(' + escaped + ')', 'gi');
  document.querySelectorAll('table tbody td').forEach(function (td) {
    walkTextNodes(td, regex);
  });
}

function walkTextNodes(node, regex) {
  if (node.nodeType === Node.TEXT_NODE) {
    regex.lastIndex = 0;
    if (!regex.test(node.textContent)) return;
    regex.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let last = 0;
    node.textContent.replace(regex, function (m, _, offset) {
      frag.appendChild(document.createTextNode(node.textContent.slice(last, offset)));
      const mark = document.createElement('mark');
      mark.textContent = m;
      frag.appendChild(mark);
      last = offset + m.length;
    });
    frag.appendChild(document.createTextNode(node.textContent.slice(last)));
    node.parentNode.replaceChild(frag, node);
  } else if (
    node.nodeType === Node.ELEMENT_NODE &&
    node.nodeName !== 'SCRIPT' &&
    node.nodeName !== 'STYLE'
  ) {
    Array.from(node.childNodes).forEach(function (c) {
      walkTextNodes(c, regex);
    });
  }
}

function initTooltips(root) {
  const bs = window.bootstrap || (window.tabler && window.tabler.bootstrap);
  if (!bs) return;
  (root || document).querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
    new bs.Tooltip(el);
  });
}

/**
 * Wire the list-page inline-edit popover (x-editable style): clicking a
 * `[data-inline-editable]` cell opens a Bootstrap popover anchored to the
 * cell immediately, in a loading state, then fills it with the field's form
 * fragment fetched from the server. Saving POSTs the single field; on
 * success the whole row is re-fetched from the row endpoint and swapped in
 * place, with no full page reload. A failed save re-renders the fragment
 * (with the submitted value and its errors) inside the open popover.
 *
 * @param {Object} config
 * @param {string} config.url - Base URL for the inline-edit endpoint (GET to
 *   open, POST to save), both taking `pk` and `field` query params.
 * @param {string} config.rowUrl - URL of the row endpoint returning the
 *   rendered `<tr>` for a `pk`, used to replace the edited row after a save.
 * @param {{refresh: function(), rebindRow: function(HTMLElement)}} [selection]
 *   - Hooks from `initRowSelection` to rewire a swapped-in row.
 */
function initInlineEdit(config, selection) {
  const bs = window.bootstrap || (window.tabler && window.tabler.bootstrap);
  if (!bs) return;

  const templateEl = document.getElementById("inline-edit-popover-template");
  const popoverTemplate = templateEl ? templateEl.innerHTML : undefined;

  // Field widgets that render outside the popover (select2 dropdown,
  // flatpickr calendar, TinyMCE dialogs, JSONEditor modals) must not count
  // as outside clicks, or interacting with them would close the popover.
  const IGNORE_OUTSIDE_CLICK =
    ".inline-edit-popover, .select2-container, .flatpickr-calendar, .tox, .jsoneditor-modal";

  let current = null; // { popover, cell, tip }

  function csrfToken() {
    return (typeof Cookies !== "undefined" && Cookies.get("starlette_admin_csrftoken")) || "";
  }

  // The popover body: the control slot starts in a loading state (spinner)
  // and is filled with the server-rendered form fragment once fetched. The
  // save button is the form's submit button so Enter in a single-line input
  // saves; it stays disabled until the fragment has loaded.
  function popoverBodyHtml() {
    return (
      '<form class="inline-edit-form" novalidate>' +
      '<div class="inline-edit-main">' +
      '<div class="inline-edit-control">' +
      '<div class="inline-edit-loading-state">' +
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>' +
      "</div>" +
      "</div>" +
      '<div class="inline-edit-actions">' +
      '<button type="submit" class="btn btn-primary btn-icon inline-edit-save" aria-label="Save" disabled><i class="' +
      StarletteAdmin.getIcon("inline_edit.save", "fa-solid fa-check") +
      '"></i></button>' +
      '<button type="button" class="btn btn-icon inline-edit-cancel" aria-label="Cancel"><i class="' +
      StarletteAdmin.getIcon("inline_edit.cancel", "fa-solid fa-xmark") +
      '"></i></button>' +
      "</div>" +
      "</div>" +
      '<div class="inline-edit-errors" role="alert" hidden></div>' +
      "</form>"
    );
  }

  function destroyEditors(controlEl) {
    if (controlEl && typeof tinymce !== "undefined") {
      controlEl.querySelectorAll(".field-tinymce-editor").forEach(function (el) {
        const editor = tinymce.get(el.id);
        if (editor) editor.remove();
      });
    }
  }

  function closeCurrent() {
    if (!current) return;
    destroyEditors(current.tip.querySelector(".inline-edit-control"));
    current.popover.dispose();
    current = null;
  }

  // Replace the control slot with a server-rendered fragment (initial load
  // or the 422/500 re-render) and bind the field widgets to it.
  function setControlHtml(tip, html) {
    const controlEl = tip.querySelector(".inline-edit-control");
    destroyEditors(controlEl);
    controlEl.innerHTML = html;
    initializeFields(controlEl);
    const firstField = controlEl.querySelector("input, select, textarea");
    if (firstField) {
      firstField.focus();
      if (
        typeof firstField.select === "function" &&
        firstField.tagName !== "SELECT" &&
        firstField.type !== "checkbox" &&
        firstField.type !== "radio"
      ) {
        firstField.select();
      }
    }
    if (current) current.popover.update();
  }

  function clearErrors(tip) {
    const box = tip.querySelector(".inline-edit-errors");
    box.hidden = true;
    box.replaceChildren();
  }

  // Transport-level failures (network error, non-fragment response) render
  // here; save failures come back as a re-rendered fragment instead.
  function showFailure(tip, message) {
    clearErrors(tip);
    const box = tip.querySelector(".inline-edit-errors");
    const line = document.createElement("div");
    line.textContent = message || "Something went wrong! The value was not saved.";
    box.appendChild(line);
    box.hidden = false;
    if (current) current.popover.update();
  }

  function setSaving(tip, saving) {
    const saveBtn = tip.querySelector(".inline-edit-save");
    const cancelBtn = tip.querySelector(".inline-edit-cancel");
    saveBtn.disabled = saving;
    cancelBtn.disabled = saving;
    saveBtn.innerHTML = saving
      ? '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'
      : '<i class="' + StarletteAdmin.getIcon("inline_edit.save", "fa-solid fa-check") + '"></i>';
  }

  // Fetch the freshly saved row from the row endpoint (carrying the current
  // list-state query params so the columns match) and swap it in place,
  // preserving the checkbox state and rewiring the row's bindings. Falls
  // back to a full reload if the row cannot be fetched: the save itself
  // already succeeded.
  function replaceRow(cell, pk) {
    const row = cell.closest("tr");
    const params = new URLSearchParams(window.location.search);
    params.set("pk", pk);
    return fetch(config.rowUrl + "?" + params.toString())
      .then(function (response) {
        if (!response.ok) throw new Error("Failed to load row");
        return response.text();
      })
      .then(function (html) {
        const tbody = document.createElement("tbody");
        tbody.innerHTML = html.trim();
        const newRow = tbody.querySelector("tr");
        if (!newRow) throw new Error("Malformed row");
        const oldCheckbox = row.querySelector(".row-checkbox");
        const newCheckbox = newRow.querySelector(".row-checkbox");
        if (oldCheckbox && newCheckbox) newCheckbox.checked = oldCheckbox.checked;
        row.replaceWith(newRow);
        initTooltips(newRow);
        if (selection) {
          selection.rebindRow(newRow);
          selection.refresh();
        }
      })
      .catch(function () {
        window.location.reload();
      });
  }

  function saveCell(cell, tip, pk, field) {
    const formEl = tip.querySelector("form.inline-edit-form");
    if (typeof tinymce !== "undefined") tinymce.triggerSave();
    const formData = new FormData(formEl);
    const url = config.url + "?" + new URLSearchParams({ pk: pk, field: field }).toString();
    clearErrors(tip);
    setSaving(tip, true);
    fetch(url, {
      method: "POST",
      body: formData,
      headers: { "X-CSRFToken": csrfToken() },
    })
      .then(function (response) {
        if (!response.ok) {
          const contentType = response.headers.get("content-type") || "";
          // 422/500 fragment: the field re-rendered with the submitted
          // value and its errors, exactly like the edit page re-renders.
          if (contentType.indexOf("text/html") !== -1) {
            return response.text().then(function (html) {
              setSaving(tip, false);
              setControlHtml(tip, html);
            });
          }
          return response
            .json()
            .catch(function () {
              return {};
            })
            .then(function (data) {
              setSaving(tip, false);
              showFailure(tip, data.msg);
            });
        }
        // Success: keep the save spinner until the row has been replaced.
        return response.json().then(function (data) {
          return replaceRow(cell, data.pk != null ? data.pk : pk).then(function () {
            closeCurrent();
            successAlert(data.msg, 4000);
          });
        });
      })
      .catch(function () {
        setSaving(tip, false);
        showFailure(tip, "Could not reach the server. Check your connection and try again.");
      });
  }

  function openCell(cell) {
    if (current && current.cell === cell) return;
    closeCurrent();

    const pk = cell.closest("tr").getAttribute("data-pk");
    const field = cell.getAttribute("data-field");
    const url = config.url + "?" + new URLSearchParams({ pk: pk, field: field }).toString();

    // Show the popover immediately, in a loading state, and fill the
    // control slot once the fragment arrives.
    const popover = new bs.Popover(cell, {
      html: true,
      sanitize: false,
      content: popoverBodyHtml(),
      template: popoverTemplate,
      placement: "bottom",
      fallbackPlacements: ["top"],
      trigger: "manual",
      container: "body",
    });
    popover.show();

    const tip = popover.tip || document.querySelector(".popover.inline-edit-popover");
    current = { popover: popover, cell: cell, tip: tip };

    tip.querySelector("form.inline-edit-form").addEventListener("submit", function (e) {
      e.preventDefault();
      saveCell(cell, tip, pk, field);
    });
    tip.querySelector(".inline-edit-cancel").addEventListener("click", function () {
      closeCurrent();
    });

    fetch(url)
      .then(function (response) {
        if (!response.ok) throw new Error("Failed to load field");
        return response.text();
      })
      .then(function (html) {
        // The popover may have been closed (or reopened elsewhere) while
        // the fragment was in flight.
        if (!current || current.cell !== cell) return;
        setControlHtml(tip, html);
        tip.querySelector(".inline-edit-save").disabled = false;
      })
      .catch(function () {
        if (!current || current.cell !== cell) return;
        showFailure(tip, "Something went wrong! The editor could not be loaded.");
      });
  }

  // Widgets can re-render under the cursor between mousedown and click
  // (select2's clear button removes itself on mousedown), leaving the click
  // target detached or retargeted to <body>. Record where the press started
  // so such clicks are not mistaken for outside clicks.
  let pressStartedInside = false;
  document.addEventListener("pointerdown", function (e) {
    pressStartedInside = !!(e.target.closest && e.target.closest(IGNORE_OUTSIDE_CLICK));
  });

  document.addEventListener("click", function (e) {
    const startedInside = pressStartedInside;
    pressStartedInside = false;
    if (startedInside || e.target.closest(IGNORE_OUTSIDE_CLICK)) return;
    const cell = e.target.closest("[data-inline-editable]");
    if (cell) {
      openCell(cell);
      return;
    }
    if (current) closeCurrent();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && current) closeCurrent();
  });
}

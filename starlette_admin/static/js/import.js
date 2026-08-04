/**
 * Import modal controller: a 3-step wizard (upload -> preview -> confirm).
 *
 * No file is stored server side between steps: the browser holds the
 * selected File object and re-posts it for both the preview and the
 * confirm request, so each request is independent and stateless.
 *
 * @param {string} importUrl  - POST endpoint for the import route
 */
function initImportModal(importUrl) {
  const modal = document.querySelector('[data-sa-hook="modal-import"]');
  if (!modal) return;

  const i18n = JSON.parse(
    document.querySelector('[data-sa-hook="import-i18n"]').textContent
  );
  const form = document.querySelector('[data-sa-hook="import-form"]');
  const stepUpload = document.querySelector('[data-sa-hook="import-step-upload"]');
  const stepPreview = document.querySelector('[data-sa-hook="import-step-preview"]');
  const stepResult = document.querySelector('[data-sa-hook="import-step-result"]');
  const previewLoading = document.querySelector('[data-sa-hook="import-preview-loading"]');
  const previewContent = document.querySelector('[data-sa-hook="import-preview-content"]');
  const stepIndicators = {
    upload: document.querySelector('[data-sa-hook="import-step-indicator-upload"]'),
    preview: document.querySelector('[data-sa-hook="import-step-indicator-preview"]'),
    result: document.querySelector('[data-sa-hook="import-step-indicator-result"]'),
  };
  const errorEl = document.querySelector('[data-sa-hook="import-error"]');
  const submitBtn = document.querySelector('[data-sa-action="import-submit"]');
  const backBtn = document.querySelector('[data-sa-action="import-back"]');

  let step = "upload";
  let loadingLabel = null;
  let fetchingPreview = false;
  let lastPreview = null;
  let excludedFields = new Set();

  function _fmt(template, vars) {
    return template.replace(/\{(\w+)\}/g, (_match, key) => vars[key]);
  }

  modal.addEventListener("show.bs.modal", _resetModal);
  submitBtn.addEventListener("click", _handleSubmit);
  backBtn.addEventListener("click", function () {
    _goToStep("upload");
  });

  function _resetModal() {
    form.reset();
    lastPreview = null;
    excludedFields = new Set();
    _hideError();
    _goToStep("upload");
  }

  function _goToStep(next, opts) {
    step = next;
    loadingLabel = (opts && opts.loadingLabel) || null;
    fetchingPreview = !!(opts && opts.fetchingPreview);
    stepUpload.classList.toggle("d-none", step !== "upload");
    stepPreview.classList.toggle("d-none", step !== "preview");
    stepResult.classList.toggle("d-none", step !== "result");
    previewLoading.classList.toggle("d-none", !fetchingPreview);
    previewContent.classList.toggle("d-none", fetchingPreview);
    backBtn.classList.toggle("d-none", step !== "preview");
    Object.entries(stepIndicators).forEach(([name, el]) => {
      el.classList.toggle("active", name === step);
    });
    _updateSubmitButton();
  }

  // Swaps the submit button between its active and done-state variant,
  // resolving both roles through the class registry so switching never
  // leaves a stale variant class behind.
  function _setButtonVariant(role) {
    StarletteAdmin.removeClass(submitBtn, StarletteAdmin.getClass("import.submit_button"));
    StarletteAdmin.removeClass(submitBtn, StarletteAdmin.getClass("import.submit_button_done"));
    StarletteAdmin.addClass(submitBtn, StarletteAdmin.getClass(role));
  }

  // Fills the submit button with an icon+label fragment, resolving iconName
  // through the icon registry.
  function _setButtonIconLabel(iconName, label) {
    const el = StarletteAdmin.template("import-button-icon-label");
    StarletteAdmin.fillSlot(el, "icon", function (n) {
      n.className = StarletteAdmin.getIcon(iconName) + " me-2";
    });
    StarletteAdmin.fillSlot(el, "label", function (n) {
      n.textContent = label;
    });
    submitBtn.replaceChildren(el);
  }

  function _setButtonSpinnerLabel(label) {
    const el = StarletteAdmin.template("import-button-spinner-label");
    StarletteAdmin.fillSlot(el, "label", function (n) {
      n.textContent = label;
    });
    submitBtn.replaceChildren(el);
  }

  function _updateSubmitButton() {
    submitBtn.disabled = !!loadingLabel;
    backBtn.disabled = !!loadingLabel;
    if (loadingLabel) {
      _setButtonVariant("import.submit_button");
      _setButtonSpinnerLabel(loadingLabel);
    } else if (step === "upload") {
      _setButtonVariant("import.submit_button");
      _setButtonIconLabel("import.preview", i18n.btnPreview);
    } else if (step === "preview") {
      _setButtonVariant("import.submit_button");
      const total = lastPreview ? lastPreview.rows_total : 0;
      _setButtonIconLabel("list.import", _fmt(i18n.btnImport, { count: total }));
    } else {
      _setButtonVariant("import.submit_button_done");
      _setButtonIconLabel("flash.success", i18n.btnDone);
    }
  }

  function _handleSubmit() {
    if (step === "upload") {
      _submitPreview();
    } else if (step === "preview") {
      _submitConfirm();
    } else {
      window.location.reload();
    }
  }

  function _buildFormData(includeFields) {
    if (!form.checkValidity()) {
      form.reportValidity();
      return null;
    }
    const formData = new FormData(form);
    const updateExisting = document.querySelector('[data-sa-hook="import-update-existing"]').checked;
    if (updateExisting) formData.append("update_existing", "1");
    if (includeFields && lastPreview) {
      lastPreview.mapping
        .filter((m) => !excludedFields.has(m.field))
        .forEach((m) => formData.append("fields", m.field));
    }
    return formData;
  }

  async function _submitPreview() {
    const formData = _buildFormData(true);
    if (!formData) return;
    _goToStep("preview", { loadingLabel: i18n.loadingPreview, fetchingPreview: true });
    let data;
    try {
      data = await $.ajax({
        url: importUrl + "?preview=1",
        method: "POST",
        data: formData,
        contentType: false,
        processData: false,
      });
    } catch (jqXHR) {
      _showError(
        (jqXHR.responseJSON && jqXHR.responseJSON.error) ||
          _fmt(i18n.networkError, { status: jqXHR.statusText })
      );
      _goToStep("upload");
      return;
    }
    _hideError();
    lastPreview = data;
    _renderPreview(data);
    _goToStep("preview");
  }

  async function _submitConfirm() {
    const formData = _buildFormData(true);
    if (!formData) return;
    loadingLabel = i18n.loadingImport;
    _updateSubmitButton();
    let data;
    try {
      data = await $.ajax({
        url: importUrl,
        method: "POST",
        data: formData,
        contentType: false,
        processData: false,
      });
    } catch (jqXHR) {
      _showError(
        (jqXHR.responseJSON && jqXHR.responseJSON.error) ||
          _fmt(i18n.networkError, { status: jqXHR.statusText })
      );
      loadingLabel = null;
      _updateSubmitButton();
      return;
    }
    _hideError();
    _renderResult(data);
    _goToStep("result");
  }

  function _showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.remove("d-none");
  }

  function _hideError() {
    errorEl.classList.add("d-none");
    errorEl.textContent = "";
  }

  // Renders an icon+message alert into container, replacing any previous
  // content. Used for both the preview and the result summary.
  function _renderSummaryAlert(container, hasErrors, text) {
    const el = StarletteAdmin.template("import-summary-alert");
    StarletteAdmin.addClass(el, StarletteAdmin.getClass(hasErrors ? "alert.warning" : "alert.success"));
    StarletteAdmin.fillSlot(el, "icon", function (n) {
      n.className = StarletteAdmin.getIcon(hasErrors ? "flash.warning" : "flash.success") + " me-2";
    });
    StarletteAdmin.fillSlot(el, "message", function (n) {
      n.textContent = text + ".";
    });
    container.replaceChildren(el);
  }

  // Renders the column-mapping checkboxes and binds their re-preview
  // handler; each toggle excludes/includes its field from the import.
  function _renderMapping(mappingEl, data) {
    const shell = StarletteAdmin.template("import-mapping-shell");
    StarletteAdmin.fillSlot(shell, "heading", function (n) {
      n.textContent = i18n.columns;
    });
    const rows = shell.querySelector('[data-sa-slot="rows"]');
    data.mapping.forEach(function (m) {
      const row = StarletteAdmin.template("import-mapping-row");
      const input = row.querySelector('[data-sa-hook="import-field-toggle"]');
      input.dataset.saField = m.field;
      input.checked = !excludedFields.has(m.field);
      StarletteAdmin.fillSlot(row, "label", function (n) {
        n.textContent = m.header + " → " + m.field;
      });
      rows.appendChild(row);
    });
    if (data.unmatched_headers.length) {
      StarletteAdmin.fillSlot(shell, "ignored", function (n) {
        n.textContent = _fmt(i18n.ignored, { headers: data.unmatched_headers.join(", ") });
      });
    } else {
      const ignored = shell.querySelector('[data-sa-slot="ignored"]');
      if (ignored) ignored.remove();
    }
    mappingEl.replaceChildren(shell);
    mappingEl.querySelectorAll('[data-sa-hook="import-field-toggle"]').forEach((el) => {
      el.addEventListener("change", function () {
        const field = this.dataset.saField;
        if (this.checked) excludedFields.delete(field);
        else excludedFields.add(field);
        _submitPreview();
      });
    });
  }

  // Renders the sample-rows preview table for the given (post-exclusion)
  // columns, or clears the container when there is no sample.
  function _renderSampleTable(sampleEl, data, columns) {
    if (!data.sample.length) {
      sampleEl.replaceChildren();
      return;
    }
    const statusLabels = { error: i18n.statusError, update: i18n.statusUpdate, new: i18n.statusNew };
    const statusVariant = {
      error: "import.status_error",
      update: "import.status_update",
      new: "import.status_new",
    };

    const shell = StarletteAdmin.template("import-sample-table");
    StarletteAdmin.fillSlot(shell, "heading", function (n) {
      n.textContent = _fmt(i18n.previewHeading, { count: data.sample.length });
    });
    const headerRow = shell.querySelector('[data-sa-slot="header-row"]');
    headerRow.appendChild(_th(i18n.colStatus));
    columns.forEach((c) => headerRow.appendChild(_th(c)));
    headerRow.appendChild(_th(i18n.colErrors));

    const body = shell.querySelector('[data-sa-slot="body"]');
    data.sample.forEach(function (row) {
      const tr = StarletteAdmin.template("import-sample-row");
      StarletteAdmin.fillSlot(tr, "status", function (n) {
        n.textContent = statusLabels[row.status] || row.status;
        StarletteAdmin.addClass(n, StarletteAdmin.getClass(statusVariant[row.status] || statusVariant.new));
      });
      columns.forEach((c) => {
        const td = document.createElement("td");
        td.textContent = String(row.cells[c] ?? "");
        tr.appendChild(td);
      });
      const errorsTd = document.createElement("td");
      errorsTd.textContent = row.errors.map((e) => e.message).join("; ");
      tr.appendChild(errorsTd);
      body.appendChild(tr);
    });
    sampleEl.replaceChildren(shell);
  }

  // Renders an error table (optionally headed) into container, or clears it
  // when there are no errors. Shared by the preview "all errors" table and
  // the result table.
  function _renderErrorsTable(errorsEl, errors, heading) {
    if (!errors.length) {
      errorsEl.replaceChildren();
      return;
    }
    const shell = StarletteAdmin.template("import-errors-table");
    if (heading) {
      StarletteAdmin.fillSlot(shell, "heading", function (n) {
        n.textContent = heading;
      });
    } else {
      const h = shell.querySelector('[data-sa-slot="heading"]');
      if (h) h.remove();
    }
    StarletteAdmin.fillSlot(shell, "col-row", (n) => (n.textContent = i18n.colRow));
    StarletteAdmin.fillSlot(shell, "col-field", (n) => (n.textContent = i18n.colField));
    StarletteAdmin.fillSlot(shell, "col-error", (n) => (n.textContent = i18n.colError));
    const body = shell.querySelector('[data-sa-slot="body"]');
    errors.forEach(function (e) {
      const tr = StarletteAdmin.template("import-error-row");
      StarletteAdmin.fillSlot(tr, "row", (n) => (n.textContent = e.row));
      StarletteAdmin.fillSlot(tr, "field", (n) => (n.textContent = e.field || ""));
      StarletteAdmin.fillSlot(tr, "message", (n) => (n.textContent = e.message));
      body.appendChild(tr);
    });
    errorsEl.replaceChildren(shell);
  }

  function _th(text) {
    const th = document.createElement("th");
    th.textContent = text;
    return th;
  }

  function _renderPreview(data) {
    const summaryEl = document.querySelector('[data-sa-hook="import-preview-summary"]');
    const mappingEl = document.querySelector('[data-sa-hook="import-preview-mapping"]');
    const sampleEl = document.querySelector('[data-sa-hook="import-preview-sample"]');
    const errorsEl = document.querySelector('[data-sa-hook="import-preview-errors"]');

    let summaryText = _fmt(i18n.previewSummary, { total: data.rows_total, new: data.rows_new });
    if (data.rows_updated) summaryText += _fmt(i18n.clauseUpdated, { count: data.rows_updated });
    if (data.errors.length) summaryText += _fmt(i18n.clauseErrors, { count: data.errors.length });
    _renderSummaryAlert(summaryEl, data.has_errors, summaryText);

    _renderMapping(mappingEl, data);

    const columns = data.mapping.filter((m) => !excludedFields.has(m.field)).map((m) => m.field);
    _renderSampleTable(sampleEl, data, columns);

    _renderErrorsTable(errorsEl, data.errors, data.errors.length ? i18n.allErrors : null);
  }

  function _renderResult(data) {
    const summaryEl = document.querySelector('[data-sa-hook="import-result-summary"]');
    const errorsEl = document.querySelector('[data-sa-hook="import-result-errors"]');

    let summaryText = _fmt(i18n.resultSummary, {
      total: data.rows_total,
      created: data.rows_created,
    });
    if (data.rows_updated) summaryText += _fmt(i18n.clauseUpdated, { count: data.rows_updated });
    if (data.rows_skipped) summaryText += _fmt(i18n.clauseSkipped, { count: data.rows_skipped });
    if (data.errors.length) summaryText += _fmt(i18n.clauseErrors, { count: data.errors.length });
    _renderSummaryAlert(summaryEl, data.has_errors, summaryText);

    _renderErrorsTable(errorsEl, data.errors, null);

    if (!data.has_errors) successAlert(summaryText, 4000);
  }
}

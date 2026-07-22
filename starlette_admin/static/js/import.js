/**
 * Import modal controller: a 3-step wizard (upload -> preview -> confirm).
 *
 * No file is stored server side between steps: the browser holds the
 * selected File object and re-posts it for both the preview and the
 * confirm request, so each request is independent and stateless.
 *
 * @param {string} importUrl  - POST endpoint for the import route
 * @param {object} i18n       - translated strings/templates, rendered server side
 */
function initImportModal(importUrl, i18n) {
  const modal = document.getElementById("modal-import");
  if (!modal) return;

  const form = document.getElementById("import-form");
  const stepUpload = document.getElementById("import-step-upload");
  const stepPreview = document.getElementById("import-step-preview");
  const stepResult = document.getElementById("import-step-result");
  const previewLoading = document.getElementById("import-preview-loading");
  const previewContent = document.getElementById("import-preview-content");
  const stepIndicators = {
    upload: document.getElementById("import-step-indicator-upload"),
    preview: document.getElementById("import-step-indicator-preview"),
    result: document.getElementById("import-step-indicator-result"),
  };
  const errorEl = document.getElementById("import-error");
  const submitBtn = document.getElementById("import-submit");
  const backBtn = document.getElementById("import-back");

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

  function _updateSubmitButton() {
    submitBtn.disabled = !!loadingLabel;
    backBtn.disabled = !!loadingLabel;
    if (loadingLabel) {
      submitBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' + loadingLabel;
      submitBtn.classList.remove("btn-secondary");
      submitBtn.classList.add("btn-primary");
    } else if (step === "upload") {
      submitBtn.innerHTML =
        '<i class="' + StarletteAdmin.getIcon("import.preview") + ' me-2"></i>' + i18n.btnPreview;
      submitBtn.classList.remove("btn-secondary");
      submitBtn.classList.add("btn-primary");
    } else if (step === "preview") {
      const total = lastPreview ? lastPreview.rows_total : 0;
      submitBtn.innerHTML =
        '<i class="' + StarletteAdmin.getIcon("list.import") + ' me-2"></i>' +
        _fmt(i18n.btnImport, { count: total });
      submitBtn.classList.remove("btn-secondary");
      submitBtn.classList.add("btn-primary");
    } else {
      submitBtn.innerHTML =
        '<i class="' + StarletteAdmin.getIcon("flash.success") + ' me-2"></i>' + i18n.btnDone;
      submitBtn.classList.remove("btn-primary");
      submitBtn.classList.add("btn-secondary");
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
    const updateExisting = document.getElementById("import-update-existing").checked;
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

  function _renderPreview(data) {
    const summaryEl = document.getElementById("import-preview-summary");
    const mappingEl = document.getElementById("import-preview-mapping");
    const sampleEl = document.getElementById("import-preview-sample");
    const errorsEl = document.getElementById("import-preview-errors");

    const alertClass = data.has_errors ? "alert-warning" : "alert-success";
    const icon =
      '<i class="' +
      StarletteAdmin.getIcon(data.has_errors ? "flash.warning" : "flash.success") +
      ' me-2"></i>';
    let summaryText = _fmt(i18n.previewSummary, { total: data.rows_total, new: data.rows_new });
    if (data.rows_updated) summaryText += _fmt(i18n.clauseUpdated, { count: data.rows_updated });
    if (data.errors.length) summaryText += _fmt(i18n.clauseErrors, { count: data.errors.length });
    summaryEl.innerHTML =
      '<div class="alert ' + alertClass + '">' + icon + summaryText + ".</div>";

    let mappingHtml = '<div class="mb-2 fw-bold">' + i18n.columns + "</div>";
    data.mapping.forEach((m) => {
      const checked = excludedFields.has(m.field) ? "" : "checked";
      mappingHtml +=
        '<label class="form-check">' +
        '<input type="checkbox" class="form-check-input import-field-toggle" data-field="' +
        _escapeHtml(m.field) +
        '" ' +
        checked +
        ">" +
        '<span class="form-check-label">' +
        _escapeHtml(m.header) +
        " &rarr; " +
        _escapeHtml(m.field) +
        "</span>" +
        "</label>";
    });
    if (data.unmatched_headers.length) {
      mappingHtml +=
        '<div class="text-muted mt-2">' +
        _fmt(i18n.ignored, { headers: data.unmatched_headers.map(_escapeHtml).join(", ") }) +
        "</div>";
    }
    mappingEl.innerHTML = mappingHtml;
    mappingEl.querySelectorAll(".import-field-toggle").forEach((el) => {
      el.addEventListener("change", function () {
        const field = this.getAttribute("data-field");
        if (this.checked) excludedFields.delete(field);
        else excludedFields.add(field);
        _submitPreview();
      });
    });

    const columns = data.mapping
      .filter((m) => !excludedFields.has(m.field))
      .map((m) => m.field);
    if (data.sample.length) {
      const statusLabels = {
        error: i18n.statusError,
        update: i18n.statusUpdate,
        new: i18n.statusNew,
      };
      let rows = data.sample
        .map((row) => {
          const badgeClass =
            row.status === "error"
              ? "text-bg-danger"
              : row.status === "update"
                ? "text-bg-primary"
                : "text-bg-success";
          const cells = columns
            .map((c) => "<td>" + _escapeHtml(String(row.cells[c] ?? "")) + "</td>")
            .join("");
          const rowErrors = row.errors.map((e) => _escapeHtml(e.message)).join("; ");
          return (
            "<tr><td><span class=\"badge " +
            badgeClass +
            '">' +
            _escapeHtml(statusLabels[row.status] || row.status) +
            "</span></td>" +
            cells +
            "<td>" +
            rowErrors +
            "</td></tr>"
          );
        })
        .join("");
      sampleEl.innerHTML =
        '<div class="mb-2 fw-bold">' +
        _fmt(i18n.previewHeading, { count: data.sample.length }) +
        "</div>" +
        '<div class="table-responsive"><table class="table table-sm table-bordered">' +
        "<thead><tr><th>" +
        i18n.colStatus +
        "</th>" +
        columns.map((c) => "<th>" + _escapeHtml(c) + "</th>").join("") +
        "<th>" +
        i18n.colErrors +
        "</th></tr></thead><tbody>" +
        rows +
        "</tbody></table></div>";
    } else {
      sampleEl.innerHTML = "";
    }

    if (data.errors.length) {
      let rows = data.errors
        .map(
          (e) =>
            "<tr><td>" +
            e.row +
            "</td><td>" +
            (e.field || "") +
            "</td><td>" +
            _escapeHtml(e.message) +
            "</td></tr>"
        )
        .join("");
      errorsEl.innerHTML =
        '<div class="mb-2 fw-bold">' + i18n.allErrors + "</div>" +
        '<div class="table-responsive"><table class="table table-sm table-bordered">' +
        "<thead><tr><th>" +
        i18n.colRow +
        "</th><th>" +
        i18n.colField +
        "</th><th>" +
        i18n.colError +
        "</th></tr></thead>" +
        "<tbody>" +
        rows +
        "</tbody></table></div>";
    } else {
      errorsEl.innerHTML = "";
    }
  }

  function _renderResult(data) {
    const summaryEl = document.getElementById("import-result-summary");
    const errorsEl = document.getElementById("import-result-errors");

    const alertClass = data.has_errors ? "alert-warning" : "alert-success";
    const icon =
      '<i class="' +
      StarletteAdmin.getIcon(data.has_errors ? "flash.warning" : "flash.success") +
      ' me-2"></i>';
    let summaryText = _fmt(i18n.resultSummary, {
      total: data.rows_total,
      created: data.rows_created,
    });
    if (data.rows_updated) summaryText += _fmt(i18n.clauseUpdated, { count: data.rows_updated });
    if (data.rows_skipped) summaryText += _fmt(i18n.clauseSkipped, { count: data.rows_skipped });
    if (data.errors.length) summaryText += _fmt(i18n.clauseErrors, { count: data.errors.length });
    summaryEl.innerHTML =
      '<div class="alert ' + alertClass + '">' + icon + summaryText + ".</div>";

    if (data.errors.length) {
      let rows = data.errors
        .map(
          (e) =>
            "<tr><td>" +
            e.row +
            "</td><td>" +
            (e.field || "") +
            "</td><td>" +
            _escapeHtml(e.message) +
            "</td></tr>"
        )
        .join("");
      errorsEl.innerHTML =
        '<div class="table-responsive"><table class="table table-sm table-bordered">' +
        "<thead><tr><th>" +
        i18n.colRow +
        "</th><th>" +
        i18n.colField +
        "</th><th>" +
        i18n.colError +
        "</th></tr></thead>" +
        "<tbody>" +
        rows +
        "</tbody></table></div>";
    } else {
      errorsEl.innerHTML = "";
    }
    if (!data.has_errors) successAlert(summaryText, 4000);
  }

  function _escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

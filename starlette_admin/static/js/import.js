/**
 * Import modal controller.
 *
 * @param {string} importUrl  - POST endpoint for the import route
 */
function initImportModal(importUrl) {
  const modal = document.getElementById("modal-import");
  if (!modal) return;

  const form = document.getElementById("import-form");
  const formSection = document.getElementById("import-form-section");
  const resultsSection = document.getElementById("import-results");
  const errorEl = document.getElementById("import-error");
  const submitBtn = document.getElementById("import-submit");
  let _lastWasDryRun = true;

  modal.addEventListener("show.bs.modal", _resetModal);

  submitBtn.addEventListener("click", _handleSubmit);

  function _resetModal() {
    form.reset();
    _lastWasDryRun = true;
    formSection.classList.remove("d-none");
    resultsSection.classList.add("d-none");
    errorEl.classList.add("d-none");
    errorEl.textContent = "";
    _setSubmitBtnToImport();
  }

  function _setSubmitBtnToImport() {
    submitBtn.disabled = false;
    submitBtn.setAttribute("data-action", "import");
    submitBtn.innerHTML = '<i class="fa-solid fa-upload me-2"></i>Import';
    submitBtn.classList.remove("btn-secondary");
    submitBtn.classList.add("btn-primary");
  }

  function _setSubmitBtnToDone() {
    submitBtn.disabled = false;
    submitBtn.setAttribute("data-action", "done");
    submitBtn.innerHTML = "Done";
    submitBtn.classList.remove("btn-primary");
    submitBtn.classList.add("btn-secondary");
  }

  async function _handleSubmit() {
    const action = submitBtn.getAttribute("data-action");
    if (action === "done") {
      if (!_lastWasDryRun) {
        window.location.reload();
        return;
      }
      const Modal = (window.bootstrap && window.bootstrap.Modal) || (window.tabler && window.tabler.Modal);
      if (Modal && Modal.getOrCreateInstance) {
        Modal.getOrCreateInstance(modal).hide();
      } else {
        modal.classList.remove("show");
        modal.style.display = "none";
      }
      return;
    }

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Importing…';

    const formData = new FormData(form);
    const isDryRun = document.getElementById("import-dry-run").checked;
    const skipPk = document.getElementById("import-skip-pk").checked;
    _lastWasDryRun = isDryRun;
    const params = [];
    if (isDryRun) params.push("dry_run=1");
    if (skipPk) params.push("skip_pk=1");
    const url = params.length ? importUrl + "?" + params.join("&") : importUrl;

    let data;
    let ok = true;
    try {
      data = await $.ajax({
        url: url,
        method: "POST",
        data: formData,
        contentType: false,
        processData: false,
      });
    } catch (jqXHR) {
      ok = false;
      data = jqXHR.responseJSON;
      if (!data) {
        _showError("Network error: " + jqXHR.statusText);
        _setSubmitBtnToImport();
        return;
      }
    }

    if (!ok) {
      _showError(data.error || "Import failed.");
      _setSubmitBtnToImport();
      return;
    }

    _renderResults(data);
    _setSubmitBtnToDone();
  }

  function _showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.remove("d-none");
  }

  function _renderResults(data) {
    formSection.classList.add("d-none");
    resultsSection.classList.remove("d-none");

    const summaryEl = document.getElementById("import-summary");
    const errorsTableEl = document.getElementById("import-errors-table");

    const alertClass = data.has_errors ? "alert-warning" : "alert-success";
    const iconHtml = data.has_errors
      ? '<i class="fa-solid fa-triangle-exclamation me-2"></i>'
      : '<i class="fa-solid fa-circle-check me-2"></i>';

    let summaryText = data.dry_run ? "Dry run: " : "";
    summaryText += data.rows_total + " row(s) scanned";
    if (!data.dry_run) {
      summaryText += ", " + data.rows_created + " created";
      if (data.rows_updated) summaryText += ", " + data.rows_updated + " updated";
      if (data.rows_skipped) summaryText += ", " + data.rows_skipped + " skipped";
    }
    if (data.errors.length) {
      summaryText += ", " + data.errors.length + " error(s)";
    }

    summaryEl.innerHTML =
      '<div class="alert ' + alertClass + '">' + iconHtml + summaryText + ".</div>";

    if (data.errors.length > 0) {
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
      errorsTableEl.innerHTML =
        '<div class="table-responsive"><table class="table table-sm table-bordered">' +
        "<thead><tr><th>Row</th><th>Field</th><th>Error</th></tr></thead>" +
        "<tbody>" +
        rows +
        "</tbody></table></div>";
    } else {
      errorsTableEl.innerHTML = "";
    }
  }

  function _escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

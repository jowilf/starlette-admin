/**
 * Show a Bootstrap modal and resolve once the shown transition has completed.
 * @param {jQuery} modal
 * @returns {Promise<void>}
 */
function showModal(modal) {
  return new Promise((resolve) => {
    modal.one("shown.bs.modal", () => resolve());
    modal.modal("show");
  });
}

/**
 * Hide a Bootstrap modal and resolve once the hidden transition has completed.
 * @param {jQuery} modal
 * @returns {Promise<void>}
 */
function hideModal(modal) {
  return new Promise((resolve) => {
    modal.one("hidden.bs.modal", () => resolve());
    modal.modal("hide");
  });
}

/**
 * A class for managing bactch and row actions in the admin interface.
 */
class ActionManager {
  /**
   * @param {string} actionUrl - The base URL for actions.
   * @param {string} rowActionUrl - The base URL for row actions.
   * @param {function(URLSearchParams, jQuery)} appendQueryParams - A function to append query parameters to the URL.
   * @param {function(string, jQuery, string)} onSuccess - A callback function to handle successful action responses.
   * @param {function(string, jQuery, string)} onError - A callback function to handle error responses.
   */
  constructor(actionUrl, rowActionUrl, appendQueryParams, onSuccess, onError) {
    this.rowActionUrl = rowActionUrl;
    this.actionUrl = actionUrl;
    this.appendQueryParams = appendQueryParams;
    this.onSuccess = onSuccess;
    this.onError = onError;
  }

  /**
   * Initialize actions that do not require user confirmation.
   * @param {HTMLElement} [root] - Scope the lookup to this element. Used to
   *   rebind a single row swapped in by inline edit; defaults to the whole
   *   document.
   */
  initNoConfirmationActions(root) {
    let self = this;
    $(root || document).find('a[data-sa-no-confirmation-action="true"]').each(function () {
      $(this).on("click", function (event) {
        let isRowAction = $(this).data("sa-is-row-action") === true;
        self.submitAction(
          $(this).data("sa-name"),
          null,
          $(this).data("sa-custom-response") === true,
          isRowAction,
          $(this)
        );
      });
    });
  }

  /**
   * Initialize actions that trigger a modal dialog for user confirmation.
   */
  initActionModal() {
    let self = this;
    $('[data-sa-hook="modal-action"]').on("show.bs.modal", function (event) {
      let button = $(event.relatedTarget); // Button that triggered the modal
      let confirmation = button.data("sa-confirmation");
      let header = button.data("sa-header");
      let form = button.data("sa-form");
      let name = button.data("sa-name");
      let submit_btn_text = button.data("sa-submit-btn-text");
      let submit_btn_class = button.data("sa-submit-btn-class");
      let modalSize = button.data("sa-modal-size") || "sm";
      let customResponse = button.data("sa-custom-response") === true;
      let isRowAction = button.data("sa-is-row-action") === true;

      let modal = $(this);
      let modalDialog = modal.find(".modal-dialog");
      modalDialog.removeClass("modal-sm modal-lg modal-xl");
      if (modalSize !== "md") {
        modalDialog.addClass(`modal-${modalSize}`);
      }
      let modalHeader = modal.find('[data-sa-hook="modal-action-header"]');
      if (header) {
        modal.find('[data-sa-hook="modal-action-title"]').text(header);
        modalHeader.removeClass("d-none");
      } else {
        modalHeader.addClass("d-none");
      }
      modal.find('[data-sa-hook="action-confirmation"]').text(confirmation);
      let modalForm = modal.find('[data-sa-hook="modal-form"]');
      modalForm.html(form);
      let actionSubmit = modal.find('[data-sa-action="action-submit"]');
      actionSubmit.text(submit_btn_text);
      actionSubmit
        .removeClass()
        .addClass(
          submit_btn_class ||
            StarletteAdmin.getClass("action.modal_confirm_button"),
        );
      actionSubmit.unbind();
      actionSubmit.on("click", function (event) {
        const formElements = modalForm.find("form");
        const form = formElements.length ? formElements.get(0) : null;
        self.submitAction(name, form, customResponse, isRowAction, button);
      });
    });
  }

  /**
   * Submit an action to the server.
   * @param {string} actionName - The name of the action.
   * @param {HTMLFormElement | null} form - The HTML form associated with the action.
   * @param {boolean} customResponse
   * @param {boolean} isRowAction - Whether the action is a row action.
   * @param {jQuery} element - The element that triggered the action.
   */
  submitAction(actionName, form, customResponse, isRowAction, element) {
    let baseUrl = isRowAction ? this.rowActionUrl : this.actionUrl;
    let query = new URLSearchParams();
    query.append("name", actionName);
    query.append("_origin", window.location.href);
    if (!isRowAction) {
      query.append("_list_query", window.location.search);
    }
    this.appendQueryParams(query, element);
    let url = baseUrl + "?" + query.toString();
    var csrfToken = (typeof Cookies !== "undefined" && Cookies.get("starlette_admin_csrftoken")) || "";
    if (customResponse) {
      if (form) {
        // Inject CSRF token so the native form submit is protected
        var existing = form.querySelector('input[name="csrftoken"]');
        if (!existing && csrfToken) {
          var inp = document.createElement("input");
          inp.type = "hidden";
          inp.name = "csrftoken";
          inp.value = csrfToken;
          form.appendChild(inp);
        }
        form.action = url;
        form.method = "POST";
        form.submit();
      } else {
        // No user-supplied form: POST via a temporary hidden form so the
        // CSRF middleware accepts the request (action routes are POST-only).
        var tempForm = document.createElement("form");
        tempForm.action = url;
        tempForm.method = "POST";
        tempForm.style.display = "none";
        if (csrfToken) {
          var inp = document.createElement("input");
          inp.type = "hidden";
          inp.name = "csrftoken";
          inp.value = csrfToken;
          tempForm.appendChild(inp);
        }
        document.body.appendChild(tempForm);
        tempForm.submit();
      }
    } else {
      var csrfHeader = csrfToken;
      let loadingModal = $('[data-sa-hook="modal-loading"]');
      (async () => {
        await showModal(loadingModal);
        let response;
        try {
          response = await fetch(url, {
            method: "POST",
            body: form ? new FormData(form) : null,
            headers: { "X-CSRFToken": csrfHeader },
          });
        } catch (networkError) {
          await hideModal(loadingModal);
          this.onError(actionName, element, "Something went wrong!");
          return;
        }
        // Hide once here so every branch below shares a single hidden.bs.modal
        // transition; calling hide() again on an already-hidden modal never
        // resolves since the event only fires on an actual state change.
        await hideModal(loadingModal);
        if (response.ok) {
          let data = await response.json();
          if (data.redirect) {
            window.location.href = data.redirect;
          } else {
            this.onSuccess(actionName, element, data.msg);
          }
        } else {
          let msg = "Something went wrong!";
          if (response.status == 400) {
            msg = (await response.json())["msg"];
          }
          this.onError(actionName, element, msg);
        }
      })();
    }
  }
}

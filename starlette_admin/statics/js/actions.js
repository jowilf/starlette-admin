/**
 * A class for managing batch and row actions in the admin interface.
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
   */
  initNoConfirmationActions() {
    let self = this;
    $('a[data-no-confirmation-action="true"]').each(function () {
      $(this).on("click", function (event) {
        let isRowAction = $(this).data("is-row-action") === true;
        self.submitAction(
          $(this).data("name"),
          null,
          $(this).data("custom-response") === true,
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
    $("[data-action-modal]").on("show.bs.modal", function (event) {
      let button = $(event.relatedTarget); // Button that triggered the modal
      let name = button.data("name");
      let customResponse = button.data("custom-response") === true;
      let isRowAction = button.data("is-row-action") === true;

      let modal = $(this);
      let actionSubmit = modal.find("[data-action-submit]");
      actionSubmit.unbind();
      actionSubmit.on("click", function (event) {
        const formElements = modal.find("form");
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
    this.appendQueryParams(query, element);
    let url = baseUrl + "?" + query.toString();
    if (customResponse) {
      if (form) {
        form.action = url;
        form.method = "POST";
        form.submit();
      } else {
        window.location.replace(url);
      }
    } else {
      $("#modal-loading").modal("show");
      fetch(url, {
        method: form ? "POST" : "GET",
        body: form ? new FormData(form) : null,
      })
        .then(async (response) => {
          await new Promise((r) => setTimeout(r, 500));
          $("#modal-loading").modal("hide");
          if (response.ok) {
            let msg = (await response.json())["msg"];
            this.onSuccess(actionName, element, msg);
          } else {
            if (response.status == 400) {
              return Promise.reject((await response.json())["msg"]);
            }
            return Promise.reject("Something went wrong!");
          }
        })
        .catch(async (error) => {
          await new Promise((r) => setTimeout(r, 500));
          this.onError(actionName, element, error);
        });
    }
  }
}

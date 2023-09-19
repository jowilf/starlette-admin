
function successAlert(msg) {
  $("#alertContainer").empty();
  $(`<div
  class="alert alert-success alert-dismissible m-0"
  role="alert"
>
  <div class="d-flex">
    <div>
      <!-- Download SVG icon from http://tabler-icons.io/i/check -->
      <svg xmlns="http://www.w3.org/2000/svg" class="icon alert-icon" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M5 12l5 5l10 -10" /></svg>
    </div>
    <div>${msg}</div>
  </div>
  <a class="btn-close" data-bs-dismiss="alert" aria-label="close"></a>
</div>
`).appendTo("#alertContainer");
}
function dangerAlert(msg) {
  $("#alertContainer").empty();
  $(`<div
  class="alert alert-danger alert-dismissible m-0"
  role="alert"
>
  <div class="d-flex">
    <div>
      <!-- Download SVG icon from http://tabler-icons.io/i/check -->
      <svg xmlns="http://www.w3.org/2000/svg" class="icon alert-icon" width="24" height="24" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" fill="none" stroke-linecap="round" stroke-linejoin="round"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12.01" y2="8" /><polyline points="11 12 12 12 12 16 13 16" /></svg>
   </div>
    <div>${msg}</div>
  </div>
  <a class="btn-close" data-bs-dismiss="alert" aria-label="close"></a>
</div>
`).appendTo("#alertContainer");
}


function submitAction(name, form, customResponse) {
  let query = new URLSearchParams();
  query.append("pks", this.location.pathname.split("/").slice(-1)[0]);
  query.append("name", name);
  let url = model.actionUrl + "?" + query.toString();
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
          successAlert((await response.json())["msg"]);
        } else {
          if (response.status == 400) {
            return Promise.reject((await response.json())["msg"]);
          }
          return Promise.reject("Something went wrong!");
        }
      })
      .catch(async (error) => {
        await new Promise((r) => setTimeout(r, 500));
        dangerAlert(error);
      });
  }
}

$("#modal-action").on("show.bs.modal", function (event) {
    console.log('modal-action', event)
    let button = $(event.relatedTarget); // Button that triggered the modal
    let confirmation = button.data("confirmation");
    let form = button.data("form");
    let name = button.data("name");
    let submit_btn_text = button.data("submit-btn-text");
    let submit_btn_class = button.data("submit-btn-class");
    let customResponse = button.data("custom-response") === true;

    let modal = $(this);
    modal.find("#actionConfirmation").text(confirmation);
    let modalForm = modal.find("#modal-form");
    modalForm.html(form);
    let actionSubmit = modal.find("#actionSubmit");
    actionSubmit.text(submit_btn_text);
    actionSubmit.removeClass().addClass(`btn ${submit_btn_class}`);
    actionSubmit.unbind();
    actionSubmit.on("click", function (event) {
      const formElements = modalForm.find("form");
      const form = formElements.length ? formElements.get(0) : null;
      submitAction(name, form, customResponse);
    });
  });

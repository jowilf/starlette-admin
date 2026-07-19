// autoDismissMs: if set, the alert closes itself after that delay.
function dismissAlertAfter($alert, autoDismissMs) {
  if (!autoDismissMs) return;
  setTimeout(function () {
    const el = $alert[0];
    if (!el || !el.isConnected) return;
    if (window.bootstrap && window.bootstrap.Alert) {
      window.bootstrap.Alert.getOrCreateInstance(el).close();
    } else {
      $alert.remove();
    }
  }, autoDismissMs);
}

function successAlert(msg, autoDismissMs) {
    const $alert = $(`<div class="alert alert-success alert-dismissible mb-2" role="alert">
    <div class="alert-icon">
      <i class="fa-solid fa-circle-check icon"></i>
    </div>
    <div>
      <div class="alert-description">${msg}</div>
    </div>
    <a class="btn-close" data-bs-dismiss="alert" aria-label="close"></a>
  </div>
  `).appendTo("#alertContainer");
    dismissAlertAfter($alert, autoDismissMs);
}

function dangerAlert(msg, autoDismissMs) {
    const $alert = $(`<div class="alert alert-danger alert-dismissible mb-2" role="alert">
    <div class="alert-icon">
      <i class="fa-solid fa-circle-exclamation icon"></i>
    </div>
    <div>
      <div class="alert-description">${msg}</div>
    </div>
    <a class="btn-close" data-bs-dismiss="alert" aria-label="close"></a>
  </div>
  `).appendTo("#alertContainer");
    dismissAlertAfter($alert, autoDismissMs);
}

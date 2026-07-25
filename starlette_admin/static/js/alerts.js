window.StarletteAdmin = window.StarletteAdmin || {};

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

// Maps an alert type to its Bootstrap contextual class and semantic icon name.
const ALERT_TYPES = {
  success: { cls: "alert-success", icon: "flash.success" },
  danger: { cls: "alert-danger", icon: "flash.error" },
  warning: { cls: "alert-warning", icon: "flash.warning" },
  info: { cls: "alert-info", icon: "flash.info" },
};

// Default alert renderer. Themes may override window.StarletteAdmin.alertHandler
// to supply their own notification UI while keeping the same signature.
window.StarletteAdmin.alertHandler = function (type, msg, autoDismissMs) {
  const spec = ALERT_TYPES[type] || ALERT_TYPES.info;
  const iconClass = window.StarletteAdmin.getIcon(spec.icon, "");
  const $alert = $(
    `<div class="alert ${spec.cls} alert-dismissible mb-2" role="alert">
    <div class="alert-icon">
      <i class="${iconClass} icon" aria-hidden="true"></i>
    </div>
    <div>
      <div class="alert-description">${msg}</div>
    </div>
    <a class="btn-close" data-bs-dismiss="alert" aria-label="close"></a>
  </div>
  `
  ).appendTo("#alertContainer");
  dismissAlertAfter($alert, autoDismissMs);
};

// Renders an alert through the active handler.
function showAlert(type, msg, autoDismissMs) {
  window.StarletteAdmin.alertHandler(type, msg, autoDismissMs);
}

// Backward-compatible wrappers.
function successAlert(msg, autoDismissMs) {
  showAlert("success", msg, autoDismissMs);
}

function dangerAlert(msg, autoDismissMs) {
  showAlert("danger", msg, autoDismissMs);
}

function warningAlert(msg, autoDismissMs) {
  showAlert("warning", msg, autoDismissMs);
}

function infoAlert(msg, autoDismissMs) {
  showAlert("info", msg, autoDismissMs);
}

window.StarletteAdmin.showAlert = showAlert;

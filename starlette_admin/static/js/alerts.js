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

// Maps an alert type to its semantic class role and icon name.
const ALERT_TYPES = {
  success: { role: "alert.success", icon: "flash.success" },
  danger: { role: "alert.error", icon: "flash.error" },
  warning: { role: "alert.warning", icon: "flash.warning" },
  info: { role: "alert.info", icon: "flash.info" },
};

// Default alert renderer. Themes may override window.StarletteAdmin.alertHandler
// to supply their own notification UI while keeping the same signature.
window.StarletteAdmin.alertHandler = function (type, msg, autoDismissMs) {
  const spec = ALERT_TYPES[type] || ALERT_TYPES.info;
  const el = StarletteAdmin.template("alert");
  StarletteAdmin.addClass(el, StarletteAdmin.getClass(spec.role));
  StarletteAdmin.fillSlot(el, "icon", function (n) {
    n.className = StarletteAdmin.getIcon(spec.icon, "") + " icon";
  });
  StarletteAdmin.fillSlot(el, "message", function (n) {
    n.textContent = msg;
  });
  const $alert = $(el).appendTo("#alertContainer");
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

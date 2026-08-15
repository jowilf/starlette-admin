function get_file_icon(mimeType) {
  mapping = {
    image: "fa-file-image",
    audio: "fa-file-audio",
    video: "fa-file-video",
    "application/pdf": "fa-file-pdf",
    "application/msword": "fa-file-word",
    "application/vnd.ms-word": "fa-file-word",
    "application/vnd.oasis.opendocument.text": "fa-file-word",
    "application/vnd.openxmlformatsfficedocument.wordprocessingml":
      "fa-file-word",
    "application/vnd.ms-excel": "fa-file-excel",
    "application/vnd.openxmlformatsfficedocument.spreadsheetml":
      "fa-file-excel",
    "application/vnd.oasis.opendocument.spreadsheet": "fa-file-excel",
    "application/vnd.ms-powerpoint": "fa-file-powerpoint",
    "application/vnd.openxmlformatsfficedocument.presentationml":
      "fa-file-powerpoint",
    "application/vnd.oasis.opendocument.presentation": "fa-file-powerpoint",
    "text/plain": "fa-file-text",
    "text/html": "fa-file-code",
    "text/csv": "fa-file-csv",
    "application/json": "fa-file-code",
    "application/gzip": "fa-file-archive",
    "application/zip": "fa-file-archive",
  };
  if (mimeType)
    for (var key in mapping) {
      if (mimeType.search(key) === 0) {
        return mapping[key];
      }
    }
  return "fa-file";
}

$(document).on("click", ".copy-to-clipboard", function () {
  var btn = $(this);
  var icon = btn.find("i");
  var copyIcon = StarletteAdmin.getIcon("action.copy", "fa-solid fa-copy");
  var doneIcon = StarletteAdmin.getIcon("action.copy_done", "fa-solid fa-check");
  navigator.clipboard.writeText(btn.attr("data-copy-value")).then(function () {
    icon.attr("class", doneIcon);
    setTimeout(function () {
      icon.attr("class", copyIcon);
    }, 1500);
  });
});

function initJsonViewers(selector) {
  $(selector || "div.field-json[data-json]").each(function () {
    var el = $(this);
    var data = JSON.parse(el.attr("data-json"));
    el.jsonViewer(data, {
      collapsed: el.data("collapsed"),
      withQuotes: el.data("withQuotes"),
      withLinks: el.data("withLinks"),
      rootCollapsable: el.data("rootCollapsable"),
    });
  });
}

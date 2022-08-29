$("#{{field.name}}").on("change", function () {
  if ($("#{{field.name}}").get(0).files.length > 0) {
    $("#_{{field.name}}-delete").prop("checked", false);
    $("#_{{field.name}}-delete").prop("disabled", true);
  } else {
    $("#_{{field.name}}-delete").prop("checked", false);
    $("#_{{field.name}}-delete").prop("disabled", false);
  }
});

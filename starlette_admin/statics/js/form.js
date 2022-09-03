$("select.field-tags, select.field-enum").each(function () {
  $(this).select2();
});

$("div.field-json").each(function () {
  let name = this.attr("id");
  new JSONEditor(
    this.get(),
    {
      mode: "tree",
      modes: ["code", "tree"],
      onChangeText: function (json) {
        $(`input[name=${name}]`).val(json);
      },
    },
    $(`input[name=${name}]`).val()
  );
});

$(':input[data-role="file-field-delete"]').each(function () {
  let el = $(this);
  related = $(`#${el.data("for")}`);
  related.on("change", function () {
    if (related.get(0).files.length > 0) {
      el.prop("checked", false);
      el.prop("disabled", true);
    } else {
      el.prop("checked", false);
      el.prop("disabled", false);
    }
  });
});

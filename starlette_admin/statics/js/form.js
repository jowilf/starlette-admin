(function () {
  function processElement(element) {
    $('select.field-tags, select.field-enum[data-role="select2"]', element).each(function () {
      $(this).select2();
    });

    $("div.field-json", element).each(function () {
      let el = $(this);
      let name = el.attr("id");
      new JSONEditor(
        this,
        {
          modes: String(el.data("modes")).split(","),
          onChangeText: function (json) {
            $(`input[name=${name}]`).val(json);
          },
        },
        JSON.parse($(`input[name=${name}]`).val())
      );
    });

    $(':input[data-role="file-field-delete"]', element).each(function () {
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

    $("select.field-has-one, select.field-has-many", element).each(function () {
      let el = $(this);
      el.select2({
        allowClear: true,
        ajax: {
          url: el.data("url"),
          dataType: "json",
          data: function (params) {
            return {
              skip: ((params.page || 1) - 1) * 20,
              limit: 20,
              select2: true,
              where: params.term,
            };
          },
          processResults: function (data, params) {
            return {
              results: $.map(data.items, function (obj) {
                obj.id = obj[el.data("pk")];
                return obj;
              }),
              pagination: {
                more: (params.page || 1) * 20 < data.total,
              },
            };
          },
          cache: true,
        },
        minimumInputLength: 0,
        templateResult: function (item) {
          if (!item.id) return "Search...";
          return $(item._select2_result);
        },
        templateSelection: function (item) {
          if (!item.id) return "Search...";
          if (item._select2_selection) return $(item._select2_selection);
          return $(item.text);
        },
      });
      data = el.data("initial");
      if (data)
        $.ajax({
          url: el.data("url"),
          data: {
            select2: true,
            pks: String(data).split(","),
          },
          traditional: true,
          dataType: "json",
        }).then(function (data) {
          for (obj of data.items) {
            obj.id = obj[el.data("pk")];
            var option = new Option(obj._select2_selection, obj.id, true, true);
            el.append(option).trigger("change");
            el.trigger({
              type: "select2:select",
              params: {
                data: obj,
              },
            });
          }
        });
    });
    $("input.field-datetime", element).each(function () {
      let el = $(this);
      el.flatpickr({
        enableTime: true,
        allowInput: true,
        enableSeconds: true,
        time_24hr: true,
        altInput: true,
        dateFormat: "Y-m-d H:i:S",
        altFormat: el.data("alt-format"),
        locale: el.data("locale"),
      });
    });

    $("input.field-date", element).each(function () {
      let el = $(this);
      el.flatpickr({
        enableTime: false,
        allowInput: true,
        altInput: true,
        dateFormat: "Y-m-d",
        altFormat: el.data("alt-format"),
        locale: el.data("locale"),
      });
    });

    $("input.field-time", element).each(function () {
      let el = $(this);
      el.flatpickr({
        noCalendar: true,
        enableTime: true,
        allowInput: true,
        enableSeconds: true,
        time_24hr: true,
        altInput: true,
        dateFormat: "H:i:S",
        altFormat: el.data("alt-format"),
        locale: el.data("locale"),
      });
    });

    $("button.field-list-btn-remove", element).each(function () {
      var el = $(this);
      el.on("click", function () {
        el.closest(".field-list-item").remove();
      });
    });

    $(".field-list-btn-add", element).each(function () {
      var el = $(this);
      el.on("click", function () {
        var field = el.closest(".field-list");
        var baseName = field.attr("id");
        var idx = field
          .children("#" + $.escapeSelector(baseName) + "-next-index")
          .val();
        var template = $(field.children(".template").text());
        function update_attr(el, attr) {
          $(`[${attr}]`, el).each(function () {
            var me = $(this);
            prefix = baseName + "." + idx;
            var val = me.attr(attr);
            val = prefix + (val ? "." + val : "");
            me.attr(attr, val);
          });
        }
        update_attr(template, "id");
        update_attr(template, "name");
        update_attr(template, "for");

        template.appendTo(field.children(".list-container"));
        field
          .children("#" + $.escapeSelector(baseName) + "-next-index")
          .val(parseInt(idx) + 1);
        processElement(template);
        $("input:first", template).focus();
      });
    });

    // TinyMCEEditorField integration

    let tinyMCEOptions = {
      height: 300,
      menubar: false,
      statusbar: false,
      toolbar:
        "undo redo | formatselect | " +
        "bold italic backcolor | alignleft aligncenter " +
        "alignright alignjustify | bullist numlist outdent indent | " +
        "removeformat",
      content_style:
        "body { font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif; font-size: 14px; -webkit-font-smoothing: antialiased; }",
    };
    if (localStorage.getItem("tablerTheme") === "dark") {
      tinyMCEOptions.skin = "oxide-dark";
      tinyMCEOptions.content_css = "dark";
    }
    $(".field-tinymce-editor", element).each(function(){
      $(this).tinymce(tinyMCEOptions);
    });

    // end TinyMCEEditorField integration
  }

  $(function () {
    processElement(document);
  });
})();

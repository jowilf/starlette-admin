/**
 * List of registered field initializer callbacks.
 * @type {function(HTMLElement)[]}
 */
const fieldInitializers = [];

/**
 * Register a new field initializer callback.
 * @param {function(HTMLElement)[]} initializer - The initializer function to register.
 */
function registerFieldInitializer(initializer) {
  fieldInitializers.push(initializer);
}

/**
 * Initialize fields
 * @param {HTMLElement} element
 */
function initializeFields(element) {
  fieldInitializers.forEach((initializer) => {
    initializer(element);
  });
}

// Public API for plugin field JS. Bare globals above stay for backward
// compatibility; this namespace is what plugins and docs target.
window.StarletteAdmin = window.StarletteAdmin || {};
window.StarletteAdmin.registerFieldInitializer = registerFieldInitializer;
window.StarletteAdmin.initializeFields = initializeFields;

/**
 * Flatpickr's altInput does not inherit the `readonly` attribute from the
 * source input, so it stays editable even when readOnly is set. Returns an
 * `onReady` callback that copies the flag onto the altInput.
 * @param {boolean} readOnly
 */
function markAltInputReadOnly(readOnly) {
  return function (selectedDates, dateStr, instance) {
    if (readOnly) {
      instance.altInput.readOnly = true;
    }
  };
}

function toSlug(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

$(function () {
  initializeFields(document);
});

// Show the loading modal on submit so large file uploads give visible feedback.
$(function () {
  $('form[enctype="multipart/form-data"]').on("submit", function () {
    $('[data-sa-hook="modal-loading"]').modal("show");
  });
});

registerFieldInitializer(function (element) {
  $('select.field-tags, select.field-enum[data-role="select2"]', element).each(
    function () {
      $(this).select2({ width: "100%" });
    }
  );

  $("div.field-json", element).each(function () {
    let el = $(this);
    let name = el.attr("id");
    new JSONEditor(
      this,
      {
        modes: String(el.data("modes")).split(","),
        schema: el.data("validationSchema") ?? undefined,
        onChangeText: function (json) {
          $(`input[name='${name}']`).val(json);
        },
      },
      JSON.parse($(`input[name='${name}']`).val())
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
      width: "100%",
      allowClear: true,
      ajax: {
        url: el.data("url"),
        dataType: "json",
        data: function (params) {
          return {
            skip: ((params.page || 1) - 1) * 20,
            limit: 20,
            q: params.term,
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
        return $(item._meta.select2.result);
      },
      templateSelection: function (item) {
        if (!item.id) return "Search...";
        if (item._meta) return $(item._meta.select2.selection);
        return $(item.text);
      },
    });
    data = el.data("initial");
    if (data)
      $.ajax({
        url: el.data("url") + "?" + $.param({ pks: data }, true),
        dataType: "json",
      }).then(function (data) {
        for (obj of data.items) {
          obj.id = obj[el.data("pk")];
          var option = new Option(
            obj._meta.select2.selection,
            obj.id,
            true,
            true
          );
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
    let readOnly = el.prop("readonly");
    el.flatpickr({
      enableTime: true,
      allowInput: !readOnly,
      clickOpens: !readOnly,
      enableSeconds: true,
      time_24hr: true,
      altInput: true,
      dateFormat: "Y-m-d H:i:S",
      altFormat: el.data("alt-format"),
      locale: el.data("locale"),
      onReady: markAltInputReadOnly(readOnly),
    });
  });

  $("input.field-date", element).each(function () {
    let el = $(this);
    let readOnly = el.prop("readonly");
    el.flatpickr({
      enableTime: false,
      allowInput: !readOnly,
      clickOpens: !readOnly,
      altInput: true,
      dateFormat: "Y-m-d",
      altFormat: el.data("alt-format"),
      locale: el.data("locale"),
      onReady: markAltInputReadOnly(readOnly),
    });
  });

  $("input.field-time", element).each(function () {
    let el = $(this);
    let readOnly = el.prop("readonly");
    el.flatpickr({
      noCalendar: true,
      enableTime: true,
      allowInput: !readOnly,
      clickOpens: !readOnly,
      enableSeconds: true,
      time_24hr: true,
      altInput: true,
      dateFormat: "H:i:S",
      altFormat: el.data("alt-format"),
      locale: el.data("locale"),
      onReady: markAltInputReadOnly(readOnly),
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
      initializeFields(template);
      $("input:first", template).focus();
    });
  });

  // Inline formsets
  $(".inline-delete-btn", element).each(function () {
    var el = $(this);
    el.on("click", function () {
      var row = el.closest(".inline-row");
      if (row.find('input[name$=".pk"]').length === 0) {
        row.remove();
      } else {
        row.find(".inline-delete-value").val("1");
        row.addClass("d-none");
      }
    });
  });

  $(".inline-add-row", element).each(function () {
    var el = $(this);
    el.on("click", function () {
      var formset = el.closest(".inline-formset");
      var prefix = formset.data("inline-prefix");
      var templateHtml = formset.find(".inline-template").text();
      var rows = formset.find(".inline-row");
      var maxIndex = -1;
      rows.each(function () {
        var idx = parseInt($(this).data("inline-index"));
        if (!isNaN(idx) && idx > maxIndex) {
          maxIndex = idx;
        }
      });
      var newIndex = maxIndex + 1;
      var newHtml = templateHtml.replace(/__prefix__/g, newIndex);
      var newRow = $(newHtml);
      newRow.attr("data-inline-index", newIndex);
      newRow.removeClass("d-none");
      newRow.find(".inline-delete-value").val("");
      formset.find(".inline-rows").append(newRow);
      initializeFields(newRow);
      newRow.find("input:visible:first").focus();
    });
  });

  // SlugField auto-populate
  $("input.field-slug[data-populate-from]", element).each(function () {
    var slugEl = $(this);
    var sourceId = slugEl.data("populate-from");
    var source = $("#" + sourceId, element);
    if (!source.length) source = $("#" + sourceId);
    var autoValue = slugEl.val();
    slugEl.on("input", function () {
      autoValue = null; // user took over
    });
    source.on("input", function () {
      if (autoValue !== null) {
        var generated = toSlug($(this).val());
        slugEl.val(generated);
        autoValue = generated;
      }
    });
  });

  // TinyMCEEditorField integration

  $(".field-tinymce-editor", element).each(function () {
    let options = $(this).data("options");
    const root = document.documentElement;
    const isDark =
      root.getAttribute("data-bs-theme") === "dark" ||
      root.classList.contains("dark") ||
      localStorage.getItem("tablerTheme") === "dark";
    if (isDark) {
      options.skin = "oxide-dark";
      options.content_css = "dark";
    }
    $(this).tinymce(options);
  });

  // end TinyMCEEditorField integration
});

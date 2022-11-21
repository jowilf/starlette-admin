$(function () {
  var selectedRows = [];
  var dt_columns = [];

  (function () {
    let fringe = model.fields;
    while (fringe.length > 0) {
      let field = fringe.shift(0);
      if (field.type === "CollectionField")
        fringe = field.fields
          .map((f) => {
            // Produce nested name (ex: category.name)
            f.name = field.name + "." + f.name;
            f.label = field.label + "." + f.label;
            return f;
          })
          .concat(fringe);
      else if (field.type === "ListField") {
        // To reduce complexity, List of CollectionField will render as json
        if (field.field.type == "CollectionField") {
          $("#table-header").append(`<th>${field.label}</th>`);
          dt_columns.push({
            name: field.name,
            data: field.name,
            orderable: field.field.orderable,
            searchBuilderType: field.search_builder_type,
            render: function (data, type, full, meta) {
              return render[field.field.render_function_key](
                data,
                type,
                full,
                meta,
                field
              );
            },
          });
        } else {
          field.field.name = field.name;
          field.field.label = field.label;
          fringe.unshift(field.field);
        }
      } else if (!field.exclude_from_list) {
        $("#table-header").append(`<th>${field.label}</th>`);
        dt_columns.push({
          name: field.name,
          data: field.name,
          orderable: field.orderable,
          searchBuilderType: field.search_builder_type,
          render: function (data, type, full, meta) {
            return render[field.render_function_key](
              data,
              type,
              full,
              meta,
              field
            );
          },
        });
      }
    }
  })();

  // Buttons declarations

  buttons = [];
  export_buttons = [];
  if (model.exportTypes.includes("csv"))
    export_buttons.push({
      extend: "csv",
      text: '<i class="fa-solid fa-file-csv"></i> CSV',
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export",
      },
    });
  if (model.exportTypes.includes("excel"))
    export_buttons.push({
      extend: "excel",
      text: '<i class="fa-solid fa-file-excel"></i> Excel',
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export",
      },
    });
  if (model.exportTypes.includes("pdf"))
    export_buttons.push({
      extend: "pdf",
      text: '<i class="fa-solid fa-file-pdf"></i> PDF',
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export",
      },
    });
  if (model.exportTypes.includes("print"))
    export_buttons.push({
      extend: "print",
      text: '<i class="fa-solid fa-print"></i> Print',
      exportOptions: {
        columns: model.exportColumns,
        orthogonal: "export",
      },
    });
  if (export_buttons.length > 0)
    buttons.push({
      extend: "collection",
      text: '<i class="fa-solid fa-file-export"></i> Export',
      className: "",
      buttons: export_buttons,
    });
  noInputCondition = function (cn) {
    return {
      conditionName: cn,
      init: function (a) {
        a.s.dt.one("draw.dtsb", function () {
          a.s.topGroup.trigger("dtsb-redrawLogic");
        });
      },
      inputValue: function () {},
      isInputValid: function () {
        return !0;
      },
    };
  };
  if (model.columnVisibility)
    buttons.push({
      extend: "colvis",
      text: '<i class="fa-solid fa-eye"></i> Column visibility',
    });

  if (model.searchBuilder)
    buttons.push({
      extend: "searchBuilder",
      text: '<i class="fa-solid fa-filter"></i> Filter',
      config: {
        columns: model.searchColumns,
        conditions: {
          bool: {
            false: noInputCondition("False"),
            true: noInputCondition("True"),
            null: noInputCondition("Empty"),
            "!null": noInputCondition("Not Empty"),
          },
          default: {
            null: noInputCondition("Empty"),
            "!null": noInputCondition("Not Empty"),
          },
        },
        greyscale: true,
      },
    });

  // End Buttons declarations

  // Search Builder
  function extractCriteria(c) {
    var d = {};
    if ((c.logic && c.logic == "OR") || c.logic == "AND") {
      d[c.logic.toLowerCase()] = [];
      c.criteria.forEach((v) => {
        d[c.logic.toLowerCase()].push(extractCriteria(v));
      });
    } else {
      if (c.type.startsWith("moment-")) {
        searchFormat = model.fields.find(
          (f) => f.name == c.origData
        )?.search_format;
        if (!searchFormat) searchFormat = moment.defaultFormat;
        c.value = [];
        if (c.value1) {
          c.value1 = moment(c.value1).format(searchFormat);
          c.value.push(c.value1);
        }
        if (c.value2) {
          c.value2 = moment(c.value2).format(searchFormat);
          c.value.push(c.value2);
        }
      } else if (c.type == "num") {
        c.value = [];
        if (c.value1) {
          c.value1 = Number(c.value1);
          c.value.push(c.value1);
        }
        if (c.value2) {
          c.value2 = Number(c.value2);
          c.value.push(c.value2);
        }
      }
      cnd = {};
      c_map = {
        "=": "eq",
        "!=": "neq",
        ">": "gt",
        ">=": "ge",
        "<": "lt",
        "<=": "le",
        contains: "contains",
        starts: "startswith",
        ends: "endswith",
        "!contains": "not_contains",
        "!starts": "not_startswith",
        "!ends": "not_endswith",
        null: "is_null",
        "!null": "is_not_null",
        false: "is_false",
        true: "is_true",
      };
      if (c.condition == "between") {
        cnd["between"] = c.value;
      } else if (c.condition == "!between") {
        cnd["not_between"] = c.value;
      } else if (c_map[c.condition]) {
        cnd[c_map[c.condition]] = c.value1 || "";
      }
      d[c.origData] = cnd;
    }
    return d;
  }
  // End Search builder

  // tables
  var table = $("#dt").DataTable({
    dom: "r<'table-responsive't><'card-footer d-flex align-items-center'<'m-0'i><'m-0 ms-auto'p>>",
    paging: true,
    lengthChange: true,
    searching: true,
    info: true,
    colReorder: true,
    searchHighlight: true,
    responsive: model.responsiveTable,
    serverSide: true,
    scrollX: false,
    lengthMenu: model.lengthMenu,
    pagingType: "full_numbers",
    pageLength: model.pageSize,
    select: {
      style: "multi",
      selector: "td:first-child .form-check-input",
      className: "row-selected",
    },
    //  buttons: buttons,
    language: {
      info: "Showing <strong>_START_</strong> to <strong>_END_</strong> off <strong>_TOTAL_</strong> records",
      infoEmpty: "No matching records found",
      infoFiltered: "",
      searchBuilder: {
        button: {
          _: '<i class="fa-solid fa-filter"></i> Filter (%d)',
        },
      },
      buttons: {
        pageLength: {
          _: "%d",
          "-1": "All",
        },
      },
    },
    ajax: function (data, callback, settings) {
      //console.log(data);
      order = [];
      data.order.forEach((o) => {
        const { column, dir } = o;
        order.push(`${data.columns[column].data} ${dir}`);
      });
      where = null;
      if (data.searchBuilder && !jQuery.isEmptyObject(data.searchBuilder)) {
        where = extractCriteria(data.searchBuilder);
        //console.log(where);
      }
      query = {
        skip: settings._iDisplayStart,
        limit: settings._iDisplayLength,
        order_by: order,
      };
      if (data.search.value != "") query.where = data.search.value;
      else if (where) query.where = JSON.stringify(where);
      $.ajax({
        url: model.apiUrl,
        type: "get",
        data: query,
        traditional: true,
        dataType: "json",
        success: function (data, status, xhr) {
          total = data.total;
          data = data.items;
          data.forEach((d) => {
            d.DT_RowId = d[model.pk];
          });
          callback({
            recordsFiltered: total,
            data: data,
          });
        },
      });
    },
    columns: [
      {
        data: "DT_RowId",
        orderable: false,
        checkboxes: {
          selectRow: true,
          selectAllRender:
            '<input class="form-check-input dt-checkboxes" type="checkbox">',
        },
        render: render.col_0,
      },
      {
        data: "DT_RowId",
        orderable: false,
        render: render.col_1,
      },
      ...dt_columns,
    ],
    order: [],
  });

  new $.fn.dataTable.Buttons(table, {
    name: "main",
    buttons: buttons,
    dom: {
      button: {
        className: "btn btn-secondary",
      },
    },
  });
  new $.fn.dataTable.Buttons(table, {
    name: "pageLength",
    buttons: [
      {
        extend: "pageLength",
        className: "btn",
      },
    ],
    dom: {
      button: {
        className: "",
      },
    },
  });

  table.buttons("main", null).container().appendTo("#btn_container");
  table
    .buttons("pageLength", null)
    .container()
    .appendTo("#pageLength_container");

  $("#searchInput").on("keyup", function () {
    table.search($(this).val()).draw();
  });

  function onSelectChange() {
    selectedRows = table.rows({ selected: true }).ids().toArray();
    if (table.rows({ selected: true }).count() == 0)
      $("#multi-delete-btn").hide();
    else $("#multi-delete-btn").show();
    $("#multi-delete-btn span").text(table.rows({ selected: true }).count());
  }

  table
    .on("select", function (e, dt, type, indexes) {
      onSelectChange();
    })
    .on("deselect", function (e, dt, type, indexes) {
      onSelectChange();
    });

  $("#modal-delete-btn").on("click", function () {
    $("#modal-delete").modal("hide");
    $("#modal-loading").modal("show");
    query = new URLSearchParams(selectedRows.map((s) => ["pks", s])).toString();
    fetch(model.apiUrl + "?" + query, {
      method: "DELETE",
    })
      .then(async (response) => {
        if (response.ok) {
          await new Promise((r) => setTimeout(r, 500));
          $("#modal-loading").modal("hide");
          table.ajax.reload();
          $("#select-all").prop("checked", false);
          $("#multi-delete-btn").hide();
        } else return Promise.reject();
      })
      .catch(async (error) => {
        await new Promise((r) => setTimeout(r, 500));
        $("#modal-loading").modal("hide");
        $("#modal-error").modal("show");
      });
  });

  $("#multi-delete-btn").on("click", function () {
    $("#modal-delete-body span").text(
      table.rows({ selected: true }).count() + ` ${model.label}`
    );
    $("#modal-delete").modal("show");
  });

  $('[data-toggle="tooltip"]').tooltip();
});

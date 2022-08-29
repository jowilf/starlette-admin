buttons = [];
export_buttons = [];
export_columns = {{model._export_columns_selector() | tojson | safe}};
//console.log(export_columns);
if (exportTypes.includes('csv'))
  export_buttons.push({
    extend: "csv",
    text: '<i class="fa-solid fa-file-csv"></i> CSV',
    exportOptions: {
      columns: export_columns,
      orthogonal: "export",
    },
  });
if (exportTypes.includes('excel'))
  export_buttons.push({
    extend: "excel",
    text: '<i class="fa-solid fa-file-excel"></i> Excel',
    exportOptions: {
      columns: export_columns,
      orthogonal: "export",
    },
  });
if (exportTypes.includes('pdf'))
  export_buttons.push({
    extend: "pdf",
    text: '<i class="fa-solid fa-file-pdf"></i> PDF',
    exportOptions: {
      columns: export_columns,
      orthogonal: "export",
    },
  });
if (exportTypes.includes('print'))
  export_buttons.push({
    extend: "print",
    text: '<i class="fa-solid fa-print"></i> Print',
    exportOptions: {
      columns: export_columns,
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
if (columnVisibility)
  buttons.push({
    extend: "colvis",
    text: '<i class="fa-solid fa-eye"></i> Column visibility',
  });

if (searchBuilder)
  buttons.push({
    extend: "searchBuilder",
    text: '<i class="fa-solid fa-filter"></i> Filter',
    config: {
      columns: {{model._search_columns_selector() | tojson | safe}},
      conditions: {
        bool: {
          false: noInputCondition("False"),
          true: noInputCondition("True"),
          null: noInputCondition("Empty"),
          "!null": noInputCondition("Not Empty"),
        },
        'default': {
          null: noInputCondition("Empty"),
          "!null": noInputCondition("Not Empty"),
        },
      },
      greyscale: true,
    },
  });

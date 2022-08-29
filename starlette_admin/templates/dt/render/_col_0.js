dt_columns.push({
  data: "DT_RowId",
  orderable: false,
  checkboxes: {
    selectRow: true,
    selectAllRender:
      '<input class="form-check-input dt-checkboxes" type="checkbox">',
  },
  render: function (data, type, full, meta) {
    return '<input class="form-check-input dt-checkboxes" type="checkbox">';
  },
});

dt_columns.push({
  name: "{{field.name}}",
  data: "{{field.name}}",
  orderable: columns["{{field.name}}"].orderable,
  searchBuilderType: "{{field.search_builder_type}}",
  render: function (data, type, full, meta) {
    if (data == null) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    if (type != "display") return data;
    return `<div class="d-flex flex-row">${(Array.isArray(data) ? data : [data])
      .map((v) =>
        v
          ? `<span class="text-center text-success me-1"><i class="fa-solid fa-check-circle fa-lg"></i></span>`
          : `<span class="text-center text-danger me-1"><i class="fa-solid fa-times-circle fa-lg"></i></span>`
      )
      .join("")}</div>`;
  },
});

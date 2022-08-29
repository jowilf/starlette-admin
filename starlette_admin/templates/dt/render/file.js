dt_columns.push({
  name: "{{field.name}}",
  data: "{{field.name}}",
  orderable: columns["{{field.name}}"].orderable,
  searchBuilderType: "{{field.search_builder_type}}",
  render: function (data, type, full, meta) {
    if (!data) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    if (Array.isArray(data) && type != "display") {
      return data.map((v) => v.url);
    } else if (type != "display") return data.url;
    data = Array.isArray(data) ? data : [data];
    return `<div class="d-flex flex-column">${data
      .map(
        (e) =>
          `<a href="${e.url?.escape()}" class="btn-link">
          <i class="fa-solid fa-fw ${get_file_icon(
            e.content_type
          )}"></i><span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title="${
            e.filename?.escape()
          }" style="max-width: 30em;">${e.filename?.escape()}</span></a>`
      )
      .join("")}</div>`;
  },
});

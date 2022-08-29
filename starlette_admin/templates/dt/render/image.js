dt_columns.push({
  name: "{{field.name}}",
  data: "{{field.name}}",
  orderable: columns["{{field.name}}"].orderable,
  searchBuilderType: "{{field.search_builder_type}}",
  render: function (data, type, full, meta) {
    if (!data) return null_column()
    if (Array.isArray(data) && data.length == 0) return empty_column();
    if (Array.isArray(data) && type != "display") {
      return data.map((v) => v.url);
    } else if (type != "display") return data.url;
    let urls = Array.isArray(data)
      ? data.map((v) => v.url.escape()): [data.url.escape()];
    return `<div class="d-flex">${urls
      .map(
        (url) =>
          `<div class="p-1"><span class="avatar avatar-sm" style="background-image: url(${url})"></span></div>`
      )
      .join("")}</div>`;
  },
});

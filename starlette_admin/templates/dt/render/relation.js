//{% set foreign_model = (field.identity | to_model)%}
dt_columns.push({
  name: "{{field.name}}",
  data: "{{field.name}}",
  orderable: columns["{{field.name}}"].orderable,
  searchBuilderType: "{{field.search_builder_type}}",
  render: function (data, type, full, meta) {
    if (!data) return null_column();
    if (Array.isArray(data) && data.length == 0) return empty_column();
    let fpk = "{{foreign_model.pk_attr}}";
    if (type != "display")
      return (Array.isArray(data) ? data : [data]).map((v) => v["_repr"]?.toString()?.escape()).join(",");
    return `<div class="d-flex flex-row">${(Array.isArray(data) ? data : [data])
      .map(
        (e) =>
          `<a class='mx-1 btn-link' href="{{ url_for(__name__ ~ ':detail', identity=foreign_model.identity,pk= '${e[fpk]}') }}"><span class='m-1 py-1 px-2 badge bg-blue-lt lead d-inline-block text-truncate' data-toggle="tooltip" data-placement="bottom" title='${e._repr.toString().escape()}'  style="max-width: 20em;">${e._repr.toString().escape()}</span></a>`
      )
      .join("")}</div>`;
  },
});

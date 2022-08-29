dt_columns.push({
    name: "{{field.name}}",
    data: "{{field.name}}",
    orderable: columns["{{field.name}}"].orderable,
    searchBuilderType: "{{field.search_builder_type}}",
    render: function (data, type, full, meta) {
      if (data==null) return null_column();
      if (Array.isArray(data) && data.length == 0) return empty_column();
      if (type != "display")
        return (Array.isArray(data) ? data : [data]).map((d)=>d.toString().escape()).join(",");
      return `<span class="align-middle d-inline-block text-truncate" data-toggle="tooltip" data-placement="bottom" title='${data.toString().escape()}' style="max-width: 30em;">
          ${(Array.isArray(data) ? data : [data]).map((d)=>d.toString().escape()).map((d)=>'<a href="mailto:'+d+'">'+d+'</a>').join(",")}</span>`;
    },
  });
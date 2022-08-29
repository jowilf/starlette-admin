{% set foreign_model = (field.identity | to_model) %}
$("#{{field.name}}").select2({
    allowClear: true,
    ajax: {
    url: "{{ url_for(__name__ ~ ':api', identity=foreign_model.identity)  | safe}}",
    dataType: 'json',
    data: function (params) {
        return {
            skip: ((params.page|| 1)-1) * 20,
            limit: 20,
            select2: true,
            where: params.term
        };
    },
    processResults: function (data, params) {
        return {
            results: $.map(data.items, function(obj) {
                obj.id = obj["{{foreign_model.pk_attr}}"];
                return obj;
            }),
            pagination: {
                more: (params.page|| 1)*20 < data.total
            }
        };
    },
    cache: true
    },
    minimumInputLength: 0,
    templateResult: function (item){
    if(!item.id) return 'Search...'
    return $(item._select2_result);
    },
    templateSelection: function (item) {
        if(!item.id) return 'Search...'
        if(item._select2_selection) return $(item._select2_selection);
        return $(item.text);
    }
});
{%if data%}
$.ajax({
  url: `{{ url_for(__name__ ~ ':api', identity=foreign_model.identity)  | safe}}`,
  data: {
    select2: true,
    pks: {{data| tojson | safe}},
  },
  traditional: true,
  dataType: "json",
}).then(function (data) {
  for (obj of data.items) {
    obj.id = obj["{{foreign_model.pk_attr}}"];
    var option = new Option(obj._select2_selection, obj.id, true, true);
    $("#{{field.name}}").append(option).trigger("change");
    $("#{{field.name}}").trigger({
      type: "select2:select",
      params: {
        data: obj,
      },
    });
  }
});

{% endif %}
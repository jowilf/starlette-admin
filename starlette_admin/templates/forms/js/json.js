const jsonEditor{{ field.name | title}} = new JSONEditor(document.getElementById("{{field.name}}"), {
    mode: "tree",
    modes: ["code", "tree"],
    onChangeText: function (json) {
        $("input[name={{field.name}}]").val(json);
    },
},{% if data %}{{(data|safe) if is_form_value else (data|tojson|safe)}}{% endif %});

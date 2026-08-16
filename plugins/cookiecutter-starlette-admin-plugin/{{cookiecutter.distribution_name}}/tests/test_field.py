def test_field_template_resolves_by_plain_and_prefixed_path(admin):
    plain = admin.templates.env.get_template(
        "plugins/{{ cookiecutter.plugin_slug }}/fields/form/slider.html"
    )
    prefixed = admin.templates.env.get_template(
        "@{{ cookiecutter.plugin_slug }}/fields/form/slider.html"
    )
    assert plain.filename == prefixed.filename


def test_create_form_renders_slider_widget(client):
    response = client.get("/admin/product/create")
    assert "data-sa-slider" in response.text
    assert "plugins/{{ cookiecutter.plugin_slug }}/css/slider.css" in response.text
    assert "plugins/{{ cookiecutter.plugin_slug }}/js/slider.js" in response.text


def test_create_and_read_back_discount(client):
    response = client.post(
        "/admin/product/create",
        data={"name": "Widget", "discount": "35"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    detail = client.get("/admin/product/detail", params={"pk": "1"})
    assert detail.status_code == 200
    assert "35%" in detail.text

def test_field_template_resolves_by_plain_and_prefixed_path(admin):
    plain = admin.templates.env.get_template(
        "plugins/{{ cookiecutter.plugin_slug }}/fields/form/rating.html"
    )
    prefixed = admin.templates.env.get_template("@{{ cookiecutter.plugin_slug }}/fields/form/rating.html")
    assert plain.filename == prefixed.filename


def test_create_form_renders_rating_widget(client):
    response = client.get("/admin/product/create")
    assert "data-sa-rating" in response.text
    assert "plugins/{{ cookiecutter.plugin_slug }}/css/rating.css" in response.text
    assert "plugins/{{ cookiecutter.plugin_slug }}/js/rating.js" in response.text


def test_create_and_read_back_rating(client):
    response = client.post(
        "/admin/product/create",
        data={"name": "Widget", "rating": "4"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    detail = client.get("/admin/product/detail", params={"pk": "1"})
    assert detail.status_code == 200
    assert detail.text.count("sa-rating-star-filled") == 4

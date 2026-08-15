def test_plugin_registers_under_its_name(admin, plugin):
    assert admin.plugins == {"{{ cookiecutter.plugin_slug }}": plugin}


def test_list_page_loads(client):
    response = client.get("/admin/product/list")
    assert response.status_code == 200


def test_create_page_loads(client):
    response = client.get("/admin/product/create")
    assert response.status_code == 200

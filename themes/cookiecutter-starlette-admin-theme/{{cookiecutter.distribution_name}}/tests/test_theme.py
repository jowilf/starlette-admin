def test_theme_is_active(admin, theme):
    assert admin.theme is theme


def test_theme_uses_custom_icon_set(theme):
    icon_set = theme.get_icon_set()
    assert icon_set.library == "tabler"
    # The full core vocabulary is mapped, so resolution never falls through.
    assert icon_set.icons["list.new"] == "ti ti-plus"
    assert icon_set.icons["default_actions.delete"] == "ti ti-trash"


def test_list_page_loads(client):
    response = client.get("/admin/product/list")
    assert response.status_code == 200


def test_create_page_loads(client):
    response = client.get("/admin/product/create")
    assert response.status_code == 200


def test_theme_stylesheet_is_linked(client):
    # base.html appends the theme stylesheet to the core_css block.
    response = client.get("/admin/product/list")
    assert "css/theme.css" in response.text


def test_icon_stylesheet_is_linked(client):
    response = client.get("/admin/product/list")
    assert "tabler-icons.min.css" in response.text

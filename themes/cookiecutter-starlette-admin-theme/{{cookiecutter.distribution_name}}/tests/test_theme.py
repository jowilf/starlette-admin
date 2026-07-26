def test_theme_is_active(admin, theme):
    assert admin.theme is theme


def test_theme_uses_custom_icon_set(theme):
    icon_set = theme.get_icon_set()
    # The full core vocabulary is mapped, so resolution never falls through.
    assert icon_set.icons["list.new"] == "ti ti-plus"
    assert icon_set.icons["default_actions.delete"] == "ti ti-trash"


def test_full_vocabulary_mapped(theme):
    from starlette_admin.theme import CoreIcons

    icon_set = theme.get_icon_set()
    missing = CoreIcons.icons.keys() - icon_set.icons.keys()
    assert not missing, f"unmapped core icon keys: {sorted(missing)}"


def test_icon_classes_use_ti_prefix(theme):
    icon_set = theme.get_icon_set()
    bad = {k: v for k, v in icon_set.icons.items() if not v.startswith("ti ")}
    assert not bad, f"non-tabler icon classes: {bad}"


def test_class_roles_are_core_vocabulary(theme):
    from starlette_admin.theme import CoreClasses

    # Unmapped roles fall through to CoreClasses, so the map only needs the
    # roles this theme restyles. Every mapped role must exist in the core
    # vocabulary, otherwise it is a typo that silently styles nothing.
    class_map = theme.get_class_map()
    unknown = class_map.classes.keys() - CoreClasses.classes.keys()
    assert not unknown, f"unknown class roles: {sorted(unknown)}"


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

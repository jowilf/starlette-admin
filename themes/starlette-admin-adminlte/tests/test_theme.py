def test_theme_is_active(admin, theme):
    assert admin.theme is theme


def test_theme_uses_core_icon_set(theme):
    from starlette_admin.theme import CoreIcons

    icon_set = theme.get_icon_set()
    assert isinstance(icon_set, CoreIcons)
    assert icon_set.library == "fontawesome"
    assert icon_set.icons["list.new"] == "fa-solid fa-plus"
    assert icon_set.icons["default_actions.delete"] == "fa-solid fa-trash"


def test_full_vocabulary_mapped(theme):
    from starlette_admin.theme import CoreIcons

    icon_set = theme.get_icon_set()
    missing = CoreIcons.icons.keys() - icon_set.icons.keys()
    assert not missing, f"unmapped core icon keys: {sorted(missing)}"


def test_icon_classes_use_fa_prefix(theme):
    icon_set = theme.get_icon_set()
    bad = {
        k: v
        for k, v in icon_set.icons.items()
        if not v.startswith(("fa-solid ", "fa ", "fa-"))
    }
    assert not bad, f"non-fontawesome icon classes: {bad}"


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
    assert "fontawesome.min.css" in response.text


def test_inline_edit_cancel_button_is_secondary(client):
    # AdminLTE leaves a bare .btn transparent, so the theme override must add
    # btn-outline-secondary (matching the Import toolbar button). The
    # inline-edit-cancel class is required by list.js and must be preserved.
    response = client.get("/admin/product/list")
    assert "btn-outline-secondary" in response.text
    assert "inline-edit-cancel" in response.text


def test_detail_page_card_actions_do_not_overlap_title(client):
    # AdminLTE floats .card-title left and .card-tools right, clearing via
    # .card-header::after. The core detail page renders the Tabler
    # .card-actions container, which the theme polyfills (in theme.css) to
    # float right so it clears the title instead of overlapping it.
    client.post("/admin/product/create", data={"name": "Widget"})
    response = client.get("/admin/product/detail", params={"pk": 1})
    assert response.status_code == 200
    assert "card-actions" in response.text
    assert "css/theme.css" in response.text

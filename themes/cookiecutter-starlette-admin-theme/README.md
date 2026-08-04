# cookiecutter-starlette-admin-theme

A [cookiecutter](https://github.com/cookiecutter/cookiecutter) template to scaffold a publishable [starlette-admin](https://github.com/jowilf/starlette-admin) theme. This generates a Python package that end users install and pass into `Admin(theme=...)`. See [docs/advanced/custom-themes.md](../../docs/advanced/custom-themes.md) for the theme API reference.

## Prerequisites

```bash
pip install cookiecutter
# or, without installing it globally:
# uvx cookiecutter ...
```

## Generate a Theme

From the root of this repository:

```bash
cookiecutter themes/cookiecutter-starlette-admin-theme/
```

From anywhere else (a third-party theme author does not need this repository checked out):

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme
```

Cookiecutter prompts for each variable in `cookiecutter.json`:

| Variable | Example | Notes |
| --- | --- | --- |
| `theme_name` | `Corporate` | Human-readable name. Everything else defaults from this. |
| `theme_slug` | `corporate` | Kebab-case. Used for logging and the entry-point key. Unlike a plugin, it does not namespace templates or static files: a theme owns the global template tree. |
| `package_slug` | `starlette_admin_corporate` | The importable Python package, under `src/`. |
| `distribution_name` | `starlette-admin-corporate` | The PyPI name. |
| `class_prefix` | `Corporate` | Produces `CorporateTheme`, `CorporateConfig`, `CorporateIcons`, and `CorporateClasses`. |
| `description` | free text | One-line package description. |
| `author_name` / `author_email` | free text | Used in `pyproject.toml` and `LICENSE`. |
| `github_username` | free text | Used to build the repo URL. |
| `version` | `0.1.0` | Initial package version. |
| `python_requires` | `>=3.11` | Match the core `starlette-admin` version you target. |
| `starlette_admin_version_spec` | `>=0.16,<1.0` | Pin the supported core range; pip/uv enforce it at install time. |
| `license` | `MIT` / `Apache-2.0` / `BSD-3-Clause` / `Proprietary` | Picks the `LICENSE` text and the `pyproject.toml` classifier. |

Accept a prompt's default by pressing enter, or answer everything non-interactively:

```bash
cookiecutter --no-input themes/cookiecutter-starlette-admin-theme/ \
    theme_name="Corporate" \
    author_name="Jane Doe" \
    author_email="jane@example.com" \
    github_username="janedoe"
```

## What You Get

```
starlette_admin_corporate/
├── pyproject.toml            # hatchling, entry point, starlette-admin version pin
├── README.md / LICENSE / .gitignore / babel.cfg / Makefile
├── .github/workflows/ci.yml  # pytest + ruff across supported Python versions
├── src/starlette_admin_corporate/
│   ├── __init__.py           # exports the Theme, Config, Icons, and Classes
│   ├── theme.py              # BaseTheme subclass + frozen Config dataclass
│   ├── icons.py              # IconSet subclass mapping the core vocabulary to Tabler Icons
│   ├── classes.py            # ClassMap subclass overriding the component roles the theme restyles
│   ├── templates/base.html   # extends @core/base.html, appends the theme stylesheet
│   └── static/css/theme.css  # example visual overrides
├── tests/
│   ├── conftest.py           # in-memory sqlite Admin(theme=...) + CsrfTestClient fixtures
│   └── test_theme.py         # registration, icon set, list/create pages render, stylesheet served
├── example/app.py            # `uv run python example/app.py` -> http://localhost:8000/admin/
└── docs/index.md             # usage doc: install, options, overriding templates/assets
```

The generated theme ships three things out of the box:

- **A custom `IconSet`** (`icons.py`) that remaps the full core icon vocabulary to [Tabler Icons](https://tabler.io/icons), swapping the default FontAwesome. `get_icon_set()` returns it, and `base.html`'s `icon_css` block pulls its stylesheet in automatically.
- **A `ClassMap`** (`classes.py`) returned by `get_class_map()`. Core templates render class attributes through `cls('role.name')`; map a role (a button, the list table, a filter chip, ...) to restyle that component everywhere, without forking a template. It starts empty with commented examples, since unmapped roles fall through to the core defaults in `starlette_admin.theme.CoreClasses`.
- **A `base.html` override** that extends `@core/base.html` and appends the theme's own stylesheet to the `core_css` block. Edit `static/css/theme.css` to restyle the admin.

Because a theme sits above plugins in Jinja's loader chain (precedence: user > theme > plugins > core), it can restyle both core and plugin templates.

## After Generating

```bash
cd starlette_admin_corporate
uv sync
uv run pytest
uv run python example/app.py   # demo admin at http://localhost:8000/admin/
```

If you are developing the theme inside this monorepo, uncomment the `[tool.uv.sources]` block at the bottom of the generated `pyproject.toml` and add the theme to this repository's root `[tool.uv.workspace]` members. This allows `uv sync` to link your local core checkout instead of resolving `starlette-admin` from PyPI. Third-party authors publishing their own repository leave it commented out.

## How this Template Avoids Double-Rendering Jinja

A generated theme ships its own Jinja templates (`base.html`, and anything else you add). These files use the exact same `{{ }}` and `{% %}` delimiters that cookiecutter uses to render this template. By default, cookiecutter would try to evaluate `{{ field.id }}` as a cookiecutter variable and silently blank it out.

To prevent this, `cookiecutter.json` lists `*.html` under `_copy_without_render`, ensuring every `.html` file is copied byte-for-byte. Only its path (which contains real cookiecutter variables, such as `src/{{cookiecutter.package_slug}}/`) is rendered.

If you add another file type that contains literal Jinja or another `{{ }}`-shaped syntax (like Vue single-file components, Go templates, or GitHub Actions `${{ }}` expressions), you must either add its pattern to `_copy_without_render` or escape the delimiters as string literals. For example, use `{{ '{%' }}` and `{{ '%}' }}` (as seen in `docs/index.md` to document the `@core` template-override syntax) or `{{ '${{ matrix.python-version }}' }}` (as seen in `ci.yml`).

## Editing this Template

- `cookiecutter.json`: Prompted variables, private ones (leading `_` convention) go last.
- After changing anything under `"{{cookiecutter.distribution_name}}"/`, render it and run the generated test suite before committing:

  ```bash
  cookiecutter --no-input -o /tmp/cc-theme-check themes/cookiecutter-starlette-admin-theme/
  cd /tmp/cc-theme-check/starlette-admin-my-theme && uv sync && uv run pytest
  ```

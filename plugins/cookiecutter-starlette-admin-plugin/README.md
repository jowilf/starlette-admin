# cookiecutter-starlette-admin-plugin

A [cookiecutter](https://github.com/cookiecutter/cookiecutter) template that
scaffolds a publishable [starlette-admin](https://github.com/jowilf/starlette-admin)
plugin: a Python package that end users install and pass into
`Admin(plugins=[...])`. See [ai/PLUGIN_DESIGN.md](../../ai/PLUGIN_DESIGN.md)
for the full plugin API this template builds on.

## Prerequisites

```bash
pip install cookiecutter
# or, without installing it globally:
# uvx cookiecutter ...
```

## Generate a plugin

From the root of this repository:

```bash
cookiecutter plugins/cookiecutter-starlette-admin-plugin/
```

From anywhere else (a third-party plugin author does not need this repo
checked out):

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

Cookiecutter prompts for each variable in `cookiecutter.json`:

| Variable | Example | Notes |
| --- | --- | --- |
| `plugin_name` | `Geospatial` | Human-readable name. Everything else defaults from this. |
| `plugin_slug` | `geospatial` | Kebab-case. Doubles as `BasePlugin.name` and the `plugins/<slug>/` template/static namespace. |
| `package_slug` | `starlette_admin_geospatial` | The importable Python package, under `src/`. |
| `distribution_name` | `starlette-admin-geospatial` | The PyPI name. |
| `class_prefix` | `Geospatial` | Produces `GeospatialPlugin`, `GeospatialConfig`, and (if included) `GeospatialRatingField`. |
| `description` | free text | One-line package description. |
| `author_name` / `author_email` | free text | Used in `pyproject.toml` and `LICENSE`. |
| `github_username` | free text | Used to build the repo URL. |
| `version` | `0.1.0` | Initial package version. |
| `python_requires` | `>=3.11` | Match the core `starlette-admin` version you target. |
| `starlette_admin_version_spec` | `>=0.16,<1.0` | Pin the supported core range; pip/uv enforce it at install time. |
| `license` | `MIT` / `Apache-2.0` / `BSD-3-Clause` / `Proprietary` | Picks the `LICENSE` text and the `pyproject.toml` classifier. |
| `include_example_field` | `yes` / `no` | Keep or drop the worked field example (see below). |

Accept a prompt's default by pressing enter, or answer everything
non-interactively:

```bash
cookiecutter --no-input plugins/cookiecutter-starlette-admin-plugin/ \
    plugin_name="Geospatial" \
    author_name="Jane Doe" \
    author_email="jane@example.com" \
    github_username="janedoe"
```

## What you get

```
starlette_admin_geospatial/
├── pyproject.toml            # hatchling, entry point, starlette-admin version pin
├── README.md / LICENSE / .gitignore / babel.cfg / Makefile
├── .github/workflows/ci.yml  # pytest + ruff across supported Python versions
├── src/starlette_admin_geospatial/
│   ├── __init__.py           # exports the Plugin, Config, and (optionally) the example field
│   ├── plugin.py             # BasePlugin subclass + frozen Config dataclass
│   ├── fields.py             # worked example field (dropped if include_example_field=no)
│   ├── templates/plugins/geospatial/fields/{form,detail,list}/rating.html
│   └── static/plugins/geospatial/{css,js}/rating.*
├── tests/
│   ├── conftest.py           # in-memory sqlite Admin + CsrfTestClient fixtures
│   ├── test_plugin.py        # registration, list/create pages load
│   └── test_field.py         # template resolution, form rendering, create+read round trip
├── example/app.py            # `uv run python example/app.py` -> http://localhost:8000/admin/
└── docs/index.md             # usage doc: install, options, overriding templates/assets
```

Every template and static file already lives under the required
`plugins/<plugin_slug>/` namespace (`BasePlugin` rejects anything outside
it at registration time), and `.html` files are copied verbatim, not
Jinja-rendered by cookiecutter itself (see "How this template avoids
double-rendering Jinja" below) — so they render correctly the moment
`Admin(plugins=[...])` picks the plugin up.

### `include_example_field`

Answering `yes` (the default) scaffolds a complete, working field —
`{ClassPrefix}RatingField`, a dependency-free star-rating widget — wired
through every layer a real field touches: a `BaseField` subclass, its three
namespaced templates, a CSS/JS pair served through the shared static mount,
and the `additional_css_links`/`additional_js_links` + `_needs_form_assets`
pattern that only ships form JS on pages that render the field. Use it as
the copy-paste starting point for your own field; delete what you don't
need. Answering `no` removes `fields.py`, its templates/static/tests, and
leaves just the plugin skeleton (`plugin.py` + `setup()`) for plugins that
only register into existing extension points (a storage backend, a model
converter, an event subscriber) rather than shipping a field.

## After generating

```bash
cd starlette_admin_geospatial
uv sync --extra dev
uv run pytest
uv run python example/app.py   # demo admin at http://localhost:8000/admin/
```

If you're developing the plugin inside this monorepo (under `plugins/`),
uncomment the `[tool.uv.sources]` block at the bottom of the generated
`pyproject.toml` and add the plugin to this repo's root
`[tool.uv.workspace] members`, so `uv sync` links your local core checkout
instead of resolving `starlette-admin` from PyPI. Third-party authors
publishing their own repo leave it commented out.

## How this template avoids double-rendering Jinja

A generated plugin ships its own Jinja templates (the field's
`form`/`detail`/`list` `.html` files), which use the exact same `{{ }}` /
`{% %}` delimiters cookiecutter itself uses to render this template. Left
alone, cookiecutter would try to evaluate `{{ field.id }}` as a cookiecutter
variable and silently blank it out. `cookiecutter.json` lists `*.html` under
`_copy_without_render`, so every `.html` file is copied byte-for-byte —
only its path (which does contain real cookiecutter variables, e.g.
`plugins/{{cookiecutter.plugin_slug}}/...`) is still rendered. If you add
another file type that contains literal Jinja or another `{{ }}`-shaped
syntax (Vue single-file components, Go templates, GitHub Actions'
`${{ }}` expressions), either add its pattern to `_copy_without_render` or
escape the delimiters as string literals, e.g. `{{ '{%' }}` / `{{ '%}' }}`
(used in `docs/index.md` to document the `@<name>` template-override
syntax) or `{{ '${{ matrix.python-version }}' }}` (used in `ci.yml`).

## Editing this template

- `cookiecutter.json`: prompted variables, private ones (leading `_`
  convention) go last.
- `hooks/post_gen_project.py`: post-generation cleanup. Cookiecutter
  renders this file as Jinja too before running it, so it can read
  `include_example_field` etc. directly as plain Python strings.
- After changing anything under `"{{cookiecutter.distribution_name}}"/`, render
  both branches and run the generated test suite before committing:

  ```bash
  cookiecutter --no-input -o /tmp/cc-check plugins/cookiecutter-starlette-admin-plugin/
  cookiecutter --no-input -o /tmp/cc-check-nofield plugins/cookiecutter-starlette-admin-plugin/ include_example_field=no
  cd /tmp/cc-check/starlette-admin-my-plugin && uv sync --extra dev && uv run pytest
  ```

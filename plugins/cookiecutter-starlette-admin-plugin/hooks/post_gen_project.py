"""Post-generation cleanup script.

Cookiecutter renders this file as a Jinja template before execution,
substituting the cookiecutter answer values directly into the code.
"""

import os
import shutil

PACKAGE_SLUG = "{{ cookiecutter.package_slug }}"
PLUGIN_SLUG = "{{ cookiecutter.plugin_slug }}"
DISTRIBUTION_NAME = "{{ cookiecutter.distribution_name }}"
INCLUDE_EXAMPLE_FIELD = "{{ cookiecutter.include_example_field }}" == "yes"

PATHS_TO_REMOVE_WITHOUT_EXAMPLE_FIELD = [
    f"src/{PACKAGE_SLUG}/fields.py",
    f"src/{PACKAGE_SLUG}/templates/plugins/{PLUGIN_SLUG}/fields",
    f"src/{PACKAGE_SLUG}/static/plugins/{PLUGIN_SLUG}/js/slider.js",
    f"src/{PACKAGE_SLUG}/static/plugins/{PLUGIN_SLUG}/css/slider.css",
    "tests/test_field.py",
]


def remove(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


if not INCLUDE_EXAMPLE_FIELD:
    for path in PATHS_TO_REMOVE_WITHOUT_EXAMPLE_FIELD:
        remove(path)

print(f"\n{PACKAGE_SLUG} scaffolded. Next steps:\n")
print(f"  cd {DISTRIBUTION_NAME}")
print("  uv sync")
print("  uv run pytest")
print("  uv run python example/app.py\n")

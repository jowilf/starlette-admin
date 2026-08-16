"""Post-generation script.

Cookiecutter renders this file as Jinja before execution, so it can read
the answer values directly as plain Python strings.
"""

PACKAGE_SLUG = "{{ cookiecutter.package_slug }}"
DISTRIBUTION_NAME = "{{ cookiecutter.distribution_name }}"

print(f"\n{PACKAGE_SLUG} scaffolded. Next steps:\n")
print(f"  cd {DISTRIBUTION_NAME}")
print("  uv sync")
print("  uv run pytest")
print("  uv run python example/app.py\n")

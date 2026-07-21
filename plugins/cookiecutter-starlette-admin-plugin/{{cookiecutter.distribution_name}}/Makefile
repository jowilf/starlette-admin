PACKAGE = src/{{ cookiecutter.package_slug }}
TRANSLATIONS = $(PACKAGE)/translations
POT = $(TRANSLATIONS)/messages.pot

.PHONY: install test lint format extract-messages update-messages compile-messages

install:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check $(PACKAGE) tests
	uv run ruff format --check $(PACKAGE) tests

format:
	uv run ruff check --fix $(PACKAGE) tests
	uv run ruff format $(PACKAGE) tests

# Requires the `i18n` extra: uv sync --extra i18n (adds babel).
extract-messages:
	mkdir -p $(TRANSLATIONS)
	uv run pybabel extract -F babel.cfg -o $(POT) $(PACKAGE)

update-messages: extract-messages
	uv run pybabel update -i $(POT) -d $(TRANSLATIONS)

compile-messages:
	uv run pybabel compile -d $(TRANSLATIONS)

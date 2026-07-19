
import click
import requests
from babel.messages.frontend import CommandLineInterface


def init_flatpickr(locale: str):
    """
    Initialize Flatpickr translations for a given locale.

    Args:
        locale (str): The target locale to download and add to the static directory.

    """
    r = requests.get(
        f"https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/l10n/{locale}.min.js"
    )
    if r.ok:
        with open(
            f"starlette_admin/static/i18n/flatpickr/{locale}.js", "w"
        ) as output_file:
            # Remove sourceMappingURL
            output_text = "\n".join(r.text.split("\n")[:-1])
            output_file.write(output_text)
            click.echo(f"Flatpickr translation for {locale} initialized successfully.")
    else:
        click.echo(
            f"Flatpickr translation not available for locale `{locale}`. Consider contributing to Flatpickr first  or "
            f"provide a Flatpickr locale close to the target locale.",
            err=True,
        )


@click.command()
@click.option(
    "--locale",
    prompt="Target locale (e.g., `en`)",
    help="The new locale being added (also the target locale).",
)
@click.option(
    "--flatpickr-locale",
    default=None,
    prompt="Flatpickr locale (e.g., `en`)",
    prompt_required=False,
    help="The locale for Flatpickr, if different from the target locale.",
    show_default="target locale",
)
def init(
    locale: str,
    flatpickr_locale: str | None,
):
    """Initialize new Language Support

    This command performs the following actions:

    1. Generates the POT file for the specified locale. The POT file is created at
    './starlette_admin/translations/{locale}/LC_MESSAGES/admin.po'.

    2. Downloads the Flatpickr localization file from the Flatpickr CDN (https://cdn.jsdelivr.net/npm/flatpickr) for the
       locale specified by `--flatpickr-locale` (or the target locale if not provided) and places it under
       './starlette_admin/static/i18n/flatpickr/{locale}.json'.

    """
    # Prepare arguments for pybabel init
    command_args = [
        "pybabel",
        "init",
        "-i",
        "i18n/admin.pot",  # Path to the input POT file
        "-d",
        "starlette_admin/translations",  # Path to the output directory
        "-D",
        "admin",  # domain
        "-l",
        locale,
    ]

    CommandLineInterface().run(command_args)

    init_flatpickr(flatpickr_locale or locale)


if __name__ == "__main__":
    init()

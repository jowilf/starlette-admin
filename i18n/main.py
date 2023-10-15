import json
from typing import Optional

import click
import requests
from babel.messages.frontend import CommandLineInterface


def deep_sort_dict_keys(input_dict):
    """
    Recursively sorts the keys of a nested dictionary.
    """
    if isinstance(input_dict, dict):
        return {
            key: deep_sort_dict_keys(value) for key, value in sorted(input_dict.items())
        }
    if isinstance(input_dict, list):
        return [deep_sort_dict_keys(element) for element in input_dict]
    return input_dict


def find_datatable_locale(locale: str) -> Optional[str]:
    """
    Find a DataTables locale based on the provided locale.

    Args:
        locale (str): The desired locale.

    Returns:
        Optional[str]: The matching DataTables locale, or None if not found.
    """
    dt_locales = (
        "af,sq,am,ar,hy,az-AZ,bn,eu,be,bs-BA,bg,ca,zh,zh-HANT,co,hr,cs,da,nl-NL,en-GB,eo,et,fil,fi,fr-FR,gl,"
        "ka,de-DE,el,gu,he,hi,hu,is,id,id-ALT,ga,it-IT,ja,jv,kn,kk,km,ko,ku,ky,lo,lv,lt,ug,mk,ms,mr,mn,ne,"
        "no-NB,no-NO,ps,fa,pl,pt-PT,pt-BR,pa,ro,rm,ru,sr,sr-SP,snd,si,sk,sl,es-ES,es-AR,es-CL,es-CO,es-MX,"
        "sw,sv-SE,tg,ta,te,th,tr,tk,uk,ur,uz,uz-CR,vi,cy"
    ).split(",")
    if locale in dt_locales:
        return locale
    locale = locale.lower()
    for key in dt_locales:
        if key.split("-", maxsplit=1)[0] == locale:
            return key
    return None


def init_datatable(locale: str):
    """
    Initialize DataTables translations.

    Args:
        locale (str): The target locale.
    """
    keys = [  # keys used by starlette-admin
        "aria",
        "buttons",
        "datetime",
        "decimal",
        "emptyTable",
        "info",
        "infoEmpty",
        "infoFiltered",
        "infoThousands",
        "lengthMenu",
        "loadingRecords",
        "paginate",
        "processing",
        "search",
        "searchBuilder",
        "select",
        "thousands",
        "zeroRecords",
    ]
    fallback_locale = "en"
    dt_locale = find_datatable_locale(locale)
    if dt_locale is None:
        click.echo(
            f"Datatable translation not available for locale `{locale}`. Consider contributing to datatable first",
            err=True,
        )
        translations = {}
    else:
        r = requests.get(
            f"https://cdn.datatables.net/plug-ins/1.13.6/i18n/{find_datatable_locale(locale)}.json"
        )
        if r.ok:
            translations = r.json()
        else:
            click.echo(
                f"Failed to download DataTables locale file for {dt_locale}. Falling back to the default translation.",
                err=True,
            )
            translations = {}
    with open(f"starlette_admin/statics/i18n/dt/{fallback_locale}.json") as file:
        default_translations = json.load(file)
    output_translations = {}
    for key in keys:
        if key in translations:
            output_translations[key] = translations[key]
        else:
            click.echo(
                f"The key `{key}` is missing in the downloaded DataTables locale file. Falling back to the default "
                "translation."
            )
            output_translations[key] = default_translations[
                key
            ]  # fallback to the default translation
    output_translations["searchBuilder"]["button"]["0"] = (
        '<i class="fa-solid fa-filter"></i> '
        + output_translations["searchBuilder"]["button"]["0"]
    )
    output_translations["searchBuilder"]["button"]["_"] = (
        '<i class="fa-solid fa-filter"></i> '
        + output_translations["searchBuilder"]["button"]["_"]
    )
    output_translations["starlette-admin"] = default_translations["starlette-admin"]
    with open(f"starlette_admin/statics/i18n/dt/{locale}.json", "w") as output_file:
        json.dump(
            deep_sort_dict_keys(output_translations),
            output_file,
            indent="\t",
            ensure_ascii=False,
        )


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
            f"starlette_admin/statics/i18n/flatpickr/{locale}.js", "w"
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


def init_moment_js(locale: str):
    r = requests.get(
        f"https://cdn.jsdelivr.net/npm/moment@2.29.4/locale/{locale}.min.js"
    )
    if r.ok:
        with open(
            f"starlette_admin/statics/i18n/momentjs/{locale}.js", "w"
        ) as output_file:
            # Remove sourceMappingURL
            output_text = "\n".join(r.text.split("\n")[:-1])
            output_file.write(output_text)
            click.echo(f"Moment.js translation for {locale} initialized successfully.")
    else:
        click.echo(
            f"Moment.js translation not available for locale `{locale}`. Consider contributing to Moment.js first or "
            "provide a Moment.js locale close to the target locale.",
            err=True,
        )


@click.command()
@click.option(
    "--locale",
    prompt="Target locale (e.g., `en`)",
    help="The locale to initialize language support for.",
)
@click.option(
    "--dt-locale",
    default=None,
    prompt="DataTables locale (e.g., `en`)",
    prompt_required=False,
    help="The locale for DataTables, if different from the target locale.",
    show_default="target locale",
)
@click.option(
    "--flatpickr-locale",
    default=None,
    prompt="Flatpickr locale (e.g., `en`)",
    prompt_required=False,
    help="The locale for Flatpickr, if different from the target locale.",
    show_default="target locale",
)
@click.option(
    "--moment-locale",
    default=None,
    prompt="Moment.js locale (e.g., `en`)",
    prompt_required=False,
    help="The locale for Moment.js, if different from the target locale.",
    show_default="target locale",
)
def init(
    locale: str,
    dt_locale: Optional[str],
    flatpickr_locale: Optional[str],
    moment_locale: Optional[str],
):
    """Initialize new Language Support"""
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

    init_datatable(dt_locale or locale)
    init_flatpickr(flatpickr_locale or locale)
    init_moment_js(moment_locale or locale)


if __name__ == "__main__":
    init()

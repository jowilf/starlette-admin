---
title: Thèmes personnalisés
description: Remplacez les variables CSS de Tabler, injectez des feuilles de style
  personnalisées et modifiez l'esthétique générale de votre tableau de bord starlette-admin.
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# Thèmes personnalisés

Vous pouvez restyler l'interface d'administration via les paramètres de thème, des templates personnalisés et des fichiers statiques. `DefaultTheme` contrôle l'apparence par défaut en écrivant des attributs data sur la balise `<html>` à partir d'un objet `TablerSettings`. Pour des modifications plus poussées, dérivez de `BaseTheme` pour regrouper vos propres templates, assets statiques et jeux d'icônes, ou passez vos propres répertoires de templates et de fichiers statiques à `Admin`.

## Appliquer un thème

Utilisez `TablerSettings` pour définir votre palette de couleurs, le rayon des bordures et le mode colorimétrique. Passez-le à `DefaultTheme`, puis passez ce dernier au paramètre `theme` de votre instance `Admin`.

```python
from myapp.models import Post
from sqlalchemy import create_engine
from starlette_admin.theme import DefaultTheme, TablerSettings
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///admin.sqlite")

admin = Admin(
    engine,
    title="My Admin",
    theme=DefaultTheme(
        settings=TablerSettings(base="slate", primary="blue", radius=2, mode="dark")
    ),
)
admin.add_view(ModelView(Post))
```

Consultez [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes) pour une application exécutable qui choisit un thème aléatoire à chaque démarrage.

Cette configuration applique les attributs `data-bs-theme*` directement à l'élément racine `<html>` :

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## Référence de `TablerSettings`

| Attribut | Type | Valeur par défaut | Valeurs valides |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Restyler les composants avec une class map

Les templates principaux ne codent pas en dur le style des composants. Ils génèrent les attributs de classe via l'aide Jinja `cls('role.name')`, qui résout un rôle sémantique tel que `form.save_button` ou `list.table` en une chaîne de classes CSS. La valeur par défaut de chaque rôle est définie dans `starlette_admin.theme.CoreClasses`.

Pour restyler un rôle, écrivez une sous-classe de `ClassMap`. Tout rôle que vous ne définissez pas retombe sur `CoreClasses` : les remplacements partiels sont donc sans risque. Gardez à l'esprit qu'un rôle de bouton définit l'intégralité de l'attribut class de l'élément, y compris la variante, la taille et l'espacement : mapper un bouton remplace donc entièrement son apparence.

Les class maps ne nécessitent pas un thème personnalisé complet. Pour ajuster le thème par défaut, dérivez de `DefaultTheme` et retournez votre map depuis `get_class_map()` :

```python
from starlette_admin.theme import ClassMap, DefaultTheme


class MyClasses(ClassMap):
    classes = {
        # Rounded success save button instead of the default primary one
        "form.save_button": "btn btn-success rounded-pill",
        # Outline create button on the list toolbar
        "list.create_button": "btn btn-outline-primary ms-2",
        # Pill-shaped filter chips
        "filter.chip": "badge rounded-pill bg-primary-subtle",
    }


class MyTheme(DefaultTheme):
    def get_class_map(self) -> ClassMap:
        return MyClasses()


admin = Admin(engine, title="My Admin", theme=MyTheme())
```

Lisez `CoreClasses.classes` dans `starlette_admin/theme.py` pour connaître l'ensemble complet des rôles. Ces rôles couvrent trois types de styles :

* **Boutons :** un rôle par emplacement de bouton, couvrant les pieds de formulaire, les barres d'outils de liste, les barres de filtres, les modales d'action et l'édition en ligne. La valeur que vous définissez devient la totalité de l'attribut class du bouton.
* **Classes de composants :** classes spécifiques à un framework CSS devant être remplacées si vous utilisez un autre framework, telles que `list.table`, `modal.base` ou `filter.chip`.
* **Classes d'exécution :** classes appliquées dynamiquement par le JavaScript principal, telles que `alert.success` ou `import.status_badge`.

## Créer et partager des thèmes personnalisés

Vous pouvez empaqueter un thème et le publier sur PyPI, à la manière d'un plugin. Dérivez de `BaseTheme` pour construire un package Python réutilisable remplaçant la mise en page et le style de l'administration dans plusieurs projets, ou pour partager un système visuel avec d'autres personnes.

### Scaffolding avec Cookiecutter

Partez du template cookiecutter officiel. Il génère un package publiable avec la structure de répertoires appropriée et les fichiers de configuration nécessaires.

Installez `cookiecutter` avec votre gestionnaire de packages. Consultez le [guide d'installation officiel](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) pour plus de détails :

```bash
pip install cookiecutter

```

Exécutez ensuite le template depuis n'importe quel répertoire :

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

Le template vous demande le nom du thème, le slug du package, la version et quelques autres variables. Une fois terminé, vous disposez d'un package autonome contenant :

* Un répertoire `src/` regroupant la classe de thème, le jeu d'icônes et la class map.
* Des répertoires `templates/`, `static/` et de traduction préconfigurés.
* Une suite de tests et un exemple d'application exécutable.

### Architecture de `BaseTheme`

Un thème se situe à la racine de la chaîne de rendu, et chaque instance `Admin` possède exactement un thème actif. Une sous-classe de `BaseTheme` configure les éléments suivants :

* **Templates :** templates de remplacement placés dans le répertoire `templates/` du package, référencés par des chemins relatifs simples tels que `base.html`, `layout.html` ou `list.html`. Le thème actif se situe au-dessus des plugins dans la chaîne de loaders Jinja : il peut donc restyler aussi bien les templates principaux que ceux des plugins.
* **Assets statiques :** feuilles de style, scripts et images placés dans le répertoire `static/` du package.
* **Jeu d'icônes :** une sous-classe personnalisée de `IconSet` retournée par `get_icon_set()`, associant des clés sémantiques telles que `list.new` ou `auth.logout` à des classes CSS.
* **Class map :** une sous-classe de `ClassMap` retournée par `get_class_map()`, comme décrit dans [Restyler les composants avec une class map](#restyler-les-composants-avec-une-class-map).
* **Variables globales de template :** variables globales exposées à Jinja en surchargeant `template_globals()`.

### Exemple de package de thème

```python
from typing import Any
from starlette_admin.theme import BaseTheme, ClassMap, IconSet


class CustomIconSet(IconSet):
    icons = {
        "list.new": "hi hi-plus",
        "default_actions.view": "hi hi-eye",
        # Map remaining semantic icon keys
    }


class CorporateClasses(ClassMap):
    classes = {
        "form.save_button": "btn btn-corporate",
        # Map remaining roles to restyle; unmapped roles keep core defaults
    }


class CorporateTheme(BaseTheme):
    name = "corporate"
    package = "corporate_theme_package"  # Auto-detected from class module if omitted

    def get_icon_set(self) -> IconSet:
        return CustomIconSet()

    def get_class_map(self) -> ClassMap:
        return CorporateClasses()

    def template_globals(self) -> dict[str, Any]:
        return {"company_name": "Acme Corp"}
```

### Hiérarchie du loader de templates

Le moteur de templates résout les fichiers dans cet ordre :

1. Votre `templates_dir`, qui prime sur tout ce qui suit.
2. Le répertoire `templates/` du thème actif, qui restyle les templates principaux et ceux des plugins.
3. Les répertoires `templates/` namespacés des plugins.
4. Les templates par défaut du cœur de `starlette-admin`.

Pour étendre un template de thème depuis un override utilisateur ou une sous-classe de thème, utilisez le préfixe Jinja `@theme`, par exemple `{% extends "@theme/layout.html" %}`.

## Répertoire de templates personnalisé

Pour remplacer le HTML par défaut sans construire un thème complet, passez un chemin de répertoire à `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Tout fichier placé dans ce répertoire masque le template intégré situé au même chemin relatif, tandis que le reste de l'arborescence intégrée continue de fonctionner comme auparavant. Pour la liste complète des templates remplaçables, consultez [Templates](templates.md).

## Répertoire statique personnalisé

Pour ajouter vos propres fichiers CSS, JavaScript ou images sans construire un thème complet, passez un chemin de répertoire à `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Les fichiers de ce répertoire sont servis aux côtés des assets intégrés sous `/admin/static/`. Par exemple, un fichier situé à `my_static/custom.css` devient accessible à `/admin/static/custom.css`.

Référencez la feuille de style depuis vos templates comme suit :

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## Et ensuite ?

* **[Templates](templates.md) :** remplacez une page, une cellule ou un widget unique sans dupliquer l'intégralité de l'arborescence de templates.
* **[Extension Points](extension-points.md) :** explorez les hooks et points de personnalisation au-delà des thèmes de base.
* **[Quickstart](../getting-started/quickstart.md) :** construisez une interface d'administration fonctionnelle à partir de zéro.

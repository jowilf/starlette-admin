---
title: Thèmes personnalisés
description: Remplacez les variables CSS de Tabler, injectez des feuilles de style
  personnalisées et modifiez l'esthétique générale de votre tableau de bord starlette-admin.
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

??? info "Traduction automatique supervisée"

    Ce contenu est généré par traduction automatique, guidée par des
    glossaires et des guides de style validés par des humains. Comme le
    texte n'est pas relu ligne par ligne, des erreurs ou des formulations
    maladroites peuvent parfois apparaître.

    En cas de divergence, la [version originale en anglais](https://jowilf.github.io/starlette-admin/) fait foi.

# Thèmes personnalisés

Vous pouvez restyler le panneau d'administration via les paramètres de thème, les templates personnalisés et les fichiers statiques. `DefaultTheme` contrôle l'apparence par défaut en écrivant des attributs data sur la balise `<html>` à partir d'un objet `TablerSettings`. Pour des modifications plus poussées, créez une sous-classe de `BaseTheme` pour regrouper vos propres templates, ressources statiques et jeux d'icônes, ou passez vos propres répertoires de templates et de fichiers statiques à `Admin`.

## Appliquer un thème

Utilisez `TablerSettings` pour définir votre palette de couleurs, le rayon des bordures et le mode colorimétrique. Passez-le à `DefaultTheme`, puis passez celui-ci au paramètre `theme` de votre instance de `Admin`.

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

Cette configuration applique directement les attributs `data-bs-theme*` à l'élément racine `<html>` :

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

## Restyler les composants avec un mappage de classes

Les templates principaux ne codent pas en dur le style des composants. Ils génèrent les attributs de classe via l'assistant Jinja `cls('role.name')`, qui résout un rôle sémantique tel que `form.save_button` ou `list.table` en une chaîne de classes CSS. La valeur par défaut de chaque rôle se trouve dans `starlette_admin.theme.CoreClasses`.

Pour restyler un rôle, écrivez une sous-classe de `ClassMap`. Tout rôle que vous ne mappez pas retombe sur `CoreClasses`, ce qui rend les remplacements partiels sans risque. Gardez à l'esprit qu'un rôle de bouton définit l'intégralité de l'attribut class de l'élément, y compris la variante, la taille et l'espacement ; mapper un tel rôle remplace donc complètement l'apparence du bouton.

Les mappages de classes ne nécessitent pas un thème entièrement personnalisé. Pour ajuster le thème par défaut, créez une sous-classe de `DefaultTheme` et renvoyez votre mappage depuis `get_class_map()` :

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

Consultez `CoreClasses.classes` dans `starlette_admin/theme.py` pour connaître tout le vocabulaire des rôles. Les rôles couvrent trois types de style :

* **Boutons :** un rôle par emplacement de bouton, couvrant les pieds de formulaire, les barres d'outils de liste, les barres de filtres, les fenêtres modales d'action et l'édition en ligne. La valeur que vous définissez devient l'attribut class complet du bouton.
* **Classes de composants :** classes spécifiques à un framework qu'un autre framework CSS doit remplacer, telles que `list.table`, `modal.base` ou `filter.chip`.
* **Classes d'exécution :** classes que le JavaScript principal applique dynamiquement, telles que `alert.success` ou `import.status_badge`.

## Créer et partager des thèmes personnalisés

Vous pouvez empaqueter un thème et le publier sur PyPI, comme un plug-in. Créez une sous-classe de `BaseTheme` pour construire un package Python réutilisable qui remplace la mise en page et le style du panneau d'administration dans plusieurs projets, ou pour partager un système visuel avec d'autres personnes.

### Générer la structure du projet avec Cookiecutter

Partez du template cookiecutter officiel. Il génère un package publiable avec la structure de répertoires et les fichiers de configuration appropriés.

Installez `cookiecutter` avec votre gestionnaire de packages. Consultez le [guide d'installation officiel](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) pour plus de détails :

```bash
pip install cookiecutter

```

Exécutez ensuite le template depuis n'importe quel répertoire :

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

Le template vous demande le nom du thème, le slug du package, la version et quelques autres variables. Une fois terminé, vous obtenez un package autonome contenant :

* Un répertoire `src/` contenant la classe du thème, le jeu d'icônes et le mappage de classes.
* Des dossiers `templates/`, `static/` et de traduction préconfigurés.
* Une suite de tests et une application exemple exécutable.

### Architecture de `BaseTheme`

Un thème se situe à la racine de la chaîne de rendu, et chaque instance de `Admin` possède exactement un thème actif. Une sous-classe de `BaseTheme` configure les éléments suivants :

* **Templates :** des templates de remplacement dans le dossier `templates/` du package, utilisant des chemins relatifs simples tels que `base.html`, `layout.html` ou `list.html`. Le thème actif se trouve au-dessus des plugins dans la chaîne de chargeurs de Jinja, il peut donc restyler aussi bien les templates principaux que ceux des plugins.
* **Ressources statiques :** feuilles de style, scripts et images dans le répertoire `static/` du package.
* **Jeu d'icônes :** une sous-classe personnalisée de `IconSet` renvoyée par `get_icon_set()`, associant des clés sémantiques telles que `list.new` ou `auth.logout` à des classes CSS.
* **Mappage de classes :** une sous-classe de `ClassMap` renvoyée par `get_class_map()`, comme décrit dans [Restyler les composants avec un mappage de classes](#restyling-components-with-a-class-map).
* **Variables globales de template :** variables globales exposées à Jinja en redéfinissant `template_globals()`.

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

### Hiérarchie des chargeurs de templates

Le moteur de templates résout les fichiers dans cet ordre :

1. Votre `templates_dir`, qui prime sur tout ce qui suit.
2. Le dossier `templates/` du thème actif, qui restyle les templates principaux et ceux des plugins.
3. Les `templates/` des plugins, avec espace de noms.
4. Les templates par défaut de `starlette_admin`.

Pour étendre un template de thème depuis un remplacement utilisateur ou une sous-classe de thème, utilisez le préfixe Jinja `@theme`, par exemple `{% extends "@theme/layout.html" %}`.

## Répertoire de templates personnalisés

Pour remplacer le HTML par défaut sans construire un thème complet, passez un chemin de répertoire à `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Tout fichier placé dans ce répertoire masque le template intégré situé au même chemin relatif, et le reste de l'arborescence intégrée continue de s'afficher comme auparavant. Pour la liste complète des templates remplaçables, consultez [Templates](templates.md).

## Répertoire statique personnalisé

Pour ajouter votre propre CSS, JavaScript ou images sans construire un thème complet, passez un chemin de répertoire à `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Les fichiers de ce répertoire sont servis aux côtés des ressources intégrées sous `/admin/static/`. Un fichier situé dans `my_static/custom.css`, par exemple, devient accessible à l'adresse `/admin/static/custom.css`.

Référencez la feuille de style depuis vos templates comme ceci :

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## Pour aller plus loin

* **[Templates](templates.md) :** remplacer une seule page, cellule ou widget sans dupliquer toute l'arborescence de templates.
* **[Extension Points](extension-points.md) :** explorer les hooks et points de personnalisation au-delà des thèmes de base.
* **[Quickstart](../getting-started/quickstart.md) :** créer une interface d'administration fonctionnelle à partir de zéro.

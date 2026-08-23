---
title: Templates
description: Surcharger les templates Jinja2 de starlette-admin pour personnaliser
  entièrement la structure HTML de vues ou de champs spécifiques.
source_hash: 92643d00ab546c400a73e995d391d57cd0f5c054cba9d3ca8a5438df8eeb86ae
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

# Templates

Chaque page du panneau d'administration est un template Jinja2 que vous pouvez surcharger. Modifiez une seule page de liste, la cellule d'un champ dans un tableau, ou un widget du tableau de bord sans dupliquer l'arborescence des templates intégrés.

## Fonctionnement du chargeur de templates

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

`Admin` construit un `ChoiceLoader` Jinja2 qui consulte d'abord votre `templates_dir`, puis le répertoire intégré `starlette_admin/templates/` du package. Placez un fichier sous `my_templates/` au même chemin relatif qu'il occupe dans `starlette_admin/templates/` et votre fichier masquera le template intégré. Tous les autres templates continuent d'être rendus depuis le répertoire intégré.

!!! note
    La chaîne de chargement enregistre également un `PrefixLoader` sous la clé `@starlette-admin`, qui pointe toujours vers les templates intégrés, quel que soit le contenu qui les masque dans `templates_dir`. Vous pouvez y accéder avec le format de chemin `@starlette-admin/<name>.html`, en omettant la barre oblique finale sur le préfixe lui-même. Consultez [Surcharger le template d'une seule page](#surcharger-le-template-dune-seule-page) ci-dessous pour comprendre son utilité.

## Carte des répertoires de templates

| Chemin | Rendu pour |
| --- | --- |
| `base.html` | Structure HTML externe (`<html>`, `<head>`, scripts) |
| `layout.html` | Habillage de la barre latérale et de la barre supérieure (étend `base.html`) |
| `index.html` | Tableau de bord ou page d'accueil |
| `list.html` | Page de liste d'un modèle (tableau, barre de filtres, pagination) |
| `detail.html` | Vue de détail (en lecture seule) d'un enregistrement |
| `create.html` | Formulaire de création |
| `edit.html` | Formulaire de modification |
| `login.html` | Page de connexion |
| `error.html` | Page d'erreur HTTP (403, 404, etc.) |
| `actions.html` | Fenêtre modale des actions groupées |
| `row-actions.html` | Menu déroulant des actions par ligne |
| `inline.html` | Ensemble de formulaires en ligne sur les pages de création/modification |
| `inline_detail.html` | Tableau en ligne sur la page de détail |
| `inline_row.html` | Ligne unique à l'intérieur d'un ensemble de formulaires en ligne |
| `_filter_bar.html` | Barre des filtres actifs au-dessus de la liste |
| `_filter_builder.html` | Fenêtre modale du constructeur de filtres |
| `_pagination.html` | Contrôles de pagination |
| `_column_header.html` | Cellule d'en-tête de colonne triable |
| `_form_footer.html` | Boutons Enregistrer, Enregistrer et continuer ou Ajouter un autre |
| `_form_group.html` | Fieldset d'un groupe de [mise en page de formulaire](form-layout.md) sur le formulaire de création/modification |
| `_form_group_fields.html` | Les champs saisis rendus à l'intérieur d'un groupe de mise en page de formulaire |
| `fields/list/<type>.html` | Cellule de colonne de liste pour un type de champ |
| `fields/detail/<type>.html` | Affichage sur la page de détail pour un type de champ |
| `fields/form/<type>.html` | Widget de saisie de formulaire pour un type de champ |
| `widgets/<name>.html` | Template de widget du tableau de bord |
| `modals/actions.html` | Fenêtre modale de confirmation d'action |
| `modals/delete.html` | Fenêtre modale de confirmation de suppression |
| `modals/error.html` | Fenêtre modale d'erreur |
| `modals/import.html` | Fenêtre modale d'importation |
| `macros/views.html` | Macros Jinja2 partagées utilisées sur plusieurs pages |

!!! note
    L'arborescence intégrée comprend également `modals/loading.html`, une fenêtre modale générique d'état de chargement, ainsi que plusieurs templates spécifiques aux champs dans `fields/list/`, `fields/detail/` et `fields/form/`. Vérifiez les noms de fichiers exacts dans `starlette_admin/templates/` pour la version installée avant de surcharger un fichier `<type>.html` générique.

## Surcharger le template d'une seule page

```
my_templates/
└── list.html   ← masque le list.html intégré

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Bannière personnalisée au-dessus de la liste.</div>
  {{ super() }}
{% endblock %}

```

`{% extends "list.html" %}` résoudrait vers votre propre fichier `my_templates/list.html`, car `templates_dir` est consulté en premier, et cette référence circulaire déclenche une erreur de récursion infinie. Le préfixe `@starlette-admin/` pointe toujours vers la copie intégrée ; chaque `extends` et `include` à l'intérieur d'une surcharge doit donc l'utiliser plutôt que le nom de fichier seul.

## Blocs surchargeables

Chaque page intégrée étend `layout.html`, qui étend elle-même `base.html`. Surchargez un seul `{% block %}` plutôt qu'un fichier entier pour modifier un fragment sans dupliquer le reste de la page :

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block list_toolbar_extra %}
  {{ super() }}
  <a class="btn btn-outline-primary" href="/reports/export">Rapport personnalisé</a>
{% endblock %}

```

### `base.html`

| Bloc | Contenu |
| --- | --- |
| `favicon` | La balise `<link>` du favicon |
| `title` | La balise `<title>` |
| `head_meta` | Les balises `<meta>` à l'intérieur de l'élément `<head>` |
| `head_css` | Les balises `<link>` des feuilles de style |
| `head` | Un point d'insertion libre à l'intérieur de l'élément `<head>` |
| `body` | L'intégralité du contenu de `<body>` (ce bloc est surchargé par `layout.html`) |
| `modal` | Un point d'insertion au niveau de la page pour les fenêtres modales |
| `script` | Les balises `<script>` situées juste avant la balise fermante `</body>` |
| `tail` | Un point d'insertion vide tout à la fin de `<body>`, après `script` |

### `layout.html`

| Bloc | Contenu |
| --- | --- |
| `sidebar` | L'intégralité de l'élément `<aside>` de la barre latérale (y compris la marque de navigation, le menu et le pied de page) |
| `brand` | L'image du logo (ou le repli `app_title`) à l'intérieur du lien de marque de navigation de la barre latérale |
| `sidebar_menu` | La liste des liens de vues à l'intérieur de la barre latérale |
| `sidebar_footer` | La zone inférieure de la barre latérale |
| `user_menu_trigger` | L'avatar et le nom d'utilisateur affichés sur le bouton du menu utilisateur. Défini une seule fois et réutilisé à la fois sur la barre latérale mobile et sur la barre de navigation de bureau via `self.user_menu_trigger()`, si bien que sa surcharge met à jour les deux |
| `user_menu_items` | Les éléments du menu déroulant situés dans le menu utilisateur |
| `navbar` | La barre de navigation supérieure |
| `navbar_extra` | Contenu supplémentaire placé dans la barre de navigation à côté du menu utilisateur |
| `header` | La zone d'en-tête de page positionnée au-dessus de `content` (inclut le titre et le fil d'Ariane) |
| `flash_messages` | La zone dédiée au rendu des messages flash |
| `content_before` | Un point d'insertion immédiatement avant `content` |
| `content` | Le contenu principal de la page (c'est le bloc rempli par `list.html`, `detail.html`, etc.) |
| `content_after` | Un point d'insertion immédiatement après `content` |
| `page_footer` | La zone de pied de page située sous le contenu de la page |

### `list.html`

| Bloc | Contenu |
| --- | --- |
| `header` | L'en-tête de la page (inclut le titre et le fil d'Ariane) |
| `page_title` | Le titre `<h1>` à l'intérieur de l'en-tête |
| `breadcrumbs` | Le fil d'Ariane à l'intérieur de l'en-tête |
| `modal` | Les fenêtres modales de suppression, d'action et d'importation |
| `content` | L'intégralité du corps de la page de liste |
| `list_search` | La zone de saisie de recherche |
| `list_toolbar` | La ligne d'outils contenant les filtres, les boutons d'exportation, d'importation et de création |
| `list_toolbar_extra` | Un point d'insertion supplémentaire tout à la fin de la barre d'outils |
| `list_before_table` | Un point d'insertion précédant le tableau |
| `list_table` | L'élément `<table>` lui-même |
| `list_header` | La ligne `<thead>` contenant la case à cocher et les cellules d'en-tête de colonne |
| `list_row` | Une seule ligne `<tr>` dans le tableau de résultats (bloc à portée limitée ; donne accès à `row`, `row_pk` et `row_clickable`) |
| `list_row_actions_before` | La cellule des actions de ligne lorsque `row_actions_position` vaut `BEFORE_COLUMNS` (bloc à portée limitée) |
| `list_row_actions_after` | La cellule des actions de ligne lorsque `row_actions_position` vaut `AFTER_COLUMNS` (bloc à portée limitée) |
| `list_empty` | Le texte indicatif « No data » (bloc à portée limitée rendu pour les états vides) |
| `list_after_table` | Un point d'insertion suivant le tableau |
| `list_footer` | Le pied de page de pagination et de plage |
| `head_css` | Ajouts de feuilles de style propres à la page |
| `script` | Ajouts de script propres à la page |

### `detail.html`

| Bloc | Contenu |
| --- | --- |
| `header` | L'en-tête de la page (inclut le titre, le fil d'Ariane et les actions) |
| `page_title` | Le titre `<h1>` à l'intérieur de l'en-tête |
| `breadcrumbs` | Le fil d'Ariane à l'intérieur de l'en-tête |
| `modal` | Les fenêtres modales de suppression et d'action |
| `content` | L'intégralité du corps de la page de détail |
| `detail_before` | Un point d'insertion précédant la carte de détail |
| `detail_title` | La zone de titre à l'intérieur de la carte de détail |
| `detail_actions` | Les boutons d'action à l'intérieur de la carte de détail |
| `details_table` | Le tableau principal des champs et valeurs |
| `detail_after` | Un point d'insertion suivant la carte de détail |
| `head_css` | Ajouts de feuilles de style propres à la page |
| `script` | Ajouts de script propres à la page |

### `create.html` / `edit.html`

| Bloc | Contenu |
| --- | --- |
| `header` | L'en-tête de la page (inclut le titre et le fil d'Ariane) |
| `page_title` | Le titre `<h1>` à l'intérieur de l'en-tête |
| `breadcrumbs` | Le fil d'Ariane à l'intérieur de l'en-tête |
| `content` | L'intégralité du corps de la page de formulaire |
| `form_before` | Un point d'insertion précédant la carte de formulaire |
| `create_card_header` / `edit_card_header` | La zone d'en-tête à l'intérieur de la carte de formulaire |
| `create_form` / `edit_form` | Les groupes de [mise en page de formulaire](form-layout.md) (chacun rendu via `_form_group.html`) et leurs éléments de saisie de champ |
| `create_inlines` / `edit_inlines` | La zone des ensembles de formulaires en ligne |
| `form_footer` | Les boutons Enregistrer, Enregistrer et continuer et Ajouter un autre |
| `form_after` | Un point d'insertion suivant la carte de formulaire |
| `head_css` | Ajouts de feuilles de style propres à la page |
| `script` | Ajouts de script propres à la page |

### `login.html`

| Bloc | Contenu |
| --- | --- |
| `header` / `sidebar` | Laissés vides (la page de connexion masque l'habillage standard de l'application) |
| `content` | L'intégralité du corps de la page de connexion |
| `login_logo` | Le logo affiché au-dessus du formulaire de connexion |
| `login_title` | Le texte du titre de la page de connexion |
| `login_form_before` | Un point d'insertion précédant les champs du formulaire |
| `login_fields` | Les champs de saisie du nom d'utilisateur et du mot de passe |
| `login_form_footer` | Un point d'insertion après les champs mais à l'intérieur du formulaire |
| `login_card_footer` | Un point d'insertion situé directement sous la carte de connexion |
| `script` | Ajouts de script propres à la page |

### `index.html`

| Bloc | Contenu |
| --- | --- |
| `head_css` | Ajouts de feuilles de style propres aux widgets |
| `content` | La grille de widgets du tableau de bord |
| `script` | Ajouts de script propres aux widgets |

### `error.html`

| Bloc | Contenu |
| --- | --- |
| `header` / `sidebar` | Laissés vides (la page d'erreur masque l'habillage standard de l'application) |
| `content` | Le message d'erreur et les actions associées |
| `error_actions` | Les boutons d'action affichés sous le message d'erreur (comme un bouton « Retour ») |

!!! tip
    Appelez `{{ super() }}` à l'intérieur d'une surcharge pour conserver le contenu du bloc intégré et y ajouter plutôt que de le remplacer. L'exemple `list_toolbar_extra` ci-dessus procède ainsi, et les fichiers intégrés `index.html` et `create.html` utilisent le même schéma pour le bloc `head_css`.

### Exemple : remplacer le logo de la barre latérale par un SVG en ligne

Passer une URL à `Admin(logo_url=...)` est le moyen le plus rapide de définir un logo et couvre la plupart des cas, y compris les fichiers `.svg` externes. Cependant, le template intégré rend cette URL à l'intérieur d'une balise `<img>`, si bien que le SVG ne peut pas hériter des propriétés CSS de la page environnante.

Surchargez le bloc `brand` avec du **balisage `<svg>` en ligne** lorsque vous avez besoin que le logo réagisse au reste de l'interface.

#### Mise en œuvre

Créez un fichier `layout.html` dans votre répertoire de templates. Chaque page du panneau d'administration hérite de `layout.html`, cette unique surcharge s'applique donc à l'ensemble du site.

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! tip "Conserver la classe navbar-logo"
    Laissez la classe CSS `navbar-logo` sur votre élément `<svg>` personnalisé. Elle confère à votre graphique en ligne l'alignement, le remplissage et le dimensionnement du framework, sans aucun CSS de votre part.

## Surcharger les templates de champs

Le contexte de chaque champ utilise trois sous-répertoires :

| Répertoire | Utilisé dans |
| --- | --- |
| `fields/list/<type>.html` | Cellule du tableau de liste (compacte, en lecture seule) |
| `fields/detail/<type>.html` | Affichage sur la page de détail (complet, en lecture seule) |
| `fields/form/<type>.html` | Champ de saisie des formulaires de création et de modification |

Vous pouvez surcharger la cellule de liste des champs de type texte sans toucher au formulaire ni à l'affichage de détail :

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

Pour faire pointer une **instance de champ** vers votre template au lieu de surcharger le type partout, définissez `list_template`, `detail_template`, `form_template`, `null_template` ou `empty_template` sur le champ lui-même :

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template` (par défaut `"fields/detail/_null.html"`) et `empty_template` (par défaut `"fields/detail/_empty.html"`) sont des emplacements distincts. Les pages de liste et de détail les rendent à la place de `list_template` ou `detail_template` chaque fois que la valeur du champ est `None` ou une liste ou un tuple vide :

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## Surcharger les templates de widgets

Les widgets suivent le même schéma de surcharge. Placez vos fichiers sous le répertoire `widgets/` :

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## Variables globales de template

Ces variables sont disponibles dans tous les templates sans être passées explicitement. `Admin` les installe comme variables globales Jinja2 une seule fois lors de la configuration :

| Variable | Type | Description |
| --- | --- | --- |
| `views` | `list[BaseView]` | Toutes les vues enregistrées (utilisées pour rendre la barre latérale) |
| `app_title` | `str` | Le titre du panneau d'administration (`Admin(title=...)`) |
| `is_auth_enabled` | `bool` | `True` si un fournisseur d'authentification est configuré |
| `__name__` | `str` | Le préfixe de nom de route du panneau d'administration (par exemple `"admin"`) |
| `static_url` | `callable` | `static_url(request, path, v=None)` → URL d'une ressource statique intégrée. L'argument `v` ajoute un paramètre de requête `?v=` d'invalidation de cache. |
| `logo_url` | `callable` | `logo_url(request)` → URL du logo de la barre latérale, ou `None` si non défini |
| `login_logo_url` | `callable` | `login_logo_url(request)` → URL du logo de la page de connexion, ou `None` si non défini |
| `favicon_url` | `callable` | `favicon_url(request)` → URL du favicon, ou `None` si non défini |
| `list_url` | `callable` | `list_url(request, **overrides)` → URL avec les `overrides` fusionnés dans sa chaîne de requête (utilisé pour les liens de tri, de pagination ou de recherche). Passez `None` pour supprimer une clé. |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → URL de la page de détail d'un enregistrement |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → URL de la page de modification d'un enregistrement |
| `export_url` | `callable` | `export_url(request, key, fmt)` → URL de téléchargement d'exportation transportant l'état de filtre/tri/recherche de la page de liste actuelle |
| `import_url` | `callable` | `import_url(request, key)` → URL POST d'importation |
| `get_locale` | `callable` | `get_locale()` → Chaîne de la locale active (ne nécessite pas d'argument `request`) |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → Nom lisible d'une chaîne de locale |
| `i18n_config` | `I18nConfig` | Objet de configuration i18n du panneau d'administration |
| `get_timezone` | `callable` | `get_timezone()` → Chaîne du fuseau horaire actif (ne nécessite pas d'argument `request`) |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → Nom lisible d'une chaîne de fuseau horaire |
| `timezone_config` | `TimezoneConfig | None` | Configuration du fuseau horaire du panneau d'administration |
| `theme_settings` | `TablerSettings` | Configuration active du thème Tabler (base, primary, radius, mode) exposée par `DefaultTheme` |
| `csrf_input` | `callable` | `csrf_input(request)` → Rend le `<input>` CSRF caché |

!!! note
    `get_locale`, `get_locale_display_name`, `get_timezone` et `get_timezone_display_name` ne prennent aucun paramètre `request`. Ils lisent la locale et le fuseau horaire depuis des `contextvars` que `LocaleMiddleware` renseigne pendant toute la durée de la requête, plutôt que depuis l'objet `Request`.

## Variables de contexte par page

En plus des variables globales ci-dessus, chaque page transmet son propre dictionnaire de contexte à `TemplateResponse`.

### `list.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | La vue courante |
| `title` | `str` | Titre de la page |
| `fields` | `list[BaseField]` | Colonnes actuellement visibles |
| `all_fields` | `list[BaseField]` | Tous les champs de liste (y compris ceux masqués) |
| `rows` | `list[dict]` | Données de lignes sérialisées |
| `total` | `int` | Nombre total d'enregistrements correspondants pour la pagination |
| `total_pages` | `int` | Nombre total de pages |
| `range_start` | `int` | Numéro du premier enregistrement sur cette page (à partir de 1) |
| `range_end` | `int` | Numéro du dernier enregistrement sur cette page |
| `list_params` | `ListParams` | État de l'URL analysé (page, page_size, q, sorts, filters) |
| `filter_logic` | `str | None` | Vaut `"and"` ou `"or"` pour le groupe de filtres de premier niveau actif |
| `filter_chips` | `list` | Descripteurs des puces de filtres actives |
| `filter_builder_fields` | `list` | Champs disponibles dans l'interface du constructeur de filtres |
| `raw_filter` | `str | None` | Chaîne JSON brute du filtre provenant de l'URL |
| `_actions` | `list` | Actions groupées disponibles |
| `row_actions` | `dict[Any, list]` | Actions de ligne disponibles par enregistrement, indexées par clé primaire |

### `detail.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | La vue courante |
| `title` | `str` | Titre de la page |
| `obj` | `dict` | Enregistrement sérialisé |
| `raw_obj` | `Any` | L'objet modèle brut avant sérialisation |
| `inlines` | `list[dict]` | Contexte en ligne (`[{"inline": InlineModelView, "rows": [...]}]`) |
| `_actions` | `list` | Actions de ligne disponibles |

### `create.html` / `edit.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | La vue courante |
| `title` | `str` | Titre de la page |
| `obj` | `dict` | Valeurs actuelles des champs (valeurs par défaut à la création, valeurs existantes à la modification) |
| `raw_obj` | `Any` | Objet modèle brut (modification uniquement, absent à la création) |
| `errors` | `dict[str, list[str]]` | Erreurs de validation indexées par nom de champ (présentes uniquement après une soumission échouée) |
| `inlines` | `list[dict]` | Contexte des ensembles de formulaires en ligne |

## Ajouter vos propres variables globales et filtres

Pour ajouter vos propres variables et fonctions aux templates, créez une sous-classe de `Admin` et surchargez `__init__`. Appelez d'abord `super().__init__()`, afin que `self.templates` existe avant que vous ne l'enrichissiez :

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin


class MyAdmin(Admin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.templates.env.globals["site_name"] = "My App"
        self.templates.env.filters["currency"] = lambda v: f"${v:,.2f}"


engine = create_engine("sqlite:///admin.sqlite")
admin = MyAdmin(engine, title="My Admin")
```

## Filtres Jinja2 intégrés

Chaque instance du panneau d'administration enregistre ces filtres lors de `_setup_templates` :

| Filtre | Signature | Description |
| --- | --- | --- |
| `is_custom_view` | `view | is_custom_view` | Renvoie `True` si la ressource est une `CustomView` |
| `is_link` | `view | is_link` | Renvoie `True` si la ressource est une `Link` |
| `is_model_view` | `view | is_model_view` | Renvoie `True` si la ressource est une `BaseModelView` |
| `is_dropdown` | `view | is_dropdown` | Renvoie `True` si la ressource est une `DropDown` |
| `tojson` | `value | tojson` | Sérialisation JSON sûre pour HTML (remplace le `tojson` par défaut de Jinja2) |
| `file_icon` | `mime_type | file_icon` | Renvoie une classe d'icône complète pour un type MIME (par exemple, `application/pdf` → `fa-solid fa-fw fa-file-pdf`) ; surchargez `self.templates.env.filters["file_icon"]` pour utiliser votre propre jeu d'icônes |
| `to_view` | `key | to_view` | Recherche une `BaseModelView` enregistrée à partir de sa chaîne de clé ; lève une `HTTPException` 404 si introuvable |
| `is_iter` | `value | is_iter` | Renvoie `True` si la valeur est une `list` ou un `tuple` |
| `is_str` | `value | is_str` | Renvoie `True` si la valeur est une `str` |
| `is_dict` | `value | is_dict` | Renvoie `True` si la valeur est un `dict` |
| `ra` | `value | ra` | Convertit une chaîne en membre de l'énumération `RequestAction` |
| `safe_url` | `url | safe_url` | Renvoie l'URL uniquement si elle passe la vérification d'URL sûre, sinon renvoie `""` |
| `sanitize_html` | `html | sanitize_html` | Supprime les balises non autorisées d'une chaîne HTML et renvoie une `Markup` |

---

## Pour aller plus loin

* **[Mises en page de formulaire](form-layout.md) :** divisez les formulaires de création et de modification en groupes titrés, éventuellement repliables, et surchargez `_form_group.html` pour modifier leur balisage.
* **[Thèmes personnalisés](custom-themes.md) :** restylez le panneau d'administration sans toucher aux templates individuels.
* **[Champs personnalisés](custom-fields.md) :** associez la classe Python d'un champ à son propre `list_template` ou `form_template`.
* **[Points d'extension](extension-points.md) :** la liste complète des surfaces enfichables au-delà des templates.

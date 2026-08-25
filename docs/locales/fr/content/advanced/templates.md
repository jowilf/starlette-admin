---
title: Templates
description: Remplacez les templates Jinja2 de starlette-admin pour personnaliser
  entièrement la structure HTML de vues ou de champs spécifiques.
source_hash: 92643d00ab546c400a73e995d391d57cd0f5c054cba9d3ca8a5438df8eeb86ae
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/templates/)
<!-- translation-notice:end -->

# Templates

Chaque page de l'admin est un template Jinja2 que vous pouvez remplacer. Modifiez une seule page de liste, la cellule d'un champ dans le tableau, ou un widget du dashboard sans dupliquer l'arborescence des templates intégrés.

## Fonctionnement du loader de templates

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

`Admin` construit un `ChoiceLoader` Jinja2 qui interroge d'abord votre `templates_dir`, puis le répertoire intégré du package `starlette_admin/templates/`. Placez un fichier sous `my_templates/` au même chemin relatif qu'il occupe dans `starlette_admin/templates/` et votre fichier masquera celui intégré. Tous les autres templates continuent d'être rendus depuis le répertoire intégré.

!!! note
    La chaîne de loaders enregistre également un `PrefixLoader` sous la clé `@starlette-admin`, qui pointe toujours vers les templates intégrés, quels que soient les fichiers qui les masquent dans `templates_dir`. Accédez-y avec le format de chemin `@starlette-admin/<name>.html`, sans barre oblique finale sur le préfixe lui-même. Consultez [Remplacer le template d'une seule page](#remplacer-le-template-dune-seule-page) ci-dessous pour connaître son utilité.

## Cartographie des répertoires de templates

| Chemin | Utilisé pour |
| --- | --- |
| `base.html` | Mise en page HTML externe (`<html>`, `<head>`, scripts) |
| `layout.html` | Habillage de la sidebar et de la barre supérieure (étend `base.html`) |
| `index.html` | Dashboard ou page d'accueil |
| `list.html` | Page de liste d'un modèle (tableau, barre de filtres, pagination) |
| `detail.html` | Vue détaillée (en lecture seule) d'un enregistrement |
| `create.html` | Formulaire de création |
| `edit.html` | Formulaire d'édition |
| `login.html` | Page de connexion |
| `error.html` | Page d'erreur HTTP (403, 404, etc.) |
| `actions.html` | Fenêtre modale d'action groupée |
| `row-actions.html` | Menu déroulant d'actions par ligne |
| `inline.html` | Formset en ligne sur les pages de création/édition |
| `inline_detail.html` | Tableau en ligne sur la page de détail |
| `inline_row.html` | Ligne unique dans un formset en ligne |
| `_filter_bar.html` | Barre des filtres actifs au-dessus de la liste |
| `_filter_builder.html` | Fenêtre modale du constructeur de filtres |
| `_pagination.html` | Contrôles de pagination |
| `_column_header.html` | Cellule d'en-tête de colonne triable |
| `_form_footer.html` | Boutons Enregistrer, Enregistrer et continuer, ou Ajouter un autre |
| `_form_group.html` | Fieldset d'un groupe de [mise en page de formulaire](form-layout.md) sur le formulaire de création/édition |
| `_form_group_fields.html` | Les champs affichés à l'intérieur d'un groupe de mise en page de formulaire |
| `fields/list/<type>.html` | Cellule de colonne pour un type de champ |
| `fields/detail/<type>.html` | Affichage sur la page de détail pour un type de champ |
| `fields/form/<type>.html` | Widget de saisie de formulaire pour un type de champ |
| `widgets/<name>.html` | Template de widget du dashboard |
| `modals/actions.html` | Fenêtre modale de confirmation d'action |
| `modals/delete.html` | Fenêtre modale de confirmation de suppression |
| `modals/error.html` | Fenêtre modale d'erreur |
| `modals/import.html` | Fenêtre modale d'importation |
| `macros/views.html` | Macros Jinja2 partagées utilisées dans plusieurs pages |

!!! note
    L'arborescence intégrée contient aussi `modals/loading.html`, une fenêtre modale générique d'état de chargement, ainsi que plusieurs templates spécifiques aux champs dans `fields/list/`, `fields/detail/` et `fields/form/`. Vérifiez les noms de fichiers exacts dans `starlette_admin/templates/` pour la version installée avant de remplacer un fichier `<type>.html` générique.

## Remplacer le template d'une seule page

```
my_templates/
└── list.html   ← remplace le list.html intégré

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Bannière personnalisée au-dessus de la liste.</div>
  {{ super() }}
{% endblock %}

```

`{% extends "list.html" %}` résoudrait vers votre propre `my_templates/list.html`, car `templates_dir` est interrogé en premier, et cette référence circulaire provoque une erreur de récursion infinie. Le préfixe `@starlette-admin/` pointe toujours vers la copie intégrée : chaque `extends` et `include` dans un fichier de remplacement doit donc l'utiliser plutôt que le nom de fichier seul.

## Blocs remplaçables

Chaque page intégrée étend `layout.html`, qui étend lui-même `base.html`. Remplacez un seul `{% block %}` plutôt qu'un fichier entier pour modifier un fragment sans dupliquer le reste de la page :

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
| `head` | Un point d'insertion libre dans l'élément `<head>` |
| `body` | Tout le contenu de `<body>` (ce bloc est remplacé par `layout.html`) |
| `modal` | Un point d'insertion au niveau de la page pour les fenêtres modales |
| `script` | Les balises `<script>` situées juste avant la balise fermante `</body>` |
| `tail` | Un point d'insertion vide tout à la fin de `<body>`, après `script` |

### `layout.html`

| Bloc | Contenu |
| --- | --- |
| `sidebar` | L'intégralité de l'élément `<aside>` de la sidebar (y compris le logo, le menu et le pied de page) |
| `brand` | L'image du logo (ou le repli `app_title`) dans le lien de marque de la sidebar |
| `sidebar_menu` | La liste des liens de vues dans la sidebar |
| `sidebar_footer` | La zone basse de la sidebar |
| `user_menu_trigger` | L'avatar et le nom d'utilisateur affichés sur le bouton du menu utilisateur. Défini une seule fois et réutilisé à la fois sur la sidebar mobile et la navbar de bureau via `self.user_menu_trigger()`, si bien que le remplacer met à jour les deux |
| `user_menu_items` | Les éléments déroulants du menu utilisateur |
| `navbar` | La barre de navigation supérieure |
| `navbar_extra` | Du contenu supplémentaire placé dans la navbar à côté du menu utilisateur |
| `header` | La zone d'en-tête de la page positionnée au-dessus de `content` (inclut le titre et le fil d'Ariane) |
| `flash_messages` | La zone dédiée à l'affichage des messages flash |
| `content_before` | Un point d'insertion immédiatement avant `content` |
| `content` | Le contenu principal de la page (c'est le bloc alimenté par `list.html`, `detail.html`, etc.) |
| `content_after` | Un point d'insertion immédiatement après `content` |
| `page_footer` | La zone de pied de page située sous le contenu de la page |

### `list.html`

| Bloc | Contenu |
| --- | --- |
| `header` | L'en-tête de la page (inclut le titre et le fil d'Ariane) |
| `page_title` | Le titre `<h1>` à l'intérieur de l'en-tête |
| `breadcrumbs` | Le fil d'Ariane à l'intérieur de l'en-tête |
| `modal` | Les fenêtres modales de suppression, d'action et d'importation |
| `content` | Le corps complet de la page de liste |
| `list_search` | La zone de saisie de recherche |
| `list_toolbar` | La rangée d'outils contenant les boutons de filtres, d'export, d'import et de création |
| `list_toolbar_extra` | Un point d'insertion supplémentaire tout à la fin de la barre d'outils |
| `list_before_table` | Un point d'insertion avant le tableau |
| `list_table` | L'élément `<table>` lui-même |
| `list_header` | La ligne `<thead>` contenant la case à cocher et les cellules d'en-tête de colonnes |
| `list_row` | Une seule ligne `<tr>` du tableau de résultats (bloc à portée ; donne accès à `row`, `row_pk` et `row_clickable`) |
| `list_row_actions_before` | La cellule des actions de ligne lorsque `row_actions_position` vaut `BEFORE_COLUMNS` (bloc à portée) |
| `list_row_actions_after` | La cellule des actions de ligne lorsque `row_actions_position` vaut `AFTER_COLUMNS` (bloc à portée) |
| `list_empty` | Le texte indicatif « No data » (bloc à portée rendu pour les états vides) |
| `list_after_table` | Un point d'insertion après le tableau |
| `list_footer` | Le pied de page de pagination et de plage |
| `head_css` | Ajouts de feuilles de style propres à la page |
| `script` | Ajouts de scripts propres à la page |

### `detail.html`

| Bloc | Contenu |
| --- | --- |
| `header` | L'en-tête de la page (inclut le titre, le fil d'Ariane et les actions) |
| `page_title` | Le titre `<h1>` à l'intérieur de l'en-tête |
| `breadcrumbs` | Le fil d'Ariane à l'intérieur de l'en-tête |
| `modal` | Les fenêtres modales de suppression et d'action |
| `content` | Le corps complet de la page de détail |
| `detail_before` | Un point d'insertion avant la carte de détail |
| `detail_title` | La zone de titre à l'intérieur de la carte de détail |
| `detail_actions` | Les boutons d'action à l'intérieur de la carte de détail |
| `details_table` | Le tableau principal des champs et valeurs |
| `detail_after` | Un point d'insertion après la carte de détail |
| `head_css` | Ajouts de feuilles de style propres à la page |
| `script` | Ajouts de scripts propres à la page |

### `create.html` / `edit.html`

| Bloc | Contenu |
| --- | --- |
| `header` | L'en-tête de la page (inclut le titre et le fil d'Ariane) |
| `page_title` | Le titre `<h1>` à l'intérieur de l'en-tête |
| `breadcrumbs` | Le fil d'Ariane à l'intérieur de l'en-tête |
| `content` | Le corps complet de la page du formulaire |
| `form_before` | Un point d'insertion avant la carte du formulaire |
| `create_card_header` / `edit_card_header` | La zone d'en-tête à l'intérieur de la carte du formulaire |
| `create_form` / `edit_form` | Les groupes de [mise en page de formulaire](form-layout.md) (chacun rendu via `_form_group.html`) et leurs éléments de saisie de champs |
| `create_inlines` / `edit_inlines` | La zone du formset en ligne |
| `form_footer` | Les boutons Enregistrer, Enregistrer et continuer, et Ajouter un autre |
| `form_after` | Un point d'insertion après la carte du formulaire |
| `head_css` | Ajouts de feuilles de style propres à la page |
| `script` | Ajouts de scripts propres à la page |

### `login.html`

| Bloc | Contenu |
| --- | --- |
| `header` / `sidebar` | Laissés vides (la page de connexion masque l'habillage standard de l'application) |
| `content` | Le corps complet de la page de connexion |
| `login_logo` | Le logo affiché au-dessus du formulaire de connexion |
| `login_title` | Le texte du titre de la page de connexion |
| `login_form_before` | Un point d'insertion avant les champs du formulaire |
| `login_fields` | Les champs de saisie du nom d'utilisateur et du mot de passe |
| `login_form_footer` | Un point d'insertion après les champs mais à l'intérieur du formulaire |
| `login_card_footer` | Un point d'insertion situé directement sous la carte de connexion |
| `script` | Ajouts de scripts propres à la page |

### `index.html`

| Bloc | Contenu |
| --- | --- |
| `head_css` | Ajouts de feuilles de style propres aux widgets |
| `content` | La grille de widgets du dashboard |
| `script` | Ajouts de scripts propres aux widgets |

### `error.html`

| Bloc | Contenu |
| --- | --- |
| `header` / `sidebar` | Laissés vides (la page d'erreur masque l'habillage standard de l'application) |
| `content` | Le message d'erreur et les actions associées |
| `error_actions` | Boutons d'action affichés sous le message d'erreur (comme un bouton « Retour ») |

!!! tip
    Appelez `{{ super() }}` dans un fichier de remplacement pour conserver le contenu du bloc intégré et y ajouter du contenu plutôt que de le remplacer. L'exemple `list_toolbar_extra` ci-dessus procède ainsi, et les fichiers intégrés `index.html` et `create.html` utilisent le même motif pour le bloc `head_css`.

### Exemple : remplacer le logo de la sidebar par un SVG en ligne

Passer une URL à `Admin(logo_url=...)` est le moyen le plus rapide de définir un logo et couvre la plupart des cas, y compris les fichiers `.svg` externes. Cependant, le template intégré affiche cette URL dans une balise `<img>`, si bien que le SVG ne peut pas hériter des propriétés CSS de la page environnante.

Remplacez le bloc `brand` avec du **balisage `<svg>` en ligne** lorsque vous avez besoin que le logo réponde au reste de l'interface.

#### Implémentation

Créez un fichier `layout.html` dans votre répertoire de templates. Chaque page de l'admin hérite de `layout.html`, ce remplacement s'applique donc à l'ensemble du site.

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! tip "Conservez la classe navbar-logo"
    Gardez la classe CSS `navbar-logo` sur votre élément `<svg>` personnalisé. Elle confère à votre graphique en ligne l'alignement, le padding et le dimensionnement du framework sans aucun CSS de votre part.

## Remplacer les templates de champs

Le contexte de chaque champ utilise trois sous-répertoires :

| Répertoire | Utilisé dans |
| --- | --- |
| `fields/list/<type>.html` | Cellule du tableau de liste (compacte, lecture seule) |
| `fields/detail/<type>.html` | Affichage sur la page de détail (complet, lecture seule) |
| `fields/form/<type>.html` | Champ de saisie des formulaires de création et d'édition |

Vous pouvez remplacer la cellule de liste pour les champs textuels sans toucher au formulaire ni à l'affichage détaillé :

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

Pour pointer une **instance de champ** précise vers votre template au lieu de remplacer le type partout, définissez `list_template`, `detail_template`, `form_template`, `null_template` ou `empty_template` directement sur le champ :

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template` (par défaut `"fields/detail/_null.html"`) et `empty_template` (par défaut `"fields/detail/_empty.html"`) sont des emplacements distincts. Les pages de liste et de détail les affichent à la place de `list_template` ou `detail_template` chaque fois que la valeur du champ est `None` ou une liste ou un tuple vide :

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## Remplacer les templates de widgets

Les widgets suivent le même motif de remplacement. Placez vos fichiers sous le répertoire `widgets/` :

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## Variables globales de template

Ces variables sont disponibles dans chaque template sans avoir à être passées explicitement. `Admin` les installe comme variables globales Jinja2 une seule fois lors de la configuration :

| Variable | Type | Description |
| --- | --- | --- |
| `views` | `list[BaseView]` | Toutes les vues enregistrées (utilisées pour rendre la sidebar) |
| `app_title` | `str` | Le titre de l'admin (`Admin(title=...)`) |
| `is_auth_enabled` | `bool` | `True` si un fournisseur d'authentification est configuré |
| `__name__` | `str` | Le préfixe de nom de route de l'admin (par exemple, `"admin"`) |
| `static_url` | `callable` | `static_url(request, path, v=None)` → URL d'une ressource statique intégrée. L'argument `v` ajoute un paramètre de requête anti-cache `?v=`. |
| `logo_url` | `callable` | `logo_url(request)` → URL du logo de la sidebar, ou `None` si non défini |
| `login_logo_url` | `callable` | `login_logo_url(request)` → URL du logo de la page de connexion, ou `None` si non défini |
| `favicon_url` | `callable` | `favicon_url(request)` → URL du favicon, ou `None` si non défini |
| `list_url` | `callable` | `list_url(request, **overrides)` → URL avec `overrides` fusionnés dans sa chaîne de requête (utilisé pour les liens de tri, de pagination ou de recherche). Passez `None` pour supprimer une clé. |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → URL de la page de détail d'un enregistrement |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → URL de la page d'édition d'un enregistrement |
| `export_url` | `callable` | `export_url(request, key, fmt)` → URL de téléchargement d'export reprenant l'état de filtrage/tri/recherche de la page de liste courante |
| `import_url` | `callable` | `import_url(request, key)` → URL POST d'importation |
| `get_locale` | `callable` | `get_locale()` → Chaîne de la locale active (ne nécessite pas d'argument `request`) |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → Nom lisible d'une chaîne de locale |
| `i18n_config` | `I18nConfig` | Objet de configuration i18n de l'admin |
| `get_timezone` | `callable` | `get_timezone()` → Chaîne du fuseau horaire actif (ne nécessite pas d'argument `request`) |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → Nom lisible d'une chaîne de fuseau horaire |
| `timezone_config` | `TimezoneConfig | None` | Configuration du fuseau horaire de l'admin |
| `theme_settings` | `TablerSettings` | Configuration active du thème Tabler (base, primary, radius, mode) exposée par `DefaultTheme` |
| `csrf_input` | `callable` | `csrf_input(request)` → Rend le champ `<input>` CSRF caché |

!!! note
    `get_locale`, `get_locale_display_name`, `get_timezone` et `get_timezone_display_name` ne prennent pas de paramètre `request`. Ils lisent la locale et le fuseau horaire depuis des `contextvars` que `LocaleMiddleware` renseigne pendant toute la durée de la requête, plutôt que depuis l'objet `Request`.

## Variables de contexte par page

En plus des variables globales ci-dessus, chaque page transmet son propre dictionnaire de contexte à `TemplateResponse`.

### `list.html`

| Variable | Type | Description |
| --- | --- | --- |
| `view` | `BaseModelView` | La vue courante |
| `title` | `str` | Titre de la page |
| `fields` | `list[BaseField]` | Colonnes actuellement visibles |
| `all_fields` | `list[BaseField]` | Tous les champs de liste (y compris ceux cachés) |
| `rows` | `list[dict]` | Données de lignes sérialisées |
| `total` | `int` | Nombre total d'enregistrements correspondants pour la pagination |
| `total_pages` | `int` | Nombre total de pages |
| `range_start` | `int` | Numéro du premier enregistrement de cette page (à partir de 1) |
| `range_end` | `int` | Numéro du dernier enregistrement de cette page |
| `list_params` | `ListParams` | État d'URL analysé (page, page_size, q, sorts, filters) |
| `filter_logic` | `str | None` | Vaut `"and"` ou `"or"` pour le groupe de filtres actif de premier niveau |
| `filter_chips` | `list` | Descripteurs des puces de filtres actives |
| `filter_builder_fields` | `list` | Champs disponibles dans l'interface du constructeur de filtres |
| `raw_filter` | `str | None` | Chaîne JSON brute du filtre provenant de l'URL |
| `_actions` | `list` | Actions groupées disponibles |
| `row_actions` | `dict[Any, list]` | Actions de ligne disponibles par enregistrement, indexées par pk |

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
| `obj` | `dict` | Valeurs actuelles des champs (valeurs par défaut à la création, valeurs existantes à l'édition) |
| `raw_obj` | `Any` | Objet modèle brut (édition uniquement, absent à la création) |
| `errors` | `dict[str, list[str]]` | Erreurs de validation indexées par nom de champ (présent uniquement après une soumission échouée) |
| `inlines` | `list[dict]` | Contexte du formset en ligne |

## Ajouter vos propres globals et filtres

Pour ajouter vos propres variables et fonctions aux templates, créez une sous-classe d'`Admin` et redéfinissez `__init__`. Appelez d'abord `super().__init__()`, afin que `self.templates` existe avant que vous ne le complétiez :

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

Chaque instance de l'admin enregistre ces filtres durant `_setup_templates` :

| Filtre | Signature | Description |
| --- | --- | --- |
| `is_custom_view` | `view | is_custom_view` | Renvoie `True` si la ressource est une `CustomView` |
| `is_link` | `view | is_link` | Renvoie `True` si la ressource est une `Link` |
| `is_model_view` | `view | is_model_view` | Renvoie `True` si la ressource est une `BaseModelView` |
| `is_dropdown` | `view | is_dropdown` | Renvoie `True` si la ressource est une `DropDown` |
| `tojson` | `value | tojson` | Sérialisation JSON sûre pour HTML (remplace le `tojson` par défaut de Jinja2) |
| `file_icon` | `mime_type | file_icon` | Renvoie une classe d'icône complète pour un type MIME (par exemple, `application/pdf` → `fa-solid fa-fw fa-file-pdf`) ; redéfinissez `self.templates.env.filters["file_icon"]` pour utiliser votre propre jeu d'icônes |
| `to_view` | `key | to_view` | Recherche une `BaseModelView` enregistrée à partir de sa clé ; lève une `HTTPException` 404 si introuvable |
| `is_iter` | `value | is_iter` | Renvoie `True` si la valeur est une `list` ou un `tuple` |
| `is_str` | `value | is_str` | Renvoie `True` si la valeur est une `str` |
| `is_dict` | `value | is_dict` | Renvoie `True` si la valeur est un `dict` |
| `ra` | `value | ra` | Convertit une chaîne en membre de l'énumération `RequestAction` |
| `safe_url` | `url | safe_url` | Renvoie l'URL uniquement si elle passe la vérification d'URL sûre, sinon renvoie `""` |
| `sanitize_html` | `html | sanitize_html` | Supprime les balises non autorisées d'une chaîne HTML et renvoie une `Markup` |

---

## Pour aller plus loin

* **[Mises en page de formulaire](form-layout.md) :** Divisez les formulaires de création et d'édition en groupes titrés, éventuellement repliables, et remplacez `_form_group.html` pour modifier leur balisage.
* **[Thèmes personnalisés](custom-themes.md) :** Redonnez du style à l'admin sans toucher aux templates individuels.
* **[Champs personnalisés](custom-fields.md) :** Associez la classe Python d'un champ à son propre `list_template` ou `form_template`.
* **[Points d'extension](extension-points.md) :** La liste complète des surfaces extensibles au-delà des templates.

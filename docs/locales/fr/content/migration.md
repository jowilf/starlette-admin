---
title: Guide de migration
description: Guide de mise à niveau pour migrer des anciennes versions de starlette-admin
  vers la dernière version, incluant les changements majeurs et les nouvelles fonctionnalités.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

# Guide de migration

Cette page rassemble les instructions de mise à niveau entre les versions de `starlette-admin`. Rendez-vous directement à la section correspondant à la version depuis laquelle vous effectuez la mise à niveau.

---

## De 0.17.x à 1.0.0

Cette version refactorise les internes de `starlette-admin` et introduit un large ensemble de nouvelles fonctionnalités. Bien que l'API de haut niveau reste largement inchangée, la mise à jour la plus significative est la réécriture du rendu de la page de liste. Nous avons abandonné DataTables au profit d'un tableau rendu côté serveur. La plupart des autres mises à jour consistent en des renommages ou des modifications mineures de signatures.

Ce guide couvre chaque changement majeur dans l'ordre où vous êtes le plus susceptible de les rencontrer. Chaque section compare l'ancienne API à son remplacement. Si votre implémentation repose sur les bases ou des personnalisations légères (comme une instance d'`Admin`, quelques sous-classes de `ModelView`, `fields` et `searchable_fields`), votre migration se limitera probablement aux sections [Prérequis](#requirements) et [Le constructeur de `Admin`](#the-admin-constructor), plus quelques renommages.

Les personnalisations de l'ancienne page de liste demandent le plus d'attention. Les options DataTables et les fonctions de rendu JavaScript n'ont pas d'équivalent direct et doivent être portées vers des templates côté serveur (voir [Suppression de DataTables](#datatables-removal)).

!!! tip
    Effectuez la mise à niveau de vos dépendances en une seule étape et démarrez votre application. La plupart des attributs supprimés ou renommés génèrent des erreurs claires au démarrage plutôt que d'échouer silencieusement à l'exécution.

### Nouveautés

Au-delà des changements majeurs décrits ci-dessous, cette version inclut :

* **Tableaux de liste natifs :** DataTables a été retiré au profit d'une implémentation intégrée rendue côté serveur. L'état du tableau est désormais entièrement piloté par l'URL, ce qui signifie que toutes les configurations de page, de filtre et de tri sont immédiatement partageables et ajoutables aux favoris.
* **[Filtres](user-guide/filters.md) :** Un constructeur de filtres imbriqués `AND`/`OR` remplace le SearchBuilder de DataTables. Les filtres sont dérivés des types de champs et sont entièrement extensibles en pur Python. Vous pouvez écrire une classe de filtre sans avoir besoin de JavaScript.
* **[Importation et exportation côté serveur](user-guide/export-import.md) :** Importez des données depuis CSV, JSON, Excel et plus encore avec un rapport d'erreurs par ligne, ainsi que des exportateurs côté serveur (CSV, JSON, Excel, PDF, etc.) qui remplacent les boutons côté client de DataTables.
* **[Événements](advanced/events.md) :** Abonnez-vous à des hooks de cycle de vie comme `before_create`, `after_edit_committed`, `after_login` et divers événements d'action.
* **[Thèmes](advanced/custom-themes.md) et [Plugins](advanced/plugins.md) :** Empaquetez et réutilisez des apparences et des comportements personnalisés. Des templates Cookiecutter sont disponibles pour vous aider à démarrer rapidement.
* **[Widgets et tableaux de bord](user-guide/custom-views.md) :** Créez des pages d'index et des vues personnalisées à l'aide de `StatWidget`, `ChartWidget`, `TableWidget` et plus encore.
* **[Mise en page des formulaires](advanced/form-layout.md) :** Organisez logiquement les formulaires de création/édition à l'aide de lignes, de colonnes, de fieldsets et d'onglets.
* **[Édition en ligne](user-guide/inline-edit.md) :** Modifiez un champ unique directement depuis la page de liste.
* **[Formulaires en ligne](user-guide/inline-forms.md) :** Modifiez des modèles liés dans un formulaire parent à l'aide d'`InlineModelView`.
* **Autres améliorations :** [Messages flash](user-guide/flash-messages.md), [connexion OAuth](user-guide/auth.md), un [backend Tortoise ORM](integrations/tortoise.md), de nouveaux champs (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), des `validators` au niveau des champs et une fonctionnalité de copie vers le presse-papiers sur n'importe quel champ.
* **[Journalisation](user-guide/admin.md#debugging) :** Le paquet journalise désormais en interne sous l'espace de noms `starlette_admin`, silencieux par défaut. Passez `Admin(debug=True)` ou appelez `starlette_admin.logging.configure_logging()` pour voir le routage des requêtes, le middleware et les décisions de permissions dans la console, ce qui est particulièrement pratique pendant la migration.
* **Couverture de tests étendue :** La suite de tests est désormais nettement plus vaste, avec des tests Playwright de bout en bout qui valident les flux critiques de l'interface d'administration.
* **Paquet plus léger :** La taille du paquet publié sur PyPI a été réduite d'environ 50 %.

### Prérequis

* **Prise en charge de Python :** Python 3.11 ou plus récent est requis. La prise en charge de Python 3.9 et 3.10 a été abandonnée.
* **Dépendances principales :** `itsdangerous` est désormais une dépendance principale utilisée pour signer les cookies d'administration (jetons CSRF et messages flash).
* **Nouveaux extras optionnels :**

    | Extra | Active |
    | --- | --- |
    | `starlette-admin[email]` | Validation côté serveur d'`EmailField` via `email-validator` |
    | `starlette-admin[pdf]` | Exportation PDF via `reportlab` |
    | `starlette-admin[s3]` | Stockage de fichiers S3 via `aiobotocore` |
    | `starlette-admin[tinymce]` | Assainissement HTML de `TinyMCEEditorField` via `nh3` |
    | `starlette-admin[i18n]` | Traductions via `babel` (inchangé) |

* **Backend Beanie :** Beanie 2.0+ est requis.
* **Backend Odmantic :** Supprimé. Si vous en dépendez, restez sur `starlette-admin<=0.17.1` et manifestez votre intérêt en [ouvrant une issue](https://github.com/jowilf/starlette-admin/issues) ; la prise en charge pourra être rétablie si la demande est suffisante.

### Le constructeur de `Admin`

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` est renommé en `static_dir`.
* **Définissez une `secret_key`.** Cette clé signe les cookies CSRF et de message flash. Si elle est omise, une clé aléatoire est générée au démarrage (ce qui convient pour le développement). Cependant, les valeurs signées seront invalidées à chaque redémarrage et entre plusieurs workers. Passez toujours un secret stable en production.
* `logo_url`, `login_logo_url` et `favicon_url` acceptent désormais un callable `(request) -> str | None`. Cela remplace la personnalisation par requête précédemment fournie par `AdminConfig`.
* **Nouveaux paramètres optionnels :** `theme`, `plugins`, `additional_loaders`, `import_config` et `export_config`.
* **Spécificités SQLAlchemy :** Le premier argument est désormais `session_provider`. Il accepte un `Engine` ou un `AsyncEngine`, et accepte maintenant aussi un `sessionmaker` ou un `async_sessionmaker`. Les appels existants `Admin(engine)` continueront de fonctionner.
* `timezone_config` prend par défaut la valeur `TimezoneConfig()` au lieu de `None`. Les dates et heures s'affichent désormais par défaut dans le fuseau horaire local du visiteur. Passez `timezone_config=None` pour conserver les valeurs brutes.

### Identifiants de vue renommés

La convention de nommage des vues est désormais unifiée. Mettez à jour vos constructeurs de `ModelView` et vos attributs de classe en conséquence :

| Avant | Après |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

```python
# Before
admin.add_view(PostView(Post, identity="post", name="Post", label="Posts"))

# After
admin.add_view(PostView(Post, key="post", display_name="Post", menu_label="Posts"))
```

Notez que `Link` et `DropDown` utilisent également `menu_label` au lieu de `label`.

### Suppression de DataTables

La page de liste n'utilise plus DataTables. Les attributs qui le configuraient auparavant ont été entièrement supprimés :

| Supprimé | Remplacement |
| --- | --- |
| `datatables_options` | Aucun. Le tableau est rendu côté serveur. Personnalisez-le via les templates. |
| `search_builder` | Le nouveau [constructeur de filtres](user-guide/filters.md), activé par `searchable_fields`. |
| `responsive_table` | Aucun. Le tableau gère nativement le débordement. |
| `save_state` | Toujours actif. L'état de la liste (page, tri, filtres, recherche, colonnes visibles) réside désormais dans l'URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (une liste de classes de filtres). |
| `BaseField.render_function_key` | `BaseField.list_template` (template Jinja côté serveur). |

Si vous aviez auparavant écrit des fonctions de rendu JavaScript personnalisées ou des plugins DataTables, portez-les vers des surcharges de `list_template`. Chaque champ rend désormais sa cellule de liste directement depuis `templates/fields/list/*.html`.

### Actions

Les gestionnaires d'actions groupées reçoivent désormais un objet `ActionSelection` au lieu d'une liste de clés primaires. Cela prend en charge la nouvelle bannière « tout sélectionner parmi les correspondances », ciblant chaque ligne correspondant au filtre courant sans les matérialiser côté client.

```python
# Before
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, pks: List[Any]) -> str:
    for article in await self.find_by_pks(request, pks):
        ...
    return f"{len(pks)} articles were published"


# After
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, selection: ActionSelection) -> None:
    for article in await selection.rows():
        ...
    flash(request, f"{await selection.count()} articles were published")
```

* Des méthodes comme `selection.rows()`, `selection.pks()` et `selection.count()` résolvent les lignes cibles paresseusement. Cela s'applique que l'utilisateur ait coché des lignes individuellement ou sélectionné toutes les lignes correspondantes.
* Des propriétés comme `selection.is_select_all`, `selection.filters` et `selection.q` vous permettent de pousser l'opération vers le bas comme une seule requête groupée.
* Le retour d'une chaîne de message de succès est remplacé par les [messages flash](user-guide/flash-messages.md).
* Les gestionnaires d'actions de ligne conservent leur signature d'origine `(request, pk)`.
* **Nouvelles options de `@action` :** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size` et des callables `form` par requête.

### Authentification

Le module `starlette_admin/auth.py` est devenu le paquet `starlette_admin.auth`. Les imports existants depuis `starlette_admin.auth` continueront de fonctionner, mais le contrat du provider a changé.

```python
# Before
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request, response):
        request.session.update({"username": username})
        return response

    async def logout(self, request, response):
        request.session.clear()
        return response

    async def is_authenticated(self, request) -> bool:
        request.state.user = my_users_db.get(request.session.get("username"))
        return request.state.user is not None

    def get_admin_user(self, request) -> AdminUser:
        return AdminUser(username=request.state.user["name"])

    def get_admin_config(self, request) -> AdminConfig:
        return AdminConfig(app_title="My Admin")


# After
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request):
        if username in my_users_db:
            request.session.update({"username": username})
            return None  # default redirect (`next` param or admin index)
        raise LoginFailed("Invalid username or password")

    async def logout(self, request):
        request.session.clear()

    async def authenticate(self, request) -> AdminUser | None:
        user = my_users_db.get(request.session.get("username"))
        return AdminUser(username=user["name"]) if user else None
```

* Les méthodes `is_authenticated`, `get_admin_user` et `get_admin_config` sont fusionnées en une seule méthode `authenticate(request) -> AdminUser | None`. Retourner `None` indique un état non authentifié.
* Les méthodes `login` et `logout` ne reçoivent ni ne retournent plus la `response` préparée. Retournez `None` pour la redirection par défaut, ou retournez une `Response` personnalisée pour modifier ce comportement.
* `AdminConfig` est supprimé. Gérez les titres et logos par requête à l'aide de la forme callable de `logo_url` et `login_logo_url` sur l'instance `Admin`.
* Un [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) intégré gère les flux de connexion OAuth2/OIDC prêts à l'emploi.
* Le décorateur `login_not_required` reste inchangé.

### Exportation et importation

Les exportations sont passées des boutons côté client de DataTables à des endpoints de streaming côté serveur. La fonctionnalité d'importation est entièrement nouvelle, et `ExportType` n'existe plus.

```python
# Before
from starlette_admin import ExportType


class PostView(ModelView):
    export_types = [ExportType.CSV, ExportType.EXCEL]
    export_fields = ["id", "title"]


# After
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["csv", "json"]
    exclude_fields_from_export = ["content"]
    exclude_fields_from_import = ["id"]
```

* `export_types` devient `exporters`. Ce paramètre accepte une liste de noms de formats ou d'instances de `BaseExporter`. Les formats intégrés pris en charge incluent `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` et `pdf`. Les formats autres que `csv` ou `json` nécessitent `tablib`, et le PDF nécessite l'extra `pdf`.
* `importers` accepte une liste de noms de formats ou d'instances de `BaseImporter`. Les formats intégrés pris en charge incluent `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` et `html`. Les formats autres que `csv`, `tsv` ou `json` nécessitent `tablib`.
* `export_fields` (une liste d'inclusion) est remplacé par `exclude_fields_from_export` (une liste d'exclusion). Cela correspond à la convention de nommage des autres attributs `exclude_fields_from_*`.
* Les champs acceptent aussi individuellement `exclude_from_export` et `exclude_from_import`.
* Configurez les limites globales à l'aide de `ExportConfig` et `ImportConfig` sur l'instance `Admin`. Consultez la documentation [Export & Import](user-guide/export-import.md) pour plus de détails.

### Champs personnalisés et remplacement de templates

Les templates de champs sont désormais réorganisés. Mettez à jour vos chemins si vous surchargez des templates intégrés ou si vous fournissez des champs personnalisés :

| Avant | Après |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (fonction de rendu côté client) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (chemin) | Même nom d'attribut, nouveau préfixe de chemin `fields/form/` |

```python
# Before
@dataclass
class RatingField(BaseField):
    display_template: str = "displays/rating.html"
    form_template: str = "forms/rating.html"
    render_function_key: str = "rating"


# After
@dataclass
class RatingField(BaseField):
    detail_template: str = "fields/detail/rating.html"
    form_template: str = "fields/form/rating.html"
    list_template: str = "fields/list/rating.html"
```

De nouvelles capacités par champ à explorer incluent `validators`, `filters`, `default`, des hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard` et un dictionnaire `extra` pour des métadonnées arbitraires. Consultez la documentation [Champs personnalisés](advanced/custom-fields.md) pour plus d'informations.

### CustomView

La classe `CustomView` n'accepte plus `template_path` ni `methods`. Créez des pages simples à l'aide de [widgets](user-guide/custom-views.md). Pour les pages nécessitant un contrôle total, héritez de `CustomView` et déclarez vos routes directement.

```python
# Before
admin.add_view(CustomView(label="Home", path="/home", template_path="home.html"))

# After: widget-based page
admin.add_view(
    CustomView(
        menu_label="System Status",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)


# After: full control
class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(request=request, name="home.html")
```

Le décorateur `@route` permet également à toute vue d'exposer des endpoints supplémentaires pour des besoins tels que des données de graphiques JSON ou des webhooks.

### Backends personnalisés

Si vous avez implémenté `BaseModelView` pour une source de données personnalisée, notez le contrat d'accès aux données mis à jour :

```python
# Before
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...


# After
async def find_all(
    self, request, skip=0, limit=100, q=None, sorts=None, filters=None
): ...
async def count(self, request, q=None, filters=None): ...
```

* Le paramètre `where` typé chaîne est scindé en `q` (pour les termes de recherche plein texte) et `filters` (un arbre `FilterGroup` typé fourni par le constructeur de filtres).
* Le paramètre `order_by` (auparavant une liste de chaînes `"field direction"`) devient `sorts`, prenant une liste de tuples `(field_name, direction)`.
* Chaque backend est désormais livré avec un registre de filtres associant les types de champs aux implémentations de filtres. Consultez la documentation [Backend personnalisé](integrations/custom-backend.md) pour le contrat complet et un exemple fonctionnel.

### Modifications de comportement à examiner

* **Fuseaux horaires :** Les dates et heures s'affichent par défaut dans le fuseau horaire local du visiteur (voir la remarque sur `timezone_config` dans la section Le constructeur de `Admin`).
* **État dans l'URL :** L'état de la liste réside désormais dans l'URL. Les URL d'administration mises en favori depuis des versions précédentes afficheront des états de liste par défaut, car les états DataTables enregistrés ne sont pas migrés.
* **Validation des e-mails :** `EmailField` valide désormais côté serveur lorsque `email-validator` est installé.
* **Protection CSRF :** La protection CSRF est intégrée et basée sur les cookies. Si vous enveloppiez auparavant l'admin avec un middleware CSRF personnalisé, vous pouvez le retirer en toute sécurité. Assurez-vous que votre `secret_key` est définie afin que les jetons survivent aux redémarrages du serveur.
* **Taille de téléversement de `FileField` :** `FileField.max_size` prend désormais par défaut la valeur 50 Mo au lieu d'être illimitée. Passez `max_size=None` pour restaurer l'ancien comportement non borné, ou définissez une valeur explicite pour modifier la limite.

### Éléments supprimés sans remplacement

* `AdminConfig` (voir [Authentification](#authentication)).
* `datatables_options`, `responsive_table` et `save_state` (voir [Suppression de DataTables](#datatables-removal)).
* Le backend Odmantic (voir [Prérequis](#requirements)).

## Obtenir de l'aide

Si vous rencontrez un problème de migration non couvert par ce guide, veuillez [ouvrir une issue](https://github.com/jowilf/starlette-admin/issues). Incluez une reproduction minimale du problème et précisez la version depuis laquelle vous effectuez la mise à niveau. Exécuter avec [`Admin(debug=True)`](user-guide/admin.md#debugging) révèle souvent directement la cause, et les journaux obtenus constituent un excellent complément à votre rapport.

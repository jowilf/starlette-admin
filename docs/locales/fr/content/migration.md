---
title: Guide de migration
description: Guide de mise à niveau pour migrer d'anciennes versions de starlette-admin
  vers la dernière version, incluant les changements incompatibles et les nouvelles
  fonctionnalités.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# Guide de migration

Cette page rassemble les instructions de mise à niveau entre les versions de `starlette-admin`. Accédez directement à la section correspondant à la version depuis laquelle vous effectuez la mise à niveau.

---

## De la version 0.17.x à la 1.0.0

Cette version refactorise les internals de `starlette-admin` et introduit un large ensemble de nouvelles fonctionnalités. Bien que l'API de haut niveau reste globalement inchangée, la mise à jour la plus significative est la réécriture du rendu de la page de liste. Nous avons abandonné DataTables au profit d'un tableau rendu côté serveur. La plupart des autres mises à jour consistent en des renommages ou des modifications mineures de signatures.

Ce guide couvre chaque changement incompatible dans l'ordre où vous êtes le plus susceptible de les rencontrer. Chaque section compare l'ancienne API à son remplacement. Si votre implémentation repose sur les bases ou des personnalisations légères (comme une instance d'`Admin`, quelques sous-classes de `ModelView`, `fields` et `searchable_fields`), votre migration se limitera probablement aux sections [Prérequis](#prérequis) et [Le constructeur Admin](#le-constructeur-admin), plus quelques renommages.

Les personnalisations de l'ancienne page de liste demandent le plus d'attention. Les options DataTables et les fonctions de rendu JavaScript n'ont pas d'équivalent direct et doivent être portées vers des templates côté serveur (voir [Suppression de DataTables](#suppression-de-datatables)).

!!! tip
    Mettez à jour vos dépendances en une seule étape puis démarrez votre application. La plupart des attributs supprimés ou renommés génèrent des erreurs claires au démarrage plutôt que d'échouer silencieusement à l'exécution.

### Nouveautés

Au-delà des changements incompatibles décrits ci-dessous, cette version inclut :

* **Tableaux de liste natifs :** DataTables a été retiré au profit d'une implémentation intégrée, rendue côté serveur. L'état du tableau est désormais entièrement piloté par l'URL, ce qui signifie que toutes les configurations de page, de filtre et de tri sont immédiatement partageables et ajoutables aux favoris.
* **[Filtres](user-guide/filters.md) :** Un constructeur de filtres imbriqués `AND`/`OR` remplace le SearchBuilder de DataTables. Les filtres sont dérivés des types de champs et sont entièrement extensibles en pur Python. Vous pouvez écrire une classe de filtre sans avoir besoin du moindre JavaScript.
* **[Import et export côté serveur](user-guide/export-import.md) :** Importez des données depuis CSV, JSON, Excel et bien plus, avec un rapport d'erreurs par ligne, ainsi que des exporteurs côté serveur (CSV, JSON, Excel, PDF, etc.) qui remplacent les boutons client-side de DataTables.
* **[Événements](advanced/events.md) :** Abonnez-vous à des hooks de cycle de vie comme `before_create`, `after_edit_committed`, `after_login`, et divers événements d'action.
* **[Thèmes](advanced/custom-themes.md) et [Plugins](advanced/plugins.md) :** Empaquetez et réutilisez des apparences et des comportements personnalisés. Des templates Cookiecutter sont disponibles pour vous aider à démarrer rapidement.
* **[Widgets et tableaux de bord](user-guide/custom-views.md) :** Créez des pages d'accueil et des vues personnalisées avec `StatWidget`, `ChartWidget`, `TableWidget`, et plus encore.
* **[Mise en page des formulaires](advanced/form-layout.md) :** Organisez logiquement les formulaires de création/édition à l'aide de lignes, de colonnes, de fieldsets et d'onglets.
* **[Édition en ligne](user-guide/inline-edit.md) :** Modifiez un champ unique directement depuis la page de liste.
* **[Formulaires inline](user-guide/inline-forms.md) :** Modifiez des modèles liés au sein d'un formulaire parent grâce à `InlineModelView`.
* **Autres améliorations :** [Messages flash](user-guide/flash-messages.md), [connexion OAuth](user-guide/auth.md), un [backend Tortoise ORM](integrations/tortoise.md), de nouveaux champs (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), des `validators` au niveau des champs, et une fonctionnalité de copie vers le presse-papiers sur n'importe quel champ.
* **[Journalisation](user-guide/admin.md#debugging) :** Le package journalise désormais en interne sous le namespace `starlette_admin`, silencieux par défaut. Passez `Admin(debug=True)` ou appelez `starlette_admin.logging.configure_logging()` pour voir le routage des requêtes, les middleware et les décisions de permissions dans la console, ce qui est particulièrement pratique pendant une migration.
* **Couverture de tests élargie :** La suite de tests est désormais considérablement plus vaste, avec des tests end-to-end Playwright qui valident les flux critiques de l'interface d'administration.
* **Package plus léger :** La taille du package publié sur PyPI a été réduite d'environ 50 %.

### Prérequis {#prérequis}

* **Support Python :** Python 3.11 ou plus récent est requis. Le support de Python 3.9 et 3.10 a été abandonné.
* **Dépendances principales :** `itsdangerous` est désormais une dépendance principale utilisée pour signer les cookies de l'admin (tokens CSRF et messages flash).
* **Nouveaux extras optionnels :**

    | Extra | Active |
    | --- | --- |
    | `starlette-admin[email]` | Validation serveur d'`EmailField` via `email-validator` |
    | `starlette-admin[pdf]` | Export PDF via `reportlab` |
    | `starlette-admin[s3]` | Stockage de fichiers S3 via `aiobotocore` |
    | `starlette-admin[tinymce]` | Assainissement HTML de `TinyMCEEditorField` via `nh3` |
    | `starlette-admin[i18n]` | Traductions via `babel` (inchangé) |

* **Backend Beanie :** Beanie 2.0+ est requis.
* **Backend Odmantic :** Supprimé. Si vous en dépendez, restez sur `starlette-admin<=0.17.1` et manifestez votre intérêt en [ouvrant une issue](https://github.com/jowilf/starlette-admin/issues) ; le support pourra être réintégré si la demande est suffisante.

### Le constructeur Admin

```python
# Avant
admin = Admin(engine, statics_dir="statics")

# Après
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` est renommé en `static_dir`.
* **Définissez un `secret_key`.** Cette clé signe les cookies CSRF et les cookies de messages flash. Si elle est omise, une clé aléatoire est générée au démarrage (ce qui convient en développement). Cependant, les valeurs signées seront invalidées à chaque redémarrage et entre plusieurs workers. Passez toujours un secret stable en production.
* `logo_url`, `login_logo_url` et `favicon_url` acceptent désormais un callable `(request) -> str | None`. Cela remplace le branding par requête auparavant fourni par `AdminConfig`.
* **Nouveaux paramètres optionnels :** `theme`, `plugins`, `additional_loaders`, `import_config` et `export_config`.
* **Spécificités SQLAlchemy :** Le premier argument est maintenant `session_provider`. Il accepte un `Engine` ou un `AsyncEngine`, et accepte désormais aussi un `sessionmaker` ou un `async_sessionmaker`. Les appels existants `Admin(engine)` continueront de fonctionner.
* `timezone_config` vaut par défaut `TimezoneConfig()` au lieu de `None`. Les datetimes s'affichent désormais par défaut dans le fuseau horaire local du visiteur. Passez `timezone_config=None` pour conserver les valeurs brutes.

### Identifiants de vues renommés

La convention de nommage des vues est désormais unifiée. Mettez à jour vos constructeurs de `ModelView` et vos attributs de classe en conséquence :

| Avant | Après |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

```python
# Avant
admin.add_view(PostView(Post, identity="post", name="Post", label="Posts"))

# Après
admin.add_view(PostView(Post, key="post", display_name="Post", menu_label="Posts"))
```

Notez que `Link` et `DropDown` utilisent également `menu_label` au lieu de `label`.

### Suppression de DataTables

La page de liste n'utilise plus DataTables. Les attributs qui la configuraient précédemment ont été entièrement supprimés :

| Supprimé | Remplacement |
| --- | --- |
| `datatables_options` | Aucun. Le tableau est rendu côté serveur. Personnalisez-le via les templates. |
| `search_builder` | Le nouveau [constructeur de filtres](user-guide/filters.md), activé par `searchable_fields`. |
| `responsive_table` | Aucun. Le tableau gère nativement le dépassement de contenu. |
| `save_state` | Toujours actif. L'état de la liste (page, tri, filtres, recherche, colonnes visibles) vit désormais dans l'URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (une liste de classes de filtres). |
| `BaseField.render_function_key` | `BaseField.list_template` (template Jinja côté serveur). |

Si vous aviez précédemment écrit des fonctions de rendu JavaScript personnalisées ou des plugins DataTables, portez-les vers des surcharges de `list_template`. Chaque champ rend désormais sa cellule de liste directement depuis `templates/fields/list/*.html`.

### Actions

Les gestionnaires d'actions par lot reçoivent désormais un objet `ActionSelection` au lieu d'une liste de clés primaires. Cela prend en charge la nouvelle bannière « tout sélectionner parmi les résultats correspondants », qui cible chaque ligne correspondant au filtre courant sans les matérialiser côté client.

```python
# Avant
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, pks: List[Any]) -> str:
    for article in await self.find_by_pks(request, pks):
        ...
    return f"{len(pks)} articles were published"


# Après
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, selection: ActionSelection) -> None:
    for article in await selection.rows():
        ...
    flash(request, f"{await selection.count()} articles were published")
```

* Des méthodes comme `selection.rows()`, `selection.pks()` et `selection.count()` résolvent les lignes cibles de manière paresseuse. Cela s'applique aussi bien lorsque l'utilisateur coche des lignes individuellement que lorsqu'il sélectionne toutes les lignes correspondantes.
* Des propriétés comme `selection.is_select_all`, `selection.filters` et `selection.q` vous permettent de pousser l'opération vers le bas sous forme d'une unique requête bulk.
* Le retour d'une chaîne de message de succès est remplacé par les [messages flash](user-guide/flash-messages.md).
* Les gestionnaires d'actions sur ligne conservent leur signature d'origine `(request, pk)`.
* **Nouvelles options de `@action` :** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size`, et des callables `form` par requête.

### Authentification

Le module `starlette_admin/auth.py` est devenu le package `starlette_admin.auth`. Les imports existants depuis `starlette_admin.auth` continueront de fonctionner, mais le contrat du provider a changé.

```python
# Avant
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


# Après
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
* Les méthodes `login` et `logout` ne reçoivent plus ni ne retournent plus la `response` préparée. Retournez `None` pour la redirection par défaut, ou retournez une `Response` personnalisée pour modifier ce comportement.
* `AdminConfig` est supprimé. Gérez les titres et logos par requête à l'aide de la forme callable de `logo_url` et `login_logo_url` sur l'instance d'`Admin`.
* Un [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) intégré prend en charge les flux de connexion OAuth2/OIDC dès l'installation.
* Le décorateur `login_not_required` reste inchangé.

### Export et import

Les exports sont passés des boutons client-side de DataTables à des endpoints de streaming côté serveur. La fonctionnalité d'import est entièrement nouvelle, et `ExportType` n'existe plus.

```python
# Avant
from starlette_admin import ExportType


class PostView(ModelView):
    export_types = [ExportType.CSV, ExportType.EXCEL]
    export_fields = ["id", "title"]


# Après
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["csv", "json"]
    exclude_fields_from_export = ["content"]
    exclude_fields_from_import = ["id"]
```

* `export_types` devient `exporters`. Il accepte une liste de noms de formats ou d'instances de `BaseExporter`. Les built-ins pris en charge incluent `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` et `pdf`. Les formats autres que `csv` ou `json` nécessitent `tablib`, et le PDF nécessite l'extra `pdf`.
* `importers` accepte une liste de noms de formats ou d'instances de `BaseImporter`. Les built-ins pris en charge incluent `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` et `html`. Les formats autres que `csv`, `tsv` ou `json` nécessitent `tablib`.
* `export_fields` (une liste d'inclusion) est remplacé par `exclude_fields_from_export` (une liste d'exclusion). Cela correspond à la convention de nommage des autres attributs `exclude_fields_from_*`.
* Les champs acceptent également `exclude_from_export` et `exclude_from_import` individuellement.
* Configurez les limites globales à l'aide de `ExportConfig` et `ImportConfig` sur l'instance d'`Admin`. Consultez la documentation [Export & Import](user-guide/export-import.md) pour plus de détails.

### Champs personnalisés et surcharge de templates

Les templates de champs ont été réorganisés. Mettez à jour vos chemins si vous surchargez les templates intégrés ou si vous fournissez des champs personnalisés :

| Avant | Après |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (fonction de rendu client-side) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (chemin) | Même nom d'attribut, nouveau préfixe de chemin `fields/form/` |

```python
# Avant
@dataclass
class RatingField(BaseField):
    display_template: str = "displays/rating.html"
    form_template: str = "forms/rating.html"
    render_function_key: str = "rating"


# Après
@dataclass
class RatingField(BaseField):
    detail_template: str = "fields/detail/rating.html"
    form_template: str = "fields/form/rating.html"
    list_template: str = "fields/list/rating.html"
```

Parmi les nouvelles capacités par champ à explorer figurent `validators`, `filters`, `default`, les hooks (`getter`, `formatter`, `parser`), `copy_to_clipboard`, et un dictionnaire `extra` pour des métadonnées arbitraires. Consultez la documentation [Champs personnalisés](advanced/custom-fields.md) pour plus d'informations.

### CustomView

La classe `CustomView` n'accepte plus `template_path` ni `methods`. Construisez des pages simples à l'aide de [widgets](user-guide/custom-views.md). Pour les pages nécessitant un contrôle total, héritez de `CustomView` et déclarez vos routes directement.

```python
# Avant
admin.add_view(CustomView(label="Home", path="/home", template_path="home.html"))

# Après : page basée sur des widgets
admin.add_view(
    CustomView(
        menu_label="System Status",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)


# Après : contrôle total
class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(request=request, name="home.html")
```

Le décorateur `@route` permet également à n'importe quelle vue d'exposer des endpoints supplémentaires pour des besoins tels que des données JSON pour graphiques ou des webhooks.

### Backends personnalisés

Si vous avez implémenté `BaseModelView` pour une source de données personnalisée, notez le contrat d'accès aux données mis à jour :

```python
# Avant
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...


# Après
async def find_all(
    self, request, skip=0, limit=100, q=None, sorts=None, filters=None
): ...
async def count(self, request, q=None, filters=None): ...
```

* Le paramètre `where` de type chaîne est scindé en `q` (pour les termes de recherche plein texte) et `filters` (un arbre typé `FilterGroup` fourni par le constructeur de filtres).
* Le paramètre `order_by` (auparavant une liste de chaînes `"field direction"`) devient `sorts`, qui prend une liste de tuples `(field_name, direction)`.
* Chaque backend embarque désormais un registre de filtres associant les types de champs à leurs implémentations de filtres. Consultez la documentation [Backend personnalisé](integrations/custom-backend.md) pour le contrat complet et un exemple fonctionnel.

### Changements de comportement à examiner

* **Fuseaux horaires :** Les datetimes sont rendus par défaut dans le fuseau horaire local du visiteur (voir la remarque sur `timezone_config` dans la section Le constructeur Admin).
* **État dans l'URL :** L'état de la liste vit désormais dans l'URL. Les URL d'administration mises en favori depuis des versions antérieures afficheront un état de liste par défaut, car les états DataTables enregistrés ne sont pas migrés.
* **Validation des e-mails :** `EmailField` valide désormais côté serveur lorsque `email-validator` est installé.
* **Protection CSRF :** La protection CSRF est intégrée et basée sur les cookies. Si vous enveloppiez précédemment l'admin avec un middleware CSRF personnalisé, vous pouvez le retirer sans risque. Assurez-vous que votre `secret_key` est défini afin que les tokens survivent aux redémarrages du serveur.
* **Taille d'upload de FileField :** `FileField.max_size` vaut désormais 50 Mo par défaut au lieu d'être illimité. Passez `max_size=None` pour restaurer l'ancien comportement sans limite, ou définissez une valeur explicite pour modifier le plafond.

### Éléments supprimés sans remplacement

* `AdminConfig` (voir [Authentification](#authentification)).
* `datatables_options`, `responsive_table` et `save_state` (voir [Suppression de DataTables](#suppression-de-datatables)).
* Le backend Odmantic (voir [Prérequis](#prérequis)).

## Obtenir de l'aide

Si vous rencontrez un problème de migration non couvert par ce guide, veuillez [ouvrir une issue](https://github.com/jowilf/starlette-admin/issues). Joignez une reproduction minimale du problème et précisez la version depuis laquelle vous effectuez la mise à niveau. Exécuter avec [`Admin(debug=True)`](user-guide/admin.md#debugging) révèle souvent directement la cause, et les logs obtenus constituent un excellent complément à votre rapport.

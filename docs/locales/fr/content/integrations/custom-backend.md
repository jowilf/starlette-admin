---
title: Intégration d'un backend personnalisé
description: Découvrez comment construire un adaptateur de backend personnalisé pour
  starlette-admin afin de connecter votre propre ORM ou votre propre magasin de données
  API à l'interface d'administration.
source_hash: 1e6a2e4cecb72a0dcb27f5f1988cd060ce3e1085b9261aec475fb4ed3bf33b8a
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

# Backends personnalisés

`starlette-admin` fournit des backends intégrés pour SQLAlchemy, SQLModel, Beanie, MongoEngine et Tortoise ORM, mais le panneau d'administration est totalement indépendant du stockage. Chaque backend est simplement une sous-classe de `BaseModelView`. Cette classe traduit les opérations CRUD standard en commandes que votre source de données spécifique comprend. Que vous utilisiez une API REST, Redis, une base de données ancienne sans ORM ou un magasin de documents léger comme TinyDB, le processus d'implémentation reste identique.

## Méthodes requises

`BaseModelView` vous demande d'implémenter six méthodes abstraites. En fournissant ces six méthodes, vous héritez automatiquement de l'ensemble complet des fonctionnalités du panneau d'administration : listage, recherche, tri, filtrage, pagination, création, modification, importation, exportation et suppression.

```python
from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
from starlette_admin.filters import FilterGroup
from starlette_admin.views import BaseModelView


class MyBackendView(BaseModelView):
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        ...

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        ...

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        ...

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        ...

    async def create(self, request: Request, data: dict) -> Any:
        ...

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        ...

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        ...

```

| Méthode | Appelée pour | Renvoie |
| --- | --- | --- |
| **`find_all`** | Page de liste, exportation | Une page d'enregistrements correspondant à `q`, `sorts` et `filters` |
| **`count`** | Pagination de la page de liste, vérification de la limite d'exportation | Le nombre total d'enregistrements correspondant à `q` et `filters` |
| **`find_by_pk`** | Détail, modification, suppression unique, actions de ligne | Un seul enregistrement, ou `None` s'il n'est pas trouvé |
| **`find_by_pks`** | Actions groupées, suppression groupée, exportation de la sélection | Une séquence d'enregistrements correspondant aux clés primaires fournies |
| **`create`** | Soumission du formulaire de création, importation | L'enregistrement nouvellement créé |
| **`edit`** | Soumission du formulaire de modification | L'enregistrement mis à jour |
| **`delete`** | Suppression groupée, suppression de ligne | Le nombre d'enregistrements supprimés, ou `None` |

Le panneau d'administration gère en interne l'analyse de la chaîne de requête de la requête (comme `?page=2&sort=views__desc&q=fire`). Vous n'aurez jamais besoin d'analyser des paramètres de requête bruts. Au moment où `find_all` ou `count` est appelé, le panneau d'administration a déjà traité les entrées :

* **La pagination** est convertie en `skip` et `limit` (`skip = (page - 1) * page_size`).
* **La recherche** est fournie sous forme de chaîne simple `q`.
* **Le tri** est formaté sous forme de liste priorisée de tuples `(field_name, direction)`.
* **Les filtres** sont analysés dans un arbre structuré `FilterGroup`.

Votre seule tâche consiste à traduire ces arguments structurés dans le langage de requête natif de votre backend.

## Clé de vue, nom d'affichage et champs

Avant le rendu, une vue `ModelView` nécessite quatre attributs essentiels pour comprendre la structure des données et le routage :

| Attribut | Objectif |
| --- | --- |
| **`key`** | Slug d'URL unique (par exemple `/admin/post/list`) et clé interne pour les abonnements aux événements. |
| **`display_name`** / **`menu_label`** | Noms d'affichage pour l'interface utilisateur. `display_name` est au singulier pour les titres de formulaires, tandis que `menu_label` est au pluriel pour la navigation et les pages de liste. |
| **`pk_attr`** | Le nom de champ spécifique qui identifie un enregistrement de manière unique. |
| **`fields`** | Une liste d'instances de `BaseField` définissant les colonnes à afficher et à modifier. |

Les backends intégrés renseignent ces attributs automatiquement par introspection de vos modèles. Par exemple, la vue `ModelView` de SQLAlchemy lit les colonnes et la clé primaire du mapper. Cette introspection est gérée par une sous-classe de `BaseModelConverter`. Ces convertisseurs utilisent des décorateurs `@converts(...)` pour associer les types de colonnes natifs à leurs équivalents `BaseField` correspondants.

Lorsque vous construisez un backend sans modèle introspectable, comme une API REST ou un simple magasin de dictionnaires, vous devez définir explicitement ces quatre attributs comme attributs de classe :

```python
class PostView(BaseModelView):
    key = "post"
    display_name = "Post"
    menu_label = "Blog Posts"
    pk_attr = "id"
    fields = [
        IntegerField("id", filters=[]),
        StringField("title"),
        TextAreaField("body"),
        IntegerField("views"),
    ]

```

Lister explicitement les champs est l'approche la plus simple pour des vues ponctuelles. Toutefois, si vous construisez une classe de base `ModelView` réutilisable conçue pour plusieurs modèles sur un backend personnalisé, vous devriez plutôt écrire un `BaseModelConverter` personnalisé. Implémentez les méthodes `convert()` et `convert_fields_list()`, décorez vos gestionnaires de types avec `@converts(...)` et appelez le convertisseur lors de l'initialisation. Ainsi, les vues concrètes héritent automatiquement des définitions de champs, ce qui correspond au comportement des backends intégrés.

## Traiter les arbres de filtres

Les filtres sont transmis à vos méthodes sous forme d'un `FilterGroup`. Cette structure est un arbre de nœuds logiques AND/OR contenant des objets feuilles `FilterRule` :

```python
@dataclass
class FilterRule:
    field: str
    filter: str         # The slug of the BaseFilter to apply (e.g., "contains", "gte")
    value: Any = None
    value2: Any = None  # Only populated for filters with has_value2 (e.g., "between")

@dataclass
class FilterGroup:
    logic: str = "and"  # Accepts "and" or "or"
    rules: list["FilterGroup | FilterRule"] = field(default_factory=list)

```

Pour convertir cet arbre en requête de base de données, vous devez le parcourir récursivement. Pour chaque `FilterRule`, récupérez la classe de filtre concrète correspondante depuis votre `FilterRegistry` et appelez sa méthode `apply()`. Pour les nœuds `FilterGroup` imbriqués, procédez récursivement et combinez les fragments obtenus à l'aide de l'opérateur logique approprié.

Voici le motif `build_query` utilisé par l'exemple de référence TinyDB :

```python
def build_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    fragments = []
    for rule in group.rules:
        if isinstance(rule, FilterGroup):
            fragment = build_query(rule, fields_by_name, registry)
        else:
            fragment = _build_rule_fragment(rule, fields_by_name, registry)
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None

    combined = fragments[0]
    for fragment in fragments[1:]:
        combined = (combined | fragment) if group.logic == "or" else (combined & fragment)
    return combined


def _build_rule_fragment(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None
    ctx = FilterApplyContext(
        query=None, field_name=rule.field, value=rule.value, value2=rule.value2
    )
    return filter_cls().apply(ctx)

```

La méthode `apply(ctx)` de chaque filtre concret reçoit un objet `FilterApplyContext` contenant la `query`, le nom du champ et les valeurs. Elle renvoie un fragment de requête spécifique au langage de votre backend. Comme ce processus évite de modifier un état partagé, vous pouvez combiner proprement les règles obtenues quelle que soit l'architecture de votre base de données sous-jacente.

## L'exemple de référence TinyDB

[`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) contient un panneau d'administration entièrement exécutable reposant sur [TinyDB](https://github.com/msiemens/tinydb). TinyDB est un magasin de documents qui enregistre les données dans un fichier JSON local. Il constitue un excellent point de référence car il ne dispose pas d'ORM, ce qui signifie que chaque méthode interagit directement avec le magasin de données.

### Définition du modèle (`models.py`)

Le modèle de données est une dataclass Python standard sans aucune logique spécifique à l'administration :

```python
@dataclass
class Post:
    title: str
    body: str
    tags: list[str]
    views: int = 0
    comments: list[Comment] = field(default_factory=list)
    cover: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "id"}

    @classmethod
    def from_document(cls, doc: Document) -> "Post":
        return cls(**doc, id=doc.doc_id)

    @classmethod
    def search_query(cls, term: str):
        q = Query()
        return (
            q.title.search(term, flags=re.IGNORECASE)
            | q.body.search(term, flags=re.IGNORECASE)
            | q.tags.test(lambda tags: any(re.match(term, tag, re.IGNORECASE) for tag in tags))
        )

```

La méthode `search_query` traite le paramètre `q` en générant une recherche plein texte sur les champs pertinents.

### Implémentation de la vue (`view.py`)

L'implémentation de `PostView` utilise `_build_query` pour fusionner la requête de recherche avec l'arbre de filtres. `find_all` et `count` s'appuient tous deux sur cette fonction utilitaire avant d'exécuter la recherche TinyDB :

```python
async def _build_query(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> QueryInstance | None:
    query = None
    if q is not None:
        query = Post.search_query(q)
    if filters is not None and not filters.is_empty():
        fields_by_name = {field.name: field for field in self.get_fields_list(request)}
        filter_query = build_query(filters, fields_by_name, self.get_filter_registry())
        if filter_query is not None:
            query = filter_query if query is None else (query & filter_query)
    return query

async def find_all(
    self,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    sorts: list[tuple[str, str]] | None = None,
    filters: FilterGroup | None = None,
) -> Sequence[Any]:
    query = await self._build_query(request, q, filters)
    docs = self.db.search(query) if query is not None else self.db.all()
    values = [Post.from_document(doc) for doc in docs]
    for sort_by, sort_dir in reversed(sorts or []):
        values.sort(
            key=lambda v, s=sort_by: (getattr(v, s) is None, getattr(v, s)),
            reverse=(sort_dir == "desc"),
        )
    if limit > 0:
        return values[skip : skip + limit]
    return values[skip:]

async def count(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> int:
    query = await self._build_query(request, q, filters)
    return len(self.db.search(query)) if query is not None else len(self.db.all())

```

Comme TinyDB ne dispose pas de capacités de tri natives, la logique de tri s'exécute en Python. Appliquer les tris dans l'ordre inverse produit un tri multi-clés fiable.

Les opérations d'écriture (`create`, `edit`, `delete`) modifient directement la base de données. Point essentiel : elles déclenchent également les hooks d'événements de la vue, garantissant que les événements du cycle de vie se produisent correctement :

```python
async def create(self, request: Request, data: dict) -> Any:
    await self.validate_data(data)
    obj = Post(**data)
    await self._emit_before_create(request, data, obj)
    new_id = self.db.insert(obj.to_dict())
    obj = await self.find_by_pk(request, new_id)
    await self._emit_after_create(request, obj)
    return obj

async def delete(self, request: Request, pks: list[Any]) -> int | None:
    ids = list(map(int, pks))
    objs = [Post.from_document(self.db.get(doc_id=i)) for i in ids if self.db.contains(doc_id=i)]
    for obj in objs:
        await self._emit_before_delete(request, await self.get_pk_value(request, obj), obj)
    removed = self.db.remove(doc_ids=ids)
    for obj in objs:
        await self._emit_after_delete(request, await self.get_pk_value(request, obj), obj)
    return len(removed)

```

### Câblage de l'application (`app.py`)

Vous n'avez pas besoin d'une sous-classe `Admin` spécialisée. La classe `Admin` de base fonctionne universellement car `BaseModelView` fait abstraction de tous les détails du backend :

```python
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette_admin import BaseAdmin as Admin
from tinydb import TinyDB
from view import PostView

db = TinyDB(Path(__file__).parent / "db.json")

app = Starlette()
admin = Admin(debug=True, secret_key="123456")
admin.add_view(PostView(db))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

Pour tester cette implémentation, exécutez `uv run app.py` depuis le répertoire de l'exemple puis accédez à `http://localhost:8000/admin/`.

## Filtres de champ personnalisés

Les filtres sont étroitement liés à la syntaxe de votre backend spécifique. Une opération « contains » nécessite un code entièrement différent dans TinyDB, SQL et MongoDB. Chaque backend personnalisé doit enregistrer ses propres sous-classes de `BaseFilter` dans un `FilterRegistry` et les renvoyer via `get_filter_registry()`.

Pour créer un filtre, créez une sous-classe d'un type de base tel que `EqualFilter` ou `ContainsFilter` et implémentez la méthode `apply` :

```python
import re

from starlette_admin.filters import FilterApplyContext
from starlette_admin.filters.string import ContainsFilter
from tinydb import Query
from tinydb.queries import QueryInstance


class TinyDBContainsFilter(ContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return Query()[ctx.field_name].search(re.escape(ctx.value), flags=re.IGNORECASE)

```

La bonne pratique pour construire le registre consiste à créer une sous-classe de `FilterRegistry` et à décorer les méthodes propres à chaque type de champ avec `@filters(...)`. C'est exactement le motif utilisé par les backends fournis :

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.fields import BaseField
from starlette_admin.filters import FilterRegistry, filters
from starlette_admin.filters.generic import IsNotNullFilter, IsNullFilter
from starlette_admin.filters.numeric import EqualFilter, GreaterThanFilter, LessThanFilter


class TinyDBFilterRegistry(FilterRegistry):
    @filters(BaseField)
    def fallback_filters(self, field: BaseField) -> list[type]:
        # Ensures every field is filterable by null-ness, even without specific registrations.
        return [IsNullFilter, IsNotNullFilter]

    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type]:
        return [TinyDBContainsFilter, EqualFilter, IsNullFilter, IsNotNullFilter]

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type]:
        return [EqualFilter, GreaterThanFilter, LessThanFilter, IsNullFilter, IsNotNullFilter]


class PostView(BaseModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return TinyDBFilterRegistry()

```

Si un champ n'a pas d'entrée correspondante dans le registre et ne comporte pas de surcharge explicite `filters=[]`, il ne sera pas filtrable. L'exemple TinyDB laisse volontairement le champ `id` non filtrable grâce à la technique de surcharge `filters=[]`.

Pour les schémas dynamiques où les types filtrables ne sont connus qu'à l'exécution, `FilterRegistry` fournit une méthode impérative `register(field_type, *filter_classes)`.

## Gérer les événements du cycle de vie

Votre backend personnalisé possède intégralement les méthodes `create`, `edit` et `delete`. Comme la classe `BaseModelView` n'accède jamais directement à votre source de données, vous devez la notifier explicitement lorsqu'une écriture se produit. À défaut, deux systèmes fondamentaux cessent de fonctionner silencieusement :

1. **Hooks de méthode :** les surcharges `before_create` et `after_create` de votre `ModelView`.
2. **Abonnés aux événements :** les gestionnaires enregistrés sur `view.events` ou `admin.events`.

La notification s'effectue en appelant des paires de méthodes utilitaires définies sur `BaseModelView`. Chaque méthode utilitaire invoque le hook de méthode correspondant et émet un `AdminEvent`.

| Méthode | Méthode utilitaire avant écriture | Méthode utilitaire après écriture |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

L'appel avant écriture accepte l'objet en mémoire construit à partir des données soumises. Il offre aux gestionnaires une dernière possibilité de rejeter l'écriture en levant une exception. L'appel après écriture exige l'objet persisté tel qu'il a été relu depuis la base de données. Cela explique pourquoi la méthode `create` de TinyDB recharge l'enregistrement au lieu de renvoyer l'objet initial en mémoire.

Deux méthodes utilitaires supplémentaires, `_emit_after_create_committed` et `_emit_after_edit_committed`, prennent en charge les backends avec validations en deux phases ou sémantique de session. Ignorez-les complètement, sauf si votre base de données impose une limite stricte de transaction.

Les opérations d'exportation et d'importation ne nécessitent aucun câblage manuel des événements. La classe `BaseAdmin` gère ces événements du cycle de vie automatiquement.

---

### Ressources supplémentaires

* **[Vues](../user-guide/views.md)** : explorez les options de configuration de `BaseModelView` indépendamment du backend.
* **[Filtres personnalisés](../advanced/custom-filters.md)** : apprenez à écrire et à enregistrer des filtres personnalisés à partir de zéro.
* **[Événements](../advanced/events.md)** : comprenez l'API complète d'abonnement aux événements, y compris les hooks de méthode, le bus d'événements et les priorités d'exécution.

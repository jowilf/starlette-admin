---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
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

# Suppression logique et vue Corbeille avec FastAPI & starlette-admin

_2026-07-10_

Une opération `DELETE` standard est sans pitié. Si un opérateur clique par erreur ou si une tâche de nettoyage automatisée s'exécute avec le mauvais filtre, les données sont perdues, sauf à effectuer une restauration complexe de la base de données. La mise en œuvre d'une « suppression logique » (*soft delete*) atténue ce risque en marquant un enregistrement comme supprimé au lieu de le retirer définitivement de la base de données. Cette approche transforme la récupération des données en une simple opération de mise à jour.

Ce guide montre comment mettre en œuvre le pattern de suppression logique dans une application FastAPI à l'aide de `starlette-admin`. Nous allons construire une solution complète utilisant :

- Un seul modèle de base de données
- Deux vues d'administration distinctes
- Un horodatage `deleted_at`
- Une interface Corbeille dédiée pour restaurer ou purger définitivement des enregistrements

**Consultez le code complet exécutable :** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## Le modèle

Ajoutez une colonne d'horodatage nullable à la table que vous souhaitez protéger. Une valeur `NULL` indique un enregistrement actif, tandis qu'un horodatage renseigné indique un enregistrement supprimé :

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Cette approche ne nécessite ni table corbeille séparée ni bibliothèque externe de mixin de suppression logique. Une seule colonne gère l'ensemble de la machine à états.

## Masquer les lignes supprimées dans la vue active

La classe `ModelView` construit ses requêtes de liste, de comptage et de détail à partir de méthodes redéfinissables. `get_detail_query` utilise `get_list_query` par défaut : filtrer la requête de liste filtre donc aussi la page de détail, y compris les URL directes. `get_count_query` est indépendante et doit être filtrée séparément. En filtrant ces requêtes pour n'inclure que les enregistrements où `deleted_at IS NULL`, vous pouvez masquer efficacement les lignes supprimées logiquement de la page de liste, des totaux de pagination et des liens directs vers la page de détail :

```python title="app.py" hl_lines="7-8 10-11"
class PostView(ModelView):
    exclude_fields_from_list = ["deleted_at"]
    exclude_fields_from_create = ["deleted_at", "created_at"]
    exclude_fields_from_edit = ["deleted_at", "created_at"]
    fields_default_sort = [("created_at", True)]

    def get_list_query(self, request: Request):
        return super().get_list_query(request).where(Post.deleted_at.is_(None))

    def get_count_query(self, request: Request):
        return super().get_count_query(request).where(Post.deleted_at.is_(None))
```

Vous devez également exclure `deleted_at` des formulaires de création et d'édition. Les opérateurs ne doivent jamais définir ce champ manuellement ; il ne doit être modifié que programmatiquement par la méthode `delete()` et l'action de restauration.

!!! warning
L'absence de `get_count_query` crée une fuite de visibilité des données : les totaux de pagination et de résultats de recherche incluront les lignes supprimées même si elles ne s'affichent pas dans la liste. `get_detail_query` n'a pas besoin d'une redéfinition distincte ici, puisqu'elle utilise `get_list_query` par défaut et hérite automatiquement du même filtre. Si vous donnez à une vue une `get_detail_query` personnalisée, elle cesse d'hériter de `get_list_query` et doit filtrer elle-même sur `deleted_at`.

## Redéfinir la suppression

L'action groupée intégrée ainsi que le bouton de suppression au niveau de la ligne invoquent tous deux `ModelView.delete()`. Redéfinir cette méthode modifie globalement le comportement de suppression pour tous les points d'entrée, sans configuration supplémentaire :

```python title="app.py" hl_lines="6-7 11"
async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()
    for obj in objs:
        await self._emit_after_delete(request, obj.id, obj)
    return len(objs)
```

Les appels à `_emit_before_delete` et `_emit_after_delete` garantissent que le [bus d'événements](../../advanced/events.md) se déclenche exactement comme il le ferait pour une suppression physique. Ainsi, un abonné à `AdminEvent.AFTER_DELETE` (tel qu'un journal d'audit ou un webhook) n'a pas besoin de savoir que la suppression était logique. L'impact change au niveau de la ligne de base de données, mais les événements du cycle de vie restent cohérents.

### AFTER_DELETE_COMMITTED nécessite son propre câblage

Les événements `BEFORE_DELETE` et `AFTER_DELETE` ne représentent pas l'intégralité du cycle de vie. La méthode `ModelView.delete()` de base de SQLAlchemy enregistre également un callback `on_commit`. Ce callback déclenche l'événement `AFTER_DELETE_COMMITTED` une fois que la transaction a été validée avec succès, permettant aux abonnés de considérer en toute sécurité que la ligne a été durablement supprimée.

Comme l'exemple `PostView` redéfinit complètement `delete()`, l'enregistrement par défaut du callback `on_commit` est contourné. Par conséquent, un gestionnaire écoutant `AdminEvent.AFTER_DELETE_COMMITTED` sur une vue à suppression logique ne se déclenchera pas, sans aucune erreur.

Pour restaurer cette fonctionnalité, vous devez enregistrer manuellement le même callback que celui utilisé par l'implémentation de base :

```python title="app.py" hl_lines="16-17 20 22"
from collections.abc import Callable

from starlette_admin.helpers import on_commit


async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()

    def _make_after_delete_committed(obj: Post, pk: Any) -> Callable[[], Any]:
        return lambda: self._emit_after_delete_committed(request, pk, obj)

    for obj in objs:
        pk = obj.id
        await self._emit_after_delete(request, pk, obj)
        on_commit(request, _make_after_delete_committed(obj, pk))
    return len(objs)
```

La fonction utilitaire `_make_after_delete_committed` accepte `obj` et `pk` comme paramètres standards. Elle est appelée une fois par ligne avec les valeurs de cette ligne spécifique. Cette structure est essentielle. Si vous construisiez une lambda directement dans le corps de la boucle, elle capturerait les variables de boucle elles-mêmes plutôt que leurs valeurs à cette itération précise. En conséquence, chaque callback se déclencherait avec les valeurs finales de `obj` et `pk` après la fin de la boucle. Leur passage en arguments à une fonction externe capture leur état exact au moment de l'appel.

Un avantage de la suppression logique s'applique ici. Une suppression physique nécessite de détacher l'objet (`session.expunge`) avant de planifier son callback de validation. Comme une ligne physiquement supprimée a disparu au moment de la validation, accéder à un attribut non chargé lève une `ObjectDeletedError`. Puisqu'une suppression logique ne retire jamais la ligne, l'objet reste attaché et tous ses attributs peuvent être lus en toute sécurité dans le callback.

Cependant, la règle principale de `on_commit` reste valable : le callback ne doit pas écrire dans la base de données via `request.state.session`. Cette session est déjà terminée. Tout ce qui est envoyé (flush) à cette session démarre une nouvelle transaction qui sera abandonnée à la fermeture de la session.

## Une seconde vue pour la même table

La `TrashView` cible le même modèle `Post` mais s'enregistre sous une `key` unique. Cette configuration indique à `starlette-admin` de la traiter comme une ressource distincte, avec une URL et une entrée de menu séparées :

```python title="app.py" hl_lines="8 11"
class TrashView(ModelView):
    menu_label = "Trash"
    icon = "fa fa-trash"
    fields_default_sort = [("deleted_at", True)]
    actions = ["restore", "delete"]

    def get_list_query(self, request: Request):
        return select(Post).where(Post.deleted_at.isnot(None))

    def get_count_query(self, request: Request):
        return select(func.count()).select_from(Post).where(Post.deleted_at.isnot(None))

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False
```

Ces requêtes sont l'exact inverse de celles de `PostView`, filtrant sur `IS NOT NULL` au lieu de `IS NULL`. `get_detail_query` utilise là encore `get_list_query` par défaut : les enregistrements mis à la corbeille sont donc correctement résolus sur leur page de détail sans redéfinition supplémentaire. Les méthodes `can_create` et `can_edit` renvoient `False` car les opérateurs ne doivent jamais créer ni modifier directement des enregistrements dans la corbeille. Les enregistrements n'entrent dans la corbeille que via `PostView.delete()` et n'en sortent que via une action de restauration ou une purge définitive.

## Restaurer, et l'intérêt d'une vraie suppression

La `TrashView` conserve l'action `delete` intégrée dans sa liste `actions` et ne la redéfinit pas. Dans la vue corbeille, l'exécution d'un `delete` effectue un `DELETE` SQL standard. Cela constitue une purge définitive. Une fois qu'une ligne est retirée de la corbeille, elle disparaît totalement.

Restaurer un enregistrement nécessite une petite [action personnalisée](../../user-guide/actions.md) qui efface l'horodatage `deleted_at` :

```python title="app.py" hl_lines="12"
@action(
    name="restore",
    text="Restore",
    confirmation="Restore the selected posts?",
    submit_btn_text="Yes, restore",
    submit_btn_class="btn btn-success",
)
async def restore_action(self, request: Request, pks: list[Any]) -> None:
    session: Session = request.state.session
    objs = await self.find_by_pks(request, pks)
    for obj in objs:
        obj.deleted_at = None
        session.add(obj)
    session.flush()
    count = len(objs)
    flash(request, f"{count} post{'s' if count != 1 else ''} restored.", "success")
```

Définir `deleted_at = None` restaure immédiatement la ligne dans la liste active de `PostView` dès la requête suivante, puisque la vue principale n'interroge que les valeurs `NULL`.

## Connecter les deux vues à la même table

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

Cette configuration établit deux vues d'administration distinctes pour une seule table de base de données. Une seule colonne détermine quelle vue affiche chaque ligne spécifique.

## Les limites de cette approche

- **Contraintes d'unicité :** une contrainte `UNIQUE` sur un champ tel que `slug` empêche les opérateurs de recréer un article actif avec le même slug tant que la version supprimée logiquement demeure dans la corbeille. Pour résoudre ce problème, excluez soit les lignes `deleted_at IS NOT NULL` de l'index unique à l'aide d'un index partiel (si votre moteur de base de données le prend en charge), soit incluez la colonne `deleted_at` dans la contrainte d'unicité elle-même.
- **Clés étrangères :** un `Post` supprimé logiquement reste une ligne valide pour les relations de clé étrangère dans d'autres tables. Les enregistrements enfants continueront de pointer vers lui. Bien que ce soit souvent le comportement souhaité, propager une suppression logique aux lignes liées nécessite une logique personnalisée explicite. La base de données ne gérera pas cela automatiquement comme elle le fait avec `ON DELETE CASCADE` pour les suppressions physiques.
- **Discipline de requête :** chaque nouvelle requête ciblant le modèle `Post` doit inclure explicitement le filtre `deleted_at IS NULL`. Si une requête brute, une tâche d'exportation ou une vue d'administration secondaire omet ce filtre, des données supprimées fuiteront dans les flux de travail actifs.
- **Croissance de la base de données :** les lignes supprimées logiquement continuent de consommer de l'espace dans la table et les index. Si votre application purge la plupart des lignes supprimées logiquement au lieu de les restaurer, envisagez de mettre en place une tâche planifiée en arrière-plan. Cette tâche peut supprimer physiquement les enregistrements plus anciens qu'une fenêtre de rétention donnée afin d'éviter une croissance illimitée de la base de données.

## Étendre à d'autres backends

Les principes fondamentaux de cette approche ne sont pas exclusifs à SQLAlchemy. Vous pouvez la mettre en œuvre sur tout backend permettant de redéfinir les requêtes de liste, de comptage et de détail, ainsi que la méthode `delete()`. Par exemple, si vous utilisez Beanie, MongoEngine ou Tortoise ORM, les redéfinitions équivalentes filtreront la requête sur un champ `deleted_at` exactement de la même manière. La syntaxe spécifique des requêtes change, mais le pattern architectural reste identique.

---

## Pour aller plus loin

- **[Événements](../../advanced/events.md) :** comprenez comment `_emit_before_delete` et `_emit_after_delete` se connectent à des abonnés externes situés hors de la vue.
- **[Actions](../../user-guide/actions.md) :** explorez le décorateur derrière `restore_action`, y compris la mise en œuvre des boîtes de dialogue de confirmation et des utilitaires de messages flash.
- **[Vues](../../user-guide/views.md) :** passez en revue l'ensemble complet des hooks de requête et de permission disponibles dans `ModelView`.

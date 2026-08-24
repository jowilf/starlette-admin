---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/blog/posts/soft-deletes-trash-view/)
<!-- translation-notice:end -->

# Soft Deletes et vue Corbeille avec FastAPI & starlette-admin

_2026-07-10_

Une opération `DELETE` standard est impitoyable. Si un opérateur clique de travers ou si une tâche de nettoyage automatisée s'exécute avec le mauvais filtre, les données sont perdues, à moins d'effectuer une restauration complexe de la base. La mise en œuvre d'un « soft delete » atténue ce risque en marquant un enregistrement comme supprimé au lieu de l'effacer définitivement de la base. Cette approche transforme la récupération des données en une simple opération de mise à jour.

Ce guide montre comment implémenter le motif du soft delete dans une application FastAPI à l'aide de `starlette-admin`. Nous allons construire une solution complète utilisant :

- Un modèle de base de données unique
- Deux vues administratives distinctes
- Un timestamp `deleted_at`
- Une interface Corbeille dédiée pour restaurer ou purger définitivement les enregistrements

**Consultez le code complet exécutable :** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## Le modèle

Ajoutez une colonne timestamp nullable à la table que vous souhaitez protéger. Une valeur `NULL` indique un enregistrement actif, tandis qu'un timestamp renseigné signale un enregistrement supprimé :

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Cette approche ne nécessite ni table corbeille distincte ni bibliothèque externe de mixin de soft delete. Une seule colonne gère toute la machine à états.

## Masquer les lignes supprimées dans la vue active

La classe `ModelView` construit ses requêtes de liste, de comptage et de détail à partir de méthodes redéfinissables. `get_detail_query` utilise par défaut `get_list_query`, donc filtrer la requête de liste filtre également la page de détail, URL directes comprises. `get_count_query` est indépendante et doit être filtrée séparément. En filtrant ces requêtes pour n'inclure que les enregistrements où `deleted_at IS NULL`, vous masquez efficacement les lignes en soft delete de la page de liste, des comptages de pagination et des liens directs vers le détail :

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

Vous devez également exclure `deleted_at` des formulaires de création et d'édition. Les opérateurs ne doivent jamais définir ce champ manuellement ; il ne doit être modifié que programmatiquement, par la méthode `delete()` et l'action de restauration.

!!! warning
L'omission de `get_count_query` crée une fuite de visibilité des données : la pagination et les totaux des résultats de recherche incluront les lignes supprimées même si elles ne s'affichent pas dans la liste. `get_detail_query` n'a pas besoin d'une redéfinition séparée ici, puisqu'elle utilise `get_list_query` par défaut et hérite automatiquement du même filtre. Si vous attribuez toutefois une `get_detail_query` personnalisée à une vue, elle cesse d'hériter de `get_list_query` et doit filtrer elle-même sur `deleted_at`.

## Redéfinir la suppression

L'action de suppression groupée intégrée comme le bouton de suppression au niveau de la ligne invoquent tous deux `ModelView.delete()`. Redéfinir cette méthode change le comportement de suppression globalement, sur tous les points d'entrée, sans configuration supplémentaire :

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

Les appels à `_emit_before_delete` et `_emit_after_delete` garantissent que le [bus d'événements](../../advanced/events.md) se déclenche exactement comme lors d'une suppression physique. Ainsi, un abonné à `AdminEvent.AFTER_DELETE` (un journal d'audit ou un webhook, par exemple) n'a pas besoin de savoir que la suppression était logique. L'impact change au niveau de la ligne en base, mais les événements du cycle de vie restent cohérents.

### AFTER_DELETE_COMMITTED a besoin de son propre câblage

Les événements `BEFORE_DELETE` et `AFTER_DELETE` ne représentent pas l'intégralité du cycle de vie. La méthode `delete()` de base de SQLAlchemy `ModelView` enregistre également un callback `on_commit`. Ce callback déclenche l'événement `AFTER_DELETE_COMMITTED` une fois la transaction validée avec succès, permettant aux abonnés de considérer sans risque que la ligne est durablement effacée.

Comme l'exemple `PostView` redéfinit entièrement `delete()`, l'enregistrement par défaut du `on_commit` est contourné. Par conséquent, un handler à l'écoute de `AdminEvent.AFTER_DELETE_COMMITTED` sur une vue à soft delete ne se déclenchera jamais, silencieusement.

Pour rétablir cette fonctionnalité, vous devez enregistrer manuellement le même callback utilisé par l'implémentation de base :

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

La fonction auxiliaire `_make_after_delete_committed` accepte `obj` et `pk` comme paramètres standards. Elle est appelée une fois par ligne avec les valeurs propres à cette ligne. Cette structure est cruciale. Si vous construisiez directement une lambda dans le corps de la boucle, celle-ci capturerait les variables de boucle elles-mêmes plutôt que leurs valeurs à cette itération précise. En conséquence, chaque callback se déclencherait avec les valeurs finales de `obj` et `pk` après la fin de la boucle. Leur passage en arguments à une fonction externe capture leur état exact au moment de l'appel.

Un avantage du soft delete s'applique ici. Une suppression physique exige de détacher l'objet (`session.expunge`) avant de planifier son callback post-commit. Comme une ligne physiquement supprimée n'existe plus au moment du commit, accéder à un attribut non chargé lève une `ObjectDeletedError`. Puisqu'un soft delete ne retire jamais la ligne, l'objet reste attaché et tous ses attributs peuvent être lus en toute sécurité dans le callback.

Cependant, la règle primordiale de `on_commit` reste valable : le callback ne doit pas écrire dans la base via `request.state.session`. Cette session est déjà terminée. Tout ce qui est flushé dans cette session démarre une nouvelle transaction qui sera abandonnée à la fermeture de la session.

## Une seconde vue pour la même table

La `TrashView` cible le même modèle `Post` mais s'enregistre sous une `key` unique. Cette configuration demande à `starlette-admin` de la traiter comme une ressource distincte, avec sa propre URL et sa propre entrée de menu :

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

Ces requêtes sont l'exact inverse de celles de la `PostView`, filtrant sur `IS NOT NULL` au lieu de `IS NULL`. `get_detail_query` utilise là encore `get_list_query` par défaut, donc les enregistrements mis à la corbeille se résolvent correctement sur leur page de détail sans redéfinition séparée. Les méthodes `can_create` et `can_edit` renvoient `False` car les opérateurs ne doivent jamais créer ni modifier directement des enregistrements dans la corbeille. Les enregistrements n'y entrent que via `PostView.delete()` et n'en sortent que via une action de restauration ou une purge définitive.

## Restaurer, et l'intérêt d'une vraie suppression

La `TrashView` conserve l'action `delete` intégrée dans sa liste `actions` et ne la redéfinit pas. Dans la vue corbeille, l'exécution d'un `delete` effectue un `DELETE` SQL standard. Cela constitue une purge définitive. Une fois une ligne retirée de la corbeille, elle disparaît totalement.

La restauration d'un enregistrement requiert une petite [action personnalisée](../../user-guide/actions.md) qui réinitialise le timestamp `deleted_at` :

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

Définir `deleted_at = None` restaure immédiatement la ligne dans la liste active de la `PostView` dès la requête suivante, puisque la vue principale n'interroge que les valeurs `NULL`.

## Relier les deux vues à la même table

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

Cette configuration établit deux vues administratives distinctes pour une seule table en base. Une unique colonne détermine quelle vue affiche chaque ligne spécifique.

## Les limites de ce motif

- **Contraintes d'unicité :** une contrainte `UNIQUE` sur un champ comme `slug` empêche les opérateurs de recréer un article actif avec le même slug tant que la version en soft delete demeure dans la corbeille. Pour résoudre ce problème, excluez soit les lignes `deleted_at IS NOT NULL` de l'index unique grâce à un index partiel (si votre moteur de base le prend en charge), soit incluez la colonne `deleted_at` directement dans la contrainte d'unicité.
- **Clés étrangères :** un `Post` en soft delete reste une ligne valide pour les relations de clé étrangère des autres tables. Les enregistrements enfants continueront de pointer vers lui. Bien que cela corresponde souvent au comportement souhaité, propager un soft delete aux lignes liées nécessite une logique personnalisée explicite. La base ne le gérera pas automatiquement comme elle le fait avec `ON DELETE CASCADE` pour les suppressions physiques.
- **Discipline des requêtes :** chaque nouvelle requête ciblant le modèle `Post` doit inclure explicitement le filtre `deleted_at IS NULL`. Si une requête brute, un job d'export ou une vue admin secondaire omet ce filtre, les données supprimées fuiteront dans les workflows actifs.
- **Croissance de la base :** les lignes en soft delete continuent de consommer de l'espace table et index. Si votre application purge la plupart des lignes supprimées au lieu de les restaurer, envisagez de mettre en place un job planifié en arrière-plan. Ce job peut supprimer physiquement les enregistrements plus anciens qu'une fenêtre de rétention donnée afin d'éviter une croissance illimitée de la base.

## Étendre à d'autres backends

Les principes fondamentaux de ce motif ne sont pas propres à SQLAlchemy. Vous pouvez appliquer cette approche sur n'importe quel backend permettant de redéfinir les requêtes de liste, de comptage et de détail ainsi que la méthode `delete()`. Par exemple, si vous utilisez Beanie, MongoEngine ou Tortoise ORM, les redéfinitions équivalentes filtreront la requête sur un champ `deleted_at` exactement de la même manière. La syntaxe des requêtes change, mais le motif architectural reste identique.

---

## Pour aller plus loin

- **[Events](../../advanced/events.md) :** comprenez comment `_emit_before_delete` et `_emit_after_delete` se connectent aux abonnés externes hors de la vue.
- **[Actions](../../user-guide/actions.md) :** explorez le décorateur derrière `restore_action`, y compris la mise en œuvre de dialogues de confirmation et des helpers de messages flash.
- **[Views](../../user-guide/views.md) :** passez en revue l'ensemble complet des hooks de requête et de permission disponibles dans `ModelView`.

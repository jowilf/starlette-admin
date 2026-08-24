---
title: Formulaires inline
description: Gérez les modèles liés directement dans les formulaires de création et
  d'édition d'un modèle parent grâce à InlineModelView.
source_hash: 0c7d60efcf81de737f205968caea2030a08bf37d63452dce2d0cc29b93309e22
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/inline-forms/)
<!-- translation-notice:end -->

# Formulaires inline

Les formulaires inline permettent aux utilisateurs de gérer des enregistrements liés directement depuis la page de création ou d'édition d'un modèle parent. Ils conviennent aux modèles enfants qui n'ont de sens qu'à côté de leur parent, comme des commentaires sur un article ou des tâches dans un projet, et vous évitent de construire une vue d'administration séparée pour le modèle enfant.

Consultez [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms) pour une application exécutable couvrant les trois schémas présentés sur cette page : clé étrangère auto-détectée, clé étrangère explicite et clé étrangère composite.

## Un inline minimal

```python hl_lines="40-43"
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.requests import Request
from starlette_admin.contrib.sqla import InlineModelView, ModelView


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="article", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, ForeignKey("articles.id"))
    author: Mapped[str] = mapped_column(String(100), default="Anonymous")
    body: Mapped[str] = mapped_column(Text)

    article: Mapped["Article"] = relationship("Article", back_populates="comments")

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.author}: {self.body[:50]}"


class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1


class ArticleView(ModelView):
    fields = ["title", "body"]
    inlines = [CommentInline]
```

Sa mise en place se fait en deux étapes : définir une sous-classe d'`InlineModelView` pour le modèle enfant, puis l'ajouter à la liste `inlines` du `ModelView` du parent.

Les pages de création et d'édition d'`ArticleView` affichent désormais un formset `Comments` sous les champs propres à l'article. Le formset démarre avec une ligne vide (`extra = 1`) et inclut les contrôles d'ajout et de suppression que le backend SQLAlchemy met en place pour vous.

Notez que `CommentInline` ne définit jamais `fk_attr`. Le backend SQLAlchemy inspecte `Article.comments` et déduit que `Comment.article_id` est la clé étrangère, car il s'agit de la seule relation pointant vers `Comment`. Définissez `fk_attr` vous-même uniquement lorsque cette inférence est ambiguë, ou lorsque la relation n'est pas déclarée sur le modèle ORM. Voir [Clés étrangères explicites et composites](#clés-étrangères-explicites-et-composites).

## Référence d'`InlineModelView`

| Attribut | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `model` | Classe de modèle ORM | `None` | Le modèle lié que cet inline gère. Requis. |
| `fk_attr` | `str | tuple[str, ...]` | `""` | Nom du champ de clé étrangère sur le modèle inline qui pointe vers le parent. Un tuple déclare une clé étrangère composite. Optionnel sur le backend SQLAlchemy, qui l'auto-détecte à partir de la relation du parent lorsque vous l'omettez. |
| `extra` | `int` | `0` | Nombre de lignes vides affichées sur les formulaires de création et d'édition, en plus des lignes existantes. |
| `allow_delete` | `bool` | `True` | Afficher une case à cocher ou un bouton de suppression sur chaque ligne existante. |
| `inline_template` | `str` | `"inline.html"` | Template utilisé pour rendre le formset. |
| `collapsible` | `bool` | `True` | Indique si les peuvent réduire et étendre le formset. |
| `collapsed` | `bool` | `False` | État initial réduit. Ne s'applique que lorsque `collapsible=True`. |


Le constructeur lève une `ValueError` lorsque vous laissez `fk_attr` vide et que le backend ne peut pas résoudre la relation sans ambiguïté.

## Formsets réductibles

Par défaut (`collapsible = True`), chaque `InlineModelView` rend son formset avec un en-tête sur lequel les peuvent cliquer pour replier les enregistrements enfants dont ils n'ont pas besoin. Définissez `collapsed = True` pour que le formset démarre fermé plutôt qu'ouvert :

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

Définissez `collapsible = False` pour exclure complètement un formset de ce comportement : il sera alors toujours rendu étendu, sans bouton de basculement :

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## Clés étrangères explicites et composites {#clés-étrangères-explicites-et-composites}

Définissez `fk_attr` vous-même lorsque le parent possède plusieurs relations vers le même modèle enfant, lorsque la relation n'est pas déclarée sur le modèle ORM, ou lorsque la clé étrangère est composite :

```python hl_lines="40-44 89-92"
from sqlalchemy import ForeignKey, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.requests import Request
from starlette_admin import StringField
from starlette_admin.contrib.sqla import InlineModelView, ModelView


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))

    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(default=False)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


class TaskInline(InlineModelView):
    model = Task
    fk_attr = "project_id"
    fields = ["title", "done"]
    extra = 2


class ProjectView(ModelView):
    fields = [StringField("name")]
    inlines = [TaskInline]


class Order(Base):
    __tablename__ = "orders"

    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer: Mapped[str] = mapped_column(String(100))

    lines: Mapped[list["OrderLine"]] = relationship(
        "OrderLine", back_populates="order", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"Order #{self.store_id}-{self.seq} ({self.customer})"


class OrderLine(Base):
    __tablename__ = "order_lines"

    order_store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    product: Mapped[str] = mapped_column(String(100))
    qty: Mapped[int] = mapped_column(Integer, default=1)

    order: Mapped["Order"] = relationship("Order", back_populates="lines")

    __table_args__ = (
        ForeignKeyConstraint(
            ["order_store_id", "order_seq"],
            ["orders.store_id", "orders.seq"],
        ),
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"Line {self.line_no}: {self.product} x {self.qty}"


class OrderLineInline(InlineModelView):
    model = OrderLine
    fields = ["line_no", "product", "qty"]
    extra = 1


class OrderView(ModelView):
    fields = ["store_id", "seq", "customer"]
    inlines = [OrderLineInline]
```

Notez que `OrderLineInline` n'a pas besoin de `fk_attr`, bien que la clé primaire de `OrderLine` soit composite (`order_store_id`, `order_seq`, `line_no`). Le backend SQLAlchemy résout la clé étrangère composite à partir de la `ForeignKeyConstraint` entre `Order` et `OrderLine` et renseigne les deux colonnes sur les nouvelles lignes. Passez un `tuple[str, ...]` à `fk_attr` uniquement lorsque l'introspection des contraintes ne trouve aucune correspondance.

## Validation

Chaque ligne soumise est validée individuellement, via les mêmes chemins `create` et `edit` qu'utilise un `ModelView` autonome. L'administration enregistre d'abord le parent, puis traite chaque ligne inline tour à tour. Une erreur de saisie dans le champ `author` d'un commentaire n'empêche pas le traitement des autres commentaires. Lorsqu'une ligne échoue à la validation, ses erreurs sont rattachées à cette ligne, et le formulaire rend à nouveau la ligne sur place avec les valeurs soumises afin que les puissent corriger et resoumettre cette entrée.

!!! important
    Sur le backend SQLAlchemy, toute la requête est traitée selon le principe du tout ou rien. Le parent et toutes les lignes inline partagent la même session limitée à la requête, et cette session n'est validée (commit) que si l'intégralité de la requête aboutit. Si une ligne échoue à la validation, la réponse renvoie une erreur et la session est annulée (rollback), de sorte que le parent et toutes les lignes inline reviennent ensemble à leur état initial, y compris celles qui avaient passé la validation. Considérez les erreurs par ligne affichées dans l'interface comme une liste de points à corriger, et non comme un relevé de ce qui a été enregistré.

---

## Et ensuite

* **[SQLAlchemy](../integrations/sqlalchemy.md):** Comment l'introspection des relations permet la détection automatique des clés étrangères.
* **[Custom Views](custom-views.md):** Construisez des pages au-delà du flux de travail standard création, édition et liste.
* **[Events](../advanced/events.md):** Réagissez aux modifications inline après l'enregistrement des données.

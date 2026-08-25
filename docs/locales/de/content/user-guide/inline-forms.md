---
title: Inline-Formulare
description: Verwalten Sie zugehörige Modelle inline direkt innerhalb der Create-
  und Edit-Formulare eines übergeordneten Modells mithilfe von InlineModelView.
source_hash: 0c7d60efcf81de737f205968caea2030a08bf37d63452dce2d0cc29b93309e22
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/inline-forms/)
<!-- translation-notice:end -->

# Inline-Formulare

Inline-Formulare ermöglichen es Benutzern, zugehörige Datensätze direkt auf der Create- oder Edit-Seite eines übergeordneten Modells zu verwalten. Sie eignen sich für untergeordnete Modelle, die nur in Verbindung mit ihrem übergeordneten Modell sinnvoll sind – etwa Kommentare zu einem Artikel oder Aufgaben in einem Projekt – und ersparen Ihnen den Aufbau einer separaten Admin-Ansicht für das untergeordnete Modell.

Unter [examples/06-inline-forms](https://github.com/jowilf/starlette-admin/tree/main/examples/06-inline-forms) finden Sie eine lauffähige App, die alle drei Muster dieser Seite abdeckt: automatisch erkannter Fremdschlüssel, expliziter Fremdschlüssel und zusammengesetzter Fremdschlüssel.

## Ein minimales Inline

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

Die Einrichtung erfolgt in zwei Schritten: Definieren Sie eine `InlineModelView`-Unterklasse für das untergeordnete Modell und fügen Sie diese anschließend zur `inlines`-Liste des `ModelView` des übergeordneten Modells hinzu.

Auf den Create- und Edit-Seiten von `ArticleView` wird nun ein `Comments`-Formset unterhalb der eigenen Felder des Artikels gerendert. Das Formset beginnt mit einer leeren Zeile (`extra = 1`) und enthält die Steuerelemente zum Hinzufügen und Löschen, die das SQLAlchemy-Backend für Sie verdrahtet.

Beachten Sie, dass `CommentInline` niemals `fk_attr` setzt. Das SQLAlchemy-Backend untersucht `Article.comments` und leitet `Comment.article_id` als Fremdschlüssel ab, da es die einzige Beziehung ist, die auf `Comment` zeigt. Setzen Sie `fk_attr` selbst nur dann, wenn diese Ableitung nicht eindeutig möglich ist oder wenn die Beziehung nicht im ORM-Modell deklariert ist. Siehe [Explizite und zusammengesetzte Fremdschlüssel](#explizite-und-zusammengesetzte-fremdschluessel).

## `InlineModelView`-Referenz

| Attribut | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `model` | ORM-Modellklasse | `None` | Das zugehörige Modell, das dieses Inline verwaltet. Erforderlich. |
| `fk_attr` | `str | tuple[str, ...]` | `""` | Name des Fremdschlüsselfelds im Inline-Modell, das auf das übergeordnete Modell zeigt. Ein Tupel deklariert einen zusammengesetzten Fremdschlüssel. Im SQLAlchemy-Backend optional; dieses erkennt ihn automatisch aus der Beziehung des übergeordneten Modells, wenn Sie ihn weglassen. |
| `extra` | `int` | `0` | Anzahl leerer Zeilen, die zusätzlich zu bestehenden Zeilen auf Create- und Edit-Formularen angezeigt werden. |
| `allow_delete` | `bool` | `True` | Zeigt eine Löschen-Checkbox bzw. einen Löschen-Button in jeder bestehenden Zeile an. |
| `inline_template` | `str` | `"inline.html"` | Template, das zum Rendern des Formsets verwendet wird. |
| `collapsible` | `bool` | `True` | Gibt an, ob Benutzer das Formset ein- und ausklappen können. |
| `collapsed` | `bool` | `False` | Anfangszustand des Einklappens. Wirkt nur bei `collapsible=True`. |


Der Konstruktor löst einen `ValueError` aus, wenn Sie `fk_attr` leer lassen und das Backend die Beziehung nicht eindeutig auflösen kann.

## Ausklappbare Formsets

Standardmäßig (`collapsible = True`) rendert jedes `InlineModelView` sein Formset mit einem Header, den Benutzer auswählen können, um nicht benötigte untergeordnete Datensätze einzuklappen. Setzen Sie `collapsed = True`, um das Formset zunächst geschlossen statt geöffnet anzuzeigen:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsed = True
```

Setzen Sie `collapsible = False`, um ein Formset vollständig vom Ausklappen auszuschließen; es wird dann immer ausgeklappt ohne Umschalter gerendert:

```python
class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1
    collapsible = False
```

## Explizite und zusammengesetzte Fremdschlüssel {#explizite-und-zusammengesetzte-fremdschluessel}

Setzen Sie `fk_attr` selbst, wenn das übergeordnete Modell mehr als eine Beziehung zum selben untergeordneten Modell hat, wenn die Beziehung nicht im ORM-Modell deklariert ist oder wenn der Fremdschlüssel zusammengesetzt ist:

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

Beachten Sie, dass `OrderLineInline` kein `fk_attr` benötigt, obwohl der Primärschlüssel von `OrderLine` zusammengesetzt ist (`order_store_id`, `order_seq`, `line_no`). Das SQLAlchemy-Backend löst den zusammengesetzten Fremdschlüssel über die `ForeignKeyConstraint` zwischen `Order` und `OrderLine` auf und füllt beide Spalten in neuen Zeilen. Übergeben Sie ein `tuple[str, ...]` an `fk_attr` nur dann, wenn die Constraint-Introspektion keine Übereinstimmung findet.

## Validierung

Jede eingereichte Zeile wird für sich allein validiert – über dieselben `create`- und `edit`-Pfade, die auch ein eigenständiges `ModelView` verwendet. Die Admin speichert zuerst das übergeordnete Modell und verarbeitet anschließend jede Inline-Zeile der Reihe nach. Ein Tippfehler im Feld `author` eines Kommentars hindert die anderen Kommentare nicht an der Verarbeitung. Schlägt die Validierung einer Zeile fehl, werden ihre Fehler dieser Zeile zugeordnet, und das Formular rendert die Zeile an Ort und Stelle mit den eingereichten Werten neu, damit Benutzer den Eintrag korrigieren und erneut absenden können.

!!! important
    Im SQLAlchemy-Backend gilt für die gesamte Anfrage Alles-oder-Nichts. Das übergeordnete Modell und jede Inline-Zeile teilen sich dieselbe request-scoped Session, und diese Session committet nur, wenn die gesamte Anfrage erfolgreich ist. Schlägt die Validierung einer beliebigen Zeile fehl, gibt die Antwort einen Fehler zurück und die Session wird zurückgerollt, sodass das übergeordnete Modell und alle Inline-Zeilen gemeinsam zurückgesetzt werden – einschließlich der Zeilen, die die Validierung bestanden haben. Betrachten Sie die Fehlermeldungen pro Zeile in der UI als Liste dessen, was zu korrigieren ist, nicht als Protokoll dessen, was gespeichert wurde.

---

## Wie es weitergeht

* **[SQLAlchemy](../integrations/sqlalchemy.md):** Wie Beziehungs-Introspektion die automatische Erkennung von Fremdschlüsseln ermöglicht.
* **[Custom Views](custom-views.md):** Erstellen Sie Seiten jenseits des Standard-Workflows aus Create, Edit und List.
* **[Events](../advanced/events.md):** Reagieren Sie auf Inline-Änderungen, nachdem Datensätze gespeichert wurden.

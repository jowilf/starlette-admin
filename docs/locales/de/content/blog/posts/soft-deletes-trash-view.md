---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/blog/posts/soft-deletes-trash-view/)
<!-- translation-notice:end -->

# Soft-Deletes und eine Papierkorb-View mit FastAPI & starlette-admin

_2026-07-10_

Ein Standard-`DELETE` ist gnadenlos. Wenn ein Operator verklickt oder ein automatisierter Aufräum-Job gegen den falschen Filter läuft, sind die Daten verloren, sofern Sie keine komplexe Wiederherstellung der Datenbank durchführen. Die Implementierung eines „Soft-Delete“ mindert dieses Risiko, indem ein Datensatz als gelöscht markiert wird, statt ihn dauerhaft aus der Datenbank zu entfernen. Dieser Ansatz macht die Datenwiederherstellung zu einer einfachen Update-Operation.

Diese Anleitung zeigt, wie Sie das Soft-Delete-Muster in einer FastAPI-Anwendung mit `starlette-admin` implementieren. Wir bauen eine vollständige Lösung auf der Grundlage von:

- Einem einzelnen Datenbankmodell
- Zwei unterschiedlichen administrativen Views
- Einem `deleted_at`-Zeitstempel
- Einer dedizierten Papierkorb-Oberfläche zum Wiederherstellen oder dauerhaften Entfernen von Datensätzen

**Den vollständigen lauffähigen Code ansehen:** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## Das Modell

Fügen Sie der Tabelle, die Sie schützen möchten, eine nullable Zeitstempelspalte hinzu. Ein `NULL`-Wert kennzeichnet einen aktiven Datensatz, während ein gefüllter Zeitstempel einen gelöschten Datensatz kennzeichnet:

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Dieser Ansatz erfordert weder eine separate Papierkorb-Tabelle noch eine externe Soft-Delete-Mixin-Bibliothek. Eine einzige Spalte verwaltet die gesamte State Machine.

## Gelöschte Zeilen in der aktiven View ausblenden

Die Klasse `ModelView` baut ihre Listen-, Zähl- und Detail-Queries mit überschreibbaren Methoden auf. `get_detail_query` greift standardmäßig auf `get_list_query` zurück, sodass das Filtern der List-Query auch die Detailseite filtert, direkte URLs eingeschlossen. `get_count_query` ist unabhängig und muss separat gefiltert werden. Indem Sie diese Queries so filtern, dass sie nur Datensätze enthalten, bei denen `deleted_at IS NULL` gilt, blenden Sie Soft-gelöschte Zeilen wirksam von der Listenseite, den Paginierungs-Zählern und direkten Detail-Links aus:

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

Sie müssen `deleted_at` außerdem von den Create- und Edit-Formularen ausschließen. Operatoren sollten dieses Feld niemals manuell setzen; es sollte nur programmatisch durch die Methode `delete()` und die Restore-Aktion geändert werden.

!!! warning
    Ein fehlendes `get_count_query` erzeugt ein Daten-Sichtbarkeitsleck: Paginierungs- und Suchergebnis-Gesamtzahlen enthalten gelöschte Zeilen, obwohl diese nicht in der Liste gerendert werden. `get_detail_query` benötigt hier keine separate Überschreibung, da es standardmäßig auf `get_list_query` zurückgreift und denselben Filter automatisch erbt. Wenn Sie einer View dennoch ein benutzerdefiniertes `get_detail_query` geben, erbt sie nicht mehr von `get_list_query` und muss `deleted_at` selbst filtern.

## Delete neu definieren

Sowohl die integrierte Massenlösch-Aktion als auch die Lösch-Schaltfläche auf Zeilenebene rufen `ModelView.delete()` auf. Das Überschreiben dieser Methode definiert das Löschverhalten global über alle Einstiegspunkte hinweg neu, ohne zusätzliche Konfiguration:

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

Die Aufrufe von `_emit_before_delete` und `_emit_after_delete` stellen sicher, dass der [Event Bus](../../advanced/events.md) genau so feuert wie bei einem Hard-Delete. Ein Abonnent von `AdminEvent.AFTER_DELETE` (etwa ein Audit-Log oder ein Webhook) muss daher nicht wissen, dass das Löschen soft war. Die Auswirkung ändert sich auf der Ebene der Datenbankzeile, aber die Lifecycle-Events bleiben konsistent.

### AFTER_DELETE_COMMITTED braucht seine eigene Verdrahtung

Die Events `BEFORE_DELETE` und `AFTER_DELETE` bilden nicht den kompletten Lifecycle ab. Die Basisimplementierung von `ModelView.delete()` in SQLAlchemy registriert zusätzlich einen `on_commit`-Callback. Dieser Callback feuert das Event `AFTER_DELETE_COMMITTED`, sobald die Transaktion erfolgreich committet, sodass Abonnenten sicher davon ausgehen können, dass die Zeile dauerhaft entfernt wurde.

Da das Beispiel `PostView` die Methode `delete()` vollständig überschreibt, wird die Standardregistrierung des `on_commit` umgangen. Ein Handler, der auf einer Soft-Delete-fähigen View auf `AdminEvent.AFTER_DELETE_COMMITTED` lauscht, feuert daher stillschweigend nicht.

Um diese Funktionalität wiederherzustellen, müssen Sie denselben Callback manuell registrieren, den auch die Basisimplementierung verwendet:

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

Die Hilfsfunktion `_make_after_delete_committed` nimmt `obj` und `pk` als normale Parameter entgegen. Sie wird pro Zeile einmalig mit den Werten genau dieser Zeile aufgerufen. Diese Struktur ist entscheidend. Würden Sie ein Lambda direkt im Schleifenkörper erstellen, würde es sich auf die Schleifenvariablen selbst beziehen statt auf ihre Werte in dem jeweiligen Durchlauf. Infolgedessen würde jeder Callback nach Abschluss der Schleife mit den finalen Werten von `obj` und `pk` feuern. Werden sie als Argumente an eine äußere Funktion übergeben, wird ihr exakter Zustand zum Aufrufzeitpunkt eingefangen.

Ein Vorteil von Soft-Deletes kommt hier zum Tragen. Ein Hard-Delete erfordert, das Objekt (`session.expunge`) zu trennen, bevor sein Committed-Callback geplant wird. Da eine hart gelöschte Zeile zum Commit-Zeitpunkt bereits weg ist, löst der Zugriff auf ein nicht geladenes Attribut einen `ObjectDeletedError` aus. Da ein Soft-Delete die Zeile nie entfernt, bleibt das Objekt angehängt und alle Attribute sind innerhalb des Callbacks sicher lesbar.

Die wichtigste Regel für `on_commit` gilt jedoch weiterhin: Der Callback darf nicht über `request.state.session` in die Datenbank schreiben. Diese Session ist bereits abgeschlossen. Alles, was in diese Session geflusht wird, startet eine neue Transaktion, die beim Schließen der Session verworfen wird.

## Eine zweite View für dieselbe Tabelle

Die `TrashView` zielt auf dasselbe Modell `Post`, registriert sich aber unter einem eigenen `key`. Diese Konfiguration weist `starlette-admin` an, sie als eigenständige Ressource mit separater URL und separatem Menüeintrag zu behandeln:

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

Diese Queries sind das exakte Gegenteil der `PostView`-Queries und filtern auf `IS NOT NULL` statt auf `IS NULL`. `get_detail_query` greift wiederum standardmäßig auf `get_list_query` zurück, sodass gelöschte Datensätze auf ihrer Detailseite korrekt aufgelöst werden, ganz ohne separate Überschreibung. Die Methoden `can_create` und `can_edit` geben `False` zurück, weil Operatoren Datensätze niemals direkt im Papierkorb erstellen oder bearbeiten sollten. Datensätze gelangen nur über `PostView.delete()` in den Papierkorb und verlassen ihn nur über eine Restore-Aktion oder eine endgültige Bereinigung.

## Wiederherstellen und das Argument für ein echtes Delete

Die `TrashView` behält die integrierte `delete`-Aktion in ihrer `actions`-Liste bei und überschreibt sie nicht. Innerhalb der Papierkorb-View führt das Ausführen eines `delete` ein normales SQL-`DELETE` aus. Dies wirkt als endgültige Bereinigung. Sobald eine Zeile aus dem Papierkorb entfernt wurde, ist sie vollständig weg.

Das Wiederherstellen eines Datensatzes erfordert eine kleine [benutzerdefinierte Aktion](../../user-guide/actions.md), die den Zeitstempel `deleted_at` leert:

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

Das Setzen von `deleted_at = None` stellt die Zeile beim nächsten Request sofort wieder in die aktive Liste der `PostView` zurück, da die primäre View nur nach `NULL`-Werten fragt.

## Beide Views mit derselben Tabelle verbinden

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

Diese Konfiguration richtet zwei separate administrative Views für eine einzige Datenbanktabelle ein. Eine einzige Spalte bestimmt, welche View jede bestimmte Zeile anzeigt.

## Wo dieses Muster an seine Grenzen stößt

- **Unique Constraints:** Eine `UNIQUE`-Constraint auf einem Feld wie `slug` verhindert, dass Operatoren einen aktiven Beitrag mit demselben Slug neu erstellen, solange die Soft-gelöschte Version noch im Papierkorb liegt. Zur Lösung entweder Zeilen mit `deleted_at IS NOT NULL` mithilfe eines partiellen Index aus dem Unique-Index ausschließen (sofern Ihre Datenbank-Engine dies unterstützt) oder die Spalte `deleted_at` selbst in die Unique-Constraint aufnehmen.
- **Foreign Keys:** Ein Soft-gelöschter `Post` bleibt eine gültige Zeile für Fremdschlüssel-Beziehungen in anderen Tabellen. Kind-Datensätze verweisen weiterhin darauf. Während dies oft das gewünschte Verhalten ist, erfordert das Kaskadieren eines Soft-Deletes auf verwandte Zeilen explizite eigene Logik. Die Datenbank handhabt das nicht automatisch so wie `ON DELETE CASCADE` bei Hard-Deletes.
- **Query-Disziplin:** Jede neue Datenbank-Query, die auf das Modell `Post` zielt, muss den Filter `deleted_at IS NULL` explizit enthalten. Lässt eine Raw-Query, ein Export-Job oder eine sekundäre Admin-View diesen Filter weg, sickern gelöschte Daten in aktive Workflows.
- **Datenbankwachstum:** Soft-gelöschte Zeilen belegen weiterhin Tabellen- und Indexplatz. Wenn Ihre Anwendung die meisten Soft-gelöschten Zeilen bereinigt, statt sie wiederherzustellen, sollten Sie einen geplanten Hintergrund-Job implementieren. Dieser Job kann Datensätze, die älter als ein bestimmtes Aufbewahrungszeitfenster sind, hart löschen, um ein unbegrenztes Datenbankwachstum zu verhindern.

## Auf andere Backends erweitern

Die Kernprinzipien dieses Musters beschränken sich nicht auf SQLAlchemy. Sie können diesen Ansatz auf jedem Backend umsetzen, das das Überschreiben von Listen-, Zähl- und Detail-Queries neben der Methode `delete()` erlaubt. Wenn Sie beispielsweise Beanie, MongoEngine oder Tortoise ORM verwenden, filtern die entsprechenden Overrides die Query auf ein Feld `deleted_at` auf exakt dieselbe Weise. Die konkrete Query-Syntax ändert sich, aber das architektonische Muster bleibt identisch.

---

## Was kommt als Nächstes

- **[Events](../../advanced/events.md):** Verstehen Sie, wie `_emit_before_delete` und `_emit_after_delete` mit externen Abonnenten außerhalb der View zusammenhängen.
- **[Actions](../../user-guide/actions.md):** Erkunden Sie den Decorator hinter `restore_action`, einschließlich der Implementierung von Bestätigungsdialogen und Flash-Nachrichten-Helfern.
- **[Views](../../user-guide/views.md):** Sehen Sie sich den vollständigen Satz an Query- und Permission-Hooks innerhalb von `ModelView` an.

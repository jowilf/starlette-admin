---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/blog/posts/soft-deletes-trash-view/)
<!-- translation-notice:end -->

# Soft Deletes und eine Trash-Ansicht mit FastAPI & starlette-admin

_2026-07-10_

Eine Standard-`DELETE`-Operation ist unerbittlich. Wenn ein Operator verklickt oder ein automatisierter Aufräum-Job mit dem falschen Filter läuft, sind die Daten verloren – es sei denn, Sie führen eine komplexe Datenbank-Wiederherstellung durch. Die Implementierung eines „Soft Delete" mildert dieses Risiko ab, indem ein Datensatz als gelöscht markiert wird, statt ihn dauerhaft aus der Datenbank zu entfernen. Dieser Ansatz macht die Datenwiederherstellung zu einer einfachen Update-Operation.

Dieser Leitfaden zeigt, wie Sie das Soft-Delete-Muster in einer FastAPI-Anwendung mit `starlette-admin` implementieren. Wir bauen eine vollständige Lösung mit folgenden Komponenten:

- Einem einzelnen Datenbankmodell
- Zwei unterschiedlichen administrativen Ansichten
- Einem `deleted_at`-Zeitstempel
- Einer dedizierten Trash-Oberfläche zum Wiederherstellen oder endgültigen Löschen von Datensätzen

**Den vollständigen lauffähigen Code anzeigen:** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## Das Modell

Fügen Sie der Tabelle, die Sie schützen möchten, eine nullable Zeitstempel-Spalte hinzu. Ein `NULL`-Wert kennzeichnet einen aktiven Datensatz, während ein gesetzter Zeitstempel einen gelöschten Datensatz anzeigt:

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Dieser Ansatz erfordert keine separate Trash-Tabelle und keine externe Soft-Delete-Mixin-Bibliothek. Eine einzelne Spalte verwaltet den gesamten Zustandsautomaten.

## Gelöschte Zeilen in der aktiven Ansicht ausblenden

Die Klasse `ModelView` erstellt ihre Listen-, Zähl- und Detailabfragen mithilfe überschreibbarer Methoden. `get_detail_query` greift standardmäßig auf `get_list_query` zurück, sodass die Filterung der Listenabfrage auch die Detailseite filtert – direkte URLs eingeschlossen. `get_count_query` ist unabhängig und muss separat gefiltert werden. Indem Sie diese Abfragen so filtern, dass sie nur Datensätze einschließen, bei denen `deleted_at IS NULL` gilt, blenden Sie soft-gelöschte Zeilen wirksam von der Listenseite, den Paginierungszählern und direkten Detail-Links aus:

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

Sie müssen `deleted_at` außerdem von den Create- und Edit-Formularen ausschließen. Operatoren sollten dieses Feld niemals manuell setzen; es sollte ausschließlich programmatisch durch die Methode `delete()` und die Restore-Aktion geändert werden.

!!! warning
Ein fehlendes `get_count_query` führt zu einem Leak bei der Datensichtbarkeit: Paginierungs- und Suchergebnis-Zähler schließen gelöschte Zeilen ein, obwohl diese nicht in der Liste gerendert werden. `get_detail_query` benötigt hier keine separate Überschreibung, da es standardmäßig auf `get_list_query` zurückgreift und denselben Filter automatisch erbt. Wenn Sie einer Ansicht jedoch ein eigenes `get_detail_query` geben, erbt sie nicht mehr von `get_list_query` und muss `deleted_at` selbst filtern.

## Delete neu definieren

Sowohl die integrierte Batch-Delete-Aktion als auch der Delete-Button auf Zeilenebene rufen die Methode `ModelView.delete()` auf. Durch das Überschreiben dieser Methode definieren Sie das Löschverhalten global über alle Einstiegspunkte hinweg neu – ohne zusätzliche Konfiguration:

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

Die Aufrufe `_emit_before_delete` und `_emit_after_delete` stellen sicher, dass der [Event Bus](../../advanced/events.md) genau so auslöst, wie er es bei einem Hard Delete täte. Folglich muss ein `AdminEvent.AFTER_DELETE`-Abonnent (etwa ein Audit-Log oder ein Webhook) nicht wissen, dass die Löschung soft erfolgte. Die Auswirkung ändert sich auf der Ebene der Datenbankzeile, aber die Lifecycle-Events bleiben konsistent.

### AFTER_DELETE_COMMITTED braucht seine eigene Verdrahtung

Die Events `BEFORE_DELETE` und `AFTER_DELETE` repräsentieren nicht den vollständigen Lifecycle. Die Basisimplementierung der Methode `ModelView.delete()` registriert zusätzlich einen `on_commit`-Callback. Dieser Callback löst das Event `AFTER_DELETE_COMMITTED` aus, sobald die Transaktion erfolgreich committet wurde, sodass Abonnenten sicher davon ausgehen können, dass die Zeile dauerhaft entfernt ist.

Da das Beispiel `PostView` die Methode `delete()` vollständig überschreibt, wird die Standardregistrierung von `on_commit` umgangen. Folglich wird ein Handler, der auf einem soft-löschbaren View auf `AdminEvent.AFTER_DELETE_COMMITTED` lauscht, stillschweigend nicht ausgelöst.

Um diese Funktionalität wiederherzustellen, müssen Sie denselben Callback manuell registrieren, den die Basisimplementierung verwendet:

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

Die Hilfsfunktion `_make_after_delete_committed` nimmt `obj` und `pk` als normale Parameter entgegen. Sie wird einmal pro Zeile mit den Werten genau dieser Zeile aufgerufen. Diese Struktur ist entscheidend. Würden Sie ein Lambda direkt im Schleifenkörper erstellen, würde es über die Schleifenvariablen selbst schließen statt über deren Werte im jeweiligen Iterationsschritt. Infolgedessen würde jeder Callback nach Abschluss der Schleife mit den finalen Werten von `obj` und `pk` ausgelöst. Werden sie als Argumente an eine äußere Funktion übergeben, wird ihr exakter Zustand zum Aufrufzeitpunkt eingefangen.

Ein Vorteil des Soft Deletes kommt hier zum Tragen. Ein Hard Delete erfordert das Detachen des Objekts (`session.expunge`), bevor sein Committed-Callback eingeplant wird. Da eine hard-gelöschte Zeile zum Commit-Zeitpunkt bereits verschwunden ist, löst der Zugriff auf ein nicht geladenes Attribut einen `ObjectDeletedError` aus. Da ein Soft Delete die Zeile nie entfernt, bleibt das Objekt attached, und alle Attribute sind innerhalb des Callbacks sicher lesbar.

Die Grundregel für `on_commit` gilt dennoch weiterhin: Der Callback darf nicht unter Verwendung von `request.state.session` in die Datenbank schreiben. Diese Session ist bereits abgeschlossen. Alles, was in diese Session geflusht wird, startet eine neue Transaktion, die beim Schließen der Session verworfen wird.

## Eine zweite Ansicht für dieselbe Tabelle

Der `TrashView` zielt auf dasselbe `Post`-Modell, registriert sich jedoch unter einem eigenen `key`. Diese Konfiguration weist `starlette-admin` an, ihn als eigenständige Ressource mit separater URL und eigenem Menüeintrag zu behandeln:

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

Diese Abfragen sind das exakte Gegenteil der `PostView`-Abfragen und filtern auf `IS NOT NULL` statt auf `IS NULL`. `get_detail_query` greift erneut standardmäßig auf `get_list_query` zurück, sodass sich gelöschte Datensätze auf ihrer Detailseite korrekt auflösen lassen – ohne separate Überschreibung. Die Methoden `can_create` und `can_edit` geben `False` zurück, da Operatoren niemals direkt im Papierkorb Datensätze erstellen oder bearbeiten sollten. Datensätze können nur über `PostView.delete()` in den Papierkorb gelangen und ihn nur über eine Restore-Aktion oder eine endgültige Bereinigung verlassen.

## Wiederherstellen – und der Fall für ein echtes Delete

Der `TrashView` behält die integrierte `delete`-Aktion in seiner `actions`-Liste bei und überschreibt sie nicht. Innerhalb der Trash-Ansicht führt die Ausführung eines `delete` ein Standard-SQL-`DELETE` durch. Dies wirkt als endgültige Bereinigung. Sobald eine Zeile aus dem Papierkorb entfernt wurde, ist sie vollständig verschwunden.

Das Wiederherstellen eines Datensatzes erfordert eine kleine [Custom Action](../../user-guide/actions.md), die den Zeitstempel `deleted_at` zurücksetzt:

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

Durch das Setzen von `deleted_at = None` erscheint die Zeile unmittelbar bei der nächsten Anfrage wieder in der aktiven Liste des `PostView`, da die primäre Ansicht ausschließlich nach `NULL`-Werten abfragt.

## Beide Ansichten mit derselben Tabelle verbinden

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

Diese Konfiguration etabliert zwei separate administrative Ansichten für eine einzige Datenbanktabelle. Eine einzelne Spalte bestimmt, welche Ansicht jede bestimmte Zeile anzeigt.

## Wo dieses Muster an seine Grenzen stößt

- **Unique Constraints:** Ein `UNIQUE`-Constraint auf einem Feld wie `slug` verhindert, dass Operatoren einen aktiven Post mit demselben Slug neu erstellen, solange die soft-gelöschte Version noch im Papierkorb liegt. Zur Lösung bieten sich zwei Wege an: Entweder schließen Sie Zeilen mit `deleted_at IS NOT NULL` mithilfe eines Partial Index (sofern Ihre Datenbank-Engine diesen unterstützt) vom Unique Index aus, oder Sie nehmen die Spalte `deleted_at` selbst in den Unique Constraint auf.
- **Foreign Keys:** Ein soft-gelöschter `Post` bleibt eine gültige Zeile für Foreign-Key-Beziehungen in anderen Tabellen. Kinddatensätze werden weiterhin auf ihn auflösen. Während dies oft das gewünschte Verhalten ist, erfordert das Kaskadieren eines Soft Deletes auf verwandte Zeilen explizite Custom Logic. Die Datenbank behandelt dies nicht automatisch so wie `ON DELETE CASCADE` bei Hard Deletes.
- **Query-Disziplin:** Jede neue Datenbankabfrage, die auf das Modell `Post` abzielt, muss den Filter `deleted_at IS NULL` explizit enthalten. Lässt eine Raw Query, ein Export-Job oder eine sekundäre Admin-Ansicht diesen Filter weg, sickern gelöschte Daten in aktive Workflows.
- **Datenbankwachstum:** Soft-gelöschte Zeilen belegen weiterhin Tabellen- und Indexspeicher. Wenn Ihre Anwendung die meisten soft-gelöschten Zeilen bereinigt statt sie wiederherzustellen, ziehen Sie die Implementierung eines geplanten Background Jobs in Betracht. Dieser Job kann Datensätze, die älter als ein bestimmtes Aufbewahrungszeitfenster sind, hard-deleten, um ein unbegrenztes Datenbankwachstum zu verhindern.

## Erweiterung auf andere Backends

Die Grundprinzipien dieses Musters sind nicht exklusiv für SQLAlchemy. Sie können diesen Ansatz auf jedem Backend implementieren, das das Überschreiben von Listen-, Zähl- und Detailabfragen gemeinsam mit der Methode `delete()` erlaubt. Wenn Sie beispielsweise Beanie, MongoEngine oder Tortoise ORM verwenden, filtern die entsprechenden Overrides die Abfrage auf ein Feld `deleted_at` auf exakt dieselbe Weise. Die konkrete Query-Syntax ändert sich, doch das architektonische Muster bleibt identisch.

---

## Was kommt als Nächstes?

- **[Events](../../advanced/events.md):** Verstehen Sie, wie `_emit_before_delete` und `_emit_after_delete` externe Abonnenten außerhalb der View anbinden.
- **[Actions](../../user-guide/actions.md):** Erkunden Sie den Decorator hinter `restore_action`, einschließlich der Implementierung von Bestätigungsdialogen und Flash-Message-Helfern.
- **[Views](../../user-guide/views.md):** Sehen Sie sich den vollständigen Satz an Query- und Permission-Hooks an, der innerhalb von `ModelView` verfügbar ist.

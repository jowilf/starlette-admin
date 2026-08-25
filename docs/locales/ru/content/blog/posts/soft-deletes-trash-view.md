---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Машинный перевод под контролем человека"

    Этот контент переведён с помощью машинной генерации, направляемой
    составленными людьми глоссариями и руководствами по стилю. Поскольку
    текст не проверяется вручную построчно, возможны отдельные ошибки или
    неестественные формулировки.

    В случае любых расхождений авторитетным источником считается
    оригинальная версия на английском языке.

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/blog/posts/soft-deletes-trash-view/)
<!-- translation-notice:end -->

# Мягкое удаление и представление «Корзина» с FastAPI и starlette-admin

_2026-07-10_

Стандартная операция `DELETE` беспощадна. Если оператор промахнётся или автоматизированная задача очистки выполнится с неверным фильтром, данные будут потеряны — восстановить их можно только с помощью сложной процедуры восстановления базы данных. Реализация «мягкого удаления» (soft delete) снижает этот риск: вместо безвозвратного удаления записи из базы данных она помечается как удалённая. Такой подход превращает восстановление данных в простую операцию обновления.

В этом руководстве показано, как реализовать шаблон мягкого удаления в приложении FastAPI с использованием `starlette-admin`. Мы построим полное решение на основе:

- одной модели базы данных;
- двух отдельных административных представлений;
- метки времени `deleted_at`;
- специализированного интерфейса Trash для восстановления или окончательного удаления записей.

**Полный исполняемый код:** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## Модель

Добавьте в таблицу, которую вы хотите защитить, допускающий значение `NULL` столбец с меткой времени. Значение `NULL` означает активную запись, а заполненная метка времени — удалённую:

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Этот подход не требует отдельной таблицы корзины или внешней библиотеки mixin для мягкого удаления. Один столбец управляет всей машиной состояний.

## Скрытие удалённых строк в основном представлении

Класс `ModelView` строит запросы списка, подсчёта и детального просмотра с помощью переопределяемых методов. `get_detail_query` по умолчанию использует `get_list_query`, поэтому фильтрация запроса списка также фильтрует страницу деталей, включая прямые URL. `get_count_query` независим и должен фильтроваться отдельно. Отфильтровав эти запросы так, чтобы они включали только записи с условием `deleted_at IS NULL`, вы эффективно скроете мягко удалённые строки со страницы списка, из счётчиков пагинации и по прямым ссылкам на детали:

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

Также необходимо исключить `deleted_at` из форм создания и редактирования. Операторы никогда не должны задавать это поле вручную; оно должно изменяться только программно — методом `delete()` и действием восстановления.

!!! warning
Отсутствие `get_count_query` приводит к утечке видимости данных: итоговые значения пагинации и результатов поиска будут включать удалённые строки, даже если те не отображаются в списке. `get_detail_query` здесь не требует отдельного переопределения, поскольку по умолчанию он использует `get_list_query` и автоматически наследует тот же фильтр. Однако если вы зададите представлению собственный `get_detail_query`, оно перестанет наследовать от `get_list_query` и должно будет само фильтровать `deleted_at`.

## Переопределение удаления

И встроенное пакетное действие удаления, и кнопка удаления отдельной строки вызывают метод `ModelView.delete()`. Переопределив этот метод, вы глобально меняете поведение удаления во всех точках входа без дополнительной конфигурации:

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

Вызовы `_emit_before_delete` и `_emit_after_delete` гарантируют, что [шина событий](../../advanced/events.md) сработает точно так же, как при жёстком удалении. Следовательно, подписчику события `AdminEvent.AFTER_DELETE` (например, журналу аудита или webhook) не нужно знать, что удаление было мягким. Изменения затрагивают уровень строк базы данных, но события жизненного цикла остаются согласованными.

### AFTER_DELETE_COMMITTED требует собственной реализации

События `BEFORE_DELETE` и `AFTER_DELETE` не охватывают весь жизненный цикл. Базовый метод `ModelView.delete()` SQLAlchemy также регистрирует callback `on_commit`. Этот callback вызывает событие `AFTER_DELETE_COMMITTED` после успешной фиксации транзакции, позволяя подписчикам безопасно считать, что строка надёжно удалена.

Поскольку пример `PostView` полностью переопределяет `delete()`, стандартная регистрация `on_commit` обходится. В результате обработчик, ожидающий событие `AdminEvent.AFTER_DELETE_COMMITTED` у представления с мягким удалением, молча не сработает.

Чтобы восстановить эту функциональность, необходимо вручную зарегистрировать тот же callback, который используется базовой реализацией:

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

Вспомогательная функция `_make_after_delete_committed` принимает `obj` и `pk` в качестве обычных параметров. Она вызывается один раз для каждой строки с значениями именно этой строки. Эта структура критически важна. Если бы вы создали lambda непосредственно внутри тела цикла, она замкнулась бы на сами переменные цикла, а не на их значения в конкретной итерации. В результате каждый callback сработал бы с финальными значениями `obj` и `pk` после завершения цикла. Передача их в качестве аргументов во внешнюю функцию фиксирует их точное состояние на момент вызова.

У мягкого удаления есть одно преимущество, применимое здесь. Жёсткое удаление требует отсоединить объект (`session.expunge`) перед планированием его committed-callback. Поскольку жёстко удалённая строка к моменту фиксации уже отсутствует, обращение к незагруженному атрибуту вызовет `ObjectDeletedError`. Так как мягкое удаление никогда не удаляет строку, объект остаётся присоединённым, и все атрибуты безопасно читаются внутри callback.

Однако основное правило `on_commit` остаётся в силе: callback не должен выполнять запись в базу данных через `request.state.session`. Эта сессия уже завершена. Всё, что будет отправлено (flushed) в эту сессию, запускает новую транзакцию, которая отбрасывается при закрытии сессии.

## Второе представление для той же таблицы

`TrashView` работает с той же моделью `Post`, но регистрируется под уникальным `key`. Такая конфигурация указывает `starlette-admin` рассматривать его как отдельный ресурс с собственным URL и пунктом меню:

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

Эти запросы являются точной инверсией запросов `PostView`: вместо условия `IS NULL` применяется `IS NOT NULL`. `get_detail_query` снова по умолчанию использует `get_list_query`, поэтому удалённые записи корректно отображаются на своей странице деталей без отдельного переопределения. Методы `can_create` и `can_edit` возвращают `False`, потому что операторы никогда не должны создавать или редактировать записи непосредственно в корзине. Записи могут попасть в корзину только через `PostView.delete()` и покинуть её только через действие восстановления или окончательное удаление.

## Восстановление и случай настоящего удаления

`TrashView` сохраняет встроенное действие `delete` в своём списке `actions` и не переопределяет его. Внутри представления корзины выполнение `delete` выполняет стандартную SQL-операцию `DELETE`. Это означает окончательное удаление. После того как строка удалена из корзины, она исчезает безвозвратно.

Для восстановления записи требуется небольшое [пользовательское действие](../../user-guide/actions.md), которое очищает метку времени `deleted_at`:

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

Присвоение `deleted_at = None` немедленно возвращает строку в список основного представления `PostView` при следующем запросе, поскольку основное представление выбирает только записи со значением `NULL`.

## Подключение обоих представлений к одной таблице

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

Эта конфигурация создаёт два отдельных административных представления для одной таблицы базы данных. Значение одного столбца определяет, какое представление отображает каждую конкретную строку.

## Ограничения этого шаблона

- **Уникальные ограничения:** ограничение `UNIQUE` на поле вроде `slug` не позволит операторам создать заново активную запись с тем же slug, пока её мягко удалённая версия находится в корзине. Чтобы решить эту проблему, либо исключите строки с условием `deleted_at IS NOT NULL` из уникального индекса с помощью частичного индекса (если ваша СУБД его поддерживает), либо включите столбец `deleted_at` непосредственно в уникальное ограничение.
- **Внешние ключи:** мягко удалённая запись `Post` остаётся валидной строкой для связей по внешним ключам в других таблицах. Дочерние записи продолжат ссылаться на неё. Зачастую это желаемое поведение, однако каскадное мягкое удаление связанных строк требует явной пользовательской логики. База данных не будет обрабатывать это автоматически, как она делает с `ON DELETE CASCADE` при жёстком удалении.
- **Дисциплина запросов:** каждый новый запрос к базе данных, работающий с моделью `Post`, должен явно включать фильтр `deleted_at IS NULL`. Если сырой запрос, задача экспорта или вторичное административное представление опустят этот фильтр, удалённые данные попадут в рабочие процессы.
- **Рост базы данных:** мягко удалённые строки продолжают занимать место в таблице и индексах. Если ваше приложение удаляет большинство мягко удалённых строк окончательно, а не восстанавливает их, рассмотрите реализацию периодической фоновой задачи. Она может жёстко удалять записи старше определённого срока хранения, чтобы предотвратить неконтролируемый рост базы данных.

## Перенос на другие backend'ы

Основные принципы этого шаблона не ограничиваются SQLAlchemy. Вы можете реализовать данный подход на любом backend'е, который позволяет переопределять запросы списка, подсчёта и деталей вместе с методом `delete()`. Например, если вы используете Beanie, MongoEngine или Tortoise ORM, эквивалентные переопределения будут фильтровать запрос по полю `deleted_at` точно таким же образом. Меняется лишь синтаксис запросов, но архитектурный шаблон остаётся идентичным.

---

## Что дальше

- **[Events](../../advanced/events.md):** узнайте, как `_emit_before_delete` и `_emit_after_delete` связываются с внешними подписчиками за пределами представления.
- **[Actions](../../user-guide/actions.md):** изучите декоратор, стоящий за `restore_action`, включая реализацию диалогов подтверждения и вспомогательных функций flash-сообщений.
- **[Views](../../user-guide/views.md):** ознакомьтесь с полным набором hook'ов запросов и прав доступа, доступных в `ModelView`.

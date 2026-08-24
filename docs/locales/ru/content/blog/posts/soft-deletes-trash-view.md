---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
prompt_hash: efac6b04187c7def41059e1c72e46a95b2ca178220b0cb995f0594e001f3f1a5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
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

Стандартная операция `DELETE` беспощадна. Если оператор промахнётся или автоматическая задача очистки выполнится с неверным фильтром, данные будут потеряны — если только вы не выполните сложное восстановление базы данных. Реализация «мягкого удаления» снижает этот риск: запись помечается как удалённая вместо её безвозвратного удаления из базы. Такой подход превращает восстановление данных в простую операцию обновления.

Это руководство показывает, как реализовать шаблон мягкого удаления в приложении FastAPI с помощью `starlette-admin`. Мы построим полное решение, использующее:

- одну модель базы данных;
- два отдельных представления администрирования;
- метку времени `deleted_at`;
- отдельный интерфейс корзины для восстановления записей или их окончательного удаления.

**Полный исполняемый код:** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## Модель

Добавьте допускающую значение `NULL` колонку с меткой времени в таблицу, которую нужно защитить. Значение `NULL` означает активную запись, а заполненная метка времени — удалённую:

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Этот подход не требует отдельной таблицы корзины или внешней библиотеки-миксина для мягкого удаления. Одна колонка управляет всем конечным автоматом состояний.

## Скрытие удалённых строк в активном представлении

Класс `ModelView` строит запросы для списка, подсчёта и деталей с помощью переопределяемых методов. `get_detail_query` по умолчанию использует `get_list_query`, поэтому фильтрация запроса списка также фильтрует страницу деталей, включая прямые URL. `get_count_query` независим и требует отдельной фильтрации. Отфильтровав эти запросы так, чтобы они включали только записи, где `deleted_at IS NULL`, вы эффективно скроете мягко удалённые строки со страницы списка, из подсчёта пагинации и по прямым ссылкам на детали:

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

Также необходимо исключить `deleted_at` из форм создания и редактирования. Операторы не должны задавать это поле вручную; оно должно изменяться только программно — методом `delete()` и действием восстановления.

!!! warning
Отсутствие `get_count_query` приводит к утечке видимости данных: итоговые значения пагинации и поиска будут включать удалённые строки, даже если они не отображаются в списке. `get_detail_query` здесь не требует отдельного переопределения, поскольку по умолчанию использует `get_list_query` и автоматически наследует тот же фильтр. Если же вы задаёте представлению собственный `get_detail_query`, оно перестаёт наследовать от `get_list_query` и должно само фильтровать по `deleted_at`.

## Переопределение удаления

И встроенное групповое действие удаления, и кнопка удаления на уровне строки вызывают `ModelView.delete()`. Переопределение этого метода меняет поведение удаления глобально во всех точках входа без дополнительной настройки:

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

Вызовы `_emit_before_delete` и `_emit_after_delete` гарантируют, что [шина событий](../../advanced/events.md) сработает точно так же, как при жёстком удалении. В результате подписчику события `AdminEvent.AFTER_DELETE` (например, журналу аудита или вебхуку) не нужно знать, что удаление было мягким. Изменения затрагивают уровень строк базы данных, но события жизненного цикла остаются согласованными.

### AFTER_DELETE_COMMITTED требует собственной реализации

События `BEFORE_DELETE` и `AFTER_DELETE` не охватывают весь жизненный цикл. Базовый метод `ModelView.delete()` в SQLAlchemy также регистрирует колбэк `on_commit`. Этот колбэк вызывает событие `AFTER_DELETE_COMMITTED` после успешной фиксации транзакции, позволяя подписчикам считать, что строка надёжно удалена.

Поскольку пример `PostView` полностью переопределяет `delete()`, регистрация `on_commit` по умолчанию обходится. Следовательно, обработчик, ожидающий событие `AdminEvent.AFTER_DELETE_COMMITTED` в представлении с мягким удалением, молча не сработает.

Чтобы вернуть эту функциональность, необходимо вручную зарегистрировать тот же колбэк, который использует базовая реализация:

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

Вспомогательная функция `_make_after_delete_committed` принимает `obj` и `pk` как обычные параметры. Она вызывается один раз для каждой строки со значениями именно этой строки. Эта структура критически важна. Если бы вы создали лямбду прямо внутри тела цикла, она замкнулась бы на сами переменные цикла, а не на их значения в конкретной итерации. В результате каждый колбэк срабатывал бы с финальными значениями `obj` и `pk` после завершения цикла. Передача их аргументами во внешнюю функцию фиксирует их точное состояние на момент вызова.

У мягкого удаления есть одно преимущество, применимое здесь. Жёсткое удаление требует отсоединить объект (`session.expunge`) перед планированием его колбэка фиксации. Поскольку жёстко удалённая строка к моменту фиксации уже исчезла, обращение к незагруженному атрибуту вызывает `ObjectDeletedError`. Так как мягкое удаление никогда не удаляет строку, объект остаётся присоединённым, и все атрибуты безопасно читаются внутри колбэка.

Однако основное правило `on_commit` всё ещё действует: колбэк не должен писать в базу данных через `request.state.session`. Эта сессия уже завершена. Всё, что будет отправлено в эту сессию, запускает новую транзакцию, которая отбрасывается при закрытии сессии.

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

Эти запросы являются точной инверсией запросов `PostView`: фильтр `IS NOT NULL` вместо `IS NULL`. `get_detail_query` снова по умолчанию использует `get_list_query`, поэтому удалённые записи корректно открываются на своей странице деталей без отдельного переопределения. Методы `can_create` и `can_edit` возвращают `False`, потому что операторы не должны создавать или редактировать записи напрямую в корзине. Записи попадают в корзину только через `PostView.delete()` и покидают её либо через действие восстановления, либо через окончательное удаление.

## Восстановление и случай настоящего удаления

`TrashView` сохраняет встроенное действие `delete` в своём списке `actions` и не переопределяет его. Внутри представления корзины выполнение `delete` выполняет стандартный SQL `DELETE`. Это окончательное удаление. После того как строка удалена из корзины, она исчезает безвозвратно.

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

Присвоение `deleted_at = None` немедленно возвращает строку в список активного `PostView` при следующем запросе, так как основное представление запрашивает только значения `NULL`.

## Подключение обоих представлений к одной таблице

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

Эта конфигурация создаёт два отдельных представления администрирования для одной таблицы базы данных. Одна колонка определяет, какое представление отображает конкретную строку.

## Ограничения этого шаблона

- **Уникальные ограничения:** ограничение `UNIQUE` на поле вроде `slug` не позволит операторам создать активную запись с тем же slug, пока мягко удалённая версия остаётся в корзине. Чтобы решить эту проблему, либо исключите строки с `deleted_at IS NOT NULL` из уникального индекса с помощью частичного индекса (если он поддерживается вашей СУБД), либо включите колонку `deleted_at` в само уникальное ограничение.
- **Внешние ключи:** мягко удалённый `Post` остаётся валидной строкой для связей по внешним ключам в других таблицах. Дочерние записи продолжат ссылаться на него. Часто это желаемое поведение, но каскадное мягкое удаление связанных строк требует явной пользовательской логики. База данных не обработает это автоматически, как она делает с `ON DELETE CASCADE` при жёстком удалении.
- **Дисциплина запросов:** каждый новый запрос к базе данных, работающий с моделью `Post`, должен явно включать фильтр `deleted_at IS NULL`. Если сырой запрос, задача экспорта или вторичное представление администрирования опустят этот фильтр, удалённые данные попадут в активные рабочие процессы.
- **Рост базы данных:** мягко удалённые строки продолжают занимать место в таблице и индексах. Если ваше приложение удаляет большинство мягко удалённых строк вместо их восстановления, рассмотрите возможность реализации фоновой задачи по расписанию. Она может жёстко удалять записи старше определённого срока хранения, чтобы предотвратить неограниченный рост базы данных.

## Расширение на другие бэкенды

Основные принципы этого шаблона не привязаны к SQLAlchemy. Вы можете реализовать этот подход на любом бэкенде, который позволяет переопределять запросы списка, подсчёта и деталей вместе с методом `delete()`. Например, если вы используете Beanie, MongoEngine или Tortoise ORM, эквивалентные переопределения будут фильтровать запрос по полю `deleted_at` точно таким же образом. Синтаксис запросов меняется, но архитектурный шаблон остаётся идентичным.

---

## Что дальше

- **[События](../../advanced/events.md):** узнайте, как `_emit_before_delete` и `_emit_after_delete` связываются с внешними подписчиками вне представления.
- **[Действия](../../user-guide/actions.md):** изучите декоратор, стоящий за `restore_action`, включая реализацию диалогов подтверждения и вспомогательных функций флеш-сообщений.
- **[Представления](../../user-guide/views.md):** ознакомьтесь с полным набором хуков запросов и прав доступа, доступных в `ModelView`.

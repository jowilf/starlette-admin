---
title: Макеты форм
description: Проектируйте сложные адаптивные макеты форм с помощью TabsWidget, FieldsetWidget
  и колонок сетки в starlette-admin.
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# Макеты форм

По умолчанию формы создания и редактирования отображают всё содержимое `fields` в виде одного плоского списка. Атрибут `form_layout` позволяет расположить эти поля ввода с помощью тех же компонуемых виджетов, которые используются для [дашбордов](../user-guide/custom-views.md): строки бок о бок, панели с заголовками или сворачиваемые панели, вкладки, статический контент и ваши собственные виджеты.

## Базовое использование

Для простейшего макета виджеты не нужны вовсе. Укажите поле по его строковому имени, чтобы оставить его на отдельной строке, а имена полей сгруппируйте в кортеж, чтобы разместить их в одной строке бок о бок.

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

В приведённом выше макете:

* `("first_name", "last_name")` создаёт одну строку, разделённую поровну между двумя полями ввода.
* `"email"` отображается на отдельной строке непосредственно под ней.
* `("salary", "notes")` создаёт вторую многоколоночную строку.

В строку можно поместить любое количество полей и свободно чередовать одноколоночные и многоколоночные строки.

Контейнерные виджеты сами разворачивают эту сокращённую запись: `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget` и `Col` при создании превращают кортежи в строки, а списки — в вертикальные колонки. Поэтому сокращённая запись работает и внутри вложенных атрибутов `children`, и внутри дашборда [`CustomView.widget`](../user-guide/custom-views.md).

## Группировка полей

### Панели с заголовками

Чтобы дать группе полей заголовок или сделать её сворачиваемой, оберните её в `PanelWidget`. Виджет принимает ту же сокращённую запись со строками и кортежами, что и верхний уровень.

```python
from starlette_admin import PanelWidget


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        PanelWidget(
            title="Identity",
            children=[("first_name", "last_name"), "email"],
        ),
        PanelWidget(
            title="Compensation",
            children=["salary", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]
```

`PanelWidget` принимает следующие атрибуты:

| Атрибут | Описание |
| --- | --- |
| `title` | Заголовок, отображаемый в шапке карточки панели. |
| `children` | Виджеты, отображаемые внутри панели, по порядку. Принимает сокращённую запись выше или вложенные виджеты. Добавьте дочерний элемент `TextWidget(card=False)`, чтобы разместить поясняющий текст под заголовком. |
| `collapsible` | Позволяет разворачивать и сворачивать панель. |
| `collapsed` | Изначально сворачивает панель. Применяется только при `collapsible=True`. |

Если группе не нужен заголовок, используйте вместо этого `ColumnWidget`. Он выстраивает дочерние элементы вертикально, не оборачивая их в стилизованную карточку.

### Fieldsets

`FieldsetWidget` группирует поля во многом так же, как `PanelWidget`, но вместо стилизованной карточки отображает нативные HTML-элементы `<fieldset>` и `<legend>`. Используйте его, когда нужна более простая группировка с рамкой.

```python
from starlette_admin import FieldsetWidget

form_layout = [
    FieldsetWidget(
        legend="Identity",
        children=[("first_name", "last_name"), "email"],
    ),
    FieldsetWidget(
        legend="Compensation",
        children=["salary", "notes"],
        disabled=True,
    ),
]
```

Атрибут `legend` задаёт подпись в элементе `<legend>`. Значение `disabled=True` устанавливает HTML-атрибут `disabled` на контейнере, что отключает все вложенные элементы управления формы. `FieldsetWidget` поддерживает ту же сокращённую запись для `children`, что и `PanelWidget`, но не поддерживает специфичные для панелей опции, такие как `collapsible` и `icon`.

## Явная ширина колонок

Сокращённая запись через кортеж всегда делит строку поровну. Для более точного управления шириной колонок соберите строку явно с помощью `RowWidget`, `Col` и `FieldRef`:

```python
from starlette_admin import Breakpoints, Col, FieldRef, RowWidget

form_layout = [
    RowWidget(
        children=[
            Col(FieldRef("first_name"), Breakpoints(default=12, md=4)),
            Col(FieldRef("last_name"), Breakpoints(default=12, md=8)),
        ]
    ),
]
```

## Скрытие подписей полей

Явное создание `FieldRef` даёт доступ к параметру `show_label`, который убирает элемент `<label>`, когда окружающий макет уже делает назначение поля очевидным.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

Параметр `show_label` по умолчанию равен `True`. Строковая и кортежная сокращённые записи всегда отображают подписи, поскольку не принимают именованных аргументов.

## Группы ввода

Параметры `prepend` и `append` прикрепляют [дополнение группы ввода](https://docs.tabler.io/ui/forms/form-elements#input-group) к любой из сторон поля ввода. Каждый из них принимает обычный текст или сырой HTML, например иконку Font Awesome.

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Дополнения работают с полями, чей шаблон формы отображает нативный элемент `<input>`: `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, числовые поля (`IntegerField`, `DecimalField`, `FloatField`) и поля даты и времени. Другие типы, такие как `EnumField`, `TextAreaField` и `BooleanField`, молча игнорируют их.

!!! warning
    Значения дополнений отображаются без экранирования, чтобы работал HTML вроде разметки иконок. Передавайте только доверенный контент, написанный вами самостоятельно, но никогда — пользовательский ввод.

## Вкладки

Чтобы разбить разделы на интерфейс с вкладками, используйте `TabsWidget`. Он принимает список пар `(label, widgets)`.

```python
from starlette_admin import TabsWidget

form_layout = [
    TabsWidget(
        tabs=[
            ("Identity", [("first_name", "last_name"), "email"]),
            ("Compensation", ["salary", "notes"]),
        ]
    ),
]
```

## Статический контент

Используйте `HtmlWidget` и `TextWidget`, чтобы отобразить произвольный контент в любом месте макета: инструкции, предупреждения или разделители.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Собственные виджеты

Поскольку `form_layout` использует ту же иерархию `BaseWidget`, что и дашборды, вы можете создать подкласс `BaseWidget`, чтобы построить собственные элементы. Это «аварийный люк» для всего, чего не покрывают встроенные виджеты: превью только для чтения, встроенных диаграмм или собственных макросов Jinja.

Общий шаблон описан в разделе [Custom Views & Widgets](../user-guide/custom-views.md), а методы, которые может переопределить подкласс, — в [справочнике API виджетов](../api/widgets.md). Собственные виджеты в `form_layout` отображаются всегда, независимо от правил видимости полей.

## Контроль доступа и видимость

`form_layout` учитывает ваши правила доступа на уровне полей. Каждый `FieldRef` проходит стандартную проверку `can_access_field`, а `exclude_from_create`, `exclude_from_edit` и права доступа на основе ролей продолжают действовать.

* **Расширение строки:** если поле в многоколоночной строке скрыто для запроса, оставшиеся видимые поля расширяются, заполняя освободившееся место.
* **Пустые контейнеры:** если все поля в контейнере (строке, панели, fieldset, колонке, сетке или вкладке) скрыты, контейнер не отображается вовсе, поэтому пустой оболочки никогда не будет.
* **Статическое отображение:** статические компоненты, такие как `HtmlWidget`, `TextWidget` и собственные подклассы `BaseWidget`, отображаются всегда, поскольку не зависят от полей формы.

## Обработка пропущенных полей

Поле, объявленное в `fields`, но не включённое в `form_layout`, добавляется в конец формы в порядке объявления, поэтому ни одно поле не теряется незаметно.

Повторное указание одного и того же поля или ссылка на имя, отсутствующее в `fields`, вызывают исключение `ValueError` при создании представления.

---

## Что дальше

* **[Custom Views & Widgets](../user-guide/custom-views.md):** иерархия виджетов, на которой строится `form_layout`, и то, как написать собственный виджет.
* **[Templates](templates.md):** переопределите `_form_group.html`, чтобы изменить разметку, которую отображает группа макета.
* **[Fields](../user-guide/fields.md):** типы полей и правила видимости, которые упорядочивает макет.

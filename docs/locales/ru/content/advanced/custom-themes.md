---
title: Пользовательские темы
description: Переопределяйте CSS-переменные Tabler, подключайте собственные таблицы
  стилей и меняйте общий внешний вид панели starlette-admin.
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# Пользовательские темы

Вы можете изменить оформление административной панели с помощью настроек темы, пользовательских шаблонов и статических файлов. `DefaultTheme` управляет внешним видом по умолчанию, записывая data-атрибуты в тег `<html>` на основе объекта `TablerSettings`. Для более глубоких изменений создайте подкласс `BaseTheme`, чтобы объединить собственные шаблоны, статические ресурсы и наборы иконок, либо передайте свои каталоги шаблонов и статических файлов в `Admin`.

## Применение темы

Используйте `TablerSettings`, чтобы задать цветовую палитру, радиус скругления и цветовой режим. Передайте его в `DefaultTheme`, а затем передайте полученный объект в параметр `theme` вашего экземпляра `Admin`.

```python
from myapp.models import Post
from sqlalchemy import create_engine
from starlette_admin.theme import DefaultTheme, TablerSettings
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///admin.sqlite")

admin = Admin(
    engine,
    title="My Admin",
    theme=DefaultTheme(
        settings=TablerSettings(base="slate", primary="blue", radius=2, mode="dark")
    ),
)
admin.add_view(ModelView(Post))
```

Пример работающего приложения, которое выбирает случайную тему при каждом запуске, можно найти в [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes).

Эта конфигурация применяет атрибуты `data-bs-theme*` непосредственно к корневому элементу `<html>`:

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## Справочник по `TablerSettings`

| Атрибут | Тип | По умолчанию | Допустимые значения |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Изменение оформления компонентов с помощью карты классов {#изменение-оформления-компонентов-с-помощью-карты-классов}

Базовые шаблоны не содержат жестко закодированного оформления компонентов. Они формируют атрибуты классов через Jinja-хелпер `cls('role.name')`, который преобразует семантическую роль, например `form.save_button` или `list.table`, в строку CSS-классов. Значение по умолчанию для каждой роли определено в `starlette_admin.theme.CoreClasses`.

Чтобы изменить оформление роли, напишите подкласс `ClassMap`. Любая роль, которую вы не переопределите, будет использовать значение из `CoreClasses`, поэтому частичные переопределения безопасны. Учтите: роль кнопки задаёт весь атрибут class элемента, включая вариант, размер и отступы, поэтому её переопределение полностью заменяет внешний вид кнопки.

Карты классов не требуют создания полноценной пользовательской темы. Чтобы настроить тему по умолчанию, создайте подкласс `DefaultTheme` и возвращайте свою карту из метода `get_class_map()`:

```python
from starlette_admin.theme import ClassMap, DefaultTheme


class MyClasses(ClassMap):
    classes = {
        # Rounded success save button instead of the default primary one
        "form.save_button": "btn btn-success rounded-pill",
        # Outline create button on the list toolbar
        "list.create_button": "btn btn-outline-primary ms-2",
        # Pill-shaped filter chips
        "filter.chip": "badge rounded-pill bg-primary-subtle",
    }


class MyTheme(DefaultTheme):
    def get_class_map(self) -> ClassMap:
        return MyClasses()


admin = Admin(engine, title="My Admin", theme=MyTheme())
```

Полный перечень ролей можно найти в `CoreClasses.classes` в файле `starlette_admin/theme.py`. Роли охватывают три вида оформления:

* **Кнопки:** одна роль для каждого расположения кнопки — футеры форм, панели инструментов списка, панели фильтров, модальные окна действий и встроенное редактирование. Заданное вами значение становится всем атрибутом class кнопки.
* **Классы компонентов:** специфичные для framework классы, которые необходимо заменять при использовании другого CSS-framework, например `list.table`, `modal.base` или `filter.chip`.
* **Runtime-классы:** классы, которые базовый JavaScript применяет динамически, например `alert.success` или `import.status_badge`.

## Создание и распространение пользовательских тем

Тему можно упаковать и опубликовать на PyPI — так же, как plugin. Создайте подкласс `BaseTheme`, чтобы собрать переиспользуемый Python-пакет, который заменяет макет и оформление панели сразу в нескольких проектах, или чтобы поделиться визуальной системой с другими разработчиками.

### Скаффолдинг с помощью Cookiecutter

Начните с официального cookiecutter-шаблона. Он генерирует готовый к публикации пакет с правильной структурой каталогов и конфигурационными файлами.

Установите `cookiecutter` с помощью вашего пакетного менеджера. Подробности см. в [официальном руководстве по установке](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter

```

Затем запустите шаблон из любого каталога:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

Шаблон запросит у вас название темы, slug пакета, версию и несколько других переменных. После завершения вы получите самодостаточный пакет со следующим содержимым:

* Каталог `src/` с классом темы, набором иконок и картой классов.
* Предварительно настроенные каталоги `templates/`, `static/` и папки переводов.
* Набор тестов и пример работающего приложения.

### Архитектура `BaseTheme`

Тема находится в корне цепочки рендеринга, и у каждого экземпляра `Admin` активна ровно одна тема. Подкласс `BaseTheme` настраивает следующие компоненты:

* **Шаблоны:** замещающие шаблоны в каталоге `templates/` пакета, использующие простые относительные пути, такие как `base.html`, `layout.html` или `list.html`. Активная тема стоит выше plugins в цепочке загрузчика Jinja, поэтому она может изменять оформление как базовых, так и plugin-шаблонов.
* **Статические ресурсы:** таблицы стилей, скрипты и изображения в каталоге `static/` пакета.
* **Набор иконок:** пользовательский подкласс `IconSet`, возвращаемый методом `get_icon_set()`, который сопоставляет семантические ключи, например `list.new` или `auth.logout`, с CSS-классами.
* **Карта классов:** подкласс `ClassMap`, возвращаемый методом `get_class_map()`, как описано в разделе [Изменение оформления компонентов с помощью карты классов](#изменение-оформления-компонентов-с-помощью-карты-классов).
* **Глобальные переменные шаблонов:** глобальные переменные, доступные Jinja, определяются путём переопределения метода `template_globals()`.

### Пример пакета темы

```python
from typing import Any
from starlette_admin.theme import BaseTheme, ClassMap, IconSet


class CustomIconSet(IconSet):
    icons = {
        "list.new": "hi hi-plus",
        "default_actions.view": "hi hi-eye",
        # Map remaining semantic icon keys
    }


class CorporateClasses(ClassMap):
    classes = {
        "form.save_button": "btn btn-corporate",
        # Map remaining roles to restyle; unmapped roles keep core defaults
    }


class CorporateTheme(BaseTheme):
    name = "corporate"
    package = "corporate_theme_package"  # Auto-detected from class module if omitted

    def get_icon_set(self) -> IconSet:
        return CustomIconSet()

    def get_class_map(self) -> ClassMap:
        return CorporateClasses()

    def template_globals(self) -> dict[str, Any]:
        return {"company_name": "Acme Corp"}
```

### Иерархия загрузчика шаблонов

Шаблонный движок разрешает файлы в следующем порядке:

1. Ваш `templates_dir`, который переопределяет всё, что ниже.
2. Каталог `templates/` активной темы, который изменяет оформление базовых и plugin-шаблонов.
3. Шаблоны `templates/` в namespace каждого plugin.
4. Базовые шаблоны `starlette-admin` по умолчанию.

Чтобы расширить шаблон темы из пользовательского переопределения или подкласса темы, используйте префикс `@theme` в Jinja, например `{% extends "@theme/layout.html" %}`.

## Пользовательский каталог шаблонов

Чтобы переопределить HTML по умолчанию без создания полноценной темы, передайте путь к каталогу в `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Любой файл, помещённый в этот каталог, перекрывает встроенный шаблон с тем же относительным путём, а остальная часть встроенного дерева продолжает рендериться как прежде. Полный список переопределяемых шаблонов см. в разделе [Шаблоны](templates.md).

## Пользовательский каталог статических файлов

Чтобы добавить собственные CSS, JavaScript или изображения без создания полноценной темы, передайте путь к каталогу в `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Файлы из этого каталога раздаются вместе со встроенными ресурсами по пути `/admin/static/`. Например, файл `my_static/custom.css` становится доступным по адресу `/admin/static/custom.css`.

Подключите таблицу стилей в своих шаблонах следующим образом:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## Что дальше

* **[Шаблоны](templates.md):** переопределяйте отдельную страницу, ячейку или widget, не форкая всё дерево шаблонов.
* **[Точки расширения](extension-points.md):** изучите hooks и точки кастомизации за пределами базовых тем.
* **[Быстрый старт](../getting-started/quickstart.md):** создайте работающий административный интерфейс с нуля.

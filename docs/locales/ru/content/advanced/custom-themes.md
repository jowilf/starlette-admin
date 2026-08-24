---
title: Пользовательские темы
description: Переопределяйте CSS-переменные Tabler, подключайте собственные стили
  и меняйте внешний вид дашборда starlette-admin.
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# Пользовательские темы

Вы можете изменить оформление панели администрирования с помощью настроек темы, пользовательских шаблонов и статических файлов. `DefaultTheme` управляет внешним видом по умолчанию, записывая data-атрибуты в тег `<html>` на основе объекта `TablerSettings`. Для более глубоких изменений создайте подкласс `BaseTheme`, чтобы объединить собственные шаблоны, статические ресурсы и наборы значков, либо передайте свои каталоги шаблонов и статических файлов в `Admin`.

## Применение темы

Используйте `TablerSettings`, чтобы задать цветовую палитру, радиус скругления углов и цветовой режим. Передайте его в `DefaultTheme`, а затем передайте тему в параметр `theme` экземпляра `Admin`.

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

См. [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes) — там находится работающее приложение, которое выбирает случайную тему при каждом запуске.

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

## Изменение стиля компонентов с помощью карты классов {#restyling-components-with-a-class-map}

Базовые шаблоны не задают стили компонентов жёстко. Они формируют атрибуты классов через Jinja-хелпер `cls('role.name')`, который преобразует семантическую роль, например `form.save_button` или `list.table`, в строку CSS-классов. Значение по умолчанию для каждой роли находится в `starlette_admin.theme.CoreClasses`.

Чтобы изменить стиль роли, создайте подкласс `ClassMap`. Любая роль, которую вы не переопределите, откатывается к `CoreClasses`, поэтому частичные переопределения безопасны. Учтите: роль кнопки задаёт весь атрибут class элемента, включая вариант, размер и отступы, поэтому её переопределение полностью заменяет внешний вид кнопки.

Карты классов не требуют полноценной пользовательской темы. Чтобы настроить тему по умолчанию, создайте подкласс `DefaultTheme` и верните свою карту из метода `get_class_map()`:

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

Полный перечень ролей смотрите в `CoreClasses.classes` в файле `starlette_admin/theme.py`. Роли охватывают три вида стилей:

* **Кнопки:** одна роль для каждого расположения кнопки — подвалы форм, панели инструментов страницы списка, панели фильтров, модальные окна действий и инлайн-редактирование. Заданное значение становится всем атрибутом class кнопки.
* **Классы компонентов:** классы конкретного CSS-фреймворка, которые нужно заменить при переходе на другой фреймворк, например `list.table`, `modal.base` или `filter.chip`.
* **Динамические классы:** классы, которые базовый JavaScript применяет во время выполнения, например `alert.success` или `import.status_badge`.

## Создание и публикация пользовательских тем

Тему можно упаковать и опубликовать на PyPI так же, как плагин. Создайте подкласс `BaseTheme`, чтобы собрать переиспользуемый Python-пакет, который заменяет компоновку и стили панели администрирования в нескольких проектах, или чтобы поделиться визуальной системой с другими людьми.

### Каркас проекта с Cookiecutter

Начните с официального шаблона cookiecutter. Он генерирует публикуемый пакет с правильной структурой каталогов и файлами конфигурации.

Установите `cookiecutter` с помощью вашего пакетного менеджера. Подробности см. в [официальном руководстве по установке](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter

```

Затем запустите шаблон из любого каталога:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

Шаблон запросит название темы, слаг пакета, версию и ещё несколько переменных. Когда он завершит работу, вы получите самодостаточный пакет со следующим содержимым:

* Каталог `src/` с классом темы, набором значков и картой классов.
* Предварительно настроенные папки `templates/`, `static/` и переводов.
* Набор тестов и работающий пример приложения.

### Архитектура `BaseTheme`

Тема находится в корне цепочки рендеринга, и у каждого экземпляра `Admin` активна ровно одна тема. Подкласс `BaseTheme` настраивает следующие компоненты:

* **Шаблоны:** замещающие шаблоны в папке `templates/` пакета, использующие простые относительные пути, например `base.html`, `layout.html` или `list.html`. Активная тема стоит выше плагинов в цепочке загрузчика Jinja, поэтому может изменять стиль как базовых, так и плагинных шаблонов.
* **Статические ресурсы:** таблицы стилей, скрипты и изображения в каталоге `static/` пакета.
* **Набор значков:** пользовательский подкласс `IconSet`, возвращаемый из `get_icon_set()`, который сопоставляет семантические ключи, например `list.new` или `auth.logout`, с CSS-классами.
* **Карта классов:** подкласс `ClassMap`, возвращаемый из `get_class_map()`, как описано в разделе [Изменение стиля компонентов с помощью карты классов](#restyling-components-with-a-class-map).
* **Глобальные переменные шаблонов:** глобальные переменные, доступные Jinja, которые определяются переопределением метода `template_globals()`.

### Пример пакета с темой

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

Шаблонизатор разрешает файлы в следующем порядке:

1. Ваш `templates_dir`, который переопределяет всё, что ниже.
2. Каталог `templates/` активной темы, который изменяет стиль базовых и плагинных шаблонов.
3. Каталоги `templates/` плагинов с пространствами имён.
4. Базовые шаблоны по умолчанию из `starlette_admin`.

Чтобы расширить шаблон темы из пользовательского переопределения или подкласса темы, используйте префикс Jinja `@theme`, например `{% extends "@theme/layout.html" %}`.

## Пользовательский каталог шаблонов

Чтобы переопределить HTML по умолчанию без создания полноценной темы, передайте путь к каталогу в `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Любой файл в этом каталоге затеняет встроенный шаблон с тем же относительным путём, а остальная часть встроенного дерева продолжает рендериться как раньше. Полный список переопределяемых шаблонов см. в разделе [Шаблоны](templates.md).

## Пользовательский каталог статических файлов

Чтобы добавить собственные CSS-, JavaScript-файлы или изображения без создания полноценной темы, передайте путь к каталогу в `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Файлы из этого каталога раздаются вместе со встроенными ресурсами по пути `/admin/static/`. Например, файл `my_static/custom.css` становится доступен по адресу `/admin/static/custom.css`.

Подключите таблицу стилей в своих шаблонах так:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## Что дальше

* **[Шаблоны](templates.md):** переопределяйте отдельную страницу, ячейку или виджет, не форкая всё дерево шаблонов.
* **[Точки расширения](extension-points.md):** изучите хуки и точки кастомизации помимо базовых тем.
* **[Быстрый старт](../getting-started/quickstart.md):** создайте работающий интерфейс администрирования с нуля.

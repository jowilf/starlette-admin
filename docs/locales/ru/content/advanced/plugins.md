---
title: Плагины
description: Упаковывайте переиспользуемые функции и расширения панели администрирования
  в подключаемые плагины для starlette-admin.
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# Плагины

Плагин — это Python-пакет, который расширяет `starlette-admin` через один аргумент конструктора. Плагин может объединять любые комбинации полей, шаблонов, статических ресурсов, конвертеров моделей, фильтров, форматов импорта/экспорта, бэкендов хранилищ, подписчиков событий, представлений, маршрутов, middleware, ресурсов тем и каталогов переводов.

## Использование плагина

Передавайте плагины через аргумент `plugins` при создании экземпляра `Admin`:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

Конструктор плагина принимает параметры, а список передаётся напрямую в `Admin`. Больше ничего настраивать или регистрировать не нужно. Параметры передаются от конструктора вниз — в Python-бэкенд, шаблоны Jinja и фронтенд на JavaScript.

## Создание плагина

Чтобы написать плагин, начните с официального шаблона cookiecutter. Он генерирует публикуемый пакет с правильной структурой каталогов и конфигурацией.

### Предварительные требования

Установите `cookiecutter` с помощью вашего пакетного менеджера. Подробности см. в [официальном руководстве по установке](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter
```

### Скаффолдинг

Запустите шаблон cookiecutter из любого каталога:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

Шаблон запросит у вас имя плагина, слаг пакета, версию и несколько других переменных. По завершении вы получите самодостаточный пакет со следующим содержимым:

* Каталог `src/` с классом вашего плагина и полями.
* Правильно именованные каталоги `templates/`, `static/` и `translations/`.
* Полный набор тестов.
* Запускаемый пример приложения.

## API плагина

В основе каждого плагина лежит подкласс `BasePlugin` (`starlette_admin.plugins.BasePlugin`), который предоставляет хуки для регистрации ваших функций во время инициализации `Admin`.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

Атрибут `name` — это уникальный идентификатор в kebab-case, который одновременно служит пространством имён для ваших шаблонов и статических ресурсов. Каждый шаблон и каждый статический файл, поставляемые с вашим плагином, должны находиться внутри `plugins/<name>/`.

### Каталоги ресурсов

Плагин может содержать ровно три каталога в корне своего пакета. Регистрировать их не нужно, потому что панель администрирования находит их по соглашению:

* `templates/`: шаблоны Jinja, которые должны располагаться в `templates/plugins/<name>/`.
* `static/`: статические ресурсы, такие как CSS- и JS-файлы, которые должны располагаться в `static/plugins/<name>/`.
* `translations/`: каталоги переводов Babel.

Если оставаться внутри пространства имён `plugins/<name>/`, ваши ресурсы не будут конфликтовать с основными файлами или другими плагинами, при этом их можно будет переопределить через собственные `templates_dir` или `static_dir` пользователя.

### Декларативные хуки

Переопределяйте декларативные хуки, чтобы добавлять ресурсы, регистрировать представления или монтировать маршруты.

* `css_links(self, request: Request) -> Sequence[str]`: добавляет таблицы стилей в компоновку каждой страницы панели администрирования.
* `js_links(self, request: Request) -> Sequence[str]`: добавляет скрипты в компоновку каждой страницы панели администрирования.
* `views(self) -> Sequence[BaseView]`: возвращает представления для регистрации в боковой панели панели администрирования. Верните `DropDown`, чтобы сгруппировать их.
* `routes(self) -> Sequence[Route | Mount]`: возвращает эндпоинты без интерфейса, монтируемые по пути `/plugins/<name>/` — это удобно для вебхуков и прокси-эндпоинтов.
* `middlewares(self) -> Sequence[Middleware]`: добавляет middleware Starlette.
* `template_globals(self) -> dict[str, Any]`: предоставляет глобальные переменные Jinja с префиксом `<name>_`, чтобы исключить конфликты имён.
* `template_filters(self) -> dict[str, Callable]`: предоставляет фильтры Jinja с таким же префиксом `<name>_`.

### Хук setup

`setup(self, admin: BaseAdmin) -> None` интегрирует ваш плагин с основными реестрами. Используйте его для регистрации конвертеров моделей, фильтров, форматов импорта и экспорта, бэкендов хранилищ и подписчиков событий. Он выполняется после применения декларативных хуков.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### Хук жизненного цикла

`on_mount(self, admin: BaseAdmin) -> None` выполняется ровно один раз после сборки и монтирования субприложения Starlette. Собранное приложение доступно как `admin.app`.

## Шаблоны и переопределения

Шаблоны плагина автоматически включаются в цепочку загрузчиков. Пользователь переопределяет шаблон, помещая файл по соответствующему пути в свой `templates_dir`, который всегда имеет приоритет. Например, чтобы переопределить `plugins/geospatial/fields/form/point.html`, пользователь создаёт файл `templates_dir/plugins/geospatial/fields/form/point.html`.

Чтобы пользовательское переопределение могло безопасно расширять оригинал, каждому плагину назначается префикс-маппинг `@<name>`, работающий так же, как префикс `@core`. Переопределение начинается с `{% extends "@geospatial/fields/form/point.html" %}` и расширяет базовый шаблон плагина без рекурсивного включения самого себя.

## Интеграция фронтенда на JavaScript

Плагин, поставляющий пользовательские поля, должен упаковывать свои фронтенд-скрипты в соответствии с контрактом инициализатора полей. Это гарантирует их работу как при полной загрузке страницы, так и при динамической вставке фрагментов.

* **Работайте локально:** выполняйте поиск внутри переданного вам элемента `container`, а не глобального `document`.
* **Соблюдайте идемпотентность:** ядро запускает инициализатор при готовности DOM и повторно всякий раз, когда вставляет строки инлайн-редактирования или фрагменты.
* **Используйте data-атрибуты:** читайте конфигурацию из атрибутов `data-*`, отрисованных на элементе поля.

```javascript title="plugins/<name>/js/slider.js"
(function () {
  function initSlider(container) {
    var input = container.querySelector('input[type="range"]');
    var output = container.querySelector(".sa-slider-output");
    var suffix = container.dataset.suffix || "";

    input.addEventListener("input", function () {
      output.textContent = input.value + suffix;
    });
  }

  // Register the initializer so core runs it on the right lifecycle events
  window.StarletteAdmin.registerFieldInitializer(function (element) {
    element.querySelectorAll("[data-sa-slider]").forEach(initSlider);
  });
})();
```

## Точки расширения через хук setup

Плагины используют существующие публичные реестры, а не отдельный механизм расширения.

* **Конвертеры**: вызовите `register_converter` из целевого contrib-бэкенда, чтобы сопоставить типы столбцов ORM с вашими классами полей. Само поле определите как обычный подкласс `StringField`, сохраняя и отображая геометрии в виде текста WKT:

  ```python
  from dataclasses import dataclass
  from typing import Any

  from starlette_admin.contrib.sqla.converters import register_converter
  from starlette_admin.fields import StringField


  @dataclass
  class MyGeoField(StringField):
    ...


  @register_converter("Geometry")
  def convert_geometry(*args: Any, **kwargs: Any) -> MyGeoField:
      return MyGeoField(*args, **kwargs)
  ```

* **Фильтры**: вызовите `register_filters`, чтобы привязать классы фильтров к типу поля.

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Хранилища**: вызовите `register_storage`, чтобы добавить новый бэкенд, например Azure или GCS.

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Импортёры и экспортёры**: используйте `register_import_format` и `register_export_format`.

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

Плагин может поддерживать несколько ORM-бэкендов, поэтому импортируйте их условно внутри `setup()`. Тогда плагин продолжит загружаться, даже если пользователь установил только один из них:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## Что дальше

* **[Пользовательские темы](custom-themes.md):** упаковывайте и делитесь полноценными визуальными системами с помощью того же процесса на основе cookiecutter.
* **[События](events.md):** API подписчиков, который плагин регистрирует в своём хуке `setup()`.
* **[Точки расширения](extension-points.md):** все реестры и базовые классы, которые может использовать плагин.

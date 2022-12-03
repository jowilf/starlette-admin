# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2022-12-02

---

### Fixed

* Fix Datatables warning when primary key is not included in `fields` by [@jowilf](https://github.com/jowilf) in [#23](https://github.com/jowilf/starlette-admin/issues/23)

### Docs

* Add spanish translation for `docs/index.md` by [@rafnixg](https://github.com/rafnixg) in [#35](https://github.com/jowilf/starlette-admin/pull/35)

### Internals

* Use Ruff for linting by [@jowilf](https://github.com/jowilf) in [#29](https://github.com/jowilf/starlette-admin/pull/29)
* Migrate to Hatch by [@jowilf](https://github.com/jowilf) in [#30](https://github.com/jowilf/starlette-admin/pull/30)
* Setup pre-commit by [@jowilf](https://github.com/jowilf) in [#33](https://github.com/jowilf/starlette-admin/pull/33)
* Add support for Python 3.11 in test suite by [@jowilf](https://github.com/jowilf) in [#34](https://github.com/jowilf/starlette-admin/pull/34)


## [0.3.1] - 2022-11-22

---

### Fixed

* Fix Regression on SQLModel backend: Duplicate instances when creating or updating a model with relationships in [#23](https://github.com/jowilf/starlette-admin/issues/23)


## [0.3.0] - 2022-11-21

---

### Breaking Changes

* Changes in `ModelView` definition

=== "Now"
    ```python
    class Post:
        id: int
        title: str

    admin.add_view(ModelView(Post, icon="fa fa-blog", label = "Blog Posts"))
    ```

=== "Before"
    ```python
    class Post:
        id: int
        title: str


    class PostView(ModelView, model=Post):
        icon = "fa fa-blog"
        label = "Blog Posts"

    admin.add_view(PostView)
    ```

* Changes in `CustomView` definition

=== "Now"
    ```python
    admin.add_view(CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"))
    ```
=== "Before"
    ```python
    class HomeView(CustomView):
        label = "Home"
        icon = "fa fa-home"
        path = "/home"
        template_path = "home.html"

    admin.add_view(HomeView)
    ```

* Changes in `Link` definition
=== "Now"
    ```python
    admin.add_view(Link(label="Back to Home", icon="fa fa-home", url="/", target = "_blank"))
    ```

=== "Before"
    ```python
    class BackToHome(Link):
        label = "Back to Home"
        icon = "fa fa-home"
        url = "/"
        target = "_blank"
    ```

These changes are inspired from *Flask-admin* and are introduced to help reduce code size and keep it simple.

### Added

* Add `CollectionField`
* Add `ListField`
* Add support for [Odmantic](https://art049.github.io/odmantic/)
* Add support for datatables [responsive extensions](https://datatables.net/extensions/responsive/)
!!! usage
    ```python
    class MyModelView(ModelView):
        responsive_table = True
    ```

### Changed

* Move `SQLModel` to it own contrib package
* MongoEngine `EmbeddedDocumentField` is now converted into `CollectionField`

### Removed

* Remove PDF from default `export_types`

## [0.2.2] - 2022-09-20

---

### Fixed

*  Null support for EnumField in [#17](https://github.com/jowilf/starlette-admin/pull/17)


## [0.2.1] - 2022-09-19

---

### Fixed

* Fix SearchBuilder not working with dates (SQLAlchemy) in [#15](https://github.com/jowilf/starlette-admin/pull/15)


## [0.2.0] - 2022-09-14

---

### Changed

* Date & Time input now use Flatpickr in [#10](https://github.com/jowilf/starlette-admin/pull/10)


## [0.1.1] - 2022-09-09

---

### Added

- Add `ColorField` in [#7](https://github.com/jowilf/starlette-admin/pull/7)
- AsyncEngine support for SQLAlchemy in [#8](https://github.com/jowilf/starlette-admin/pull/8)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.5] - 2023-03-06

### Fixed

* Fix [#116](https://github.com/jowilf/starlette-admin/issues/116) : Internal Server Error when login credentials are wrong by [@jowilf](https://github.com/jowilf) in [#117](https://github.com/jowilf/starlette-admin/pull/117)

## [0.5.4] - 2023-03-03

### Fixed

* Fix [#99](https://github.com/jowilf/starlette-admin/issues/99) : Show error message when an error occur on `delete` action (detail view).

### Added

* Display meaningfully error message when SQLAlchemyError occur during action execution by [@jowilf](https://github.com/jowilf) and [@dolamroth](https://github.com/dolamroth) in [#105](https://github.com/jowilf/starlette-admin/pull/105)

## [0.5.3] - 2023-02-25

### Fixed

* Fix Bug with SQLAlchemy column converters by [@jowilf](https://github.com/jowilf) in [#103](https://github.com/jowilf/starlette-admin/pull/103)

## [0.5.2] - 2022-12-29

### Fixed

* Fix Bug with `search_format` params for [DateField][starlette_admin.fields.DateField] and [TimeField][starlette_admin.fields.TimeField] by [@jowilf](https://github.com/jowilf) & [@ihuro](https://github.com/ihuro) in [#68](https://github.com/jowilf/starlette-admin/pull/68) & [#71](https://github.com/jowilf/starlette-admin/pull/71)

## [0.5.1] - 2022-12-27

### Fixed

* Fix Bug with `sqlalchemy.dialects.postgresql.base.UUID` column by [@jowilf](https://github.com/jowilf) in [#65](https://github.com/jowilf/starlette-admin/pull/65)

## [0.5.0] - 2022-12-17

### Added

* Introduce [`AdminUser`][starlette_admin.auth.AuthProvider.get_admin_user] and add navbar to show the current [`AdminUser`][starlette_admin.auth.AuthProvider.get_admin_user] information (`username` and `photo`) by [@jowilf](https://github.com/jowilf) in [#49](https://github.com/jowilf/starlette-admin/pull/49)

### Internals

* Add auth example by [@jowilf](https://github.com/jowilf) in [#51](https://github.com/jowilf/starlette-admin/pull/51)

## [0.4.0] - 2022-12-07

---

### Added

* Custom batch actions by [@jowilf](https://github.com/jowilf) in [#44](https://github.com/jowilf/starlette-admin/pull/44)
* Add `get_list_query`, `get_count_query` and `get_search_query` methods to SQLAlchemy backend that can be inherited for customization by [@jowilf](https://github.com/jowilf) in [#47](https://github.com/jowilf/starlette-admin/pull/47)

### Internals

* Update datatables to `1.13.1`
* Update Search builder UI to fit tabler design

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

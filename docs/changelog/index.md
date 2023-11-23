# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.12.2] - 2023-11-13

* Fixed issue where "Empty" and "Not Empty" filters raised NotImplementedError on SQLAlchemy relationship attributes
  by [@whchi](https://github.com/whchi) in [#394](https://github.com/jowilf/starlette-admin/pull/394)

## [0.12.1] - 2023-11-07

* Fixed a regression caused by [#361](https://github.com/jowilf/starlette-admin/pull/361) where SQLAlchemy models with
  Mixin Classes raises AttributeError by [@hasansezertasan](https://github.com/hasansezertasan)
  in [#385](https://github.com/jowilf/starlette-admin/pull/385)

## [0.12.0] - 2023-11-07

### Added

* Add Before and After Hooks for Create, Edit, and Delete Operations by [@jowilf](https://github.com/jowilf)
  in [#327](https://github.com/jowilf/starlette-admin/pull/327)
* Feature: Row actions by [@jowilf](https://github.com/jowilf) & [@mrharpo](https://github.com/mrharpo)
  in [#348](https://github.com/jowilf/starlette-admin/pull/348)
  and [#302](https://github.com/jowilf/starlette-admin/pull/302)
* Add Support for Custom Sortable Field Mapping in SQLAlchemy ModelView by [@jowilf](https://github.com/jowilf)
  in [#328](https://github.com/jowilf/starlette-admin/pull/328)

???+ usage

    ```python hl_lines="12"
    class Post(Base):
        __tablename__ = "post"

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str] = mapped_column()
        user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
        user: Mapped[User] = relationship(back_populates="posts")

    class PostView(ModelView):
        sortable_field = ["id", "title", "user"]
        sortable_field_mapping = {
            "user": User.age,  # Sort by the age of the related user
        }
    ```

* Add support for Turkish language by [@hasansezertasan](https://github.com/hasansezertasan)
  in [#330](https://github.com/jowilf/starlette-admin/pull/330) & [#377](https://github.com/jowilf/starlette-admin/pull/377).
* Allow the page title customization from the ModelView by [@mrharpo](https://github.com/mrharpo)
  in [#311](https://github.com/jowilf/starlette-admin/pull/311)
* Add support for custom DataTables options by [@mrharpo](https://github.com/mrharpo)
  in [#308](https://github.com/jowilf/starlette-admin/pull/308)
* Add support for datatables [state saving](https://datatables.net/examples/basic_init/state_save.html)

???+ usage

    ```python
    class MyModelView(ModelView):
        save_state = True
    ```

### Fixed

* Fix [#347](https://github.com/jowilf/starlette-admin/issues/347): Detect SQLAlchemy primary key with custom column
  name by [@jowilf](https://github.com/jowilf)
  in [#361](https://github.com/jowilf/starlette-admin/pull/361)

* Fixed a bug with field access authorization where restricted users could not modify a partial list of fields in an
  entity by [@jowilf](https://github.com/jowilf) in [#360](https://github.com/jowilf/starlette-admin/pull/360)

### Internals

* Explicitly export all public functions and classes by [@jowilf](https://github.com/jowilf)
  in [#362](https://github.com/jowilf/starlette-admin/pull/362)

## [0.11.2] - 2023-08-31

### Fixed

* Bug Fix: Current Enum Value Not Pre-Selected on Edit by [@jowilf](https://github.com/jowilf)
  in [#273](https://github.com/jowilf/starlette-admin/pull/273)

## [0.11.1] - 2023-07-29

### Fixed

* Bug Fix: Ensure Excluded fields from a RequestAction are not treated by [@jowilf](https://github.com/jowilf)
  in [#251](https://github.com/jowilf/starlette-admin/pull/251)

## [0.11.0] - 2023-07-26

### Added

* Improve the Authentication Provider to support custom flow such as oauth2/OIDC by [@jowilf](https://github.com/jowilf)
  in [#221](https://github.com/jowilf/starlette-admin/pull/221).

### Internals

* Drop python 3.7 support by [@jowilf](https://github.com/jowilf)
  in [#248](https://github.com/jowilf/starlette-admin/pull/248)

## [0.10.1] - 2023-07-22

### Fixed

* Fix [#224](https://github.com/jowilf/starlette-admin/issues/224) by [@jowilf](https://github.com/jowilf)
  in [#227](https://github.com/jowilf/starlette-admin/pull/227)
* Fix [#239](https://github.com/jowilf/starlette-admin/issues/239): Order Select2 data by primary key during fetching by
  [@jowilf](https://github.com/jowilf) in [#241](https://github.com/jowilf/starlette-admin/issues/241)

## [0.10.0] - 2023-06-26

### Added

* Added support for Russian language in the web interface by [@nessshon](https://github.com/nessshon)
  in [#201](https://github.com/jowilf/starlette-admin/pull/201)
* i18n: Update message catalogs by [@jowilf](https://github.com/jowilf)
  in [#202](https://github.com/jowilf/starlette-admin/pull/202)
* Support custom response for batch actions by [@jowilf](https://github.com/jowilf)
  in [#212](https://github.com/jowilf/starlette-admin/pull/212)

### Fixed

* Fixed [#206](https://github.com/jowilf/starlette-admin/issues/206): Setting `add_to_menu=False` in CustomView still
  results in the view being displayed in the menu

## [0.9.0] - 2023-05-25

### Added

* Enhance fields conversion logic to support custom converters
  by [@jowilf](https://github.com/jowilf) in [#191](https://github.com/jowilf/starlette-admin/pull/191)
* Add deployment section to documentation by [@jowilf](https://github.com/jowilf)
  in [#195](https://github.com/jowilf/starlette-admin/pull/195)

### Fixed

* Blank Edit Form Displayed for IntegerField with Value 0 by [@jowilf](https://github.com/jowilf)
  in [#194](https://github.com/jowilf/starlette-admin/pull/194)

## [0.8.2] - 2023-05-12

### Added

* Add `allow_paths` parameter to AuthProvider to allow unauthenticated access to specific paths
  by [@jowilf](https://github.com/jowilf)
  in [#187](https://github.com/jowilf/starlette-admin/pull/187)
* Allow Unauthenticated Access to `js.cookie.min.js` by [@mixartemev](https://github.com/mixartemev)
  in [#183](https://github.com/jowilf/starlette-admin/pull/183)

## [0.8.1] - 2023-04-30

### Added

* Update fontawesome to 6.4.0 & add missings webfonts by [@jowilf](https://github.com/jowilf)
  in [#176](https://github.com/jowilf/starlette-admin/pull/176)
* Allow class level configuration for ModelView identity, name & label by [@jowilf](https://github.com/jowilf)
  in [#178](https://github.com/jowilf/starlette-admin/pull/178)

## [0.8.0] - 2023-04-09

### Added

* Add extension to autovalidate SQLAlchemy data with pydantic by [@jowilf](https://github.com/jowilf)
  in [#144](https://github.com/jowilf/starlette-admin/pull/144)
* Make `_extract_fields()` method in BaseModelView public and renamed
  to [get_fields_list()][starlette_admin.views.BaseModelView.get_fields_list] by [@jowilf](https://github.com/jowilf)
  in [#148](https://github.com/jowilf/starlette-admin/pull/148)
* Add support for custom object representations in the admin interface with `__admin_repr__`
  and `__admin_select2_repr__`  by [@jowilf](https://github.com/jowilf)
  in [#152](https://github.com/jowilf/starlette-admin/pull/152). The documentation can be
  found [here](../tutorial/configurations/modelview/#object-representation)

### Internals

* Enhance code quality with additional ruff rules by [@jowilf](https://github.com/jowilf)
  in [#159](https://github.com/jowilf/starlette-admin/pull/159)

## [0.7.0] - 2023-03-24

### Added

* Allow custom form for batch actions by [@giaptx](https://github.com/giaptx) and [@jowilf](https://github.com/jowilf)
  in [#61](https://github.com/jowilf/starlette-admin/pull/61)
* Add [TinyMCEEditorField][starlette_admin.fields.TinyMCEEditorField] by [@sinisaos](https://github.com/sinisaos)
  and [@jowilf](https://github.com/jowilf)
  in [#131](https://github.com/jowilf/starlette-admin/pull/131)

### Internals

* Add SQLAlchemy model with Pydantic validation example [@jowilf](https://github.com/jowilf)
  in [#125](https://github.com/jowilf/starlette-admin/pull/125)
* Refactor and format HTML files for better readability by [@jowilf](https://github.com/jowilf)
  in [#136](https://github.com/jowilf/starlette-admin/pull/136)

## [0.6.0] - 2023-03-12

### Added

* Setup i18n and Add French translations by [@jowilf](https://github.com/jowilf)
  in [#74](https://github.com/jowilf/starlette-admin/pull/74)
*

Add [TimeZoneField][starlette_admin.fields.TimeZoneField], [CountryField][starlette_admin.fields.CountryField], [CurrencyField][starlette_admin.fields.CurrencyField] & [ArrowField][starlette_admin.fields.ArrowField]

* Add support for [sqlalchemy_utils](https://github.com/kvesteri/sqlalchemy-utils) data types
* Add SQLAlchemy 2 support by  [@jowilf](https://github.com/jowilf)
  in [#113](https://github.com/jowilf/starlette-admin/pull/113)
* Add support for initial order (sort) to apply to the table by [@jowilf](https://github.com/jowilf)
  in [#115](https://github.com/jowilf/starlette-admin/pull/115)

!!! usage

    ```python
    class User:
        id: int
        last_name: str
        first_name: str


    class UserView(ModelView):
        fields_default_sort = ["last_name", ("first_name", True)]

    admin.add_view(UserView(User))
    ```

### Fixed

* Fix [#69](https://github.com/jowilf/starlette-admin/issues/69) : Return `HTTP_422_UNPROCESSABLE_ENTITY` when form data
  is not valid

### Deprecated

* `EnumField.from_enum("status", Status)` is deprecated. Use `EnumField("status", enum=Status)` instead.
* `EnumField.from_choices("language", [('cpp', 'C++'), ('py', 'Python')])` is deprecated.
  Use `EnumField("name", choices=[('cpp', 'C++'), ('py', 'Python')])` instead.

## [0.5.5] - 2023-03-06

### Fixed

* Fix [#116](https://github.com/jowilf/starlette-admin/issues/116) : Internal Server Error when login credentials are
  wrong by [@jowilf](https://github.com/jowilf) in [#117](https://github.com/jowilf/starlette-admin/pull/117)

## [0.5.4] - 2023-03-03

### Fixed

* Fix [#99](https://github.com/jowilf/starlette-admin/issues/99) : Show error message when an error occur on `delete`
  action (detail view).

### Added

* Display meaningfully error message when SQLAlchemyError occur during action execution
  by [@jowilf](https://github.com/jowilf) and [@dolamroth](https://github.com/dolamroth)
  in [#105](https://github.com/jowilf/starlette-admin/pull/105)

## [0.5.3] - 2023-02-25

### Fixed

* Fix Bug with SQLAlchemy column converters by [@jowilf](https://github.com/jowilf)
  in [#103](https://github.com/jowilf/starlette-admin/pull/103)

## [0.5.2] - 2022-12-29

### Fixed

* Fix Bug with `search_format` params for [DateField][starlette_admin.fields.DateField]
  and [TimeField][starlette_admin.fields.TimeField]
  by [@jowilf](https://github.com/jowilf) & [@ihuro](https://github.com/ihuro)
  in [#68](https://github.com/jowilf/starlette-admin/pull/68) & [#71](https://github.com/jowilf/starlette-admin/pull/71)

## [0.5.1] - 2022-12-27

### Fixed

* Fix Bug with `sqlalchemy.dialects.postgresql.base.UUID` column by [@jowilf](https://github.com/jowilf)
  in [#65](https://github.com/jowilf/starlette-admin/pull/65)

## [0.5.0] - 2022-12-17

### Added

* Introduce [`AdminUser`][starlette_admin.auth.AuthProvider.get_admin_user] and add navbar to show the
  current [`AdminUser`][starlette_admin.auth.AuthProvider.get_admin_user] information (`username` and `photo`)
  by [@jowilf](https://github.com/jowilf) in [#49](https://github.com/jowilf/starlette-admin/pull/49)

### Internals

* Add auth example by [@jowilf](https://github.com/jowilf) in [#51](https://github.com/jowilf/starlette-admin/pull/51)

## [0.4.0] - 2022-12-07

---

### Added

* Custom batch actions by [@jowilf](https://github.com/jowilf)
  in [#44](https://github.com/jowilf/starlette-admin/pull/44)
* Add `get_list_query`, `get_count_query` and `get_search_query` methods to SQLAlchemy backend that can be inherited for
  customization by [@jowilf](https://github.com/jowilf) in [#47](https://github.com/jowilf/starlette-admin/pull/47)

### Internals

* Update datatables to `1.13.1`
* Update Search builder UI to fit tabler design

## [0.3.2] - 2022-12-02

---

### Fixed

* Fix Datatables warning when primary key is not included in `fields` by [@jowilf](https://github.com/jowilf)
  in [#23](https://github.com/jowilf/starlette-admin/issues/23)

### Docs

* Add spanish translation for `docs/index.md` by [@rafnixg](https://github.com/rafnixg)
  in [#35](https://github.com/jowilf/starlette-admin/pull/35)

### Internals

* Use Ruff for linting by [@jowilf](https://github.com/jowilf)
  in [#29](https://github.com/jowilf/starlette-admin/pull/29)
* Migrate to Hatch by [@jowilf](https://github.com/jowilf) in [#30](https://github.com/jowilf/starlette-admin/pull/30)
* Setup pre-commit by [@jowilf](https://github.com/jowilf) in [#33](https://github.com/jowilf/starlette-admin/pull/33)
* Add support for Python 3.11 in test suite by [@jowilf](https://github.com/jowilf)
  in [#34](https://github.com/jowilf/starlette-admin/pull/34)

## [0.3.1] - 2022-11-22

---

### Fixed

* Fix Regression on SQLModel backend: Duplicate instances when creating or updating a model with relationships
  in [#23](https://github.com/jowilf/starlette-admin/issues/23)

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

* Null support for EnumField in [#17](https://github.com/jowilf/starlette-admin/pull/17)

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

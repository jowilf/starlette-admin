# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2022-11-21

---

### Added

* Add `CollectionField`
* Add `ListField`
* Add support for [Odmantic](https://art049.github.io/odmantic/) 
* Add support for datatables [responsive extensions](https://datatables.net/extensions/responsive/)
  
### Changed

* Move `SQLModel` to it own contrib package
* MongoEngine `EmbeddedDocumentField` is now converted into `CollectionField`

### Removed

* Remove PDF from default `export_types`

**Full Changelog**: https://github.com/jowilf/starlette-admin/compare/0.2.2...0.3.0

## [0.2.2] - 2022-09-20

---

### Fixed

*  Null support for EnumField by @jowilf in https://github.com/jowilf/starlette-admin/pull/17

**Full Changelog**: https://github.com/jowilf/starlette-admin/compare/0.2.1...0.2.2


## [0.2.1] - 2022-09-19

---

### Fixed

* Fix SearchBuilder not working with dates (SQLAlchemy) by @jowilf in https://github.com/jowilf/starlette-admin/pull/15

**Full Changelog**: https://github.com/jowilf/starlette-admin/compare/0.2.0...0.2.1


## [0.2.0] - 2022-09-14

---

### Changed

* Date & Time input now use Flatpickr by @jowilf in https://github.com/jowilf/starlette-admin/pull/10

**Full Changelog**: https://github.com/jowilf/starlette-admin/compare/0.1.1...0.2.0


## [0.1.1] - 2022-09-09

---

### Added

- Add `ColorField` by @jowilf in https://github.com/jowilf/starlette-admin/pull/7
- AsyncEngine support for SQLAlchemy by @jowilf in https://github.com/jowilf/starlette-admin/pull/8


**Full Changelog**: https://github.com/jowilf/starlette-admin/compare/0.1.0...0.1.1
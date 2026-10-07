---
title: Community extensions
description: Discover community-built plugins and themes that extend starlette-admin without forking the core project.
---

# Community extensions

You can install community extensions to add features or change the appearance of starlette-admin. Themes control the visual presentation, and plugins add specific functionality. Both extension types are Python packages that you install from PyPI and pass to the `Admin` class.

This article lists third-party extensions that are available for installation. For authoring guidance, see [Plugins](advanced/plugins.md) and [Custom Themes](advanced/custom-themes.md).

!!! important "Support and maintenance"
    Community extensions are published on PyPI and maintained by their respective authors. These packages are not part of the core starlette-admin project and are not officially supported. Always verify compatibility with your specific starlette-admin version and backend before installation.

## Themes

| Package | Description | Links |
| --- | --- | --- |
| **starlette-admin-adminlte** | An AdminLTE 4 theme for starlette-admin. This theme provides a fixed dark sidebar, a top navigation bar with a sidebar toggle, Bootstrap 5 components, and a built-in toggle for light and dark modes. | [GitHub](https://github.com/jowilf/starlette-admin-adminlte) |

## Plugins

| Package | Description | Links |
| --- | --- | --- |
| **starlette-admin-infinite-scroll** | Infinite scrolling for the list view. This plugin appends the next page as you scroll and keeps search, sorting, filters, and row actions working. | [GitHub](https://github.com/Alwinator/starlette-admin-infinite-scroll) |

## Create an extension

You can build reusable extensions by using the official Cookiecutter templates. The following guides cover project scaffolding, asset layout, and publishing requirements:

* To create a plugin, see [Building a plugin](advanced/plugins.md#building-a-plugin).
* To create a theme, see [Building and sharing custom themes](advanced/custom-themes.md#building-and-sharing-custom-themes).

## See also

* **[Plugins](advanced/plugins.md)**
* **[Custom Themes](advanced/custom-themes.md)**
* **[Extension Points](advanced/extension-points.md)**

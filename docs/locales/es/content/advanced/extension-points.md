---
title: Puntos de extensión
description: Una descripción general de todos los métodos hook personalizables, clases
  base y puntos de configuración disponibles en starlette-admin.
source_hash: d9fad2e9fd41b2f2ccc685090f07423b0ee2b96bf0a00b08ef0fbf2b4027ebf2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/extension-points/)
<!-- translation-notice:end -->

# Puntos de extensión

Esta página reúne en un solo lugar todas las superficies conectables de `starlette-admin`. Encuentre la clase, el hook o el decorador que se ajuste a lo que desea modificar y siga el enlace correspondiente para consultar la guía completa.

| Punto de extensión | Interfaz de API o hook | Documentación |
| --- | --- | --- |
| **Filtro personalizado** | Cree una subclase de `BaseFilter` y sobrescriba `get_filter_registry()` en un `ModelView`. | [Filtros personalizados](custom-filters.md) |
| **Exportador personalizado** | Cree una subclase de `BaseExporter`. | [Exportación e importación](../user-guide/export-import.md) |
| **Importador personalizado** | Cree una subclase de `BaseImporter`. | [Exportación e importación](../user-guide/export-import.md) |
| **Tema personalizado** | Cree una subclase de `BaseTheme`. | [Temas personalizados](custom-themes.md) |
| **Backend de autenticación personalizado** | Cree una subclase de `BaseAuthProvider`. | [Autenticación](../user-guide/auth.md) |
| **Almacenamiento de archivos personalizado** | Cree una subclase de `BaseStorage`, que se registra automáticamente mediante su atributo `name`. | [Almacenamiento de archivos](../user-guide/file-storage.md) |
| **Widget personalizado** | Cree una subclase de `BaseWidget`. | [Vistas personalizadas](../user-guide/custom-views.md) |
| **Rutas adicionales en una vista personalizada** | Aplique el decorador `@route("/path", methods=["GET"])` a un método de `CustomView`. | [Vistas personalizadas](../user-guide/custom-views.md) |
| **Plugin** | Cree una subclase de `BasePlugin` para agrupar campos, vistas, assets y más. | [Plugins](plugins.md) |

!!! tip
    Para cambiar los colores del tema Tabler predeterminado, no necesita un tema personalizado. En su lugar, pase un objeto `TablerSettings` a una instancia de `DefaultTheme`.

---

## ¿Qué sigue?

* **[Conceptos](../getting-started/concepts.md):** Vea cómo estas piezas conectables se integran en la arquitectura del framework.
* **[Vistas](../user-guide/views.md):** Explore las vistas principales a las que se asocian la mayoría de estos puntos de extensión.

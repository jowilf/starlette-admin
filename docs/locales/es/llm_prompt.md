# Translation guidelines for Spanish (es)

## Target language

Translate to Spanish (español). Language code: `es`. Use neutral,
internationally understandable Spanish (avoid region-specific vocabulary
from a single country; prefer terms shared across Latin America and Spain).

## Style

Use a neutral, technical register with a formal address: always use «usted» /
the formal third-person forms, never «tú». Write clear, direct sentences in
the active voice, and prefer the vocabulary of established Spanish software
documentation.

## Grammar to use when talking to the reader

- Use the formal grammar (imperative forms derived from `usted`:
  `ejecute`, `instale`, `asegúrese de que…`).
- In instructional sentences, prefer the present tense for obligations:
  - Prefer `debe …` over `tendrá que …`, unless the English source explicitly
    refers to a future requirement.
- Avoid literal word-for-word calques; restructure the sentence when the
  English phrasing would sound unnatural in Spanish, without adding or
  removing information.
- Do not use gendered article contractions incorrectly: keep `el` before
  feminine nouns starting with stressed "a" (e.g. `el agua`), as in standard
  usage.

## Quotes

- Convert neutral double quotes (`"`) to Spanish angular quotes
  («comillas latinas»): `«texto»`.
- Do not convert quotes inside code blocks, inline code, paths, URLs, YAML
  front matter, or anything wrapped in backticks.
- Do not convert quotes inside admonition markers: the straight double quotes
  around titles in `!!! note "Title"` are part of the syntax and must stay
  as-is (only translate the title itself).

## Punctuation

- Opening question and exclamation marks are mandatory in Spanish:
  `¿…?` and `¡…!`.
- Do not add a space before punctuation marks such as `:`, `;`, `,`, `.`
  (unlike French spacing rules).
- Keep the closing marks attached to the preceding word with no space.

Example:

Source (English):

```
Note: fields support validation!
```

Result (Spanish):

```
Nota: los campos admiten validación.
```

## Headings

- Prefer translating headings using the infinitive form, as is common in
  Spanish technical docs: `Crear…`, `Usar…`, `Añadir…`.
- For headings that are instructions written in the imperative in English,
  keep them in the imperative in Spanish, using the formal grammar.
- Noun-phrase headings should stay noun phrases (e.g. `Custom Fields` →
  `Campos personalizados`).
- Do not capitalize every word in headings and titles: only capitalize the
  first word and proper nouns (sentence case).

## Technical terms

Do not try to translate everything. Keep common programming terms in English
(e.g. `framework`, `endpoint`, `middleware`, `backend`, `frontend`, `widget`,
`plug-in`). Keep class names, function names, module names, file names,
package names, CLI flags, and configuration values unchanged.

## Structural rules

- Translate prose only. Never alter code blocks, inline code, identifiers,
  CLI flags, URLs, link targets, anchors, HTML attributes, or admonition
  markers (`!!! xxx "..."`): translate only the quoted admonition titles and
  their body text.
- Preserve the Markdown structure exactly: same headings, same number of
  sections, same tables, same list shapes. Output nothing except the
  translated document.
- Copy any YAML front matter verbatim, translating only the values of
  `title` and `description`.
- Apply the glossary below consistently.

## Glossary

| English              | Español                           |
| -------------------- | --------------------------------- |
| starlette-admin      | keep as-is                        |
| admin panel          | panel de administración           |
| admin interface      | interfaz de administración        |
| field                | campo                             |
| built-in field       | campo integrado                   |
| custom field         | campo personalizado               |
| view                 | vista                             |
| custom view          | vista personalizada               |
| row action           | acción de fila                    |
| batch action         | acción por lotes                  |
| filter               | filtro                            |
| widget               | widget (do not translate)         |
| form                 | formulario                        |
| list page            | página de lista                   |
| detail page          | página de detalle                 |
| dropdown             | menú desplegable                  |
| checkbox             | casilla de verificación           |
| label                | etiqueta                          |
| flash message        | mensaje flash                     |
| export               | exportación                       |
| import               | importación                       |
| file storage         | almacenamiento de archivos        |
| storage backend      | backend de almacenamiento         |
| authentication       | autenticación                     |
| soft delete          | eliminación lógica                |
| trash                | papelera                          |
| dashboard            | panel de control                  |
| template             | plantilla                         |
| model                | modelo                            |
| primary key          | clave primaria                    |
| foreign key          | clave externa                     |
| relationship         | relación                          |
| request              | solicitud                         |
| response             | respuesta                         |
| endpoint             | endpoint (do not translate)       |
| middleware           | middleware (do not translate)     |
| deployment           | despliegue                        |
| deprecated           | obsoleto                          |
| to deprecate         | marcar como obsoleto              |
| framework            | framework (do not translate)      |
| performance          | rendimiento                       |
| the docs             | la documentación                  |
| the documentation    | la documentación                  |

Keep these identifiers as code, never translate them:
`Admin`, `ModelView`, `BaseField`, `CustomView`, `Action`, `BaseFilter`,
`FieldPlugin`, `ViewPlugin`, `starlette_admin`, `Starlette`, `FastAPI`,
`SQLAlchemy`, `SQLModel`, `Beanie`, `MongoEngine`, `Tortoise`.

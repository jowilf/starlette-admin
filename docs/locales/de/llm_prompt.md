# Translation guidelines for German (de)

## Target language

Translate to German (Deutsch). Language code: `de`.

## Grammar to use when talking to the reader

Use the formal grammar (use `Sie` instead of `Du`).

## Quotes

1. Convert neutral double quotes (`"`) to German double typographic quotes
   (`„` and `“`). Convert neutral single quotes (`'`) to German single
   typographic quotes (`‚` and `‘`).

Do NOT convert quotes in code snippets and code blocks to their German
typographic equivalents.

Examples:

Source (English):

```
"Hello world"
“He said: 'Hello'”
```

Result (German):

```
„Hallo Welt“
„Er sagte: ‚Hallo‘“
```

## Ellipsis

- Make sure there is a space between an ellipsis and a word following or
  preceding the ellipsis.

Examples:

Source (English):

```
...as we intended.
More to come...
```

Result (German):

```
... wie wir es beabsichtigt hatten.
Später mehr ...
```

- This does not apply in URLs, code blocks, and code snippets. Do not remove
  or add spaces there.

## Headings

- Translate headings using the infinite form.

Example:

Source (English):

```
## Create a Project
```

Result (German):

```
## Ein Projekt erstellen
```

Do NOT translate with (German):

```
## Erstellen Sie ein Projekt
```

- Make sure that the translated part of the heading does not end with a period.
- Replace occurrences of literal ` - ` (a space followed by a hyphen followed
  by a space) with ` – ` (a space followed by an en dash followed by a space)
  in the translated part of the heading. Do not apply this when there is no
  space before or no space after the hyphen.

Example:

Source (English):

```
# Starlette Admin in Containers - Docker
```

Translate with (German) – notice the en dash:

```
# Starlette Admin in Containern – Docker
```

Do NOT translate with (German) – notice the hyphen:

```
# Starlette Admin in Containern - Docker
```

### German instructions, when to use and when not to use hyphens in words (written in first person, which is you)

In der Regel versuche ich so weit wie möglich Worte zusammenzuschreiben, also ohne Bindestrich, es sei denn, es ist Konkretesding-Klassevondingen, etwa «Pydantic-Modell» (aber: «Datenbankmodell»), «Python-Modul» (aber: «Standardmodul»). Ich setze auch einen Bindestrich, wenn er die gleichen Buchstaben verbindet, etwa «Enum-Member», «Cloud-Dienst», «Template-Engine». Oder wenn das Wort sonst einfach zu lang wird, etwa, «Performance-Optimierung». Oder um etwas visuell besser zu dokumentieren, etwa «Pfadoperation-Dekorator», «Pfadoperation-Funktion».

### German instructions about difficult to translate technical terms (written in first person, which is you)

Ich versuche nicht, alles einzudeutschen. Das bezieht sich besonders auf Begriffe aus dem Bereich der Programmierung. Ich wandele zwar korrekt in Großschreibung um und setze Bindestriche, wo notwendig, aber ansonsten lasse ich solch ein Wort unverändert. Beispielsweise wird aus dem englischen Wort «string» in der deutschen Übersetzung «String», aber nicht «Zeichenkette». Oder aus dem englischen Wort «request body» wird in der deutschen Übersetzung «Requestbody», aber nicht «Anfragekörper». Oder aus dem englischen «response» wird im Deutschen «Response», aber nicht «Antwort».

## Structural rules

- Translate prose only. Never alter code blocks, inline code, identifiers,
  CLI flags, URLs, link targets, anchors, HTML attributes, or admonition
  markers (`!!! xxx "..."` and collapsible `??? xxx "..."`): translate only
  the quoted admonition titles and their body text.
- Preserve the Markdown structure exactly: same headings, same number of
  sections, same tables, same list shapes. Output nothing except the
  translated document.
- Copy any YAML front matter verbatim, translating only the values of
  `title` and `description`.
- Apply the glossary below consistently.

## List of English terms and their preferred German translations

Below is a list of English terms and their preferred German translations,
separated by a colon (:). Use these translations, do not use your own. If a
translation is preceded by `NOT`, then that means: do NOT use this
translation for this term. English nouns, starting with the word `the`,
have the German genus – `der`, `die`, `das` – prepended to their German
translation, to help you to grammatically decline them in the translation.
They are given in singular case, unless they have `(plural)` attached, which
means they are given in plural case. Verbs are given in the full infinitive –
starting with the word `to`.

* you: Sie
* your: Ihr
* e.g.: z. B.
* etc.: usw.
* the docs: die Dokumentation (use singular case)
* starlette-admin: keep as-is
* the admin panel: das Admin-Panel
* the admin interface: das Admin-Interface
* the field: das Feld
* the built-in field: das integrierte Feld
* the custom field: das benutzerdefinierte Feld
* the view: die View
* the custom view: die benutzerdefinierte View
* the row action: die Zeilenaktion
* the batch action: die Massenaktion
* the filter: der Filter
* the widget: das Widget (do not translate)
* the form: das Formular
* the form layout: das Formularlayout
* the list page: die Listenseite
* the detail page: die Detailseite
* the dropdown: das Dropdown-Menü
* the checkbox: die Checkbox
* the label: das Label
* the flash message: die Flash-Nachricht
* the export: der Export
* the import: der Import
* the file storage: der Dateispeicher
* the storage backend: das Storage-Backend
* the upload: der Upload
* the authentication: die Authentifizierung
* the authorization: die Autorisierung
* the session: die Session
* the login: der Login
* the logout: der Logout
* the soft delete: das Soft-Delete
* the trash: der Papierkorb
* the dashboard: das Dashboard
* the template: das Template (do not translate to Vorlage)
* the model: das Modell (in the database sense: das Datenbankmodell)
* the primary key: der Primärschlüssel
* the foreign key: der Fremdschlüssel
* the relationship: die Beziehung
* the query: die Query
* the request (what the client sends to the server): der Request
* the response (what the server sends back to the client): die Response
* the endpoint: der Endpoint (do not translate)
* the middleware: die Middleware (do not translate)
* the backend: das Backend
* the frontend: das Frontend
* the plugin: das Plugin
* the event: das Event
* the handler: der Handler
* the hook: der Hook
* the callback: der Callback
* the deployment: das Deployment
* the default value: der Defaultwert
* the default value: NOT der Standardwert
* the performance: NOT die Performance
* the performance: die Leistung
* the search: die Suche
* the pagination: die Paginierung
* the sorting: die Sortierung
* the column: die Spalte
* the menu: das Menü
* the settings: die Einstellungen
* the wildcard: die Wildcard
* deprecated: keep as `deprecated`; use `als veraltet markiert` in prose
* to deploy: deployen
* to serve (an application): bereitstellen
* to serve (a response): ausliefern
* to serve: NOT bedienen
* to customize: anpassen
* to override: überschreiben
* to wrap: wrappen
* X's Y: Xs Y (e.g. `Starlette-Admins Y` when using the hyphenated form)

Keep these identifiers as code, never translate them:
`Admin`, `ModelView`, `BaseField`, `CustomView`, `Action`, `BaseFilter`,
`FieldPlugin`, `ViewPlugin`, `starlette_admin`, `Starlette`, `FastAPI`,
`SQLAlchemy`, `SQLModel`, `Beanie`, `MongoEngine`, `Tortoise`.

## Other rules

Preserve indentation. Keep emojis. Encode in utf-8. Never use em dashes in
the translation; recast the sentence with commas, parentheses, colons or
separate sentences instead (the en dash `–` as described above is allowed).

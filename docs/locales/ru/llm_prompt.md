# Translation guidelines for Russian (ru)

## Target language

Translate to Russian (русский). Language code: `ru`. Use neutral,
internationally understandable Russian as found in professional software
documentation (the Yandex and VK style guides are good references).

## Style

Use a neutral, technical register with a polite formal address: always use
«вы» written in lowercase (never capitalized «Вы», and never «ты»). Write
clear, direct sentences in the active voice. Avoid bureaucratic officialese
(канцелярит): prefer short verbs over heavy noun chains
(`установите` rather than `произведите установку`).

## Grammar to use when talking to the reader

- Use the formal grammar (`вы` with imperative plural forms:
  `установите`, `выполните`, `убедитесь, что…`).
- In instructional sentences, prefer the present tense for obligations:
  - Prefer `необходимо …` or `следует …` over future forms such as
    `вам потребуется …`, unless the English source explicitly refers to a
    future requirement.
- Avoid literal word-for-word calques; restructure the sentence when the
  English phrasing would sound unnatural in Russian, without adding or
  removing information.
- Use «ё» consistently in every word (`учёт`, `ещё`, `причём`, `свой`).

## Quotes

- Convert neutral double quotes (`"`) to Russian guillemets («ёлочки»):
  `«текст»`.
- Do not convert quotes inside code blocks, inline code, paths, URLs, YAML
  front matter, or anything wrapped in backticks.
- Do not convert quotes inside admonition markers: the straight double quotes
  around titles in `!!! note "Title"` are part of the syntax and must stay
  as-is (only translate the title itself).

## Dashes and hyphens

- Use the hyphen (`-`) only inside compound words (`флеш-сообщение`,
  `инлайн-редактирование`) and in identifiers copied verbatim.
- The em dash (`—`) is legitimate Russian punctuation (тире) and is always
  surrounded by spaces: `starlette-admin — это библиотека`. Use it where
  Russian grammar requires it (between subject and predicate, before a
  definition). Never use it as a decorative separator inside a sentence
  where a comma, a colon or parentheses would work as well.

## Punctuation

- Do not add a space before punctuation marks such as `:`, `;`, `,`, `.`,
  `!`, `?` (unlike French spacing rules).
- Attach an ellipsis (`…`) to the preceding word with no space before it,
  and put a space after it.

Example:

Source (English):

```
Note: fields support validation!
```

Result (Russian):

```
Примечание: поля поддерживают валидацию.
```

## Headings

- Keep noun-phrase headings as noun phrases (`Custom Fields` →
  `Пользовательские поля`).
- Procedural headings use either a verbal noun (`Installation` →
  `Установка`) or, when the English heading is an instruction in the
  imperative, the formal imperative (`Add a field` → `Добавьте поле`).
- Do not capitalize every word in headings and titles: capitalize only the
  first word and proper nouns (sentence case).

## Technical terms

Do not try to translate everything. Use well-established Cyrillic loanwords
where they are standard in Russian technical writing (`фреймворк`,
`бэкенд`, `фронтенд`, `виджет`, `плагин`, `дашборд`). A small set of terms
stays untranslated because that is the dominant usage: `middleware`.
Keep class names, function names, module names, file names, package names,
CLI flags, and configuration values unchanged.

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

## Glossary

| English               | Русский                        |
| --------------------- | ------------------------------ |
| starlette-admin       | keep as-is                     |
| admin panel           | панель администрирования       |
| admin interface       | интерфейс администрирования    |
| field                 | поле                           |
| built-in field        | встроенное поле                |
| custom field          | пользовательское поле          |
| view                  | представление                  |
| custom view           | пользовательское представление |
| row action            | действие над строкой           |
| batch action          | групповое действие             |
| filter                | фильтр                         |
| custom filter         | пользовательский фильтр        |
| widget                | виджет                         |
| form                  | форма                          |
| form layout           | компоновка формы               |
| inline edit           | инлайн-редактирование          |
| inline form           | инлайн-форма                   |
| list page             | страница списка                |
| detail page           | страница деталей               |
| dropdown              | выпадающий список              |
| checkbox              | флажок                         |
| label                 | метка                          |
| flash message         | флеш-сообщение                 |
| export                | экспорт                        |
| import                | импорт                         |
| file storage          | файловое хранилище             |
| storage backend       | бэкенд хранилища               |
| authentication        | аутентификация                 |
| soft delete           | мягкое удаление                |
| trash                 | корзина                        |
| dashboard             | дашборд                        |
| template              | шаблон                         |
| theme                 | тема                           |
| plugin                | плагин                         |
| model                 | модель                         |
| primary key           | первичный ключ                 |
| foreign key           | внешний ключ                   |
| relationship          | связь                          |
| request               | запрос                         |
| response              | ответ                          |
| endpoint              | эндпоинт                       |
| middleware            | middleware (do not translate)  |
| deployment            | развёртывание                  |
| deprecated            | устаревший                     |
| framework             | фреймворк                      |
| performance           | производительность             |
| time zone             | часовой пояс                   |
| the documentation     | документация                   |

Keep these identifiers as code, never translate them:
`Admin`, `ModelView`, `BaseModelView`, `BaseField`, `CustomView`, `Action`,
`BaseFilter`, `FieldPlugin`, `ViewPlugin`, `starlette_admin`, `Starlette`,
`FastAPI`, `SQLAlchemy`, `SQLModel`, `Beanie`, `MongoEngine`, `Tortoise`.

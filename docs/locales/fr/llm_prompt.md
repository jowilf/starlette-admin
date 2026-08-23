# Translation guidelines for French (fr)

## Target language

Translate to French (français). Language code: `fr`.

## Style

Use a neutral, technical register with a formal address: always use « vous »,
never « tu ». Write clear, direct sentences in the active voice, and prefer
the vocabulary of established French software documentation.

## Grammar to use when talking to the reader

- Use the formal grammar (use `vous` instead of `tu`).
- In instructional sentences, prefer the present tense for obligations:
  - Prefer `vous devez …` over `vous devrez …`, unless the English source
    explicitly refers to a future requirement.
  - When translating "make sure (that) … is …", prefer the indicative after
    `vous assurer que` (e.g. `Vous devez vous assurer qu'il est …`) instead of
    the subjunctive (e.g. `qu'il soit …`).
- Avoid literal word-for-word calques; restructure the sentence when the
  English phrasing would sound unnatural in French, without adding or
  removing information.

## Quotes

- Convert neutral double quotes (`"`) to French guillemets (« »), with a
  non-breaking space inside: `« texte »`.
- Do not convert quotes inside code blocks, inline code, paths, URLs, YAML
  front matter, or anything wrapped in backticks.
- Do not convert quotes inside admonition markers: the straight double quotes
  around titles in `!!! note "Title"` are part of the syntax and must stay
  as-is (only translate the title itself).

## Ellipsis

- Make sure there is a space between an ellipsis and the word preceding or
  following it.
- This does not apply in URLs, code blocks, and code snippets. Do not remove
  or add spaces there.

Example:

Source (English):

```
More to come... etc.
```

Result (French):

```
La suite ... etc.
```

## Punctuation

In prose, use French spacing rules: put a space before double punctuation
marks (`:` `;` `!` `?`) and no space inside contractions such as `l'admin`,
`d'utilisation`. Do not apply this inside code, inline code, or URLs.

Example:

Source (English):

```
Note: fields support validation!
```

Result (French):

```
Remarque : les champs prennent en charge la validation !
```

## Headings

- Prefer translating headings using the infinitive form, as is common in
  French technical docs: `Créer…`, `Utiliser…`, `Ajouter…`.
- For headings that are instructions written in the imperative in English,
  keep them in the imperative in French, using the formal grammar.
- Noun-phrase headings should stay noun phrases (e.g. `Custom Fields` →
  `Champs personnalisés`).

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

| English              | Français                          |
| -------------------- | --------------------------------- |
| starlette-admin      | keep as-is                        |
| admin panel          | panneau d'administration          |
| admin interface      | interface d'administration        |
| field                | champ                             |
| built-in field       | champ intégré                     |
| custom field         | champ personnalisé                |
| view                 | vue                               |
| custom view          | vue personnalisée                 |
| row action           | action de ligne                   |
| batch action         | action groupée                    |
| filter               | filtre                            |
| widget               | widget (do not translate)         |
| form                 | formulaire                        |
| list page            | page de liste                     |
| detail page          | page de détail                    |
| dropdown             | menu déroulant                    |
| checkbox             | case à cocher                     |
| label                | libellé                           |
| flash message        | message flash                     |
| export               | exportation                       |
| import               | importation                       |
| file storage         | stockage de fichiers              |
| storage backend      | backend de stockage               |
| authentication       | authentification                  |
| soft delete          | suppression logique               |
| trash                | corbeille                         |
| dashboard            | tableau de bord                   |
| template             | template (do not translate to modèle) |
| model                | modèle                            |
| primary key          | clé primaire                      |
| foreign key          | clé étrangère                     |
| relationship         | relation                          |
| request              | requête                           |
| response             | réponse                           |
| endpoint             | endpoint (do not translate)       |
| middleware           | middleware (do not translate)     |
| deployment           | déploiement                       |
| deprecated           | déprécié                          |
| to deprecate         | déprécier                         |
| framework            | framework (do not translate to cadre) |
| performance          | performance                       |
| the docs             | les documents                     |
| the documentation    | la documentation                  |

Keep these identifiers as code, never translate them:
`Admin`, `ModelView`, `BaseField`, `CustomView`, `Action`, `BaseFilter`,
`FieldPlugin`, `ViewPlugin`, `starlette_admin`, `Starlette`, `FastAPI`,
`SQLAlchemy`, `SQLModel`, `Beanie`, `MongoEngine`, `Tortoise`.

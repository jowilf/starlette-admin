# Contributing to *starlette-admin*

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways
to help and details about how this project handles them. Please make sure to read the relevant section before making
your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The
community looks forward to your contributions. 🎉

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support
> the project and show your appreciation, which we would also be very happy about:
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Your First Code Contribution](#your-first-code-contribution)
    - [Adding support for a new locale](#adding-support-for-a-new-locale)
    - [Improving The Documentation](#improving-the-documentation)

## Code of Conduct

This project and everyone participating in it is governed by the
[Starlette-Admin Code of Conduct](https://github.com/jowilf/starlette-admin/blob/main/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to <hounonj@gmail.com>.

## I Have a Question

> If you want to ask a question, we assume that you have read the
> available [Documentation](https://jowilf.github.io/starlette-admin/).

Before you ask a question, it is best to search for existing [Issues](https://github.com/jowilf/starlette-admin/issues)
that might help you. In case you have found a suitable issue and still need clarification, you can write your question
in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/jowilf/starlette-admin/issues/new).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions, depending on what seems relevant.

We will then take care of the issue as soon as possible.

## I Want To Contribute

> ### Legal Notice
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the
> necessary rights to the content and that the content you contribute may be provided under the project license.

### Reporting Bugs

#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to
investigate carefully, collect information and describe the issue in detail in your report. Please complete the
following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment
  components/versions (Make sure that you have read the [documentation](https://jowilf.github.io/starlette-admin/). If
  you are looking for support, you might want to check [this section](#i-have-a-question)).
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there
  is not already a bug report existing for your bug or error in
  the [bug tracker](https://github.com/jowilf/starlette-admin/issues?q=label%3Abug).
- Also make sure to search the internet (including Stack Overflow) to see if users outside of the GitHub community have
  discussed the issue.
- Collect information about the bug:
    - Stack trace (Traceback)
    - OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
    - Version of the interpreter, compiler, SDK, runtime environment, package manager, depending on what seems relevant.
    - Possibly your input and the output
    - Can you reliably reproduce the issue? And can you also reproduce it with older versions?

#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue
> tracker, or elsewhere in public. Instead, sensitive bugs must be sent by email to <hounonj@gmail.com>.

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/jowilf/starlette-admin/issues/new). (Since we can't be sure at this point whether
  it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to
  recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem
  and create a reduced test case.
- Provide the information you collected in the previous section.

Once it's filed:

- The project team will label the issue accordingly.
- A team member will try to reproduce the issue with your provided steps. If there are no reproduction steps or no
  obvious way to reproduce the issue, the team will ask you for those steps and mark the issue as `needs-repro`. Bugs
  with the `needs-repro` tag will not be addressed until they are reproduced.
- If the team is able to reproduce the issue, it will be marked `needs-fix`, as well as possibly other tags (such
  as `critical`), and the issue will be left to be [implemented by someone](#your-first-code-contribution).

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for *starlette-admin*, **including completely new
features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the
community to understand your suggestion and find related suggestions.

#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation](https://jowilf.github.io/starlette-admin/) carefully and find out if the functionality is
  already covered, maybe by an individual configuration.
- Perform a [search](https://github.com/jowilf/starlette-admin/issues) to see if the enhancement has already been
  suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to
  convince the project's developers of the merits of this feature. Keep in mind that we want features that will be
  useful to the majority of our users and not just a small subset. If you're just targeting a minority of users,
  consider writing an add-on/plugin library.

#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/jowilf/starlette-admin/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point
  you can also tell which alternatives do not work for you.
- You may want to **include screenshots and animated GIFs** which help you demonstrate the steps or point out the part
  which the suggestion is related to. You can use [this tool](https://www.cockos.com/licecap/) to record GIFs on macOS
  and Windows, and [this tool](https://github.com/colinkeenan/silentcast)
  or [this tool](https://github.com/GNOME/byzanz) on
  Linux.
- **Explain why this enhancement would be useful** to most *starlette-admin* users. You may also want to point out the
  other projects that solved it better and which could serve as inspiration.

### Your First Code Contribution

#### Setting up the development environment

Before you start contributing to *starlette-admin*, ensure you have a proper development environment set up. Familiarize
yourself with the open-source contribution workflow by following the guidelines
available [here](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).

To manage dependencies and packaging for *starlette-admin*, we use [hatch](https://hatch.pypa.io/). Please make sure to
install it globally.

For example, you can install Hatch using pip:

```shell
pip install hatch
```

For more detailed installation instructions, refer to the [Hatch documentation](https://hatch.pypa.io/latest/install/)

#### Code Linting & Formatting

To maintain code consistency, ensure proper code formatting, and enforce type safety, *starlette-admin*
uses [black](https://github.com/psf/black), [mypy](https://mypy-lang.org/)
and [ruff](https://github.com/charliermarsh/ruff).

Run the following command to format your code:

```shell
hatch run format
```

To perform linting checks, run:

```shell
hatch run test:lint
```

#### Testing

We use [pytest](https://docs.pytest.org) for unit testing. To ensure the stability of *starlette-admin*,
every new feature must be tested in a separate unit test. Run the test suite to validate your changes:

```shell
hatch run test:all
```

#### Submitting new code

First, add the pre-commit command to your git's pre-commit hooks. This will ensure that you never forget to format your
code

```shell
pre-commit install
```

To make the pull request reviewing easier and keep the version tree clean your pull request should consist of a single
commit.
It is natural that your branch might contain multiple commits, so you will need to squash these into a single commit.
Instructions can be
found [here](https://docs.github.com/en/desktop/contributing-and-collaborating-using-github-desktop/managing-commits/squashing-commits)

### Adding support for a new locale

*starlette-admin* relies on [babel](https://babel.pocoo.org/) for internationalization
and localization.

#### Current supported locales

The `SUPPORTED_LOCALES` variable in the [i18n.py](./starlette_admin/i18n.py) module contains the list of locales
currently supported.

#### Step-By-Step Guide

##### Step 1: Initialize the new locale

To add support for a new locale, the first thing to do is to run the initialization script:

```shell
# replace <locale> by the new locale
hatch run i18n:init --locale <locale>

# use --help to see all available options
```

##### Step 2: Translate Messages

* Update all the `msgstr` keys in the POT file located
  at  `./starlette_admin/translations/<locale>/LC_MESSAGES/admin.po`.
  Translate these messages to your target language.

Example (French):

```po
msgid "Are you sure you want to delete selected items?"
msgstr "Êtes-vous sûr de vouloir supprimer ces éléments?"
```

* Check and update the generated JSON file for datatables located at `./starlette_admin/statics/i18n/dt/<locale>.json`.
  Most of
  the time, you will only need to update the `starlette-admin` key, which is internal to *starlette-admin*

Example (French):

```json5
{
    // ...
    "starlette-admin": {
        "buttons": {
            "export": "Export"
        },
        "conditions": {
            "false": "Faux",
            "true": "Vrai",
            "empty": "Vide",
            "notEmpty": "Non vide"
        }
    },
    // ...
}
```

##### Step 3: Update the supported locales

Make sure to update the `SUPPORTED_LOCALES` variable in the [i18n.py](./starlette_admin/i18n.py) module to
include the new locale.

#### Step 4: Compile the new message catalogs

After translating the messages, compile the POT file into a binary MO file using the following command:

```shell
# replace <locale> by the new locale
hatch run i18n:compile -l <locale>
```

#### Step 5: Test the New Locale

To ensure that your new locale can be fully loaded by *starlette-admin*, include the new locale in
the `test_default_locale`
unit test in the [test_i18n](./tests/test_i18n.py) module.

### Improving The Documentation

Please write clear documentation for any new functionality you add. Docstrings will be converted to the API
documentation, but more human friendly documentation might also be needed.

The documentation is generated using [mkdocs](https://www.mkdocs.org/).
To preview your documentation locally, run:

```shell
hatch run docs:serve
```

and visit http://localhost:8080 in your browser to see a live preview of your documentation.

## Attribution

This guide is based on the **contributing.md**. [Make your own](https://contributing.md/)!

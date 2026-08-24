---
title: Comparaison de starlette-admin, Django Admin et Flask-Admin
description: Une comparaison côte à côte de starlette-admin, Django Admin et Flask-Admin
  couvrant les stacks web, les ORM pris en charge, la profondeur des fonctionnalités
  et les compromis.
source_hash: 7d6cd31a303552e61610bea128e3774a750ae1b417d7633fbffbf94df239a4cf
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/comparison/)
<!-- translation-notice:end -->

# Comparer starlette-admin, Django Admin et Flask-Admin

Django Admin, Flask-Admin et starlette-admin résolvent le même problème : ils génèrent une interface d'administration prête pour la production à partir de vos modèles de données, vous évitant ainsi d'écrire les écrans CRUD à la main. Ils se distinguent par les stacks web qu'ils ciblent, les ORM qu'ils prennent en charge et l'étendue de ce qu'ils intègrent nativement par rapport à ce qu'ils vous laissent implémenter.

Cette page compare ces trois outils. Si vous connaissez déjà Django Admin ou Flask-Admin et souhaitez une correspondance directe entre leurs API respectives et celle de starlette-admin, consultez le guide de migration correspondant :

* [Migrer depuis Django Admin](django-admin.md)
* [Migrer depuis Flask-Admin](flask-admin.md)

## Positionnement en un coup d'œil

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Framework web** | Django uniquement | Flask uniquement | Starlette, FastAPI et toute application ASGI capable de monter des sous-applications |
| **Modèle d'exécution** | Synchrone (orienté WSGI) | Synchrone (WSGI) | Asynchrone d'abord (ASGI) |
| **Couche de données** | Django ORM uniquement | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM ou un [backend personnalisé](../integrations/custom-backend.md) |
| **Toolkit UI** | Templates Django, thème admin classique | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), mode sombre, [thèmes personnalisés](../advanced/custom-themes.md) |
| **Inclus avec le framework** | Oui, fait partie de Django | Non, package distinct | Non, package distinct |
| **Authentification** | Intégrée via `django.contrib.auth` | À votre charge (`is_accessible`) | [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md) enfichable, magasin d'utilisateurs à votre charge |

## Quel framework pour quel cas

### Django Admin

Django Admin convient aux applications natives de Django. Il est mature et s'intègre à `django.contrib.auth`, ce qui vous fournit utilisateurs, groupes, permissions par modèle et historique des modifications sans aucune configuration. Il ne fonctionne que dans l'écosystème Django.

### Flask-Admin

Flask-Admin a introduit la génération automatique dans Flask et a popularisé le style de configuration par `ModelView`. Il est synchrone et lié à Flask ; il ne peut donc pas fonctionner sur une stack asynchrone.

### starlette-admin

starlette-admin cible la stack Python asynchrone. Si votre application utilise FastAPI ou Starlette, vous montez l'interface d'administration sur votre application et elle s'exécute sur la même boucle d'événements. Elle fonctionne avec des couches de données SQL comme NoSQL, conserve le style de configuration par `ModelView` hérité de Flask-Admin et couvre la profondeur de fonctionnalités attendue par les utilisateurs de Django Admin : inlines, actions groupées, permissions par requête et internationalisation.

## Matrice des fonctionnalités

**Légende :**

* **Oui :** intégré nativement
* **Partiel :** possible via des packages tiers ou du code personnalisé
* **Non :** indisponible

| Fonctionnalité | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| Vues CRUD générées automatiquement | **Oui** | **Oui** | **Oui** |
| Recherche plein texte | **Oui** `search_fields` | **Oui** `column_searchable_list` | **Oui** [`searchable_fields`](../user-guide/filters.md) |
| Filtres de colonnes | **Oui** `list_filter` | **Oui** `column_filters` | **Oui** [Constructeur visuel de filtres](../user-guide/filters.md) avec groupes `AND`/`OR` |
| Tri et ordre par défaut | **Oui** | **Oui** | **Oui** [`sortable_fields`, `fields_default_sort`](../user-guide/views.md#search-and-sort) |
| Édition en ligne dans la vue liste | **Oui** `list_editable` | **Oui** `column_editable_list` | **Oui** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| Formulaires inline pour modèles liés | **Oui** `TabularInline` / `StackedInline` | **Oui** `inline_models` | **Oui** [`InlineModelView`](../user-guide/inline-forms.md) |
| Actions groupées | **Oui** `actions` | **Oui** `@action` | **Oui** [`@action`](../user-guide/actions.md) avec boîtes de dialogue de confirmation et formulaires personnalisés |
| Actions par ligne | **Partiel** templates personnalisés | **Partiel** formateurs personnalisés | **Oui** [`@row_action`, `@link_row_action`](../user-guide/actions.md#row-actions) |
| Export de données | **Partiel** `django-import-export` | **Oui** CSV et autres | **Oui** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| Import de données | **Partiel** `django-import-export` | **Non** | **Oui** [CSV, JSON, Excel](../user-guide/export-import.md) avec validation d'aperçu et upsert |
| Téléversement de fichiers et d'images | **Oui** `FileField` / `ImageField` | **Partiel** configuration supplémentaire nécessaire | **Oui** [Stockage local et S3](../user-guide/file-storage.md) |
| Widgets de tableau de bord | **Partiel** thèmes tiers | **Partiel** vue index personnalisée | **Oui** [Système de widgets intégré](../user-guide/custom-views.md) |
| Pages autonomes personnalisées | **Oui** URLs `AdminSite` personnalisées | **Oui** `BaseView` + `@expose` | **Oui** [`CustomView`](../user-guide/custom-views.md) |
| Contrôle de la mise en page des formulaires | **Oui** `fieldsets` | **Oui** `form_rules` | **Oui** [`form_layout`](../advanced/form-layout.md) avec onglets et grilles |
| Authentification | **Oui** `django.contrib.auth` | **Non** à votre charge | **Oui** [`AuthProvider`](../user-guide/auth.md) ou `OAuthProvider` |
| Permissions par modèle | **Oui** framework de permissions | **Oui** surcharge des indicateurs `can_*` | **Oui** [méthodes par requête](../user-guide/views.md#security-and-authorization) |
| Permissions par champ | **Partiel** `get_readonly_fields` | **Non** | **Oui** [`can_access_field`](../user-guide/views.md#security-and-authorization) |
| Hooks de cycle de vie | **Oui** `save_model`, signals | **Oui** `on_model_change` | **Oui** [Hooks de cycle de vie](../user-guide/views.md#lifecycle-hooks) et [events](../advanced/events.md) |
| Protection CSRF | **Oui** middleware Django | **Oui** via Flask-WTF | **Oui** [Intégrée dans `Admin`](../user-guide/security.md) |
| Historique des modifications / journal d'audit | **Oui** `LogEntry` | **Non** | **Partiel** construisez le vôtre avec les [events](../advanced/events.md) |
| Internationalisation | **Oui** | **Oui** via Flask-Babel | **Oui** [`I18nConfig`](../user-guide/i18n.md) |
| Instances d'administration multiples | **Oui** plusieurs `AdminSite` | **Oui** | **Oui** [Montages multiples de `Admin`](../advanced/multiple-admin.md) |
| Prise en charge des ORM async | **Partiel** | **Non** | **Oui** SQLAlchemy async, Beanie, Tortoise ORM |

## Compromis

* **Système utilisateur complet :** Django Admin embarque un système utilisateur complet. `django.contrib.auth` gère pour vous les utilisateurs, les groupes, les permissions et la gestion des mots de passe. Dans starlette-admin, vous implémentez `authenticate()` contre votre propre magasin de données, ce qui représente plus de configuration au départ mais davantage de liberté architecturale ensuite.
* **Historique automatisé des modifications :** Django Admin enregistre l'historique des modifications dans `LogEntry`. Dans starlette-admin, vous construisez vous-même la piste d'audit en vous abonnant aux [events](../advanced/events.md) du cycle de vie. Cela demande quelques lignes de code, mais ce n'est pas automatique.
* **Écosystème tiers :** Django Admin dispose d'un large écosystème de packages tiers pour les thèmes, les widgets et les flux de données. starlette-admin couvre nativement nombre de ces fonctionnalités, mais il est possible qu'une extension spécifique dont vous dépendez n'existe pas encore.
* **Gestion des fichiers :** Flask-Admin fournit `FileAdmin`, un navigateur du système de fichiers du serveur. starlette-admin gère les fichiers associés aux champs de modèles via un [stockage disque local ou S3](../user-guide/file-storage.md), mais ne propose pas de navigateur de fichiers serveur à usage général.

## Prochaines étapes

* Vous venez de Django ? Consultez [Migrer depuis Django Admin](django-admin.md).
* Vous venez de Flask-Admin ? Consultez [Migrer depuis Flask-Admin](flask-admin.md).
* Vous démarrez de zéro ? Le [Quickstart](../getting-started/quickstart.md) vous permet d'obtenir une interface d'administration opérationnelle en quelques minutes.

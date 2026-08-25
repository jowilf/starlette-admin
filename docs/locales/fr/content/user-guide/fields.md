---
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# Champs

Les champs sont les éléments constitutifs de vos vues. Sous le capot, ce sont de simples dataclasses Python : chaque attribut que vous passez à un constructeur de champ devient un attribut de champ, et chaque type de champ hérite de `BaseField`, que vous pouvez inspecter, sous-classer ou instancier directement.

## Attributs communs

Chaque type de champ hérite cet ensemble d'attributs de configuration de `BaseField`.

| Attribut | Type | Défaut | Description |
| --- | --- | --- | --- |
| `name` | `str` | **Requis** | Le nom de l'attribut sur votre modèle. |
| `label` | `str | None` | `name` en majuscules au début | L'en-tête de colonne et l'étiquette du formulaire. |
| `help_text` | `str | None` | `None` | Texte d'aide affiché sous le champ de saisie du formulaire. |
| `required` | `bool` | `False` | Exige une valeur dans les formulaires, à la fois côté client et côté serveur. |
| `validators` | `list[Validator]` | `[]` | Validateurs côté serveur exécutés sur la valeur soumise. Voir [Validation](#validation). |
| `disabled` | `bool` | `False` | Grise et verrouille le champ dans les formulaires. |
| `read_only` | `bool` | `False` | Affiche le champ mais bloque les modifications. |
| `default` | `Any | Callable` | `None` | La valeur de préremplissage sur le formulaire de création. |
| `getter` | `Callable | None` | `None` | Remplace la recherche de l'attribut du modèle lors de la lecture de la valeur. Voir [Calcul, formatage et analyse des valeurs](#computing-formatting-and-parsing-values). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Formatage d'affichage par action, qui remplace la sérialisation pour cette action. Voir [Calcul, formatage et analyse des valeurs](#computing-formatting-and-parsing-values). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Analyse des entrées par action, qui remplace l'analyse par défaut du champ. Voir [Calcul, formatage et analyse des valeurs](#computing-formatting-and-parsing-values). |
| `searchable` | `bool` | `True` | Inclus lorsque le paramètre de recherche `q` correspond. |
| `orderable` | `bool` | `True` | Ajoute un lien de tri dans l'en-tête de la liste. |
| `copy_to_clipboard` | `bool` | `False` | Ajoute un bouton de copie à côté de la valeur sur la page de détail. |
| `filters` | `list | None` | `None` | Surcharge explicite pour les filtres de la page de liste. |
| `extra` | `dict[str, Any]` | `{}` | Un dictionnaire pour vos propres métadonnées. |

### Contrôles de visibilité

Utilisez ces indicateurs booléens, tous `False` par défaut, pour contrôler où un champ apparaît :

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Définition des valeurs par défaut

L'attribut `default` accepte une valeur statique, une fonction sans argument, ou une fonction tenant compte de la requête :

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### Calcul, formatage et analyse des valeurs {#computing-formatting-and-parsing-values}

Chaque champ accepte trois hooks appelables, `getter`, `formatter` et `parser`, qui interceptent et transforment les données lorsqu'elles circulent entre votre modèle et l'interface utilisateur. Chacun accepte une fonction synchrone ou asynchrone.

#### `getter` : lecture de valeurs personnalisées

Le hook `getter` remplace la recherche `getattr()` par défaut lorsque le champ lit une instance de modèle. Le champ appelle `getter(request, obj)` et affiche la valeur retournée.

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Comme les valeurs de `getter` correspondent rarement à une colonne physique de base de données, elles s'associent le mieux à un affichage en lecture seule. [`ComputedField`](#computedfield) est un raccourci intégré pour cette combinaison.

#### `formatter` : transformation de la sortie d'affichage

Le hook `formatter` définit comment une valeur stockée est rendue sur des pages spécifiques. Il associe une `RequestAction`, telle que `LIST`, `DETAIL` ou `EXPORT`, à une fonction `(request, value) -> value`.

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Mask the key on list views; show the full key on detail/export views
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**Comportements de formatage à garder en tête :**

* **Les valeurs nulles atteignent le formatter :** Contrairement à la sérialisation par défaut, les formatters reçoivent les valeurs `None`, vous pouvez donc fournir un texte de repli, tel que `"unset"` ci-dessus.
* **La sérialisation est contournée :** Un formatter correspondant remplace les méthodes `serialize_value` et `serialize_none_value` du champ. La valeur retournée est utilisée telle quelle, le formatter est donc entièrement responsable de la sortie finale.
* **Exigence JSON :** Les valeurs retournées pour les actions `LIST` et `RELATION_LOOKUP` doivent rester sérialisables en JSON.

#### `parser` : traitement des données entrantes

Le hook `parser` remplace l'analyse par défaut du champ pour les données soumises ou importées. Il associe une `RequestAction` à une fonction `(request, raw) -> value`.

* **Formulaires (`CREATE`, `EDIT`, `INLINE_EDIT`) :** `raw` est la saisie du formulaire soumis, ou une liste lorsque `multiple=True`.
* **Imports (`IMPORT`) :** `raw` est la valeur brute de la cellule provenant du fichier.

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Strip currency symbols during import and convert to integer cents
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

Après l'analyse, la valeur retournée passe par la chaîne de validation standard, `required` puis `validators`, exactement comme si le champ avait analysé lui-même les données.

!!! tip "Hooks ou sous-classe ?"
    Pour une personnalisation ponctuelle sur un seul champ, vous avez rarement besoin d'une sous-classe. Passez ces hooks comme arguments au constructeur pour gérer la lecture, le formatage d'affichage et l'analyse des entrées. [Sous-classez le champ](../advanced/custom-fields.md) lorsque vous réutilisez la logique entre plusieurs vues, ou lorsque vous devez modifier les templates de rendu HTML.

### Validation

La validation côté serveur s'exécute sur chaque champ lorsqu'un formulaire de création ou de modification est soumis, afin que les données invalides n'atteignent jamais la base de données.

Le cycle de vie est fixe :

1. **Valeurs vides :** Lorsqu'une valeur soumise est vide, telle que `None`, `""` ou une collection vide, seul l'indicateur `required` est vérifié. Les validateurs sont ignorés.
2. **Valeurs renseignées :** Lorsque des données sont présentes, chaque fonction de la liste `validators` s'exécute dans l'ordre sur la valeur analysée.

#### Signature du validateur

Un validateur reçoit quatre arguments : `(request, field, value, form_values)`.

* **`request` :** L'objet de requête Starlette courant.
* **`field` :** L'instance de champ en cours de validation.
* **`value` :** La valeur analysée soumise pour ce champ.
* **`form_values` :** Un dictionnaire de toutes les données de formulaire analysées, indexé par nom de champ, ce qui permet d'inspecter les autres champs.

Pour rejeter une valeur, levez une `ValueError`. L'admin intercepte la première erreur d'un champ, ignore les validateurs restants de ce champ et collecte toutes les erreurs pour les afficher à côté de leurs champs de saisie.

#### Validateurs intégrés

Le module [`starlette_admin.validators`](../api/validators.md) fournit des règles standard :

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Validation personnalisée et asynchrone

Écrivez des validateurs personnalisés sous forme de fonctions synchrones ou asynchrones. Ils reçoivent la `request`, ils peuvent donc interroger la base de données pour vérifier des contraintes complexes.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

Avec l'argument `form_values`, un validateur au niveau du champ peut également appliquer une règle qui dépend d'un autre champ soumis.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Validation spécifique au contexte

* **Champs relationnels :** `HasOne` et `HasMany` reçoivent les clés primaires des enregistrements liés lors de la validation.
* **Champs de fichiers :** La validation s'exécute une fois par fichier téléversé. Voir [Champs de fichiers et médias](#file-media-fields).
* **Validation multi-champs :** Utilisez `form_values` pour une règle simple. Pour une règle qui couvre l'ensemble du formulaire, redéfinissez plutôt la méthode `validate()` sur votre vue. La validation au niveau de la vue ne s'exécute qu'après que chaque champ a franchi sa propre chaîne de validation.

### Stockage de métadonnées personnalisées

`extra` est un simple `dict` que `starlette-admin` ne lit ni n'écrit jamais. Utilisez-le pour attacher vos propres données à une instance de champ, pour un template personnalisé, un hook dans votre sous-classe de [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin), ou tout autre point d'intégration, sans sous-classer le champ :

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Champs de texte

### StringField & TextAreaField

`StringField` rend un champ de texte sur une seule ligne pour du contenu court. `TextAreaField` l'étend avec un élément `<textarea>` pour du texte long sur plusieurs lignes.

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| Attribut supplémentaire | Type | Défaut | Description |
| --- | --- | --- | --- |
| `maxlength` and `minlength` | `int | None` | `None` | Contraintes de longueur HTML. |
| `placeholder` | `str | None` | `None` | Texte indicatif du champ de saisie. |
| `rows` *(TextArea only)* | `int` | `6` | Nombre de lignes de texte visibles. |

### TinyMCEEditorField

Étend `TextAreaField` avec un éditeur WYSIWYG issu de la bibliothèque TinyMCE. Il nécessite le paquet additionnel `tinymce`.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    Les attributs `height`, `menubar`, `statusbar` et `toolbar` contrôlent l'interface de l'éditeur. Passez toute autre configuration native de TinyMCE via `extra_options`.

### Champs de texte formatés

Ces variantes de `StringField` rendent un type de saisie HTML correspondant et formatent la valeur lors de l'affichage de l'enregistrement.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField` et `IPAddressField` ajoutent chacun un validateur correspondant (`email`, `url`, `uuid` et `ip_address` issus de [`starlette_admin.validators`](../api/validators.md)) lorsque vous laissez `validators` vide. Passez vos propres `validators` pour le remplacer.

    `UUIDField` définit `copy_to_clipboard=True` par défaut. `IPAddressField` accepte `ipv4`, `True` par défaut, et `ipv6`, `False` par défaut, qui contrôlent les familles d'adresses acceptées par son validateur par défaut.

### PasswordField

Rend un élément `<input type="password">` dans les formulaires pour masquer ce que l'utilisateur tape.

!!! danger
    `PasswordField` masque la saisie uniquement sur les formulaires de création et de modification. Il ne remplace pas les templates d'affichage, les valeurs sont donc rendues en **texte brut** sur les pages de liste et de détail, et il journalise les valeurs brutes soumises au niveau `DEBUG`.

    Définissez `exclude_from_list = True` et `exclude_from_detail = True` sur les champs de mot de passe, et désactivez la journalisation `DEBUG` en production.

## Champs numériques

Les champs numériques gèrent les entiers, les flottants et les décimaux.

```python
from starlette_admin import DecimalField, FloatField, IntegerField
from starlette_admin.contrib.sqla import ModelView


class ProductView(ModelView):
    fields = [
        IntegerField("stock", min=0, max=10_000),
        FloatField("rating"),
        DecimalField("price", min=0, step="0.01"),
    ]
```

| Attribut supplémentaire | S'applique à | Description |
| --- | --- | --- |
| `min` and `max` | Integer, Decimal | Valeurs minimale et maximale autorisées. |
| `step` | Integer, Decimal | La contrainte de pas d'incrémentation. |

!!! note
    `FloatField` fonctionne différemment : il se rend comme un champ de texte simple, convertit la soumission en `float` et ne prend pas en charge `min`, `max` ni `step`.

## Champs de date et d'heure

Ces champs utilisent les sélecteurs natifs de date et d'heure du navigateur, adossés aux types correspondants de la bibliothèque standard (`datetime.date`, `datetime.datetime` et `datetime.time`).

```python
from starlette_admin import DateField, DateTimeField, TimeField
from starlette_admin.contrib.sqla import ModelView


class EventView(ModelView):
    fields = [
        DateField("event_date"),
        DateTimeField("starts_at", output_format="medium"),
        TimeField("daily_reminder"),
    ]
```

| Attribut supplémentaire | Type | Défaut | Description |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Format d'affichage Babel : `"short"`, `"medium"`, `"long"`, `"full"`, ou un motif personnalisé. |
| `search_format` | `str | None` | Spécifique à l'ORM | Format utilisé pour construire les requêtes de recherche en base de données. |

!!! note
    Lorsque la prise en charge des fuseaux horaires est activée, `DateTimeField` effectue pour vous les conversions entre le fuseau horaire d'affichage et le fuseau horaire de la base de données.

### ArrowField

Une variante de `DateTimeField` adossée à un objet `Arrow`. Hors des formulaires de modification, elle affiche une heure relative humanisée, telle que « il y a 3 heures ». Elle nécessite le paquet `arrow`.

## Champs de sélection et de collection

### EnumField

Le champ de sélection polyvalent. Il rend une liste déroulante `<select>`, ou un multi-select `select2` lorsque `multiple=True`. Adossez-le à une sous-classe de `Enum` Python, une liste de tuples, ou des choix chargés au moment de la requête.

```python
import enum
from starlette_admin import EnumField
from starlette_admin.contrib.sqla import ModelView


class Status(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class PostView(ModelView):
    fields = [
        EnumField("status", enum=Status),
        EnumField("language", choices=[("en", "English"), ("fr", "French")]),
    ]
```

| Attribut supplémentaire | Type | Description |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | Construit les choix à partir d'une classe `Enum` Python. |
| `choices` | `Sequence | None` | Paires `(value, label)` statiques, ou valeurs simples. |
| `choices_loader` | `Callable | None` | Calcule les choix à chaque requête. |
| `multiple` | `bool` | Active la sélection multiple et stocke les valeurs sous forme de liste. |

!!! important
    Fournissez exactement l'un parmi `enum`, `choices` ou `choices_loader`.

`TimeZoneField`, `CountryField` et `CurrencyField` sont des sous-classes de `EnumField` adossées aux données de localisation Babel, ce qui nécessite l'option `i18n`. Elles localisent leurs étiquettes selon la requête courante.

### TagsField

Un champ de saisie de tags en texte libre construit sur `select2`. Il stocke une `list[str]` et ne nécessite aucun choix prédéfini.

### ListField

Enveloppe un autre champ pour stocker une liste ordonnée de valeurs de ce type. Il se rend sous forme de lignes répétables avec des contrôles d'ajout et de suppression. Le nom du champ enveloppé devient le nom du `ListField`.

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Regroupe plusieurs sous-champs en un seul objet imbriqué. Utilisez-le pour des données intégrées ou de type structure, telles qu'un document intégré MongoDB.

```python
from starlette_admin import CollectionField, IntegerField, StringField

fields = [
    CollectionField(
        "shipping_address",
        fields=[
            StringField("street"),
            StringField("city"),
            IntegerField("floor", required=False),
        ],
    ),
]
```

## Champs spécialisés

### JSONField

Rend un arbre JSON et un éditeur de code, et stocke un `dict` Python. Passez un dictionnaire JSON Schema standard à `validation_schema` pour obtenir un retour côté client.

### SlugField

Une variante de `StringField` qui se remplit automatiquement côté client à partir de la saisie d'un autre champ. Une modification manuelle arrête le remplissage automatique.

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! important
    `populate_from` est requis et doit pointer vers un autre champ du même formulaire. Le slug généré est soumis et stocké comme toute autre chaîne.

### ComputedField

Un champ virtuel dérivé de l'instance de modèle au moment de l'affichage, sans colonne de base de données derrière lui. Il repose sur le [hook `getter`](#computing-formatting-and-parsing-values) dont dispose chaque champ, et ajoute les valeurs par défaut dont un champ virtuel a besoin : exclu des formulaires de création, en lecture seule, non recherchable et non triable.

```python
from starlette_admin import ComputedField

fields = [
    "first_name",
    "last_name",
    ComputedField(
        "full_name", getter=lambda request, obj: f"{obj.first_name} {obj.last_name}"
    ),
]
```

Pour une logique complexe ou réutilisable, sous-classez `ComputedField` et redéfinissez `parse_obj()` au lieu de passer un `getter` en ligne :

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` et `parse_obj` font le même travail : utilisez `getter` pour des expressions courtes, et sous-classez `ComputedField` lorsque la logique s'étend sur plusieurs lignes ou est réutilisée entre plusieurs vues. Sur les formulaires de modification, le champ apparaît toujours comme un affichage en texte brut, l'utilisateur voit donc la valeur calculée actuelle.

Chaque sous-classe de `ComputedField` conserve le rendu de `StringField`. Pour calculer une valeur qui doit être rendue comme un autre type, tel qu'une date, un badge ou une image, définissez `getter=` directement sur ce type de champ, accompagné des indicateurs `read_only` et `exclude_from_*` correspondants.

## Champs de fichiers et médias {#file-media-fields}

`FileField` rend un champ de téléversement de fichier, et `ImageField` ajoute un aperçu d'image et une vérification de validité. Attachez un backend `storage=` pour enregistrer automatiquement les téléversements et stocker un dictionnaire JSON `FileInfo` dans la base de données. Pour la configuration complète, consultez le [guide de stockage de fichiers](file-storage.md).

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")
documents_storage = LocalStorage(base_dir="uploads/documents", name="documents")


class ArticleView(ModelView):
    fields = [
        "id",
        "title",
        ImageField(
            "cover",
            storage=covers_storage,
            upload_folder="covers",
            max_size=5 * 1024 * 1024,
            thumbnail_size=(50, 50),
        ),
        FileField(
            "document",
            storage=documents_storage,
            upload_folder="documents",
            accept=".pdf,.doc,.docx",
        ),
    ]
```

| Attribut supplémentaire | Type | Défaut | Description |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | Liste séparée par des virgules des extensions de fichiers ou types MIME acceptés, passée à l'attribut HTML `accept`. |
| `multiple` | `bool` | `False` | Accepte plusieurs fichiers dans un seul champ. |
| `storage` | `BaseStorage | None` | `None` | Backend de stockage qui enregistre les téléversements. Sans lui, le champ transmet les téléversements bruts à votre backend. |
| `upload_folder` | `str` | `""` | Le dossier relatif au stockage pour les fichiers enregistrés. |
| `max_size` | `int | None` | `None` | Taille maximale de téléversement acceptée, en octets. |
| `validators` | `list[Validator]` | `[]` | Validateurs personnalisés, chacun appelé sous la forme `(request, field, upload)` une fois par fichier téléversé, après les vérifications `accept` et `max_size`. Levez une `ValueError` pour rejeter. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | `ImageField` uniquement. Lorsqu'il est défini, Pillow génère une vignette bornée à l'enregistrement, et la page de liste l'utilise à la place de l'image complète. |

!!! note
    `ImageField` ajoute en tête de la liste `validators` une vérification de validité d'image basée sur Pillow. Lorsque Pillow est installé et que le stockage est configuré, il enregistre également `width` et `height` dans le `FileInfo` résultant.

Avec `thumbnail_size` défini, l'admin génère une vignette aux côtés de l'image complète, en préservant le rapport hauteur/largeur et sans jamais agrandir l'image, et la stocke sous sa propre clé. Par exemple, `covers/cat.jpg` obtient un fichier voisin `covers/cat.thumb.jpg`. La page de liste utilise la vignette automatiquement. Les lignes qui n'en ont pas, issues de données préexistantes ou parce que `thumbnail_size` n'est pas défini, reviennent à l'image complète. Un échec de génération de vignette est journalisé et ne fait jamais échouer le téléversement.

La page de détail ouvre chaque image de `ImageField` dans une lightbox, permettant ainsi de parcourir les images en pleine résolution. Les images appartenant au même champ (`multiple=True`) sont regroupées dans une seule galerie.

Consultez [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) pour une application complète exécutable, incluant un validateur de type MIME personnalisé.

### Sans stockage

Sans `storage=` attaché, le champ transmet les téléversements bruts à votre backend au lieu de les enregistrer :

* **Dans les formulaires de création et de modification**, la valeur analysée est un tuple, `(UploadFile | list[UploadFile] | None, bool)`. Le premier élément est le `UploadFile` Starlette brut, une liste lorsque `multiple=True`, ou `None` lorsque l'utilisateur n'a rien sélectionné. Le second élément est `True` lorsque l'utilisateur coche la case de suppression sur le formulaire de modification, ce qui signifie qu'il souhaite supprimer le fichier existant sans le remplacer. La logique `create()` et `edit()` de votre backend enregistre le téléversement et honore l'indicateur de suppression.
* **Sur les pages de liste et de détail**, le champ attend que la valeur expose trois clés, sous forme de `dict`, ou trois attributs, sous forme d'objet : `url`, requis, la cible du lien ; `filename`, l'étiquette d'affichage ; et `content_type`, qui sélectionne l'icône de type de fichier.

Ce contrat est la façon dont les intégrations ORM ci-dessous branchent leur propre gestion de fichiers sur le même champ.

### Colonnes de fichiers natives ORM

**MongoEngine** prend en charge `mongoengine.FileField` et `mongoengine.ImageField` dès l'origine, avec **GridFS** comme stockage. L'admin téléverse dans GridFS, sert et supprime les fichiers de GridFS pour vous. Vous n'avez besoin d'aucune configuration `storage=` : listez simplement le champ par son nom.

**SQLAlchemy** bénéficie du même traitement via [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Déclarez ses types de colonnes `FileField` ou `ImageField` sur vos modèles, et `starlette-admin` les détecte, rend le champ admin correspondant et enregistre une route pour servir les fichiers stockés. Vous configurez le stockage via le `StorageManager` propre à sqlalchemy-file, adossé à des conteneurs Apache Libcloud, et les téléversements rejoignent la transaction de session, de sorte qu'une session annulée rejette le fichier stocké.

```python
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_file import ImageField
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import SizeValidator
from starlette_admin.contrib.sqla import ModelView


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    avatar = mapped_column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )


# sqlalchemy-file storage setup, independent of starlette-admin's BaseStorage
os.makedirs("upload/avatars", exist_ok=True)
StorageManager.add_storage(
    "avatar", LocalStorageDriver("upload").get_container("avatars")
)


class AuthorView(ModelView):
    fields = ["id", "name", "avatar"]
```

Consultez [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) pour une application complète avec plusieurs stockages, une validation de type de contenu et des champs `multiple=True`.

## HasOne & HasMany

Champs relationnels qui se rendent comme des entrées `select2`, adossés au endpoint de recherche de la vue liée.

```python
from starlette_admin import HasMany, HasOne, IntegerField, StringField
from starlette_admin.contrib.sqla import Admin, ModelView


class AuthorView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", identity="book"),
    ]


class BookView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        HasOne("author", identity="author"),
    ]
```

Le paramètre `identity` pointe vers la vue `ModelView` correspondante. Enregistrez les deux vues sur la même instance `Admin` pour que les clés se résolvent.

---

## À suivre

* [Filtres](filters.md) : construisez le générateur de filtres de vos pages de liste.
* [Stockage de fichiers](file-storage.md) : configurez les backends de stockage pour `FileField` et `ImageField`.
* [Champs personnalisés](../advanced/custom-fields.md) : créez un champ sur mesure.

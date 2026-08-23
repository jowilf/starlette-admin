---
title: Champs
description: Référence complète de tous les champs intégrés de starlette-admin pour
  mapper vos colonnes de base de données à des composants d'interface.
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

??? info "Traduction automatique supervisée"

    Ce contenu est généré par traduction automatique, guidée par des
    glossaires et des guides de style validés par des humains. Comme le
    texte n'est pas relu ligne par ligne, des erreurs ou des formulations
    maladroites peuvent parfois apparaître.

    En cas de divergence, la [version originale en anglais](https://jowilf.github.io/starlette-admin/) fait foi.

# Champs

Les champs sont les éléments constitutifs de vos vues. Sous le capot, ce sont de simples dataclasses Python : chaque attribut que vous passez au constructeur d'un champ devient un champ de la dataclass, et chaque type de champ hérite de `BaseField`, ce qui vous permet de l'inspecter, d'en créer une sous-classe ou de l'instancier directement.

## Attributs communs

Chaque type de champ hérite de `BaseField` cet ensemble d'attributs de configuration.

| Attribut | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `name` | `str` | **Obligatoire** | Le nom de l'attribut sur votre modèle. |
| `label` | `str | None` | `name` en casse de titre | L'en-tête de colonne et le libellé du formulaire. |
| `help_text` | `str | None` | `None` | Texte d'aide affiché sous la saisie du formulaire. |
| `required` | `bool` | `False` | Exige une valeur dans les formulaires, côté client comme côté serveur. |
| `validators` | `list[Validator]` | `[]` | Validateurs côté serveur exécutés sur la valeur soumise. Voir [Validation](#validation). |
| `disabled` | `bool` | `False` | Grise et verrouille la saisie dans les formulaires. |
| `read_only` | `bool` | `False` | Affiche le champ mais bloque les modifications. |
| `default` | `Any | Callable` | `None` | La valeur de préremplissage du formulaire de création. |
| `getter` | `Callable | None` | `None` | Remplace l'accès à l'attribut du modèle lors de la lecture de la valeur. Voir [Calculer, mettre en forme et analyser les valeurs](#computing-formatting-and-parsing-values). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Mise en forme d'affichage par action, qui remplace la sérialisation pour cette action. Voir [Calculer, mettre en forme et analyser les valeurs](#computing-formatting-and-parsing-values). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Analyse des entrées par action, qui remplace l'analyse par défaut du champ. Voir [Calculer, mettre en forme et analyser les valeurs](#computing-formatting-and-parsing-values). |
| `searchable` | `bool` | `True` | Inclus lorsque le paramètre de recherche `q` correspond. |
| `orderable` | `bool` | `True` | Ajoute un lien de tri dans l'en-tête de la page de liste. |
| `copy_to_clipboard` | `bool` | `False` | Ajoute un bouton de copie à côté de la valeur sur la page de détail. |
| `filters` | `list | None` | `None` | Remplacement explicite des filtres de la page de liste. |
| `extra` | `dict[str, Any]` | `{}` | Un dictionnaire pour vos propres métadonnées. |

### Contrôles de visibilité

Utilisez ces indicateurs booléens, tous à `False` par défaut, pour contrôler où un champ apparaît :

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Définir des valeurs par défaut

L'attribut `default` accepte une valeur statique, un callable sans argument ou une fonction tenant compte de la requête :

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### Calculer, mettre en forme et analyser les valeurs

Chaque champ accepte trois hooks appelables, `getter`, `formatter` et `parser`, qui interceptent et transforment les données lors de leurs échanges entre votre modèle et l'interface. Chacun accepte une fonction synchrone ou asynchrone.

#### `getter` : lire des valeurs personnalisées

Le hook `getter` remplace l'accès par défaut via `getattr()` lorsque le champ lit une instance de modèle. Le champ appelle `getter(request, obj)` et affiche la valeur retournée.

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Comme les valeurs produites par `getter` ne correspondent que rarement à une colonne physique de la base de données, elles s'accordent mieux avec un affichage en lecture seule. [`ComputedField`](#computedfield) est un raccourci intégré pour cette combinaison.

#### `formatter` : transformer la sortie affichée

Le hook `formatter` définit la façon dont une valeur stockée est rendue sur des pages spécifiques. Il associe une `RequestAction`, telle que `LIST`, `DETAIL` ou `EXPORT`, à un callable `(request, value) -> value`.

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

**Comportement de mise en forme à garder à l'esprit :**

* **Les valeurs nulles atteignent le formatter :** contrairement à la sérialisation par défaut, les formatters reçoivent les valeurs `None`, ce qui permet de fournir un texte de repli, tel que « unset » ci-dessus.
* **La sérialisation est ignorée :** un formatter correspondant remplace les méthodes `serialize_value` et `serialize_none_value` du champ. La valeur retournée est utilisée telle quelle, le formatter étant donc entièrement responsable du résultat final.
* **Exigence JSON :** les valeurs retournées pour les actions `LIST` et `RELATION_LOOKUP` doivent rester sérialisables en JSON.

#### `parser` : traiter les données entrantes

Le hook `parser` surcharge l'analyse par défaut des données soumises ou importées par le champ. Il associe une `RequestAction` à un callable `(request, raw) -> value`.

* **Formulaires (`CREATE`, `EDIT`, `INLINE_EDIT`) :** `raw` est la saisie du formulaire soumis, ou une liste lorsque `multiple=True`.
* **Importations (`IMPORT`) :** `raw` est la valeur brute de la cellule du fichier.

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

Après l'analyse, la valeur retournée suit la chaîne de validation standard, `required` puis `validators`, exactement comme si le champ avait analysé lui-même les données.

!!! tip "Hooks ou sous-classe ?"
    Pour une personnalisation ponctuelle sur un seul champ, vous avez rarement besoin d'une sous-classe. Passez ces hooks comme arguments du constructeur pour gérer la lecture, la mise en forme de l'affichage et l'analyse des entrées. [Créez une sous-classe du champ](../advanced/custom-fields.md) lorsque vous réutilisez la logique entre plusieurs vues, ou lorsque vous devez modifier les templates de rendu HTML.

### Validation

La validation côté serveur s'exécute sur chaque champ lorsqu'un formulaire de création ou de modification est soumis, afin que des données erronées n'atteignent jamais la base de données.

Le cycle de vie est fixe :

1. **Valeurs vides :** lorsqu'une valeur soumise est vide, comme `None`, `""` ou une collection vide, seul l'indicateur `required` est vérifié. Les validateurs sont ignorés.
2. **Valeurs renseignées :** lorsque des données sont présentes, chaque callable de la liste `validators` est exécuté dans l'ordre sur la valeur analysée.

#### Signature d'un validateur

Un validateur reçoit quatre arguments : `(request, field, value, form_values)`.

* **`request` :** l'objet requête Starlette courant.
* **`field` :** l'instance de champ en cours de validation.
* **`value` :** la valeur analysée soumise pour ce champ.
* **`form_values` :** un dictionnaire contenant toutes les données du formulaire analysées, indexé par nom de champ, ce qui permet d'inspecter les autres champs.

Pour rejeter une valeur, levez une `ValueError`. Le panneau d'administration intercepte la première erreur d'un champ, ignore ses validateurs restants et collecte toutes les erreurs pour les afficher à côté des champs concernés.

#### Validateurs intégrés

Le module [`starlette_admin.validators`](../api/validators.md) fournit des règles standards :

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Validation personnalisée et asynchrone

Écrivez des validateurs personnalisés sous forme de fonctions synchrones ou asynchrones. Ils reçoivent la `request` et peuvent donc interroger la base de données pour vérifier des contraintes complexes.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

Grâce à l'argument `form_values`, un validateur au niveau d'un champ peut aussi imposer une règle dépendant d'un autre champ soumis.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Règles de validation spécifiques au contexte

* **Champs de relation :** `HasOne` et `HasMany` reçoivent les clés primaires des enregistrements liés pendant la validation.
* **Champs de fichier :** la validation s'exécute une fois par `UploadFile` présent dans la charge utile. Voir [Champs de fichiers et médias](#file-media-fields).
* **Validation multi-champs :** utilisez `form_values` pour une simple dépendance. Pour une règle couvrant tout le formulaire, surchargez plutôt la méthode `validate()` de votre vue. La validation au niveau de la vue ne s'exécute qu'une fois que chaque champ a franchi sa propre chaîne de validation.

### Stocker des métadonnées personnalisées

`extra` est un simple `dict` que `starlette-admin` ne lit ni n'écrit jamais. Utilisez-le pour associer vos propres données à une instance de champ, pour un template personnalisé, un hook dans votre sous-classe de [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin), ou tout autre point d'intégration, sans créer de sous-classe du champ :

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Champs de texte

### StringField & TextAreaField

`StringField` affiche un champ de saisie texte sur une seule ligne pour les contenus courts. `TextAreaField` l'étend avec un élément `<textarea>` pour les textes longs sur plusieurs lignes.

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| Attribut supplémentaire | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `maxlength` et `minlength` | `int | None` | `None` | Contraintes de longueur HTML. |
| `placeholder` | `str | None` | `None` | Texte placeholder de la saisie. |
| `rows` *(TextArea uniquement)* | `int` | `6` | Nombre de lignes de texte visibles. |

### TinyMCEEditorField

Étend `TextAreaField` avec un éditeur WYSIWYG issu de la bibliothèque TinyMCE. Nécessite l'extra `tinymce`.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    Les attributs `height`, `menubar`, `statusbar` et `toolbar` contrôlent l'interface de l'éditeur. Passez toute autre configuration native de TinyMCE via `extra_options`.

### Champs de texte formatés

Ces variantes de `StringField` affichent un type de saisie HTML correspondant et mettent en forme la valeur lors de l'affichage de l'enregistrement.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField` et `IPAddressField` ajoutent chacun un validateur correspondant (`email`, `url`, `uuid` et `ip_address` de [`starlette_admin.validators`](../api/validators.md)) lorsque `validators` est laissé vide. Passez vos propres `validators` pour le remplacer.

    `UUIDField` définit `copy_to_clipboard=True` par défaut. `IPAddressField` accepte `ipv4` (`True` par défaut) et `ipv6` (`False` par défaut), qui contrôlent les familles d'adresses acceptées par son validateur par défaut.

### PasswordField

Affiche un élément `<input type="password">` dans les formulaires pour masquer la saisie de l'utilisateur.

!!! danger
    `PasswordField` masque la saisie uniquement sur les formulaires de création et de modification. Il ne surcharge pas les templates d'affichage : les valeurs apparaissent donc en **texte brut** sur les pages de liste et de détail, et il consigne les valeurs brutes soumises au niveau `DEBUG`.

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
| `min` et `max` | Integer, Decimal | Valeurs minimale et maximale autorisées. |
| `step` | Integer, Decimal | Contrainte de pas d'incrémentation. |

!!! note
    `FloatField` fonctionne différemment : il s'affiche comme un champ de saisie texte simple, convertit la valeur soumise en `float` et ne prend pas en charge `min`, `max` ni `step`.

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

| Attribut supplémentaire | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Format d'affichage Babel : « short », « medium », « long », « full » ou un motif personnalisé. |
| `search_format` | `str | None` | Spécifique à l'ORM | Format utilisé pour construire les requêtes de recherche en base de données. |

!!! note
    Lorsque la prise en charge des fuseaux horaires est activée, `DateTimeField` effectue pour vous les conversions entre le fuseau horaire d'affichage et celui de la base de données.

### ArrowField

Une variante de `DateTimeField` adossée à un objet `Arrow`. En dehors des formulaires de modification, elle affiche une durée relative humanisée, telle que « il y a 3 heures ». Nécessite le paquet `arrow`.

## Champs de sélection et de collections

### EnumField

Le champ de sélection universel. Il affiche un menu déroulant `<select>`, ou une sélection multiple `select2` lorsque `multiple=True`. Adossez-le à une sous-classe de `Enum` Python, à une liste de tuples ou à des choix chargés au moment de la requête.

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
| `choices` | `Sequence | None` | Paires statiques `(value, label)`, ou valeurs simples. |
| `choices_loader` | `Callable | None` | Calcule les choix à chaque requête. |
| `multiple` | `bool` | Active la sélection multiple et stocke les valeurs sous forme de liste. |

!!! important
    Fournissez exactement l'un des paramètres suivants : `enum`, `choices` ou `choices_loader`.

`TimeZoneField`, `CountryField` et `CurrencyField` sont des sous-classes de `EnumField` adossées aux données locales de Babel, ce qui nécessite l'extra `i18n`. Elles localisent leurs libellés selon la requête courante.

### TagsField

Un champ de saisie de balises en texte libre construit sur `select2`. Il stocke une `list[str]` et ne nécessite aucun choix prédéfini.

### ListField

Enveloppe un autre champ pour stocker une liste ordonnée de valeurs de ce type. Il s'affiche sous forme de lignes répétables avec des contrôles d'ajout et de suppression. Le nom du champ enveloppé devient le nom du `ListField`.

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Regroupe plusieurs sous-champs dans un objet imbriqué. Utilisez-le pour des données embarquées ou de type struct, telles qu'un document MongoDB embarqué.

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

Affiche un arbre JSON et un éditeur de code, et stocke un `dict` Python. Passez un dictionnaire JSON Schema standard à `validation_schema` pour obtenir un retour côté client.

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
    `populate_from` est obligatoire et doit pointer vers un autre champ du même formulaire. Le slug généré est soumis et stocké comme toute autre chaîne de caractères.

### ComputedField

Un champ virtuel en lecture seule, calculé à partir de l'instance de modèle au moment de l'affichage, sans colonne de base de données sous-jacente. Il s'appuie sur le [hook `getter`](#computing-formatting-and-parsing-values) présent dans chaque champ et ajoute les valeurs par défaut nécessaires à une colonne virtuelle : exclu des formulaires de création, en lecture seule, non recherchable et non triable.

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

Pour une logique complexe ou réutilisable, créez une sous-classe de `ComputedField` et surchargez `parse_obj()` au lieu de passer un `getter` inline :

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` et `parse_obj` font le même travail : utilisez `getter` pour des expressions courtes et créez une sous-classe de `ComputedField` lorsque la logique tient sur plusieurs lignes ou est réutilisée entre plusieurs vues. Sur les formulaires de modification, le champ reste affiché comme du texte simple, si bien que l'utilisateur voit la valeur calculée actuelle.

Chaque sous-classe de `ComputedField` conserve le rendu de `StringField`. Pour calculer une valeur devant s'afficher sous un autre type, comme une date, un badge ou une image, définissez directement `getter=` sur ce type de champ, accompagné des indicateurs `read_only` et `exclude_from_*` appropriés.

## Champs de fichiers et médias

`FileField` affiche un champ de téléversement de fichier, et `ImageField` ajoute un aperçu de l'image et une vérification de validité. Attachez un backend via `storage=` pour sauvegarder automatiquement les fichiers téléversés et stocker un dictionnaire JSON `FileInfo` dans la base de données. Pour la configuration complète, consultez le [guide du stockage de fichiers](file-storage.md).

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

| Attribut supplémentaire | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | Liste séparée par des virgules des extensions de fichier ou types MIME acceptés, passée à l'attribut HTML `accept`. |
| `multiple` | `bool` | `False` | Accepte plusieurs fichiers dans un même champ. |
| `storage` | `BaseStorage | None` | `None` | Backend de stockage qui sauvegarde les fichiers téléversés. Sans lui, le champ transmet les fichiers bruts à votre backend. |
| `upload_folder` | `str` | `""` | Dossier relatif au stockage pour les fichiers sauvegardés. |
| `max_size` | `int | None` | `None` | Taille maximale de téléversement acceptée, en octets. |
| `validators` | `list[Validator]` | `[]` | Validateurs personnalisés, chacun appelé sous la forme `(request, field, upload)` une fois par fichier téléversé, après les vérifications `accept` et `max_size`. Levez une `ValueError` pour rejeter. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | `ImageField` uniquement. Lorsqu'il est défini, Pillow génère une vignette dimensionnée à la sauvegarde, et la page de liste l'utilise à la place de l'image complète. |

!!! note
    `ImageField` ajoute une vérification de validité d'image basée sur Pillow au début de la liste `validators`. Lorsque Pillow est installé et que le stockage est configuré, il enregistre aussi `width` et `height` dans le `FileInfo` résultant.

Lorsque `thumbnail_size` est défini, le panneau d'administration génère une vignette en plus de l'image complète, en préservant le ratio d'aspect et sans jamais agrandir l'image, puis la stocke sous sa propre clé. Par exemple, `covers/cat.jpg` obtient un fichier frère `covers/cat.thumb.jpg`. La page de liste utilise automatiquement la vignette. Les lignes dépourvues de vignette, qu'il s'agisse de données préexistantes ou parce que `thumbnail_size` n'est pas défini, utilisent l'image complète en solution de repli. Un échec de génération de vignette est journalisé et ne fait jamais échouer le téléversement.

La page de détail ouvre chaque image d'un `ImageField` dans une lightbox, ce qui permet de parcourir les images en pleine résolution. Les images appartenant à un même champ (`multiple=True`) sont regroupées dans une seule galerie.

Consultez [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) pour une application complète et exécutable, incluant un validateur de type MIME personnalisé.

### Sans backend de stockage

Sans `storage=` attaché, le champ transmet les fichiers téléversés bruts à votre backend au lieu de les sauvegarder :

* **Dans les formulaires de création et de modification**, la valeur analysée est un tuple `(UploadFile | list[UploadFile] | None, bool)`. Le premier élément est le `UploadFile` Starlette brut, une liste lorsque `multiple=True`, ou `None` lorsque l'utilisateur n'a rien sélectionné. Le second élément vaut `True` lorsque l'utilisateur coche la case de suppression sur le formulaire de modification, ce qui signifie qu'il souhaite supprimer le fichier existant sans le remplacer. La logique `create()` et `edit()` de votre backend sauvegarde le fichier téléversé et honore le drapeau de suppression.
* **Sur les pages de liste et de détail**, le champ attend que la valeur expose trois clés, sous forme de `dict`, ou trois attributs, sous forme d'objet : `url`, obligatoire, la cible du lien ; `filename`, le libellé affiché ; et `content_type`, qui sélectionne l'icône de type de fichier.

C'est ce contrat qui permet aux intégrations ORM ci-dessous de brancher leur propre gestion de fichiers sur le même champ.

### Colonnes de fichiers natives ORM

**MongoEngine** prend en charge `mongoengine.FileField` et `mongoengine.ImageField` dès l'installation, avec **GridFS** comme stockage. Le panneau d'administration téléverse vers GridFS, sert et supprime les fichiers pour vous. Aucune configuration `storage=` n'est nécessaire : il suffit de lister le champ par son nom.

**SQLAlchemy** bénéficie du même traitement via [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Déclarez ses types de colonnes `FileField` ou `ImageField` sur vos modèles, et `starlette-admin` les détecte, affiche le champ d'administration correspondant et enregistre un endpoint pour servir les fichiers stockés. Vous configurez le stockage via le `StorageManager` propre à sqlalchemy-file, adossé à des containers Apache Libcloud, et les téléversements participent à la transaction de la session : une session annulée abandonne donc le fichier stocké.

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

Des champs de relation qui s'affichent sous forme de champs `select2`, adossés à l'endpoint de recherche de la vue associée.

```python
from starlette_admin import HasMany, HasOne, IntegerField, StringField
from starlette_admin.contrib.sqla import Admin, ModelView


class AuthorView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", key="book"),
    ]


class BookView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        HasOne("author", key="author"),
    ]
```

Le paramètre `key` pointe vers le `ModelView` correspondant. Inscrivez les deux vues sur la même instance `Admin` afin que les clés soient résolues.

---

## Pour aller plus loin

* [Filtres](filters.md) : personnalisez le générateur de filtres de vos pages de liste.
* [Stockage de fichiers](file-storage.md) : configurez les backends de stockage pour `FileField` et `ImageField`.
* [Champs personnalisés](../advanced/custom-fields.md) : créez un champ personnalisé.

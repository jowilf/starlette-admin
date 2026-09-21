---
title: Export et import
description: Activer l'export CSV, JSON et PDF ainsi que les imports de données en
  masse avec validation dans starlette-admin.
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/export-import/)
<!-- translation-notice:end -->

# Export et import

Chaque page de liste permet aux utilisateurs d'exporter les données vers un fichier et d'importer des données depuis un fichier, sans que vous ayez à écrire de routes personnalisées.

## Vue d'ensemble

* **Export :** L'utilisateur clique sur le bouton de la barre d'outils, puis définit la portée, les champs, le format et le nom du fichier.
* **Import :** L'utilisateur clique sur le bouton de la barre d'outils pour ouvrir un assistant en trois étapes : upload, aperçu et résultats.
* **Formats :** Les formats CSV, JSON, XLSX, ODS, YAML, PDF et les formats personnalisés sont pris en charge nativement.
* **Upsert :** Les imports peuvent optionnellement mettre à jour les enregistrements existants correspondant par clé primaire.
* **Intégration :** Les deux fonctionnalités fonctionnent avec le filtrage, le tri, la sélection de lignes et les champs adossés au stockage.
* **Aucun endpoint supplémentaire :** Tout est fourni avec la vue.

## Exemple minimal

```python hl_lines="23 24"
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///store.sqlite")


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column()


class ProductView(ModelView):
    fields = ["id", "name", "description", "price"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

`ProductView` affiche désormais un bouton **Export** et un bouton **Import** dans la barre d'outils de la liste. Chaque boîte de dialogue propose exactement les formats que vous listez dans `exporters` et `importers`.

---

## Activation de l'export

L'attribut `exporters` liste les formats à exposer, sous forme de simples chaînes d'extension :

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]
```

La valeur par défaut est `["csv", "json"]`. Le tableau ci-dessous récapitule chaque format intégré et le paquet dont il dépend. Les formats `csv`, `tsv` et `json` ne nécessitent aucune dépendance supplémentaire. Tous les autres formats tabulaires utilisent `tablib`, et `pdf` utilise `reportlab`. Une chaîne de format inconnue, ou un format dont le paquet n'est pas installé, provoque une erreur au démarrage.

| Format | Dépendance à installer |
| --- | --- |
| `csv`, `tsv`, `json` | Inclus dans le cœur |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Surcharge des options de format

Chaque chaîne de format correspond à une instance d'exportateur préconfigurée avec des valeurs par défaut raisonnables. Lorsqu'un format nécessite des réglages différents, passez une instance d'exportateur plutôt que la chaîne. Vous pouvez mélanger chaînes et instances dans la même liste :

```python hl_lines="5"
from starlette_admin.export import CsvExporter


class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]
```

`CsvExporter` transmet les arguments nommés à `csv.writer` et accepte un paramètre `escape_formulas`. `TablibExporter(format, **kwargs)` couvre tous les formats de tablib et transmet les arguments nommés à `tablib.Dataset.export()`.

!!! warning
    L'échappement des formules est désactivé par défaut. Si les champs exportés peuvent contenir des chaînes saisies par l'utilisateur, définissez `escape_formulas=True` sur `CsvExporter`, `TsvExporter` ou `TablibExporter` pour éviter l'injection de formules lorsque quelqu'un ouvre le fichier dans un tableur. Consultez [Injection de formules](security.md#formula-injection).

L'export est activé par défaut. Le bouton **Export** apparaît dans la barre d'outils dès que la liste `exporters` n'est pas vide. Pour restreindre qui peut exporter, redéfinissez la méthode `can_export(request)` :

```python hl_lines="5 6"
from starlette.requests import Request


class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"
```

### La boîte de dialogue d'export

L'export est une action globale intégrée. Un clic sur **Export** ouvre une boîte de dialogue où l'utilisateur configure l'export avant de le télécharger.

* **Portée :** Ce qu'il faut exporter. Les options sont « Selected rows », la valeur par défaut lorsque des lignes sont cochées, « All matching rows », disponible via la bannière de sélection globale, et « Current page », la valeur par défaut lorsqu'aucune ligne n'est sélectionnée.
* **Champs :** Une case à cocher par champ exportable. Désélectionner une case supprime cette colonne. Les champs marqués `exclude_from_export=True` n'apparaissent jamais ici.
* **Format :** Une entrée par format présent dans `exporters`.
* **Nom du fichier :** Par défaut, la clé de la vue. Le serveur ajoute l'extension du fichier.

Chaque portée tient compte de la recherche, des filtres et de l'ordre de tri courants de la page de liste : ce que l'utilisateur voit est ce qu'il exporte.

### Le plafond de lignes

```python
from starlette_admin.export import ExportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    export_config=ExportConfig(max_rows=50_000),
)
```

`ExportConfig.max_rows` vaut 100 000 par défaut. Ce plafond s'applique au nombre de lignes que la portée choisie produirait réellement, et l'interface d'administration vérifie ce nombre avant de récupérer la moindre ligne. Lorsque le nombre dépasse la limite, l'interface affiche un message d'erreur et redirige vers la page de liste au lieu de générer le fichier. Cela évite qu'un export large et non filtré sur une grande table ne bloque la requête. Définissez `max_rows=None` pour supprimer la limite.

---

## Activation de l'import

L'attribut `importers` fonctionne exactement comme `exporters` et accepte des chaînes de format :

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]
```

Les formats d'import intégrés sont `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` et `html`, avec les mêmes dépendances que leurs équivalents d'export. Pour surcharger les valeurs par défaut d'un format, passez une instance d'importeur, telle que `CsvImporter(delimiter=";")` issue de `starlette_admin.importers`.

L'import est activé par défaut, avec `["csv", "json"]`. Le bouton **Import** apparaît dans la barre d'outils dès que la liste `importers` n'est pas vide. Pour restreindre qui peut importer, redéfinissez la méthode `can_import(request)` :

```python hl_lines="5 6"
from starlette.requests import Request


class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"
```

### L'assistant d'import

Un clic sur **Import** ouvre un assistant en trois étapes. Rien n'est écrit dans la base de données avant la confirmation finale, et aucun fichier n'est stocké sur le serveur entre les étapes : le navigateur conserve le fichier et le renvoie à chaque étape.

1. **Upload :** Choisissez un format, sélectionnez un fichier et cochez éventuellement **Update existing records by primary key**. Lorsque cette option est cochée, une ligne dont la clé primaire correspond à un enregistrement existant met celui-ci à jour au lieu d'en créer un nouveau. Sinon, chaque ligne est créée.
2. **Preview :** La soumission de l'upload déclenche une validation complète sans rien écrire. L'assistant affiche un résumé, les correspondances de colonnes, des exemples de lignes et un tableau détaillé des erreurs.
3. **Result :** L'assistant valide l'import et indique les nombres finaux d'enregistrements créés, mis à jour et ignorés. Les lignes ayant échoué à la validation lors de l'aperçu sont ignorées.

!!! tip
    Pour laisser le backend générer les clés primaires, désélectionnez la colonne de clé primaire dans les correspondances de l'aperçu. Les lignes importées ne portent alors aucune valeur de clé, si bien que réimporter un fichier précédemment exporté crée de nouveaux enregistrements au lieu d'échouer sur des identifiants obsolètes.

### Plafonds d'upload et de lignes

```python
from starlette_admin.importers import ImportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    import_config=ImportConfig(max_rows=50_000),
)
```

L'endpoint d'import applique le même plafond de lignes que l'export. `ImportConfig.max_rows` vaut 100 000 par défaut et est contrôlé avant la création de tout enregistrement. L'interface d'administration compte les lignes du fichier téléversé dans une pré-passe et rejette, avec une erreur HTTP 400, tout fichier contenant plus de lignes que le plafond autorisé. Définissez `max_rows=None` pour supprimer la limite. `ImportConfig.max_upload_size` limite également les uploads à 10 Mo par défaut.

### Correspondance des en-têtes

L'assistant fait correspondre chaque en-tête du fichier d'abord au `label` de votre champ, puis à son `name`. Un fichier avec la colonne `Name` et un fichier avec la colonne `name` correspondent tous deux au champ nommé `name`. Les colonnes non reconnues sont ignorées, et les champs sans colonne correspondante reçoivent `None`.

## Champs fichier

Une vue comportant un champ `FileField` ou `ImageField` adossé au stockage s'exporte sous forme d'archive ZIP, afin que le contenu des fichiers accompagne les données des lignes :

```python
from sqlalchemy import Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///catalog.sqlite")
covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    photo: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ProductView(ModelView):
    fields = [
        "id",
        "name",
        ImageField("photo", storage=covers_storage, upload_folder="products"),
    ]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Catalog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

L'export de `ProductView` vers CSV produit un `export.zip` structuré ainsi :

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

La colonne `photo` de `export.csv` contient le chemin du fichier relatif à la racine du ZIP, soit `assets/<storage-name>/<key>`, ce qui maintient le CSV lisible dans un tableur. L'interface d'administration récupère chaque fichier référencé depuis son backend de stockage et le place sous `assets/`.

L'import n'accepte pas les archives ZIP. Les champs `FileField` et `ImageField` sont toujours exclus de l'import, car ils ont `exclude_from_import=True` par défaut ; l'assistant ignore donc la colonne `photo` lors de l'upload. Réimportez un simple fichier de données, puis joignez les fichiers via les formulaires de création ou d'édition.


## Écrire un exportateur personnalisé

Pour écrire un exportateur personnalisé, héritez de `BaseExporter` et implémentez la méthode `generate`. La classe de base gère l'emballage ZIP, le téléchargement des fichiers et les en-têtes de réponse :

```python
from typing import Any
from starlette_admin.export import BaseExporter
from starlette_admin.fields import BaseField


class MarkdownExporter(BaseExporter):
    content_type = "text/markdown"
    extension = "md"

    async def generate(
        self, fields: list[BaseField], rows: list[dict[str, Any]]
    ) -> bytes:
        lines = [
            " | ".join(f.label or f.name for f in fields),
            " | ".join("---" for _ in fields),
        ]
        for row in rows:
            lines.append(" | ".join(str(row.get(f.name, "")) for f in fields))
        return "\n".join(lines).encode("utf-8")
```

Les données de `rows` arrivent déjà nettoyées : l'interface d'administration remplace d'abord chaque valeur `FileField` et `ImageField` par sa chaîne de chemin relative au ZIP, de sorte que votre méthode `generate` ne manipule jamais de dictionnaires de fichiers. Enregistrez `MarkdownExporter()` dans votre liste `exporters` pour l'afficher dans le menu déroulant des formats.

## Écrire un importateur personnalisé

Pour écrire un importateur personnalisé, héritez de `BaseImporter` et implémentez `parse` comme un générateur asynchrone produisant un dictionnaire par ligne :

```python
import json
from collections.abc import AsyncGenerator
from typing import Any
from starlette_admin.importers import BaseImporter, ImportContext


class NdjsonImporter(BaseImporter):
    extension = "ndjson"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        for line in ctx.content.decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)
```

---

## Et ensuite

* **[File Storage](file-storage.md) :** Configurer les backends de stockage référencés dans l'archive ZIP d'export.
* **[Security](security.md) :** Plafonds de lignes d'export et limites de taille d'upload pour l'import.
* **[Actions](actions.md) :** Ajouter des actions groupées et des actions par ligne en complément de l'export et de l'import.

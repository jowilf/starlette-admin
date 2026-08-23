---
title: Exportation et importation
description: Activez l'exportation CSV, JSON et PDF ainsi que l'importation de données
  en masse avec validation dans starlette-admin.
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
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

# Exportation et importation

Chaque page de liste permet aux utilisateurs d'exporter des données vers un fichier et d'importer des données depuis un fichier, ce qui vous évite d'écrire des routes personnalisées.

## Vue d'ensemble

* **Exportation :** Les utilisateurs sélectionnent le bouton de la barre d'outils, puis définissent la portée, les champs, le format et le nom du fichier.
* **Importation :** Les utilisateurs sélectionnent le bouton de la barre d'outils pour ouvrir un assistant en trois étapes : téléversement, aperçu et résultats.
* **Formats :** CSV, JSON, XLSX, ODS, YAML, PDF et des formats personnalisés sont pris en charge par défaut.
* **Upsert :** Les importations peuvent mettre à jour des enregistrements existants correspondant à une clé primaire.
* **Intégration :** Ces deux fonctionnalités fonctionnent avec le filtrage, le tri, la sélection de lignes et les champs adossés à un stockage.
* **Aucun endpoint supplémentaire :** Tout est inclus dans la vue.

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

`ProductView` affiche désormais un bouton **Export** et un bouton **Import** dans la barre d'outils de la page de liste. Chaque boîte de dialogue propose exactement les formats que vous listez dans `exporters` et `importers`.

---

## Activer l'exportation

L'attribut `exporters` liste les formats à exposer, sous forme de chaînes d'extension simples :

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

La valeur par défaut est `["csv", "json"]`. Le tableau ci-dessous liste chaque format intégré et le package dont il a besoin. Les formats `csv`, `tsv` et `json` ne nécessitent aucune dépendance supplémentaire. Tous les autres formats tabulaires utilisent `tablib`, et `pdf` utilise `reportlab`. Une chaîne de format inconnue, ou un format dont le package n'est pas installé, provoque une erreur au démarrage.

| Format | Dépendance à installer |
| --- | --- |
| `csv`, `tsv`, `json` | Inclus dans le cœur |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Surcharger les options de format

Chaque chaîne de format correspond à une instance d'exportateur préconfigurée avec des valeurs par défaut raisonnables. Lorsqu'un format nécessite des réglages différents, passez une instance d'exportateur plutôt que la chaîne. Vous pouvez mélanger chaînes et instances dans la même liste :

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` transmet ses arguments nommés à `csv.writer` et accepte un paramètre `escape_formulas`. `TablibExporter(format, **kwargs)` couvre tous les formats de tablib et transmet ses arguments nommés à `tablib.Dataset.export()`.

!!! warning
    L'échappement des formules est désactivé par défaut. Si les champs exportés peuvent contenir des chaînes fournies par les utilisateurs, définissez `escape_formulas=True` sur `CsvExporter`, `TsvExporter` ou `TablibExporter` afin de prévenir l'injection de formules lorsqu'une personne ouvre le fichier dans un tableur. Voir [Injection de formules](security.md#formula-injection).

L'exportation est activée par défaut. Le bouton **Export** apparaît dans la barre d'outils dès lors que la liste `exporters` n'est pas vide. Pour restreindre qui peut exporter, redéfinissez la méthode `can_export(request)` :

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### La boîte de dialogue d'exportation

L'exportation est une action globale intégrée. Sélectionner **Export** ouvre une boîte de dialogue où l'utilisateur configure l'exportation avant de la télécharger.

* **Portée :** Ce qu'il faut exporter. Les options sont « Selected rows », la valeur par défaut lorsque des lignes sont cochées, « All matching rows », disponible depuis la bannière de sélection globale, et « Current page », la valeur par défaut lorsqu'aucune ligne n'est sélectionnée.
* **Champs :** Une case à cocher par champ exportable. Décocher une case supprime cette colonne. Les champs marqués `exclude_from_export=True` n'apparaissent jamais ici.
* **Format :** Une entrée par format présent dans `exporters`.
* **Nom du fichier :** Par défaut, la clé de la vue. Le serveur ajoute l'extension du fichier.

Chaque portée respecte la recherche, les filtres et l'ordre de tri actuels de la page de liste ; ainsi, ce que l'utilisateur voit est ce qu'il exporte.

### La limite de lignes

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

`ExportConfig.max_rows` vaut 100 000 par défaut. La limite s'applique au nombre de lignes que la portée choisie produirait réellement, et le panneau d'administration vérifie ce décompte avant de récupérer la moindre ligne. Lorsque le décompte dépasse la limite, le panneau d'affiche un message flash d'erreur et redirige vers la page de liste au lieu de générer le fichier. Cela évite qu'un export large et non filtré sur une grande table ne bloque la requête. Définissez `max_rows=None` pour supprimer la limite.

---

## Activer l'importation

L'attribut `importers` fonctionne exactement comme `exporters` et accepte des chaînes de format :

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

Les formats d'importation intégrés sont `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` et `html`, avec les mêmes dépendances que leurs homologues d'exportation. Pour remplacer les valeurs par défaut d'un format, passez une instance d'importeur, telle que `CsvImporter(delimiter=";")` issue de `starlette_admin.importers`.

L'importation est activée par défaut, avec `["csv", "json"]`. Le bouton **Import** apparaît dans la barre d'outils dès lors que la liste `importers` n'est pas vide. Pour restreindre qui peut importer, redéfinissez la méthode `can_import(request)` :

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### L'assistant d'importation

Sélectionner **Import** ouvre un assistant en trois étapes. Rien n'est écrit dans la base de données avant la confirmation finale, et aucun fichier n'est stocké sur le serveur entre les étapes : le navigateur conserve le fichier et le renvoie à chaque étape.

1. **Téléversement :** Choisissez un format, sélectionnez un fichier et, éventuellement, cochez **Update existing records by primary key**. Lorsque vous cochez cette option, une ligne dont la clé primaire correspond à un enregistrement existant met à jour cet enregistrement au lieu d'en créer un nouveau. Sinon, toutes les lignes sont créées.
2. **Aperçu :** La soumission du téléversement lance une validation complète sans rien écrire. L'assistant affiche un résumé, les correspondances de colonnes, des exemples de lignes et un tableau détaillé des erreurs.
3. **Résultat :** L'assistant valide l'importation et rapporte les décomptes finaux des enregistrements créés, mis à jour et ignorés. Les lignes ayant échoué à la validation pendant l'aperçu sont ignorées.

!!! tip
    Pour laisser le backend générer les clés primaires, effacez la colonne de clé primaire dans la correspondance de l'aperçu. Les lignes importées ne porteront alors aucune valeur de clé, si bien que la réimportation d'un fichier que vous avez exporté crée de nouveaux enregistrements au lieu d'échouer sur des identifiants obsolètes.

### Limites de téléversement et de lignes

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

L'endpoint d'importation reflète la limite de lignes de l'exportation. `ImportConfig.max_rows` vaut 100 000 par défaut et est appliqué avant la création de tout enregistrement. Le panneau d'administration compte le fichier téléversé lors d'une passe préliminaire et rejette tout fichier contenant plus de lignes que la limite avec une erreur HTTP 400. Définissez `max_rows=None` pour supprimer la limite. `ImportConfig.max_upload_size` plafonne également les téléversements à 10 Mo par défaut.

### Correspondance des en-têtes

L'assistant fait correspondre chaque en-tête du fichier d'abord au `label` de votre champ, puis à son `name`. Un fichier avec la colonne `Name` et un fichier avec la colonne `name` correspondent tous deux au champ nommé `name`. Les colonnes non reconnues sont ignorées, et les champs sans colonne correspondante reçoivent `None`.

## Champs de fichiers

Une vue comportant un `FileField` ou un `ImageField` adossé à un stockage exporte sous forme d'archive ZIP, de sorte que le contenu des fichiers accompagne les données des lignes :

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

L'exportation de `ProductView` en CSV produit un fichier `export.zip` avec cette structure :

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

La colonne `photo` dans `export.csv` contient le chemin du fichier relatif à la racine du ZIP, `assets/<storage-name>/<key>`, ce qui garde le CSV lisible dans un tableur. Le panneau d'administration récupère chaque fichier référencé depuis son backend de stockage et l'empaquette sous `assets/`.

L'importation n'accepte pas les archives ZIP. `FileField` et `ImageField` sont toujours exclus de l'importation, car ils ont `exclude_from_import=True` par défaut ; l'assistant ignore donc la colonne `photo` lors du téléversement. Réimportez un simple fichier de données, puis joignez les fichiers via les formulaires de création ou de modification.


## Écrire un exportateur personnalisé

Pour écrire un exportateur personnalisé, héritez de `BaseExporter` et implémentez la méthode `generate`. La classe de base gère l'enveloppement ZIP, le téléchargement de fichiers et les en-têtes de réponse :

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

Les données `rows` arrivent déjà nettoyées : le panneau d'administration remplace d'abord chaque valeur de `FileField` et `ImageField` par sa chaîne de chemin relative à la racine du ZIP, de sorte que votre méthode `generate` ne traite jamais de dictionnaires de fichiers. Enregistrez `MarkdownExporter()` dans votre liste `exporters` pour l'afficher dans le menu déroulant des formats.

## Écrire un importeur personnalisé

Pour écrire un importeur personnalisé, héritez de `BaseImporter` et implémentez `parse` comme un générateur asynchrone qui produit un dictionnaire par ligne :

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

## Et ensuite ?

* **[Stockage de fichiers](file-storage.md) :** Configurez les backends de stockage référencés dans l'archive ZIP d'exportation.
* **[Sécurité](security.md) :** Limites de lignes pour l'exportation et limites de taille des téléversements pour l'importation.
* **[Actions](actions.md) :** Ajoutez des actions groupées et des actions de ligne en complément de l'exportation et de l'importation.

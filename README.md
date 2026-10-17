<p align="center">
  <img src="assets/logo/png/rainbow-bim_256.png" width="150" alt="Logo Rainbow BIM">
</p>

<h1 align="center">Rainbow BIM</h1>

<p align="center">
  Coloration des réseaux MEP et ajout de propriétés dans les maquettes IFC
</p>

---

## À quoi ça sert ?

**Rainbow BIM** est un petit outil Windows pour les équipes BIM :

- il colore entre autres les réseaux MEP d'une maquette IFC (canalisations, gaines, chemins de câbles, raccords, isolants) selon leur système à partir d'un simple tableau de couleurs ;
- il ajoute des propriétés (Pset) à des éléments choisis par leur GUID, à partir d'un tableau.

Les fichiers d'origine ne sont jamais modifiés : chaque traitement crée un nouveau fichier (`_couleur.ifc` ou `_pset.ifc`) à côté de l'original.

## Fonctionnalités

**Coloration**
- Couleurs définies dans un CSV (séparateur `,` ou `;`, compatible Excel).
- Eléments paramétrables : classe IFC, Pset et paramètre contenant l'abréviation du système.
- Gabarits de paramètres à importer / exporter (`.json`), prêts pour IFC4 et IFC2x3.
- Isolants (`IfcCovering`) en gris transparent, en option.
- Fichiers produits valides et lisibles par les principales visionneuses (testé avec BIMcollab Zoom, Navisworks, Autodesk Viewer et Flinker IFC Viewer).

**Ajout de Pset**
- CSV « une ligne par élément » : 1re colonne = GUID, une colonne par propriété.
- Pset créé s'il n'existe pas, complété s'il existe, valeur remplacée si la propriété existe déjà.
- Bilan détaillé en fin de traitement (éléments modifiés, GUID introuvables…).

**Compatibilité** : IFC4 et IFC2x3.

## Télécharger et lancer (Windows, sans installation)

1. Ouvrir la page [**Releases**](../../releases) du dépôt et télécharger le fichier `RainbowBIM-vX.Y.Z-windows.zip` de la dernière version.
2. Dézipper le fichier (clic droit → *Extraire tout…*).
3. Dans le dossier `RainbowBIM`, lancer **`RainbowBIM.exe`**.

> **Avertissement Windows** : au premier lancement, Windows peut afficher « Windows a protégé votre ordinateur », car le programme n'est pas signé numériquement. Cliquer sur **Informations complémentaires** puis **Exécuter quand même**.

Aucune installation de Python ou d'autre logiciel n'est nécessaire.

## Utilisation

Le mode d'emploi complet est intégré à l'application, dans l'onglet **Aide**.

Des fichiers d'exemple (CSV de couleurs, gabarits de paramètres, CSV de propriétés) sont fournis dans le dossier [`data/`](data/).

Un script Dynamo pour Revit, qui exporte le CSV des couleurs de systèmes depuis la maquette, est fourni dans le dossier [`rvt/`](rvt/).

### Format du CSV des couleurs

```
Abreviation;Red;Green;Blue
ECS;255;0;0
EF;0;0;255
```

Le séparateur peut être `;` ou `,` : il est détecté automatiquement.

### Format du CSV des propriétés

```
GUID;Lot;Zone
0TVbGQLWfFYO5q4wV3CaSD;CVC;R+1
```

## Pour les développeurs

### Lancer depuis le code source

Prérequis : Python 3.10 ou plus récent.

```
pip install -r requirements.txt
python src/main.py
```

### Fabriquer le .exe

- **Automatiquement** : publier une version avec une étiquette du type `v1.0.0`. GitHub Actions fabrique le programme Windows et ajoute le `.zip` à la page *Releases* (voir `.github/workflows/fabrication-exe.yml`).
- **Sur son PC** :
  ```
  pip install -r requirements.txt pyinstaller
  pyinstaller --noconfirm rainbow_bim.spec
  ```
  Le programme est créé dans `dist/RainbowBIM/`.

### Organisation du dépôt

```
src/          code Python : main.py (interface), coloration.py, ajout_pset.py
assets/       logo (charte, icône, images) et aide.md (texte de l'onglet Aide)
data/         fichiers d'exemple
rvt/          script Dynamo (Revit) d'export du CSV des couleurs
rainbow_bim.spec   recette de fabrication du .exe (PyInstaller)
```

Bibliothèque principale : [IfcOpenShell](https://ifcopenshell.org) 0.8.4.

## Licence

Rainbow BIM est distribué sous licence **MIT** (voir [`LICENSE`](LICENSE)).

Il utilise IfcOpenShell, sous licence LGPL-3.0, ainsi que d'autres logiciels libres listés dans [`LICENCES_TIERCES.md`](LICENCES_TIERCES.md).

## Auteur

Maxime Mulliez

# Bienvenue dans Rainbow BIM

Rainbow BIM colore les réseaux MEP de vos maquettes IFC selon leur système, et permet d'ajouter des propriétés aux éléments.
Les fichiers d'origine ne sont **jamais modifiés** : chaque traitement crée un nouveau fichier à côté de l'original.

## Tutoriel vidéo

(https://youtu.be/7pbdAPIkQMQ)

# Onglet Coloration

1. Cliquer sur **Choisir IFC** et sélectionner la maquette (IFC4 ou IFC2x3).
2. Cliquer sur **Choisir CSV** et sélectionner le fichier des couleurs.
3. Vérifier si besoin les **Paramètres** (voir plus bas).
4. Cliquer sur **Lancer le traitement**.

Le fichier produit porte le même nom que l'original, suivi de `_couleur` (exemple : `Maquette_couleur.ifc`).

## Exigences IFC (2x3 ou 4)

1. Les IFC se doivent d'être classifier de manière à distinguer les différents éléments à coloriser.
En IFC2x3, les canalisations, gaines et chemins de câbles sont tous des `IfcFlowSegment`, et leurs raccords des `IfcFlowFitting`. Dans le tableau des paramètres, remplacer les classes IFC4 par ces deux classes. **Gabarits de paramètrage présents dans le dossier data**
2. Les abréviations des systèmes MEP ou tout autre propriété permettant de distinguer les éléments MEP (ex:type pour CDC) doivent être présentes dans des property set.

## Structuration du CSV des couleurs

- 1re ligne : les titres des colonnes, par exemple `Abreviation;Red;Green;Blue`
- 1re colonne : l'abréviation du système, telle qu'elle est écrite dans la maquette (exemple : `ECS`)
- Colonnes **Red**, **Green**, **Blue** : la couleur, chaque valeur de 0 à 255
- Séparateur `,` ou `;` : les deux sont acceptés (Excel français enregistre avec `;`)

Exemple de ligne : `ECS;255;0;0` colore en rouge tous les éléments du système ECS.

**Exemple de fichier CSV dans le dossier data**

## Paramètres de coloration

Le bouton **Paramètres** ouvre un tableau qui indique, pour chaque famille d'éléments à colorer :

- la **classe IFC** (exemple : `IfcPipeSegment`) ;
- le **Pset** qui contient l'abréviation (exemple : `Pset_Canalisations`) ;
- le **paramètre** qui contient l'abréviation (exemple : `Abréviation du système`).

Boutons disponibles :

- **+ Ajouter une ligne** / **✕** : ajouter ou supprimer une famille ;
- **Valeurs par défaut** : revenir au réglage d'origine ;
- **Importer** / **Exporter** : charger ou enregistrer un gabarit de paramètres (fichier `.json`) ;
- **Valider** pour appliquer, **Annuler** pour abandonner les modifications.

La case **Isolants (IfcCovering) en gris transparent** colore tous les isolants en gris à 50 % de transparence. Décochée, les isolants ne sont colorés que s'ils ont une ligne dans le tableau.

# Onglet Ajout Pset

1. Choisir le fichier IFC.
2. Choisir le CSV des propriétés.
3. Saisir le **nom du Pset** dans lequel écrire les propriétés.
4. Cliquer sur **Lancer le traitement**.

Le fichier produit se termine par `_pset` (exemple : `Maquette_pset.ifc`). Un bilan s'affiche à la fin : éléments modifiés, propriétés ajoutées ou écrasées, GUID introuvables.

## Format du CSV des propriétés

- 1re ligne : les titres des colonnes, par exemple `GUID;Property1;Property2...`
- 1re colonne : le **GUID** de l'élément (quel que soit le titre de la colonne)
- Colonnes suivantes : une propriété par colonne, le titre de la colonne est le nom de la propriété
- Une case vide : la propriété n'est pas ajoutée pour cet élément
- Toutes les valeurs sont écrites en texte

Exemple :

- `GUID;Lot;Zone`
- `0TVbGQLWfFYO5q4wV3CaSD;CVC;R+1`

**Exemple de fichier CSV dans le dossier data**

## Règles d'écriture

- Le Pset n'existe pas sur l'élément : il est créé.
- Le Pset existe déjà : les nouvelles propriétés s'y ajoutent.
- La propriété existe déjà : la nouvelle valeur remplace l'ancienne.
- Le nom du Pset respecte les majuscules : `RNB_Suivi` et `rnb_suivi` sont deux Psets différents.

# Problèmes fréquents

- **« Classe IFC inconnue »** : la classe est mal écrite, ou c'est une classe IFC4 utilisée dans une maquette IFC2x3.
- **Des éléments ne sont pas colorés** : les propriétés "abréviation" sont absentes de la maquette ou du CSV des couleurs.
- **GUID introuvables** : le GUID a changé (nouvel export de la maquette) ou il appartient à une autre maquette.
- **Toutes les canalisations se sont vues rajouter la même propriété** : Le GUID renseigné était celui du type et non des éléments.
- **Retraiter un fichier déjà traité** : toujours repartir de l'IFC d'origine plutôt que d'un fichier `_couleur`.

# Logo Rainbow BIM — mini-charte

Un **R** tracé par un faisceau de 6 réseaux arc-en-ciel. La panse du R est fermée par un raccord en té
sur le fût ; la jambe s'enroule en **goutte**, raccordée en té sur elle-même, et dessine aussi le lobe d'un **B**.

## Palette « Spectre franc »

| Bande (extérieur → intérieur) | Hex |
|---|---|
| Rouge   | `#E5383B` |
| Orange  | `#F3802B` |
| Jaune   | `#F6C324` |
| Vert    | `#34B36B` |
| Bleu    | `#2B8BD8` |
| Violet  | `#7A4FD0` |
| Monochrome sombre | `#1B1B1F` |

Version petites tailles (16 et 20 px, 3 bandes) : `#E5383B` · `#F6C324` · `#2B8BD8`.

## Quel fichier pour quel usage

| Usage | Fichier |
|---|---|
| Icône de l'application Windows (barre de titre, barre des tâches, raccourci) | `rainbow-bim.ico` (9 tailles : 16, 20, 24, 32, 40, 48, 64, 128, 256 px — voir « Détails de l'icône ») |
| Logo vectoriel (doc, présentation, site, impression) | `svg/rainbow-bim_couleur.svg` |
| Une seule couleur (cartouche, tampon, gravure) | `svg/rainbow-bim_noir.svg` / `svg/rainbow-bim_blanc.svg` |
| Filigrane dans l'appli Tkinter (fond par défaut #F0F0F0) | `png/rainbow-bim_filigrane_fond-F0F0F0_300.png` |
| Filigrane sur un autre fond | `png/rainbow-bim_filigrane_transparent_300.png` ou `svg/rainbow-bim_filigrane.svg` |
| Images matricielles prêtes à l'emploi | `png/rainbow-bim_<taille>.png` (16, 20, 24, 32, 40, 48, 64, 128, 256, 512, 1024 px, fond transparent) |

## Règles d'usage

- **Ne pas** déformer, pivoter, changer l'ordre des couleurs ni ajouter d'ombre/contour.
- **Zone de protection** : laisser autour du logo un vide au moins égal à la largeur d'une bande (≈ 1/30 de la hauteur).
- **Taille minimale** : 24 px pour la version 6 bandes ; en dessous (16 et 20 px), utiliser la version 3 bandes.
- Sur fond chargé (photo, maquette 3D), préférer la version blanche ou noire.

## Utilisation dans Tkinter (exemple)

```python
from pathlib import Path
import tkinter as tk

# Dossier du logo, calculé depuis l'emplacement de ce fichier .py
# (évite les chemins absolus qui cassent sur un autre PC)
LOGO = Path(__file__).resolve().parent.parent / "assets" / "logo"

root = tk.Tk()
root.iconbitmap(str(LOGO / "rainbow-bim.ico"))      # icône de fenêtre (Windows) ; str() pour les vieilles versions de Tk

# Filigrane : PhotoImage lit le PNG (Tk >= 8.6, inclus dans Python 3 sous Windows)
filigrane = tk.PhotoImage(file=str(LOGO / "png" / "rainbow-bim_filigrane_fond-F0F0F0_300.png"))
fond = tk.Label(root, image=filigrane, borderwidth=0)
fond.image = filigrane          # PIÈGE : sans cette référence, Python efface l'image et le label devient vide
fond.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)   # coin bas-droit, 10 px de marge
fond.lower()                    # passe derrière les autres widgets
```

## Régénérer les SVG

`source/export_logo.py` redessine les SVG à partir de quelques paramètres (épaisseur des bandes,
inclinaison de la jambe, taille de la goutte, palette) — Python seul, aucune dépendance :

```
python source/export_logo.py
```
(Les PNG de 512 et 1024 px peuvent se régénérer à partir des SVG avec n'importe quel outil de conversion, ex. Inkscape.
**Attention** : le .ico et les PNG de 16 à 256 px ne doivent PAS être refaits par simple réduction d'une grande image —
voir ci-dessous.)

## Détails de l'icône (.ico et PNG 16 → 256 px)

Chaque taille est dessinée **nativement** depuis les contours vectoriels, à sa taille finale, avec les bandes
**calées sur la grille de pixels** (bords nets, pas de flou) :

| Taille | Version | Calage | Format dans le .ico |
|---|---|---|---|
| 16 px | 3 bandes (R raccourci à 15 px de haut) | bandes de 1 px | BMP 32 bits |
| 20 px | 3 bandes | bandes de 1 px | BMP 32 bits |
| 24 px | 6 bandes | bords du faisceau (4 px) | BMP 32 bits |
| 32 px | 6 bandes | bords du faisceau (5 px) | BMP 32 bits |
| 40 px | 6 bandes | bandes de 1 px | BMP 32 bits |
| 48 px | 6 bandes | bords du faisceau (8 px) | BMP 32 bits |
| 64 px | 6 bandes | bords du faisceau (10 px) | BMP 32 bits |
| 128 px | 6 bandes | bandes de 3 px | BMP 32 bits |
| 256 px | 6 bandes | bandes de 7 px | PNG |

- **Pourquoi du BMP de 16 à 128 px ?** Le PNG compressé à l'intérieur d'un .ico n'est fiable que pour le 256 px ;
  pour les petites tailles, certains lecteurs (dont Windows dans certains cas, et Tkinter) le gèrent mal et finissent
  par agrandir une petite image → icône pixelisée dans la barre des tâches.
- **Pourquoi 20 et 40 px ?** Ce sont les tailles utilisées par Windows avec un affichage à 125 % (24 et 48 px à 150 %).
  Sans elles, Windows redimensionne une autre taille.
- Les PNG `png/rainbow-bim_16.png` → `_256.png` sont exactement les images contenues dans le .ico.

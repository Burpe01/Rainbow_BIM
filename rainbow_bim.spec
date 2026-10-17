# -*- mode: python ; coding: utf-8 -*-
# =========================================================
# RAINBOW BIM - rainbow_bim.spec
# "Recette" de fabrication du .exe pour PyInstaller.
# Utilisation (depuis le dossier du projet) :
#     pyinstaller --noconfirm rainbow_bim.spec
# Résultat : dist/RainbowBIM/RainbowBIM.exe (+ ses fichiers dans _internal/)
# =========================================================

from PyInstaller.utils.hooks import collect_all

# Fichiers non-Python à embarquer : (dossier source, dossier dans le .exe)
# main.py les retrouve grâce à DOSSIER_APPLI (= sys._MEIPASS dans le .exe).
datas = [("assets", "assets")]
binaries = []
hiddenimports = []

# IfcOpenShell charge une partie de ses modules et de ses fichiers (schémas IFC,
# bibliothèque compilée) "dynamiquement" : PyInstaller ne les voit pas tout seul.
# collect_all les ajoute tous d'office.
for paquet in ["ifcopenshell"]:
    d, b, h = collect_all(paquet)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["src/main.py"],
    pathex=["src"],                 # pour trouver coloration.py et ajout_pset.py
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
    excludes=["matplotlib", "IPython", "pytest"],   # inutiles, allègent le .exe
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # mode "dossier" : les fichiers restent à côté de l'exe
    name="RainbowBIM",
    icon="assets/logo/rainbow-bim.ico",
    console=False,                  # pas de fenêtre noire de terminal derrière l'appli
    upx=False,                      # pas de compression : moins de fausses alertes antivirus
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="RainbowBIM",
    upx=False,
)

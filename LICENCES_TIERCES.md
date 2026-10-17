# Logiciels tiers utilisés par Rainbow BIM

Le code de Rainbow BIM est sous licence MIT (voir `LICENSE`).
Le programme s'appuie sur les logiciels suivants, chacun sous sa propre licence.
La version .exe les embarque tels quels, sans modification.

| Logiciel | Rôle | Licence | Site |
|---|---|---|---|
| IfcOpenShell | lecture et écriture des fichiers IFC | LGPL-3.0 | https://ifcopenshell.org |
| Python | langage et bibliothèque standard | PSF License | https://www.python.org |
| Tcl/Tk (Tkinter) | interface graphique | licence de type BSD | https://www.tcl-lang.org |
| PyInstaller | fabrication du .exe (non embarqué, sauf son lanceur) | GPL-2.0 avec exception pour les programmes distribués | https://pyinstaller.org |

Les dépendances installées automatiquement avec IfcOpenShell (par exemple numpy)
restent sous leurs licences respectives, consultables sur https://pypi.org.

**IfcOpenShell (LGPL-3.0)** : vous pouvez remplacer la bibliothèque IfcOpenShell
embarquée par une autre version compatible : dans la version .exe, elle se trouve
dans le dossier `_internal/ifcopenshell/`. Le texte de la licence LGPL-3.0 est
disponible sur https://www.gnu.org/licenses/lgpl-3.0.html

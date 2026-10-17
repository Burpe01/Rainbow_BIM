# =========================================================
# RAINBOW BIM - main.py
# Créateur : Maxime Mulliez
#
# Interface Tkinter. C'est CE fichier qu'on lance (F5).
# Les traitements IFC sont dans coloration.py et ajout_pset.py,
# qui doivent rester dans le même dossier que main.py.
# =========================================================

import json
import re           # "expressions régulières" : rechercher des motifs dans un texte
import sys
import webbrowser   # ouvrir une adresse internet dans le navigateur par défaut
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# On va chercher la fonction traiter_ifc dans le fichier coloration.py
# (on écrit le nom du fichier SANS ".py").
from coloration import traiter_ifc
from ajout_pset import traiter_ajout_pset

# ---------------------------------------------------------
# BARRE DE PROGRESSION ARC-EN-CIEL ("faisceau")
# ---------------------------------------------------------
# La barre standard de Tkinter (ttk.Progressbar) n'a qu'une seule couleur.
# On dessine donc notre propre barre dans un Canvas (zone de dessin) :
# 6 bandes horizontales aux couleurs du logo, qui avancent ensemble.
#
# "class BarreArcEnCiel(tk.Canvas)" : on crée un nouveau type d'objet qui
# HÉRITE de tk.Canvas, c'est-à-dire qu'il sait déjà tout faire comme un Canvas
# (.pack(), etc.), et on lui ajoute nos propres fonctions (ici : set).

class BarreArcEnCiel(tk.Canvas):
    # Palette "Spectre franc" de la charte, de haut en bas
    COULEURS = ["#E5383B", "#F3802B", "#F6C324", "#34B36B", "#2B8BD8", "#7A4FD0"]

    def __init__(self, parent, largeur=400, hauteur=18):
        # __init__ est appelée à la création de la barre ;
        # super().__init__ crée d'abord le Canvas lui-même.
        # highlightthickness=0 : pas de cadre de sélection autour du dessin.
        super().__init__(parent, width=largeur, height=hauteur,
                         bg="#E6E6E6", highlightthickness=0)
        self.largeur = largeur
        self.bandes = []   # liste de (numéro du rectangle, haut, bas)

        hauteur_bande = hauteur / len(self.COULEURS)
        for numero, couleur in enumerate(self.COULEURS):
            haut = numero * hauteur_bande
            bas = (numero + 1) * hauteur_bande
            # Rectangle de largeur 0 au départ (barre vide) ; width=0 = sans bordure
            rectangle = self.create_rectangle(0, haut, 0, bas, fill=couleur, width=0)
            self.bandes.append((rectangle, haut, bas))

    def set(self, pourcentage):
        """Affiche la progression (de 0 à 100) en allongeant les 6 bandes."""
        # Sécurité : on reste entre 0 et 100 même si on reçoit 105 ou -3
        pourcentage = max(0, min(100, pourcentage))
        droite = self.largeur * pourcentage / 100
        for rectangle, haut, bas in self.bandes:
            # coords() déplace les coins d'un rectangle déjà dessiné :
            # bien plus rapide que de tout effacer et redessiner.
            self.coords(rectangle, 0, haut, droite, bas)


# =========================================================
# INTERFACE TKINTER
# =========================================================

# Dossier du logo, calculé à partir de l'emplacement de CE fichier :
# main.py est dans src/, le logo dans assets/logo/ (on remonte d'un cran avec .parent).
# Ainsi ça marche quel que soit le dossier d'où on lance l'application.
#
# Cas du .exe (fabriqué par PyInstaller) : le programme n'est plus un fichier
# main.py rangé dans src/. PyInstaller signale ce cas avec sys.frozen = True et
# range les fichiers embarqués (dont assets/) dans le dossier sys._MEIPASS.
# getattr(sys, "frozen", False) renvoie False quand l'attribut n'existe pas
# (lancement normal avec F5).
if getattr(sys, "frozen", False):
    DOSSIER_APPLI = Path(sys._MEIPASS)
else:
    DOSSIER_APPLI = Path(__file__).resolve().parent.parent

DOSSIER_LOGO = DOSSIER_APPLI / "assets" / "logo"

# Windows : sans cette ligne, l'application lancée par python.exe apparaît
# dans la barre des tâches sous l'icône de Python. On la déclare comme un
# programme à part entière (un "AppUserModelID") pour qu'elle ait sa propre icône.
# Doit être fait AVANT de créer la fenêtre.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RainbowBIM.Application")
    except Exception:
        pass   # simple confort visuel : en cas d'échec, on continue sans

root = tk.Tk()
root.title("Rainbow BIM")
root.geometry("650x520")   # 450 + la hauteur du bandeau

# --- Icône de la fenêtre (barre de titre + barre des tâches) ---
# Une SEULE méthode : le fichier .ico, format natif de Windows. Il contient
# toutes les tailles (16 à 256 px) et Windows choisit lui-même la bonne
# (petite pour la barre de titre, grande pour la barre des tâches).
# PIÈGE constaté : combiner iconbitmap ET iconphoto fait disparaître l'icône
# sous Windows (la seconde méthode écrase la première par une icône vide).
#
# default=... : l'icône s'applique à la fenêtre principale ET à toutes les
# fenêtres ouvertes ensuite (fenêtre Paramètres, messages...).
# try/except : si le fichier est absent (copie partielle du dossier) ou si le
# système ne lit pas le format .ico (hors Windows), l'appli démarre sans icône.
try:
    root.iconbitmap(default=str(DOSSIER_LOGO / "rainbow-bim.ico"))
except tk.TclError:
    pass

# --- Bandeau d'en-tête : logo + nom de l'application ---
bandeau = ttk.Frame(root)
bandeau.pack(fill="x", padx=12, pady=(10, 4))

try:
    image_logo = tk.PhotoImage(file=str(DOSSIER_LOGO / "png" / "rainbow-bim_48.png"))
    label_logo = ttk.Label(bandeau, image=image_logo)
    # PIÈGE : sans cette ligne, Python "oublie" l'image (ramasse-miettes)
    # et le label s'affiche vide. On garde donc une référence dans le label.
    label_logo.image = image_logo
    label_logo.pack(side="left")
except tk.TclError:
    pass   # logo introuvable : le bandeau garde seulement le titre

# Titre et signature, l'un sous l'autre, dans un petit cadre à droite du logo
cadre_titre = ttk.Frame(bandeau)
cadre_titre.pack(side="left", padx=10)

label_titre = ttk.Label(cadre_titre, text="Rainbow BIM", font=("Segoe UI", 16, "bold"),
                        foreground="#1B1B1F")   # #1B1B1F = couleur sombre de la charte
label_titre.pack(anchor="w")                    # anchor="w" : aligné à gauche (w = west)

label_auteur = ttk.Label(cadre_titre, text="by Maxime Mulliez", font=("Segoe UI", 9),
                         foreground="#555555")
label_auteur.pack(anchor="w")

ttk.Separator(root).pack(fill="x", padx=12, pady=(4, 6))

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ---------------------------------------------------------
# PARAMÈTRES DE COLORATION (fenêtre séparée)
# ---------------------------------------------------------

# Valeurs par défaut : (classe IFC, Pset, paramètre contenant l'abréviation)
# Rien n'est mémorisé : à chaque lancement de Rainbow BIM, on repart de cette liste.
FAMILLES_PAR_DEFAUT = [
    ("IfcPipeSegment",         "Pset_Canalisations",                 "Abréviation du système"),
    ("IfcPipeFitting",         "Pset_Raccords de canalisation",      "Abréviation du système"),
    ("IfcDuctSegment",         "Pset_Gaines",                        "Abréviation du système"),
    ("IfcDuctFitting",         "Pset_Raccords de gaine",             "Abréviation du système"),
    ("IfcCableCarrierSegment", "Pset_Chemins de câbles",             "Type"),
    ("IfcCableCarrierFitting", "Pset_Raccords de chemins de câbles", "Type"),
]

# Familles réellement utilisées par le traitement (modifiées par la fenêtre).
# list(...) crée une COPIE : on ne touche jamais à la liste par défaut.
familles_courantes = list(FAMILLES_PAR_DEFAUT)

# État de la case "Isolants (IfcCovering) en gris transparent".
# tk.BooleanVar = une variable Tkinter qui contient True ou False ;
# on lit sa valeur avec .get() et on la change avec .set(...).
# Cochée par défaut, non mémorisée d'un lancement à l'autre.
isolants_transparents_courant = tk.BooleanVar(value=True)


def ouvrir_parametres_coloration():
    """Ouvre la fenêtre Paramètres de l'onglet Coloration :
    un tableau de cases Classe / Pset / Paramètre.
    (Suffixe "_coloration" pour ne pas confondre avec les paramètres
    du futur onglet "Ajout Pset".)"""
    fenetre = tk.Toplevel(root)
    fenetre.title("Paramètres de coloration")
    fenetre.transient(root)   # reste au-dessus de la fenêtre principale
    fenetre.grab_set()        # fenêtre "modale" : il faut la fermer pour revenir à l'autre

    cadre = ttk.Frame(fenetre, padding=10)
    cadre.pack(fill="both", expand=True)

    # En-têtes de colonnes (ligne 0 de la grille)
    for col, titre in enumerate(["Classe IFC", "Pset", "Paramètre"]):
        ttk.Label(cadre, text=titre).grid(row=0, column=col, padx=2, pady=(0, 4), sticky="w")

    # Lignes affichées. Chaque ligne = (case classe, case pset, case paramètre, bouton ✕)
    lignes = []

    def placer_lignes():
        # (Re)place chaque ligne dans la grille, à partir de la ligne 1
        for i, ligne in enumerate(lignes, start=1):
            for col, widget in enumerate(ligne):
                widget.grid(row=i, column=col, padx=2, pady=2, sticky="we")

    def supprimer_ligne(ligne):
        for widget in ligne:
            widget.destroy()
        lignes.remove(ligne)
        placer_lignes()

    def ajouter_ligne(classe="", pset="", param=""):
        cases = []
        for valeur, largeur in [(classe, 24), (pset, 34), (param, 26)]:
            case = ttk.Entry(cadre, width=largeur)
            case.insert(0, valeur)
            cases.append(case)
        bouton = ttk.Button(cadre, text="✕", width=3)
        ligne = (cases[0], cases[1], cases[2], bouton)
        # Piège classique : "l=ligne" fige la ligne au moment de la création,
        # sinon TOUS les boutons ✕ supprimeraient la dernière ligne créée.
        bouton.config(command=lambda l=ligne: supprimer_ligne(l))
        lignes.append(ligne)
        placer_lignes()

    def remplir_tableau(familles, isolants):
        """Remplace TOUT le contenu de la fenêtre : les lignes et la case."""
        for ligne in list(lignes):   # list(...) : copie, car on vide "lignes" pendant la boucle
            supprimer_ligne(ligne)
        for famille in familles:
            ajouter_ligne(*famille)  # *famille "déballe" le triplet en 3 arguments
        case_isolants.set(isolants)

    def lire_tableau():
        """Lit les lignes affichées à l'écran.
        Renvoie la liste des familles, ou None si une ligne est incomplète
        (dans ce cas un message d'erreur a déjà été affiché)."""
        familles = []
        for numero, ligne in enumerate(lignes, start=1):
            classe = ligne[0].get().strip()   # strip() enlève les espaces en trop
            pset = ligne[1].get().strip()
            param = ligne[2].get().strip()
            if not classe and not pset and not param:
                continue                      # ligne entièrement vide : ignorée
            if not (classe and pset and param):
                messagebox.showerror("Ligne incomplète",
                                     f"La ligne {numero} doit avoir une classe, un Pset ET un paramètre.",
                                     parent=fenetre)
                return None
            familles.append((classe, pset, param))
        return familles

    def valeurs_par_defaut():
        remplir_tableau(FAMILLES_PAR_DEFAUT, True)

    def exporter():
        """Enregistre dans un fichier JSON ce qui est affiché (lignes + case)."""
        familles = lire_tableau()
        if familles is None:
            return                            # ligne incomplète : on n'exporte pas

        chemin = filedialog.asksaveasfilename(
            parent=fenetre,
            title="Exporter la configuration",
            defaultextension=".json",         # ajoute ".json" si on ne le tape pas
            filetypes=[("Configuration JSON", "*.json")]
        )
        if not chemin:
            return                            # l'utilisateur a cliqué sur Annuler

        # On construit un dictionnaire : c'est lui qui sera écrit dans le fichier.
        config = {
            "isolants_transparents": case_isolants.get(),
            "familles": []
        }
        for classe, pset, param in familles:
            config["familles"].append({"classe": classe, "pset": pset, "parametre": param})

        try:
            with open(chemin, "w", encoding="utf-8") as f:
                # ensure_ascii=False : garde les accents lisibles ("é" et non "é")
                # indent=2 : une information par ligne, lisible dans un éditeur
                json.dump(config, f, ensure_ascii=False, indent=2)
        except OSError as e:
            # OSError = problème de disque : dossier protégé, fichier ouvert ailleurs...
            messagebox.showerror("Export impossible", f"Le fichier n'a pas pu être écrit :\n{e}",
                                 parent=fenetre)

    def importer():
        """Charge un fichier JSON et REMPLACE le contenu de la fenêtre.
        Rien n'est appliqué au traitement tant qu'on n'a pas cliqué sur Valider."""
        chemin = filedialog.askopenfilename(
            parent=fenetre,
            title="Importer une configuration",
            filetypes=[("Configuration JSON", "*.json")]
        )
        if not chemin:
            return

        # On lit et on contrôle TOUT le fichier avant de toucher au tableau :
        # ainsi un fichier incorrect n'efface pas ce qui est affiché.
        try:
            with open(chemin, "r", encoding="utf-8-sig") as f:
                config = json.load(f)
            familles = []
            for famille in config["familles"]:
                familles.append((str(famille["classe"]), str(famille["pset"]), str(famille["parametre"])))
            # .get(clé, True) : si la clé est absente du fichier, la case est cochée
            isolants = bool(config.get("isolants_transparents", True))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # OSError : fichier illisible / ValueError : ce n'est pas du JSON
            # KeyError, TypeError, AttributeError : JSON valide mais pas la structure attendue
            messagebox.showerror("Import impossible",
                                 "Ce fichier n'est pas une configuration Rainbow BIM valide.\n\n"
                                 "Il doit contenir une liste \"familles\" dont chaque élément a "
                                 "les clés \"classe\", \"pset\" et \"parametre\".",
                                 parent=fenetre)
            return

        remplir_tableau(familles, isolants)

    def valider():
        nouvelles = lire_tableau()
        if nouvelles is None:
            return                            # on reste dans la fenêtre pour corriger
        # [:] remplace le CONTENU de la liste existante (pas besoin du mot-clé "global")
        familles_courantes[:] = nouvelles
        isolants_transparents_courant.set(case_isolants.get())
        fenetre.destroy()

    # Remplissage avec les familles actuelles
    for famille in familles_courantes:
        ajouter_ligne(*famille)

    # Case à cocher, sous le tableau.
    # On travaille sur une COPIE (case_isolants) de l'état courant : ainsi
    # "Annuler" ne change rien, seul "Valider" recopie la valeur.
    case_isolants = tk.BooleanVar(master=fenetre, value=isolants_transparents_courant.get())
    ttk.Checkbutton(fenetre, text="Isolants (IfcCovering) en gris transparent",
                    variable=case_isolants).pack(anchor="w", padx=12, pady=(0, 10))

    # Boutons du bas
    bas = ttk.Frame(fenetre, padding=(10, 0, 10, 10))
    bas.pack(fill="x")
    ttk.Button(bas, text="+ Ajouter une ligne", command=ajouter_ligne).pack(side="left")
    ttk.Button(bas, text="Valeurs par défaut", command=valeurs_par_defaut).pack(side="left", padx=5)
    ttk.Button(bas, text="Importer", command=importer).pack(side="left")
    ttk.Button(bas, text="Exporter", command=exporter).pack(side="left", padx=5)
    ttk.Button(bas, text="Valider", command=valider).pack(side="right")
    ttk.Button(bas, text="Annuler", command=fenetre.destroy).pack(side="right", padx=5)

# ---------------------------------------------------------
# ONGLET 1 : COLORATION
# ---------------------------------------------------------

tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="Coloration")

label_ifc = ttk.Label(tab1, text="Fichier IFC :")
label_ifc.pack(pady=5)

entry_ifc = ttk.Entry(tab1, width=60)
entry_ifc.pack()

def choisir_ifc():
    fichier = filedialog.askopenfilename(filetypes=[("IFC", "*.ifc")])
    entry_ifc.delete(0, tk.END)
    entry_ifc.insert(0, fichier)

btn_ifc = ttk.Button(tab1, text="Choisir IFC", command=choisir_ifc)
btn_ifc.pack(pady=5)

label_csv = ttk.Label(tab1, text="Fichier CSV des couleurs :")
label_csv.pack(pady=5)

entry_csv = ttk.Entry(tab1, width=60)
entry_csv.pack()

def choisir_csv():
    fichier = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    entry_csv.delete(0, tk.END)
    entry_csv.insert(0, fichier)

btn_csv = ttk.Button(tab1, text="Choisir CSV", command=choisir_csv)
btn_csv.pack(pady=5)

# --- BARRE DE PROGRESSION ---
# Même disposition que les blocs IFC et CSV : texte (le %) au-dessus,
# barre au milieu, bouton "Lancer le traitement" juste en dessous.
# Attention : avec pack(), c'est l'ORDRE des .pack() qui fixe l'ordre à l'écran.
label_progress = ttk.Label(tab1, text="")
label_progress.pack(pady=(15, 5))   # (15, 5) = 15 px au-dessus, 5 px en dessous

progress = BarreArcEnCiel(tab1, largeur=400)
progress.pack()

def update_progress(count, total):
    progress.set((count / total) * 100)
    label_progress.config(text=f"{int((count/total)*100)} %")
    root.update_idletasks()

def lancer_traitement():
    chemin_ifc = entry_ifc.get()
    chemin_csv = entry_csv.get()

    if not chemin_ifc or not chemin_csv:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier IFC et un fichier CSV.")
        return

    progress.set(0)
    label_progress.config(text="0 %")
    root.update_idletasks()

    try:
        sortie, ignores = traiter_ifc(
            chemin_ifc, chemin_csv,
            familles_courantes,
            isolants_transparents_courant.get(),
            update_progress
        )

        message = f"Traitement terminé.\nFichier généré :\n{sortie}"
        if ignores > 0:
            message += f"\n\n{ignores} élément(s) ignoré(s) : pas de géométrie 3D (Body)."
        messagebox.showinfo("Succès", message)

    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue :\n{e}")

btn_lancer = ttk.Button(tab1, text="Lancer le traitement", command=lancer_traitement)
btn_lancer.pack(pady=5)

# Bouton Paramètres de la coloration, en bas de l'onglet.
# side="bottom" le colle au bas de l'onglet, quelle que soit la hauteur de la fenêtre.
btn_parametres_coloration = ttk.Button(tab1, text="Paramètres", command=ouvrir_parametres_coloration)
btn_parametres_coloration.pack(side="bottom", pady=10)

# ---------------------------------------------------------
# ONGLET 2 : AJOUT PSET
# ---------------------------------------------------------
# Tous les noms de cet onglet finissent par "_pset" pour ne pas
# être confondus avec ceux de l'onglet Coloration.

tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Ajout Pset")

label_ifc_pset = ttk.Label(tab2, text="Fichier IFC :")
label_ifc_pset.pack(pady=5)

entry_ifc_pset = ttk.Entry(tab2, width=60)
entry_ifc_pset.pack()

def choisir_ifc_pset():
    fichier = filedialog.askopenfilename(filetypes=[("IFC", "*.ifc")])
    entry_ifc_pset.delete(0, tk.END)
    entry_ifc_pset.insert(0, fichier)

btn_ifc_pset = ttk.Button(tab2, text="Choisir IFC", command=choisir_ifc_pset)
btn_ifc_pset.pack(pady=5)

label_csv_pset = ttk.Label(tab2, text="Fichier CSV des propriétés :")
label_csv_pset.pack(pady=5)

entry_csv_pset = ttk.Entry(tab2, width=60)
entry_csv_pset.pack()

def choisir_csv_pset():
    fichier = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    entry_csv_pset.delete(0, tk.END)
    entry_csv_pset.insert(0, fichier)

btn_csv_pset = ttk.Button(tab2, text="Choisir CSV", command=choisir_csv_pset)
btn_csv_pset.pack(pady=5)

# Nom du Pset : saisi librement par l'utilisateur (avec ou sans "Pset_" devant).
label_nom_pset = ttk.Label(tab2, text="Nom du Pset :")
label_nom_pset.pack(pady=5)

entry_nom_pset = ttk.Entry(tab2, width=40)
entry_nom_pset.pack()

# --- BARRE DE PROGRESSION ---
label_progress_pset = ttk.Label(tab2, text="")
label_progress_pset.pack(pady=(15, 5))

progress_pset = BarreArcEnCiel(tab2, largeur=400)
progress_pset.pack()

def update_progress_pset(count, total):
    progress_pset.set((count / total) * 100)
    label_progress_pset.config(text=f"{int((count/total)*100)} %")
    root.update_idletasks()

def texte_bilan_pset(sortie, nom_pset, bilan):
    """Construit le message de fin à partir du bilan renvoyé par traiter_ajout_pset."""
    message = f"Traitement terminé.\nFichier généré :\n{sortie}\n\n"
    message += f"Pset « {nom_pset} » :\n"
    message += f"- {bilan['elements_modifies']} élément(s) modifié(s)\n"
    message += f"- {bilan['proprietes_ajoutees']} propriété(s) ajoutée(s)\n"
    message += f"- {bilan['proprietes_ecrasees']} propriété(s) existante(s) écrasée(s)\n"
    message += f"- {bilan['psets_crees']} Pset(s) créé(s)"

    # Les lignes suivantes n'apparaissent que s'il y a quelque chose à signaler.
    if bilan["psets_detaches"] > 0:
        message += f"\n- {bilan['psets_detaches']} Pset(s) partagé(s) copié(s) pour un seul élément"
    if bilan["lignes_sans_valeur"] > 0:
        message += f"\n- {bilan['lignes_sans_valeur']} ligne(s) du CSV sans aucune valeur"

    # Pour les deux listes de GUID, on n'affiche que les 10 premiers :
    # une fenêtre de message avec 500 lignes serait inutilisable.
    for titre, liste in [("GUID introuvable(s) dans l'IFC", bilan["guid_introuvables"]),
                         ("GUID d'objet(s) ne pouvant pas porter de Pset", bilan["guid_non_compatibles"])]:
        if liste:
            message += f"\n\n{len(liste)} {titre} :\n" + "\n".join(liste[:10])
            if len(liste) > 10:
                message += f"\n… et {len(liste) - 10} autre(s)"
    return message

def lancer_traitement_pset():
    chemin_ifc = entry_ifc_pset.get()
    chemin_csv = entry_csv_pset.get()
    nom_pset = entry_nom_pset.get().strip()

    if not chemin_ifc or not chemin_csv:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier IFC et un fichier CSV.")
        return
    if not nom_pset:
        messagebox.showerror("Erreur", "Veuillez saisir le nom du Pset.")
        return

    progress_pset.set(0)
    label_progress_pset.config(text="0 %")
    root.update_idletasks()

    try:
        sortie, bilan = traiter_ajout_pset(chemin_ifc, chemin_csv, nom_pset, update_progress_pset)
        messagebox.showinfo("Succès", texte_bilan_pset(sortie, nom_pset, bilan))

    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue :\n{e}")

btn_lancer_pset = ttk.Button(tab2, text="Lancer le traitement", command=lancer_traitement_pset)
btn_lancer_pset.pack(pady=5)

# ---------------------------------------------------------
# ONGLET 3 : AIDE
# ---------------------------------------------------------
# Le texte de l'aide est dans assets/aide.md : on le modifie comme un
# document, sans toucher au code. Il est relu à chaque lancement.
# Mise en forme reconnue ("Markdown simplifié") :
#   # Titre          ## Sous-titre        - élément de liste
#   **gras**         `code`               [texte du lien](https://...)
#   une adresse https://... écrite seule devient aussi cliquable.

FICHIER_AIDE = DOSSIER_APPLI / "assets" / "aide.md"   # DOSSIER_APPLI : voir en haut du fichier

tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="Aide")

# Zone de texte + barre de défilement verticale
zone_aide = tk.Text(tab3, wrap="word", relief="flat", padx=14, pady=10,
                    font=("Segoe UI", 10), bg="white", cursor="arrow")
defilement_aide = ttk.Scrollbar(tab3, orient="vertical", command=zone_aide.yview)
zone_aide.configure(yscrollcommand=defilement_aide.set)
defilement_aide.pack(side="right", fill="y")
zone_aide.pack(side="left", fill="both", expand=True)

# Les "tags" sont des styles qu'on applique à des morceaux de texte
zone_aide.tag_configure("titre1", font=("Segoe UI", 14, "bold"), foreground="#1B1B1F",
                        spacing1=14, spacing3=4)   # spacing1 = espace au-dessus, spacing3 = en dessous
zone_aide.tag_configure("titre2", font=("Segoe UI", 11, "bold"), foreground="#1B1B1F",
                        spacing1=10, spacing3=2)
zone_aide.tag_configure("gras", font=("Segoe UI", 10, "bold"))
zone_aide.tag_configure("code", font=("Consolas", 10), background="#F0F0F0")
zone_aide.tag_configure("puce", lmargin1=12, lmargin2=28)   # retrait des listes
zone_aide.tag_configure("lien", foreground="#2B8BD8", underline=True)  # bleu de la charte

# Motif qui repère, dans une ligne, les morceaux à mettre en forme.
# Chaque (...) est un "groupe" : on sait ainsi lequel des 4 cas a été trouvé.
MOTIF_EN_LIGNE = re.compile(
    r"\*\*(.+?)\*\*"                            # 1 : **gras**
    r"|`([^`]+)`"                               # 2 : `code`
    r"|\[([^\]]+)\]\((https?://[^)\s]+)\)"      # 3 et 4 : [texte](adresse)
    r"|(https?://[^\s)]+)"                      # 5 : adresse seule
)

nombre_de_liens = 0   # sert à donner un nom unique à chaque lien

def inserer_lien(texte, adresse, styles):
    """Insère un texte cliquable qui ouvre "adresse" dans le navigateur."""
    global nombre_de_liens
    nombre_de_liens += 1
    nom = f"lien_{nombre_de_liens}"   # un tag par lien, pour savoir lequel est cliqué
    zone_aide.insert("end", texte, styles + ("lien", nom))
    # PIÈGE : "a=adresse" fige l'adresse au moment de la création du lien,
    # sinon tous les liens ouvriraient la dernière adresse lue.
    zone_aide.tag_bind(nom, "<Button-1>", lambda evenement, a=adresse: webbrowser.open(a))
    zone_aide.tag_bind(nom, "<Enter>", lambda evenement: zone_aide.config(cursor="hand2"))
    zone_aide.tag_bind(nom, "<Leave>", lambda evenement: zone_aide.config(cursor="arrow"))

def inserer_texte_en_ligne(texte, styles):
    """Insère une ligne en appliquant **gras**, `code` et les liens."""
    position = 0
    for trouve in MOTIF_EN_LIGNE.finditer(texte):
        # Le texte "normal" avant le morceau trouvé
        zone_aide.insert("end", texte[position:trouve.start()], styles)
        if trouve.group(1):
            zone_aide.insert("end", trouve.group(1), styles + ("gras",))
        elif trouve.group(2):
            zone_aide.insert("end", trouve.group(2), styles + ("code",))
        elif trouve.group(3):
            inserer_lien(trouve.group(3), trouve.group(4), styles)
        else:
            inserer_lien(trouve.group(5), trouve.group(5), styles)
        position = trouve.end()
    zone_aide.insert("end", texte[position:], styles)   # la fin de la ligne

def afficher_aide():
    """Lit assets/aide.md et l'affiche, ligne par ligne, avec sa mise en forme."""
    zone_aide.config(state="normal")    # autorise l'écriture le temps du remplissage
    zone_aide.delete("1.0", "end")
    try:
        lignes = FICHIER_AIDE.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        zone_aide.insert("end", f"Fichier d'aide introuvable :\n{FICHIER_AIDE}")
        zone_aide.config(state="disabled")
        return

    for ligne in lignes:
        if ligne.startswith("## ") or ligne.startswith("### "):
            inserer_texte_en_ligne(ligne.lstrip("#").strip(), ("titre2",))
        elif ligne.startswith("# "):
            inserer_texte_en_ligne(ligne[2:].strip(), ("titre1",))
        elif ligne.lstrip().startswith(("- ", "* ")):
            zone_aide.insert("end", "•  ", ("puce",))
            inserer_texte_en_ligne(ligne.lstrip()[2:], ("puce",))
        elif re.match(r"\s*\d+\.\s", ligne):          # liste numérotée : 1. 2. 3.
            inserer_texte_en_ligne(ligne.strip(), ("puce",))
        else:
            inserer_texte_en_ligne(ligne, ())
        zone_aide.insert("end", "\n")

    # Lecture seule : l'utilisateur ne peut pas modifier le texte affiché
    # (les liens restent cliquables).
    zone_aide.config(state="disabled")

afficher_aide()

root.mainloop()

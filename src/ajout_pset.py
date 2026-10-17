# =========================================================
# RAINBOW BIM - ajout_pset.py
# Créateur : Maxime Mulliez
#
# Traitement IFC de l'ajout de propriétés : lit un CSV dont
# la 1re colonne contient les GUID et les colonnes suivantes
# les propriétés, puis écrit ces valeurs dans un Pset
# (jeu de propriétés) des éléments concernés.
# Ce fichier ne contient AUCUNE interface : c'est main.py
# qui l'utilisera.
# =========================================================

import ifcopenshell
import ifcopenshell.api.pset
import ifcopenshell.util.element

# On réutilise la lecture de CSV déjà écrite pour la coloration
# (séparateur "," ou ";", accents, lignes vides ignorées).
from coloration import lire_csv


def lire_csv_proprietes(chemin_csv):
    """
    Lit le CSV d'ajout de propriétés. Exemple de fichier :

        GUID;Lot;Zone
        0TVbGQLWfFYO5q4wV3CaSD;CVC;R+1
        1hOSvn6df7F8_7GcBWlRGQ;PLB;

    Renvoie une liste de couples (guid, valeurs), un par ligne du CSV :
        [("0TVbG...", {"Lot": "CVC", "Zone": "R+1"}),
         ("1hOSv...", {"Lot": "PLB"})]
    Une case vide n'apparaît pas dans le dictionnaire "valeurs" :
    la propriété ne sera donc pas ajoutée pour cet élément.
    """
    lignes = lire_csv(chemin_csv)
    if not lignes:
        raise ValueError("Le fichier CSV est vide.")

    # La 1re ligne contient les titres. La 1re colonne est TOUJOURS le GUID,
    # quel que soit son titre ; les autres titres sont les noms des propriétés.
    titres = [titre.strip() for titre in lignes[0]]
    lignes_elements = lignes[1:]
    if not lignes_elements:
        raise ValueError("Le CSV ne contient que la ligne de titres : aucun élément à traiter.")

    # colonnes = {numéro de colonne: nom de la propriété}
    colonnes = {}
    for numero in range(1, len(titres)):
        nom = titres[numero]
        if nom == "":
            # Colonne sans titre : acceptée seulement si elle est entièrement
            # vide (Excel en laisse parfois en fin de tableau).
            for ligne in lignes_elements:
                if numero < len(ligne) and ligne[numero].strip():
                    raise ValueError(f"La colonne n°{numero + 1} du CSV contient des valeurs mais n'a pas de titre.")
            continue
        if nom in colonnes.values():
            raise ValueError(f"Le CSV contient deux colonnes nommées « {nom} ».")
        colonnes[numero] = nom

    if not colonnes:
        raise ValueError("Le CSV doit contenir au moins une colonne de propriété après la colonne des GUID.")

    resultat = []
    for ligne in lignes_elements:
        guid = ligne[0].strip()
        valeurs = {}
        for numero, nom in colonnes.items():
            # Une ligne peut être plus courte que la ligne de titres :
            # les cases manquantes sont considérées comme vides.
            if numero < len(ligne):
                valeur = ligne[numero].strip()
                if valeur != "":
                    valeurs[nom] = valeur
        resultat.append((guid, valeurs))
    return resultat


def traiter_ajout_pset(chemin_ifc, chemin_csv, nom_pset, update_progress):
    """
    Ajoute dans le Pset "nom_pset" les propriétés du CSV, élément par élément.

    Règles :
      - le Pset n'existe pas sur l'élément -> il est créé ;
      - le Pset existe déjà                -> les propriétés s'y ajoutent ;
      - la propriété existe déjà           -> la nouvelle valeur écrase l'ancienne ;
      - case vide dans le CSV              -> propriété non ajoutée ;
      - toutes les valeurs sont écrites en TEXTE.

    Renvoie 2 valeurs : le chemin du fichier créé et un "bilan"
    (dictionnaire de compteurs et de listes, pour le message de fin).
    """
    nom_pset = nom_pset.strip()
    if nom_pset == "":
        raise ValueError("Le nom du Pset est vide.")

    lignes = lire_csv_proprietes(chemin_csv)
    model_IFC = ifcopenshell.open(chemin_ifc)

    bilan = {
        "elements_modifies": 0,       # éléments ayant reçu au moins une propriété
        "psets_crees": 0,             # Psets créés (ils n'existaient pas sur l'élément)
        "psets_detaches": 0,          # Psets partagés, copiés pour un seul élément
        "proprietes_ajoutees": 0,     # propriétés nouvelles
        "proprietes_ecrasees": 0,     # propriétés existantes dont la valeur a été remplacée
        "lignes_sans_valeur": 0,      # lignes dont toutes les cases de propriété sont vides
        "guid_introuvables": [],      # GUID absents de l'IFC (ou case GUID vide)
        "guid_non_compatibles": [],   # GUID d'un objet qui ne peut pas porter de Pset
    }
    # Un "set" (ensemble) ne garde chaque valeur qu'une fois : un élément présent
    # sur deux lignes du CSV ne sera compté qu'une fois.
    guid_modifies = set()

    total = len(lignes)
    count = 0

    for guid, valeurs in lignes:
        # La progression est mise à jour en DÉBUT de boucle : avec les "continue"
        # plus bas, une mise à jour placée à la fin serait sautée.
        count += 1
        update_progress(count, total)

        if guid == "":
            bilan["guid_introuvables"].append("(case GUID vide)")
            continue

        if not valeurs:
            bilan["lignes_sans_valeur"] += 1
            continue

        # --- Recherche de l'élément par son GUID ---
        try:
            element = model_IFC.by_guid(guid)
        except RuntimeError:
            # IfcOpenShell lève une RuntimeError si le GUID n'existe pas.
            bilan["guid_introuvables"].append(guid)
            continue

        # Un GUID peut désigner autre chose qu'un élément (une relation, un Pset...).
        # Seuls les objets (IfcObject) et les types (IfcTypeObject) portent des Psets.
        if not (element.is_a("IfcObject") or element.is_a("IfcTypeObject")):
            bilan["guid_non_compatibles"].append(guid)
            continue

        # --- Le Pset existe-t-il déjà SUR CET ÉLÉMENT ? ---
        # should_inherit=False : on ne regarde pas les Psets hérités du type,
        # car les modifier changerait tous les éléments de ce type.
        # psets_only=True : on ignore les quantités (IfcElementQuantity).
        psets = ifcopenshell.util.element.get_psets(element, should_inherit=False, psets_only=True)

        if nom_pset in psets:
            pset = model_IFC.by_id(psets[nom_pset]["id"])
            noms_existants = set(psets[nom_pset].keys())

            # Pset PARTAGÉ : un même Pset peut être relié à plusieurs éléments.
            # Le modifier changerait aussi les autres. On en fait donc d'abord
            # une copie réservée à notre élément, et c'est elle qu'on modifie.
            if len(ifcopenshell.util.element.get_elements_by_pset(pset)) > 1:
                pset = ifcopenshell.api.pset.unshare_pset(model_IFC, products=[element], pset=pset)[0]
                bilan["psets_detaches"] += 1
        else:
            pset = ifcopenshell.api.pset.add_pset(model_IFC, product=element, name=nom_pset)
            noms_existants = set()
            bilan["psets_crees"] += 1

        # --- Préparation des valeurs, toutes en texte ---
        # On crée explicitement un IfcLabel (texte court, 255 caractères maximum)
        # ou un IfcText (texte long). Piège : si on passait un simple texte Python
        # pour écraser une propriété existante d'un autre type (un booléen par
        # exemple), IfcOpenShell le convertirait dans cet ancien type.
        proprietes = {}
        for nom, valeur in valeurs.items():
            if len(valeur) <= 255:
                proprietes[nom] = model_IFC.create_entity("IfcLabel", valeur)
            else:
                proprietes[nom] = model_IFC.create_entity("IfcText", valeur)

            if nom in noms_existants:
                bilan["proprietes_ecrasees"] += 1
            else:
                bilan["proprietes_ajoutees"] += 1

        ifcopenshell.api.pset.edit_pset(model_IFC, pset=pset, properties=proprietes)
        guid_modifies.add(guid)

    bilan["elements_modifies"] = len(guid_modifies)

    # --- Export IFC ---
    sortie = chemin_ifc.replace(".ifc", "_pset.ifc")
    model_IFC.write(sortie)

    return sortie, bilan

# =========================================================
# RAINBOW BIM - coloration.py
# Créateur : Maxime Mulliez
#
# Traitement IFC de la coloration : tout ce qui lit le CSV,
# ouvre l'IFC, crée les styles et écrit le fichier "_couleur".
# Ce fichier ne contient AUCUNE interface : il ne connaît pas
# Tkinter. C'est main.py qui l'utilise.
# =========================================================

import csv
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

# =========================================================
# TRAITEMENT IFC
# =========================================================

style_cache = {}

# Formes partagées (IfcRepresentationMap, la géométrie commune des raccords)
# rencontrées pendant le traitement. Pour chaque forme on note les "copies
# placées" (IfcMappedItem) à colorer et leur style. Elles sont toutes traitées
# ensemble, à la fin, par colorer_formes_partagees().
# Clé = numéro de la forme dans le fichier ; valeur = (forme, {numéro de la
# copie placée: (copie placée, style)}).
formes_partagees = {}

def definir_couleur(fichier, key, r, g, b, transparency=None):
    """
    Crée (une seule fois par clé, grâce au cache) le style de surface
    correspondant à une couleur, et renvoie l'objet à mettre dans
    l'attribut Styles d'un IfcStyledItem :
      - IFC4   : le IfcSurfaceStyle lui-même
      - IFC2x3 : un IfcPresentationStyleAssignment qui "emballe" le style
    """
    if key in style_cache:
        return style_cache[key]

    R = r / 255
    G = g / 255
    B = b / 255

    color = fichier.create_entity("IfcColourRgb", Name=None, Red=R, Green=G, Blue=B)

    # ReflectanceMethod (façon de réfléchir la lumière) est OBLIGATOIRE dans
    # le schéma IFC : "NOTDEFINED" = non défini, la valeur neutre.
    # Transparency=None signifie simplement "pas de transparence".
    rendering = fichier.create_entity(
        "IfcSurfaceStyleRendering",
        SurfaceColour=color,
        Transparency=transparency,
        ReflectanceMethod="NOTDEFINED"
    )

    surface_style = fichier.create_entity(
        "IfcSurfaceStyle",
        Name=f"Style_{key}",
        Side="BOTH",
        Styles=[rendering]
    )

    # En IFC2x3, un IfcStyledItem ne peut pas pointer directement sur un
    # IfcSurfaceStyle : le schéma impose une "enveloppe" intermédiaire,
    # le IfcPresentationStyleAssignment. En IFC4, on pointe directement.
    if fichier.schema == "IFC2X3":
        style = fichier.create_entity("IfcPresentationStyleAssignment", Styles=[surface_style])
    else:
        style = surface_style

    style_cache[key] = style
    return style


def appliquer_style(fichier, element, style):
    """
    Applique un style (couleur) à la géométrie 3D d'un élément.
    Renvoie True si l'élément a été coloré,
    False s'il a été ignoré (aucune géométrie "Body").
    """
    # 1) L'élément a-t-il une géométrie ? (Representation vaut None sinon)
    if not element.Representation:
        return False

    # 2) On cherche la représentation "Body" (le volume 3D) par son nom,
    #    au lieu de prendre la première : certains logiciels mettent
    #    l'axe ("Axis") ou une boîte ("Box") en premier.
    body = None
    for representation in element.Representation.Representations:
        if representation.RepresentationIdentifier == "Body":
            body = representation
            break

    if body is None or not body.Items:
        return False

    # 3) On colore TOUS les morceaux du Body (une gaine peut en avoir plusieurs).
    for item in body.Items:
        if item.is_a("IfcMappedItem"):
            # Géométrie PARTAGÉE (raccords...) : l'élément n'a qu'une "copie
            # placée" d'une forme commune, qui peut servir à d'autres éléments,
            # parfois d'autres couleurs. On ne la colore pas tout de suite : on
            # note la demande, et colorer_formes_partagees() traitera chaque
            # forme une seule fois, à la fin, en connaissant tous ses utilisateurs.
            forme = item.MappingSource
            if forme.id() not in formes_partagees:
                formes_partagees[forme.id()] = (forme, {})
            # Si le même élément est traité deux fois, la dernière couleur gagne.
            formes_partagees[forme.id()][1][item.id()] = (item, style)
        else:
            poser_style(fichier, item, style)

    return True


def poser_style(fichier, item, style):
    """
    Pose le style sur un morceau de géométrie et supprime sa carte de couleurs.

    Le schéma IFC n'autorise qu'UN SEUL IfcStyledItem ("étiquette" de style)
    par morceau. Le logiciel d'export en a souvent déjà posé un : dans ce cas
    on le réutilise et on REMPLACE son style par le nôtre.
    """
    etiquettes = item.StyledByItem   # étiquettes déjà posées sur ce morceau
    if etiquettes:
        for etiquette in etiquettes:
            etiquette.Styles = [style]
    else:
        fichier.create_entity("IfcStyledItem", Item=item, Styles=[style], Name=None)

    supprimer_cartes_couleur(fichier, item)


def supprimer_cartes_couleur(fichier, item):
    """
    Supprime les cartes de couleurs (IfcIndexedColourMap) d'un morceau.

    En IFC4, un maillage (IfcPolygonalFaceSet, IfcTriangulatedFaceSet) peut
    porter une couleur par facette. Revit en écrit une avec la couleur
    d'origine, et Navisworks ou Autodesk Viewer la font passer AVANT le style :
    on la supprime donc sur tout ce que l'on recolorise.
    """
    # getattr(objet, "nom", None) renvoie None si l'attribut n'existe pas :
    # HasColours n'existe ni en IFC2x3 ni sur les autres types de géométrie.
    cartes = getattr(item, "HasColours", None) or []
    for carte in list(cartes):       # list(...) : copie, car on supprime pendant la boucle
        liste_couleurs = carte.Colours
        fichier.remove(carte)
        # La liste de couleurs n'est supprimée que si plus rien ne l'utilise.
        if liste_couleurs is not None and fichier.get_total_inverses(liste_couleurs) == 0:
            fichier.remove(liste_couleurs)


def copier_forme(fichier, forme):
    """
    Copie "légère" d'une forme partagée (IfcRepresentationMap).

    On copie seulement les "enveloppes" (la forme, sa représentation et ses
    morceaux de premier niveau). La géométrie détaillée (points, faces,
    profils) reste partagée avec l'original : la copie ne pèse presque rien.
    Une copie n'a ni étiquette de style ni carte de couleurs (ce sont des
    liens "inverses", qui ne sont pas recopiés).
    """
    representation = forme.MappedRepresentation
    nouveaux_items = []
    for item in representation.Items:
        nouveaux_items.append(ifcopenshell.util.element.copy(fichier, item))
    nouvelle_representation = ifcopenshell.util.element.copy(fichier, representation)
    nouvelle_representation.Items = nouveaux_items
    nouvelle_forme = ifcopenshell.util.element.copy(fichier, forme)
    nouvelle_forme.MappedRepresentation = nouvelle_representation
    return nouvelle_forme


def colorer_formes_partagees(fichier):
    """
    Colore les formes partagées notées par appliquer_style().

    Le style est posé SUR LA FORME elle-même, et non sur la copie placée :
    Navisworks, Flinker et Autodesk Viewer donnent la priorité au style de la
    forme. Une forme ne pouvant avoir qu'une couleur :
      - tous ses utilisateurs sont recolorisés -> la forme garde la couleur
        la plus utilisée, et chaque autre couleur reçoit sa propre copie ;
      - elle sert aussi à des éléments NON recolorisés (une vanne...) -> on
        n'y touche pas, et chaque couleur reçoit sa propre copie.
    Renvoie le nombre de copies créées.
    """
    copies = 0
    for forme, demandes in formes_partagees.values():
        # Regroupement des copies placées par style : {numéro du style: (style, [copies placées])}
        par_style = {}
        for copie_placee, style in demandes.values():
            if style.id() not in par_style:
                par_style[style.id()] = (style, [])
            par_style[style.id()][1].append(copie_placee)

        # MapUsage = toutes les copies placées qui utilisent cette forme
        tous_recolorises = len(forme.MapUsage) == len(demandes)

        # Le groupe le plus nombreux en premier : c'est lui qui garde la forme
        # d'origine (s'il le peut), pour créer le moins de copies possible.
        groupes = sorted(par_style.values(), key=lambda groupe: len(groupe[1]), reverse=True)

        for numero, (style, copies_placees) in enumerate(groupes):
            if numero == 0 and tous_recolorises:
                forme_cible = forme
            else:
                forme_cible = copier_forme(fichier, forme)
                for copie_placee in copies_placees:
                    copie_placee.MappingSource = forme_cible
                copies += 1

            for item in forme_cible.MappedRepresentation.Items:
                poser_style(fichier, item, style)

            # Si une étiquette existe déjà sur une copie placée, on lui donne
            # le même style, pour qu'aucune visionneuse ne voie deux couleurs.
            for copie_placee in copies_placees:
                for etiquette in copie_placee.StyledByItem or []:
                    etiquette.Styles = [style]
    return copies


def lire_csv(chemin_csv):
    """
    Lit un fichier CSV et renvoie la liste de ses lignes
    (chaque ligne = une liste de valeurs, ex : ["ECS", "255", "0", "0"]).

    - Encodage : essaie UTF-8, puis Windows-1252 (encodage utilisé par
      Excel en français quand on choisit "CSV (séparateur : point-virgule)").
    - Séparateur : détecté automatiquement entre "," et ";" en regardant
      la première ligne (celle des en-têtes).
    """
    # 1) Lecture du texte avec le bon encodage
    # "utf-8-sig" = UTF-8 qui ignore le BOM, un caractère invisible
    # qu'Excel ajoute au tout début des fichiers "CSV UTF-8".
    try:
        with open(chemin_csv, "r", encoding="utf-8-sig", newline="") as f:
            contenu = f.read()
    except UnicodeDecodeError:
        # Le fichier n'est pas en UTF-8 (les accents ne se décodent pas) :
        # on le relit en Windows-1252, l'encodage "ANSI" d'Excel.
        with open(chemin_csv, "r", encoding="cp1252", newline="") as f:
            contenu = f.read()

    lignes = contenu.splitlines()

    # 2) Détection du séparateur sur la ligne d'en-têtes
    #    = la première ligne NON vide (strip() enlève espaces et tabulations ;
    #    une ligne qui ne contient que ça donne "" et est donc sautée).
    premiere_ligne = ""
    for ligne in lignes:
        if ligne.strip():
            premiere_ligne = ligne
            break
    if premiere_ligne.count(";") > premiere_ligne.count(","):
        separateur = ";"
    else:
        separateur = ","

    # 3) Découpage de chaque ligne en colonnes
    lecteur = csv.reader(lignes, delimiter=separateur)

    # 4) On ne garde que les lignes qui contiennent au moins une valeur.
    #    Deux sortes de lignes "vides" existent :
    #      - une vraie ligne vide           -> []
    #      - une ligne d'Excel du type ;;;  -> ["", "", "", ""]
    #    any(...) répond True dès qu'UNE case de la ligne n'est pas vide.
    resultat = []
    for ligne in lecteur:
        if any(case.strip() for case in ligne):
            resultat.append(ligne)
    return resultat


def traiter_ifc(chemin_ifc, chemin_csv, familles, isolants_transparents, update_progress):
    """
    familles : liste de triplets (classe IFC, nom du Pset, nom du paramètre)
               ex : [("IfcPipeSegment", "Pset_Canalisations", "Abréviation du système"), ...]
               Elle vient du tableau de la fenêtre "Paramètres de coloration".
    isolants_transparents : True ou False (case à cocher des Paramètres).
               True  -> TOUS les IfcCovering passent en gris transparent
                        (une ligne IfcCovering du tableau est alors ignorée).
               False -> les IfcCovering ne sont colorés que s'ils ont une
                        ligne dans le tableau (couleur selon l'abréviation).
    """

    global style_cache, formes_partagees
    style_cache = {}
    formes_partagees = {}   # vidé à chaque traitement, comme le cache de styles

    # --- Import CSV ---
    # Encodage et séparateur ("," ou ";") sont gérés par lire_csv()
    list_CSV = lire_csv(chemin_csv)

    cles = list_CSV[0]
    valeurs = list_CSV[1:]
    couleur_systeme = {}
    for v in valeurs:
        d = dict(zip(cles, v))
        couleur_systeme[v[0]] = d

    # --- Import IFC ---
    model_IFC = ifcopenshell.open(chemin_ifc)

    # --- Familles d'éléments MEP à colorer ---
    # La liste "familles" est reçue en paramètre (tableau des Paramètres).

    # On récupère les éléments de chaque famille une seule fois.
    # elements_par_famille contiendra des triplets : (liste d'éléments, pset, param)
    elements_par_famille = []
    for classe, pset, param in familles:
        # Case cochée : les IfcCovering sont traités plus bas (gris transparent),
        # on saute donc leur ligne du tableau. lower() = comparaison sans tenir
        # compte des majuscules ("ifccovering" == "IfcCovering").
        if isolants_transparents and classe.lower() == "ifccovering":
            continue

        try:
            elements = model_IFC.by_type(classe)
        except RuntimeError:
            # IfcOpenShell lève une RuntimeError si la classe n'existe pas
            # dans le schéma du fichier (faute de frappe, ou classe IFC4
            # demandée dans un fichier IFC2x3). On la remplace par un
            # message clair en français.
            raise ValueError(f"Classe IFC inconnue dans ce fichier ({model_IFC.schema}) : {classe}")
        elements_par_famille.append((elements, pset, param))

    # Isolants : tous les IfcCovering, SANS filtre sur le type INSULATION
    # (tous les logiciels ne renseignent pas ce type à l'export).
    # Case décochée -> liste vide : aucun traitement spécial.
    if isolants_transparents:
        Calorifuges = model_IFC.by_type("IfcCovering")
    else:
        Calorifuges = []

    # Total éléments pour la progression
    total = len(Calorifuges)
    for elements, pset, param in elements_par_famille:
        total += len(elements)
    count = 0
    ignores = 0  # éléments sans géométrie "Body", donc non colorés

    # --- Traitement des familles MEP (une seule boucle pour toutes) ---
    for elements, pset, param in elements_par_famille:
        for element in elements:
            psets = ifcopenshell.util.element.get_psets(element)
            abv = psets.get(pset, {}).get(param)

            if abv in couleur_systeme:
                couleur = couleur_systeme[abv]
                style = definir_couleur(model_IFC, abv, int(couleur["Red"]), int(couleur["Green"]), int(couleur["Blue"]))
                if not appliquer_style(model_IFC, element, style):
                    ignores += 1

            count += 1
            update_progress(count, total)

    # --- Traitement calorifuges (gris transparent, si la case est cochée) ---
    for c in Calorifuges:
        style = definir_couleur(model_IFC, "CALO", 128, 128, 128, transparency=0.5)
        if not appliquer_style(model_IFC, c, style):
            ignores += 1

        count += 1
        update_progress(count, total)

    # --- Formes partagées (raccords...), traitées en une fois ---
    colorer_formes_partagees(model_IFC)

    # --- Export IFC ---
    sortie = chemin_ifc.replace(".ifc", "_couleur.ifc")
    model_IFC.write(sortie)

    # On renvoie 2 valeurs : le chemin du fichier créé et le nombre d'ignorés
    return sortie, ignores

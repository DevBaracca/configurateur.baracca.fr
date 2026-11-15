#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BARACCA-IMPORT v2.24 — vérifiez la présence de cette ligne : elle prouve
# que vous exécutez bien la dernière version du script.
# v2.24 : ouvertures envoyées avec refSide=true -> côté soleil (extérieur) de
# la fenêtre/porte sur la face EXTÉRIEURE du mur (murs en beg<->end échangés).
# v2.23 : murs envoyés avec beg<->end échangés (axes_envoi) + "Inside" :
# la ligne directrice reste en place, le corps part vers l'EXTÉRIEUR et la
# face extérieure (côté soleil des fenêtres/portes) est sur la face opposée
# à la ligne. (v2.21 axes d'origine + "Outside" : corps OK mais face
# extérieure marquée côté ligne -> ouvrants inversés.)
# v2.22 : centerOffset des ouvertures mesuré depuis le beg envoyé (swap).
# v2.21 : compositeId envoyé en OBJET {"guid": ...} (et non en chaîne) —
# Tapir 2.0 ignore silencieusement une chaîne et Archicad garde la structure
# par défaut (cf. exemple officiel create_composite_slab.py).
# v2.20 : liste des composites via GetAttributesByType {"attributeType":
# "Composite"} (GetComposites exige des attributeIds et refuse {}).
# v2.19 : murs / plancher / toitures reçoivent la STRUCTURE COMPOSITE de la
# « Référence Archicad » (résolue par NOM, insensible à la casse/accents et au
# sous-dossier « BARACCA ») à la création — JAMAIS de favori
# sur ces éléments (un favori
# écraserait l'orientation du mur et la pente/niveau du toit) : si le nom
# n'existe pas comme composite, avertissement + réglages par défaut.
# Favoris (favoriteName + ApplyFavoritesToElements) réservés aux ouvrants,
# poteaux/poutres et fenêtres de toit. Plus de poutre faîtière (doublon) :
# charpente = 2 poteaux + 1 sablière.
# v2.18 : composite au lieu de favori pour murs/plancher/toitures ; murs créés
# avec axes d'origine + referenceLineLocation="Outside".
# v2.17 : cible unique Archicad 30 / Tapir >= 2.0 (les replis AC29/Tapir 1.7.2
# sont retirés). Murs : axes d'origine + referenceLineLocation="Outside"
# -> corps vers l'extérieur ET côté soleil des ouvrants vers l'extérieur.
# Toitures deux-pentes asymétriques : pente = versant NORD, pente2 = versant
# SUD, faîtage excentré (plus au milieu). Favoris : favoriteName à la création
# + réapplication par ApplyFavoritesToElements en fin d'import (keepFields
# referenceLineLocation pour les murs) ; type fenêtre/porte des ouvertures
# résolu via GetFavoritesByType quand un favori est renseigné.
# v2.16 : repli robuste sur les favoris — si Archicad refuse un item parce que
# le favori est inconnu du gabarit (erreur PAR ITEM, pas une exception), le
# favoriteName est retiré et l'élément recréé (tapir_cree, repli n°2) ;
# les ouvertures signalent maintenant leurs vrais échecs.
# v2.15 : favoris lus dans le champ « favori » de l'export (référence Archicad
# du catalogue) pour murs, plancher, toiture, ouvertures, charpente et
# fenêtres de toit (repli sur les dictionnaires FAVORIS_* du script) ;
# côtés nature="charpente" = poteaux + poutres (CreateColumns/CreateBeams),
# plus de mur ; mur est/ouest partagé entre deux modules = pignon intérieur
# relevé au faîtage ; débord de couverture sur mur partagé = épaisseur/2 (les
# toitures se rejoignent au milieu du mur) ; fenêtres de toit via
# CreateSkylights sur la couverture du versant concerné ; correction du
# centerOffset des ouvertures (classification vertical/horizontal sur les
# axes envoyés).
# v2.14 : tous les murs sont créés avec +0,40 m de hauteur (SURHAUSSE_MURS)
# et TOUS sont découpés par la couverture de leur(s) module(s) en opération
# solide SEO (CreateSolidElementLinks, SubtractionUpwards) -> les murs ne
# dépassent jamais la toiture, pignons compris.
# v2.13 : sens de tracé des murs adapté à la version de Tapir — Tapir >= 2.0
# a inversé le côté du corps du mur par rapport à la ligne directrice :
# axes_envoi() échange beg<->end à l'envoi (la ligne ne bouge pas, seul le
# corps bascule du bon côté : EXTÉRIEUR).
# v2.12 : toitures en multi-plans par niveau avec débords d'arête natifs
# (pivotEdges, Tapir >= 2.0) : le polygone reste la LIGNE DIRECTRICE et
# Archicad calcule le contour -> hauteur identique au droit des murs, même
# aux jonctions entre modules ; niveau couverture = H + épaisseur du complexe
# (toit.epaisseur du configurateur). Repli v2.9 (versants monoplanes, angle
# = -angle car le miroir Y inverse le sens de rotation, pivot sur la ligne
# directrice, polygone étendu) si CreateRoofs refuse levels/pivotEdges.
# Pignons : murs est/ouest libres montés au faîtage, découpés par la
# couverture en OPÉRATION SOLIDE (CreateSolidElementLinks, mur = cible,
# toit = opérateur, SubtractionUpwards, section 3b) — plus de TrimElements.
# v2.9 : ligne de référence = face INTÉRIEURE, compatible Tapir 1.7.2 :
# CreateWalls y refuse le champ "flipped", donc on inverse le SENS de tracé
# de chaque mur (beg<->end) + referenceLineLocation "Inside" — avec la
# convention Archicad de Tapir 1.7.2 (face extérieure d'un mur non flippé =
# DROITE du sens beg->end), ce couple pose la ligne sur la face intérieure
# tout en gardant le corps vers l'extérieur.
# v2.7 : miroir Y (dans l'export +Y = Sud, dans Archicad +Y = Nord) ; dédup des
# murs partagés robuste (arrondi au cm) ; couverture = débord + épaisseur de
# mur, au-delà du mur.
# v2.6 : murs créés un par un (id fiables) ; toitures superposées complexe +
# couverture par module.
# v2.4 : déballe l'enveloppe de soumission (clé « configuration » des fichiers
# téléchargés depuis le back-office), importe TOUTES les instances (modules
# accolés, module["instances"]), lit le plancher en objet ou en chaîne,
# pilote la toiture par « geometrie » (repli sur l'ancien « type »).
# v2.5 : sens de tracé inversé (ligne directrice = face INTÉRIEURE, corps du
# mur vers l'EXTÉRIEUR, comme dans le configurateur) ; murs partagés entre
# modules accolés dédoublonnés ; ouvertures placées par centre absolu (bon mur
# garanti) ; pignons (murs extrêmes montant au faîtage, taillés par la
# toiture) ; UN plancher et UNE toiture PAR module.
"""
Baracca — Import de module configuré depuis le site web vers Archicad
=====================================================================
Brique 2 du flux : lit le JSON exporté par le configurateur web Baracca
(ou l'enveloppe de soumission téléchargée depuis le back-office)
et génère les éléments dans le projet Archicad ouvert.

Schémas Tapir v1.7.2 (vérifiés contre les exemples officiels du dépôt
ENZYME-APD/tapir-archicad-automation, fichier create_elements.py) :

  CreateLayers  : {"layerDataArray": [{"name": ...}]}
  CreateWalls   : {"wallsData": [{"begCoordinate": {x,y},
                                  "endCoordinate": {x,y},
                                  "height": h, "thickness": t,
                                  "favoriteName": "..." (optionnel)}]}
      -> réponse : {"elements": [{"elementId": {...}}, ...]}
  CreateWindows : {"windowsData": [{"ownerWallId": <elementId>,
                                    "centerOffset": d (centre, depuis
                                    begCoordinate du mur),
                                    "width": w, "height": h,
                                    "favoriteName": ... (optionnel)}]}
  CreateDoors   : {"doorsData": [mêmes champs que CreateWindows]}
  CreateSlabs   : {"slabsData": [{"level": z,
                                  "polygonCoordinates": [{x,y}...]}]}
  CreateRoofs   : {"roofsData": [{"level": z,
                                  "polygonCoordinates": [{x,y}...},
                                  "pivotLine": {begin,end} + "angle":
                                  pour une toiture monopente]}

Prérequis :
  1. Archicad lancé, projet/gabarit Baracca ouvert.
  2. Add-on Tapir installé (Options > Gestionnaire d'add-ons).
  3. pip install archicad

Utilisation :
  python baracca_import.py module.json          # à l'origine (0,0)
  python baracca_import.py module.json --pick   # origine cliquée
  python baracca_import.py --probe              # diagnostic des commandes

Méthode : murs, planchers et toitures reçoivent la STRUCTURE COMPOSITE dont
le nom est la « Référence Archicad » du catalogue (résolue via
GetAttributesByType, insensible à la casse/accents/dossier) — jamais de
favori sur ces éléments, car un
favori écraserait l'orientation du mur et la pente/niveau du toit. Les favoris
ne sont appliqués qu'aux ouvrants, poteaux/poutres et fenêtres de toit.
"""

import argparse
import json
import math
import sys
import unicodedata

from archicad import ACConnection

# ---------------------------------------------------------------------------
# Favoris du gabarit Baracca (Fichier > Systèmes d'environnement > Favoris).
# Créez un favori de l'outil Mur par type Baracca avec le bon composite et
# calque, et reportez son nom exact ici. Laissez None pour utiliser les
# réglages par défaut de l'outil.
# ---------------------------------------------------------------------------
FAVORIS_MURS = {
    "Mur CLT 90 mm": None,           # ex. "Baracca CLT 90"
    "Mur CLT 140 mm": None,          # ex. "Baracca CLT 140"
    "Ossature bois 160 mm": None,    # ex. "Baracca OSS 160"
    "Bloc béton 200 mm": None,       # ex. "Baracca BET 200"
}
FAVORIS_PLANCHER = {
    "Dalle CLT + chape": None,
    "Plancher bois sur lambourdes": None,
    "Dalle béton": None,
}
FAVORIS_OUVERTURES = {
    "baie": None,
    "fenetre": None,
    "porte": None,
}
FAVORIS_TOITURE = {}      # repli si l'export n'a pas de champ « favori »
FAVORIS_CHARPENTE = {}    # idem pour poteaux/poutres


def favori_de(obj, repli_dict, cle):
    """Favori Archicad d'un élément : le champ « favori » de l'export (colonne
    « Référence Archicad » du catalogue back-office), sinon repli sur le
    dictionnaire FAVORIS_* du script."""
    f = ""
    if isinstance(obj, dict):
        f = str(obj.get("favori") or "").strip()
    return f or repli_dict.get(cle)

LAYER = "BARACCA_Modules"

# Orientation des murs (Archicad 30 / Tapir >= 2.0 uniquement). Convention
# configurateur : la ligne directrice tracée = la face INTÉRIEURE du mur, le
# corps s'étend vers l'EXTÉRIEUR, la face EXTÉRIEURE (côté « soleil » des
# fenêtres/portes) est sur la face opposée à la ligne.
# Sur AC30/Tapir 2.0, la combinaison qui marche est : axes beg<->end échangés
# à l'envoi (axes_envoi) + referenceLineLocation="Inside" — la ligne reste aux
# mêmes coordonnées, le corps part vers l'EXTÉRIEUR et la face extérieure est
# du bon côté (testé en v2.14 : « la face est du bon côté »). Axes tels quels +
# "Outside" (v2.21) donnait le bon corps mais la face extérieure marquée côté
# ligne (ouvrants inversés). Le champ "flipped" reste refusé par le schéma
# CreateWalls de Tapir 2.0.0.
WALL_REFERENCE_LINE_LOCATION = "Inside"

# Découpe des pignons par la couverture via OPÉRATION SOLIDE (SEO), et non via
# TrimElements : mur pignon = CIBLE (targetId), toit de couverture du module =
# OPÉRATEUR (operatorId), opération = "SubtractionUpwards" (soustraction avec
# extrusion vers le haut) -> le toit extrudé vers le haut rogne le mur au-dessus
# de sa face inférieure : on garde la partie SOUS la toiture -> triangle de
# pignon. (Commande Tapir : CreateSolidElementLinks.)
SEO_OPERATION = "SubtractionUpwards"

# Surhaussement appliqué à TOUS les murs à la création (m) : les murs montent
# au-dessus des toitures, puis sont rognés par la couverture via l'opération
# solide (section 3b) -> pignons et rives correctement découpés, quelle que
# soit la hauteur de toit.
SURHAUSSE_MURS = 0.40

def guid_of(element_id):
    """Normalise un elementId Tapir (objet {"guid": ...} ou chaîne) en guid."""
    if isinstance(element_id, dict):
        return element_id.get("guid")
    return element_id


class ArchicadBridge:
    """Surcouche au-dessus de l'API JSON + Tapir, avec diagnostic."""

    def __init__(self):
        self.conn = ACConnection.connect()
        if self.conn is None:
            sys.exit("Aucune instance d'Archicad détectée. "
                     "Lancez Archicad avec un projet ouvert.")
        self.commands = self.conn.commands
        self.types = self.conn.types
        self._check_tapir()

    def _check_tapir(self):
        try:
            version = self.tapir("GetAddOnVersion")
            v = str(version.get("version", ""))
            print(f"Tapir détecté : v{v}")
            try:
                major = int(v.split(".")[0])
            except (ValueError, IndexError):
                major = 99
            if major < 2:
                print("  ! Ce script ne cible que Archicad 30 / Tapir >= 2.0 : "
                      "résultat non garanti sur cette version.")
        except Exception as exc:
            sys.exit(f"Add-on Tapir introuvable : {exc}")

    def tapir(self, command, parameters=None):
        """Exécute une commande Tapir ; sur erreur, affiche payload et
        message exact pour un diagnostic immédiat."""
        try:
            return self.commands.ExecuteAddOnCommand(
                self.types.AddOnCommandId("TapirCommand", command),
                parameters or {},
            )
        except Exception as exc:
            print(f"\n[ÉCHEC Tapir] {command}")
            print(f"  payload : {json.dumps(parameters, default=str)[:800]}")
            print(f"  erreur  : {exc}")
            raise

    def tapir_cree(self, command, parameters):
        """Commande de CRÉATION avec replis :
        1. si Tapir refuse un champ optionnel (favoriteName,
           referenceLineLocation...) via 'additionalProperties', on le retire
           de tous les items et on réessaie, une fois par champ ;
        2. si la réponse contient une ERREUR PAR ITEM (ex. favori inconnu du
           gabarit Archicad) alors que les items avaient un favoriteName, on
           retire le favori partout et on réessaie une fois.
        Toute autre erreur est relancée."""
        repli = ("favoriteName", "referenceLineLocation",
                 "compositeId", "structureType", "buildingMaterialId",
                 "refSide", "oSide", "reflected")
        while True:
            key = next((k for k, v in parameters.items()
                        if isinstance(v, list)), None)
            try:
                resp = self.tapir(command, parameters)
            except Exception as exc:
                msg = str(exc)
                champ = next((c for c in repli
                              if c in msg and key is not None
                              and any(isinstance(d, dict) and c in d
                                      for d in parameters[key])), None)
                if champ is None:
                    raise
                for d in parameters[key]:
                    if isinstance(d, dict):
                        d.pop(champ, None)
                print(f"  ! Champ {champ} refusé par {command} : éléments "
                      f"recréés sans ce champ.")
                continue
            elems = resp.get("elements") if isinstance(resp, dict) else None
            if (key and elems
                    and any(isinstance(e, dict) and e.get("error") for e in elems)
                    and any(isinstance(d, dict)
                            and any(c in d for c in repli)
                            for d in parameters[key])):
                for d in parameters[key]:
                    if isinstance(d, dict):
                        for c in repli:
                            d.pop(c, None)
                print(f"  ! {command} : favori/composite refusé par Archicad "
                      f"(introuvable dans le gabarit ?) : éléments recréés sans.")
                continue
            return resp

    def ensure_layer(self, name):
        """Crée le calque ; 'Already exists' (créé par un import
        précédent) est traité comme un succès."""
        response = self.tapir("CreateLayers",
                              {"layerDataArray": [{"name": name}]})
        for entry in response.get("attributeIds", []):
            err = entry.get("error", {})
            if err and "Already exists" not in err.get("message", ""):
                print(f"  ! Calque {name} : {err}")

    def pick_point(self):
        return self.tapir("GetPointFromUser")["point"]


# ---------------------------------------------------------------------------
# Mode --probe : valide chaque commande avec une charge minimale
# ---------------------------------------------------------------------------
def probe():
    bridge = ArchicadBridge()
    print("=" * 64)
    print("MODE PROBE — validation des commandes (schémas Tapir 1.7.2)")
    print("=" * 64)

    ok = []

    # 1. Calque (« Already exists » = déjà créé par un import précédent : OK)
    try:
        r = bridge.tapir("CreateLayers",
                         {"layerDataArray": [{"name": LAYER}]})
        deja = any("Already exists" in str(e) for e in r.get("attributeIds", []))
        print(f"CreateLayers           OK : "
              f"{'(calque déjà existant)' if deja else json.dumps(r, default=str)[:120]}")
        ok.append(True)
    except Exception:
        ok.append(False)

    # 2. Mur (ligne directrice sur le contour : corps du mur vers
    #    l'intérieur avec le gabarit Baracca)
    wall_id = None
    try:
        payload = {
            "begCoordinate": {"x": 0.0, "y": 0.0},
            "endCoordinate": {"x": 3.0, "y": 0.0},
            "height": 2.8,
            "thickness": 0.14,
        }
        r = bridge.tapir("CreateWalls", {"wallsData": [payload]})
        print(f"CreateWalls            OK : {json.dumps(r, default=str)[:200]}")
        wall_id = r["elements"][0]["elementId"]
        ok.append(True)
    except Exception:
        ok.append(False)

    # 3. Plancher (RDC : niveau 0)
    try:
        r = bridge.tapir("CreateSlabs", {"slabsData": [{
            "level": 0.0,
            "polygonCoordinates": [
                {"x": 0.0, "y": 0.0}, {"x": 3.0, "y": 0.0},
                {"x": 3.0, "y": 2.0}, {"x": 0.0, "y": 2.0},
            ],
        }]})
        print(f"CreateSlabs            OK : {json.dumps(r, default=str)[:160]}")
        ok.append(True)
    except Exception:
        ok.append(False)

    # 4. Toiture monopente (pivotLine + angle en radians)
    try:
        r = bridge.tapir("CreateRoofs", {"roofsData": [{
            "level": 2.8,
            "polygonCoordinates": [
                {"x": 0.0, "y": 0.0}, {"x": 3.0, "y": 0.0},
                {"x": 3.0, "y": 2.0}, {"x": 0.0, "y": 2.0},
            ],
            "pivotLine": {
                "begCoordinate": {"x": 0.0, "y": 0.0},
                "endCoordinate": {"x": 3.0, "y": 0.0},
            },
            # 15° exprimés en radians (convention API Archicad)
            "angle": round(math.radians(15), 6),
        }]})
        errs = [e.get("error") for e in r.get("elements", [])
                if e.get("error")]
        if errs:
            print(f"CreateRoofs (monopente) ERREUR PAR ÉLÉMENT : {errs}")
            ok.append(False)
        else:
            print(f"CreateRoofs (monopente) OK : "
                  f"{json.dumps(r, default=str)[:160]}")
            # Lecture retour : angle réellement stocké par Archicad
            roof_id = r["elements"][0]["elementId"]
            try:
                details = bridge.tapir("GetDetailsOfElements",
                                       {"elements": [roof_id]})
                print("  Lecture retour (GetDetailsOfElements) :")
                print(f"  {json.dumps(details, default=str)[:600]}")
                print("  -> vérifiez dans Archicad que la pente affichée"
                      " est ~15°")
            except Exception as exc:
                print(f"  (lecture retour impossible : {exc})")
            ok.append(True)
    except Exception:
        ok.append(False)

    # 5. Fenêtre + porte dans le mur de test
    if wall_id is not None:
        try:
            r = bridge.tapir("CreateWindows", {"windowsData": [{
                "ownerWallId": wall_id,
                "centerOffset": 1.0,
                "width": 1.0,
                "height": 1.2,
            }]})
            print(f"CreateWindows          OK : "
                  f"{json.dumps(r, default=str)[:160]}")
            ok.append(True)
        except Exception:
            ok.append(False)
        try:
            r = bridge.tapir("CreateDoors", {"doorsData": [{
                "ownerWallId": wall_id,
                "centerOffset": 2.2,
                "width": 0.9,
                "height": 2.1,
            }]})
            print(f"CreateDoors            OK : "
                  f"{json.dumps(r, default=str)[:160]}")
            ok.append(True)
        except Exception:
            ok.append(False)

    print("-" * 64)
    if all(ok):
        print("TOUT EST VALIDE ✓ — les éléments de test peuvent être "
              "supprimés (Ctrl+Z) et l'import peut être lancé.")
    else:
        print(f"{ok.count(False)} commande(s) en échec — envoyez la sortie "
              "complète pour ajustement.")


# ---------------------------------------------------------------------------
# Géométrie du module
# Origine au coin Sud-Ouest ; X vers l'Est, Y vers le Nord.
# begCoordinate de chaque mur = point depuis lequel le configurateur mesure
# la position des ouvertures.
# ---------------------------------------------------------------------------
def liste_unites(module):
    """Unités à importer : toutes les instances placées (modules accolés,
    module["instances"]) ; repli sur l'ancien schéma (module.murs = 1 module)."""
    insts = module.get("instances")
    if isinstance(insts, list) and insts:
        return insts
    return [{"id": "m0", "x": 0.0, "y": 0.0,
             "dimensions": module["dimensions"], "murs": module.get("murs", {})}]


def wall_segments(unite):
    """Axes des murs d'une unité (un module) pour la création dans Archicad.

    Origine au coin Sud-Ouest de l'unité (x, y de l'instance) ; X vers
    l'Est, Y vers le Nord ; le contour du module = face EXTÉRIEURE des murs.

    Convention du configurateur (vérifiée sur les exports) : dans le JSON,
    +Y va vers le SUD (le plan SVG a Y vers le bas, Nord en haut) ; on applique
    un miroir Y à l'import (v2.7) pour avoir +Y = Nord dans Archicad.
    Axes exprimés en coordonnées EXPORT (avant miroir) : nord en y=by,
    sud en y=by+l. Envoyés tels quels à CreateWalls avec
    referenceLineLocation="Outside" (AC30/Tapir >= 2.0) : le corps du mur
    part vers l'EXTÉRIEUR et le côté soleil des ouvrants aussi.

    Convention du configurateur pour les ouvertures (voir le plan) :
      - sud et nord : position mesurée depuis le coin OUEST du module ;
      - est et ouest : position mesurée depuis le coin NORD du module (y=by).
    """
    dims = unite["dimensions"]
    L, l, H = dims["longueur"], dims["largeur"], dims["hauteur"]
    bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
    axes = {
        "nord":  ((bx + L, by),     (bx, by)),           # Est -> Ouest
        "sud":   ((bx, by + l),     (bx + L, by + l)),   # Ouest -> Est
        "est":   ((bx + L, by + l), (bx + L, by)),       # vers le -Y export
        "ouest": ((bx, by),         (bx, by + l)),       # vers le +Y export
    }
    segments = {}
    for face_key in ("sud", "est", "nord", "ouest"):
        face = unite.get("murs", {}).get(face_key) or {}
        if not face.get("actif"):
            continue
        if str(face.get("nature") or "").lower() == "charpente":
            continue   # v2.18 : côté charpente = poteaux + poutres (section 1b), pas de mur
        beg, end = axes[face_key]
        segments[face_key] = {
            "face": face_key,
            "beg": beg, "end": end,
            "hauteur": H,
            "epaisseur": face.get("epaisseur", 0.14),
            "type": face.get("type", ""),
            "favori": face.get("favori", ""),   # v2.18 : référence Archicad du mur
            "ouvertures": face.get("ouvertures", []),
            "L": L, "l": l,  # dimensions du module : calcul des centerOffset
        }
    return segments


def slab_polygon(module):
    """Polygone du plancher : rectangle de la ligne directrice des murs,
    élargi du débord de plancher si l'export le fournit (plancher en objet)."""
    dims = module["dimensions"]
    L, l = dims["longueur"], dims["largeur"]
    pl = module.get("plancher")
    if isinstance(pl, dict) and pl.get("longueur") and pl.get("largeur"):
        dL = (float(pl["longueur"]) - L) / 2.0
        dl = (float(pl["largeur"]) - l) / 2.0
        return [{"x": -dL, "y": -dl}, {"x": L + dL, "y": -dl},
                {"x": L + dL, "y": l + dl}, {"x": -dL, "y": l + dl}]
    return [{"x": 0.0, "y": 0.0}, {"x": L, "y": 0.0},
            {"x": L, "y": l}, {"x": 0.0, "y": l}]


def plancher_nom(module):
    """Nom du plancher : l'export actuel fournit un objet {nom, favori, ...},
    les anciens exports une simple chaîne."""
    pl = module.get("plancher")
    if isinstance(pl, dict):
        return pl.get("nom", "")
    return pl or ""


def toiture_geo(toit):
    """Géométrie de la toiture : champ stable « geometrie » de l'export
    (monopente / deuxpentes / quatrepentes / terrasse), avec repli sur
    l'ancien champ « type » (« Deux pentes »…) des exports d'avant v2.4."""
    geo = (toit.get("geometrie") or "").strip().lower()
    if geo:
        return geo
    t = (toit.get("type") or "").strip().lower()
    return {"monopente": "monopente", "deux pentes": "deuxpentes",
            "quatre pentes": "quatrepentes", "terrasse": "terrasse"}.get(
                t, t.replace(" ", ""))


def cle_ligne(beg, end):
    """Clé normalisée d'une ligne (indépendante du sens de tracé).
    Arrondi au cm (2 décimales) : robuste aux bruits flottants
    (ex. 4.82+0.255/2 vs 5.075-0.255/2) qui sinon séparent un mur partagé."""
    a = (round(beg[0], 2), round(beg[1], 2))
    b = (round(end[0], 2), round(end[1], 2))
    return (a, b) if a <= b else (b, a)


def cle_mur(face_key, seg):
    """Clé d'un MUR physique = sa ligne médiane (corps), pas sa directrice.
    Convention configurateur : la ligne directrice est la face INTÉRIEURE,
    le corps s'étend vers l'EXTÉRIEUR d'une épaisseur. Deux modules accolés
    ont donc des directrices distantes d'une épaisseur mais le MÊME mur
    physique -> même clé, le mur partagé n'est créé qu'une fois."""
    ep = float(seg.get("epaisseur", 0.0))
    # normales EXTÉRIEURES en coordonnées EXPORT (+Y = Sud, v2.7) :
    # le corps du mur s'étend vers l'extérieur de chaque module.
    nx, ny = {"sud": (0.0, 1.0), "nord": (0.0, -1.0),
              "est": (1.0, 0.0), "ouest": (-1.0, 0.0)}.get(face_key, (0.0, 0.0))
    dx, dy = nx * ep / 2.0, ny * ep / 2.0
    return cle_ligne((seg["beg"][0] + dx, seg["beg"][1] + dy),
                     (seg["end"][0] + dx, seg["end"][1] + dy))


def ouverture_centre(unite, face_key, ouv):
    """Centre de l'ouverture en coordonnées EXPORT de l'unité.
    Convention configurateur : position depuis le coin OUEST pour sud/nord
    (axe X), depuis le coin NORD pour est/ouest — le coin nord est à y=by
    (petit Y, car +Y export = Sud)."""
    dims = unite["dimensions"]
    L, l = float(dims["longueur"]), float(dims["largeur"])
    bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
    p = float(ouv.get("position", 0.0))
    w = float(ouv.get("largeur", 0.0))
    if face_key == "nord":
        return (bx + p + w / 2.0, by)
    if face_key == "sud":
        return (bx + p + w / 2.0, by + l)
    if face_key == "est":
        return (bx + L, by + p + w / 2.0)
    return (bx, by + p + w / 2.0)  # ouest


def debord_plancher(module):
    """Débord du plancher de chaque côté (dL, dl), lu dans l'export (plancher
    en objet) ; défaut 0,217 m (constante PLANCHER_DEPASSEMENT du configurateur)."""
    pl = module.get("plancher")
    dims = module.get("dimensions", {})
    if isinstance(pl, dict) and pl.get("longueur") and pl.get("largeur"):
        return (max(0.0, (float(pl["longueur"]) - float(dims.get("longueur", 0.0))) / 2.0),
                max(0.0, (float(pl["largeur"]) - float(dims.get("largeur", 0.0))) / 2.0))
    return (0.217, 0.217)


# ---------------------------------------------------------------------------
# Import principal
# ---------------------------------------------------------------------------
def import_module(data, pick_origin=False):
    module = data["module"]
    name = module["nom"]
    unites = liste_unites(module)
    print(f"Import du module « {name} » (schéma {data.get('schemaVersion')}, "
          f"{len(unites)} module(s) placé(s))…")

    bridge = ArchicadBridge()
    bridge.ensure_layer(LAYER)

    # v2.19 : la « Référence Archicad » des murs / plancher / toitures est le
    # NOM DU COMPOSITE (les composites portent le même nom que les favoris).
    # On applique la structure composite à la création (structureType +
    # compositeId), JAMAIS le favori : un favori de mur/toiture écraserait
    # l'orientation du mur (refLine/flip) et la pente/niveau du toit.
    # Correspondance de nom insensible à la casse et aux accents.
    def normaliser_nom(s):
        s = unicodedata.normalize("NFKD", str(s))
        s = "".join(c for c in s if not unicodedata.combining(c))
        return " ".join(s.lower().split())

    def guid_de(a):
        """guid d'un attribut Tapir, quel que soit l'imbrication :
        {"guid": ...}, {"attributeId": "..."} ou
        {"attributeId": {"guid": ...}} / {"attributeId": {"attributeId": {"guid": ...}}}"""
        if not isinstance(a, dict):
            return None
        if isinstance(a.get("guid"), str):
            return a["guid"]
        for k in ("attributeId", "id"):
            v = a.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, dict):
                g = guid_de(v)
                if g:
                    return g
        return None

    def lire_composites(rep):
        """Extrait {nom normalisé -> [(nom affiché, guid), ...]} de la réponse
        GetAttributesByType, en parcourant toute la structure (listes et
        sous-dossiers « children »/« folders »). Les composites rangés dans un
        dossier (ex. « BARACCA ») sont enregistrés sous leur nom complet
        « DOSSIER/Nom » ET sous leur dernier segment « Nom » : la
        « Référence Archicad » du catalogue retrouve ainsi le composite quel
        que soit son dossier. En cas de doublons (même nom dans deux dossiers),
        TOUS les candidats sont conservés."""
        out = {}

        def registre(nom, g):
            nom = str(nom)
            # v2.21 : on conserve l'OBJET id {"guid": ...} — Tapir 2.0 attend
            # compositeId en objet (cf. exemple officiel create_composite_slab.py),
            # une simple chaîne est ignorée silencieusement par Archicad.
            g_obj = {"guid": str(g)}
            cles = {normaliser_nom(nom)}
            for sep in ("/", "\\"):
                if sep in nom:
                    cles.add(normaliser_nom(nom.rsplit(sep, 1)[-1]))
            for c in cles:
                out.setdefault(c, []).append((nom, g_obj))

        def walk(obj):
            if isinstance(obj, list):
                for v in obj:
                    walk(v)
            elif isinstance(obj, dict):
                nm = obj.get("name") or obj.get("attributeName")
                g = guid_de(obj)
                if nm and g:
                    registre(nm, g)
                    return
                for v in obj.values():
                    walk(v)

        walk(rep)
        return out

    composites_par_nom = {}
    try:
        # GetComposites exige des attributeIds : pour LISTER tous les
        # composites du gabarit, on passe par GetAttributesByType.
        rep = bridge.tapir("GetAttributesByType", {"attributeType": "Composite"})
        composites_par_nom = lire_composites(rep)
        noms_lus = sorted({v[0] for lst in composites_par_nom.values() for v in lst})
        print(f"  {len(noms_lus)} composite(s) lu(s) dans le gabarit Archicad :")
        for nm in noms_lus[:300]:
            print(f"    - {nm}")
    except Exception as exc:
        print(f"  ! GetAttributesByType indisponible ({exc}) : composites non appliqués.")

    def dossier_de(nom):
        """partie « dossier » d'un nom complet « DOSSIER/Nom » (normalisée)."""
        for sep in ("/", "\\"):
            if sep in nom:
                return normaliser_nom(nom.rsplit(sep, 1)[0])
        return ""

    _resolutions_affichees = set()

    def resoudre_composite(nom_ref):
        """guid du composite dont le nom correspond à la « Référence Archicad »
        (avec ou sans préfixe de dossier), sinon None + avertissement
        (jamais de repli sur le favori). En cas de doublons, on préfère le
        nom exact sans dossier, puis le dossier « BARACCA », et on affiche
        le choix effectué (une seule fois par référence)."""
        if not nom_ref:
            return None
        cles = [normaliser_nom(nom_ref)]
        for sep in ("/", "\\"):
            if sep in str(nom_ref):
                cles.append(normaliser_nom(str(nom_ref).rsplit(sep, 1)[-1]))
        for c in cles:
            candidats = composites_par_nom.get(c)
            if not candidats:
                continue
            if nom_ref not in _resolutions_affichees:
                _resolutions_affichees.add(nom_ref)
                if len(candidats) > 1:
                    print(f"  ! Plusieurs composites correspondant à « {nom_ref} » :")
                    for nm, g in candidats:
                        print(f"      - {nm}  ({g.get('guid')})")
                exact = [x for x in candidats
                         if normaliser_nom(x[0]) == c and not dossier_de(x[0])]
                pool = exact or candidats
                pref = [x for x in pool if dossier_de(x[0]) == "baracca"]
                choix = (pref or pool)[0]
                print(f"  Référence « {nom_ref} » -> composite « {choix[0]} » "
                      f"({choix[1].get('guid')})")
            exact = [x for x in candidats
                     if normaliser_nom(x[0]) == c and not dossier_de(x[0])]
            pool = exact or candidats
            pref = [x for x in pool if dossier_de(x[0]) == "baracca"]
            return (pref or pool)[0][1]
        if nom_ref not in _resolutions_affichees:
            _resolutions_affichees.add(nom_ref)
            print(f"  ! Composite « {nom_ref} » introuvable dans le gabarit : "
                  f"élément créé avec les réglages par défaut (pas de favori).")
        return None

    ox, oy = 0.0, 0.0
    if pick_origin:
        print("Cliquez l'origine du module dans la fenêtre Archicad…")
        point = bridge.pick_point()
        ox, oy = point["x"], point["y"]
        print(f"Origine retenue : ({ox:.2f}, {oy:.2f})")

    # v2.7 : miroir Y — dans l'export +Y = Sud (plan SVG, Nord en haut) ;
    # dans Archicad +Y = Nord. y_ac = YG - y_export (+ origine choisie).
    YG = float(module["dimensions"]["largeur"])

    def tr(pt):
        return {"x": pt[0] + ox, "y": (YG - pt[1]) + oy}

    # --- 1. Murs (toutes les instances, murs partagés dédoublonnés) --------
    # Ligne directrice = face INTÉRIEURE (convention configurateur : le corps
    # du mur va vers l'EXTÉRIEUR). AC30/Tapir >= 2.0 : axes de wall_segments
    # envoyés tels quels + referenceLineLocation="Outside" (voir constante
    # WALL_REFERENCE_LINE_LOCATION). AUCUN décalage de demi-épaisseur.
    # v2.18 : tous les murs reçoivent + SURHAUSSE_MURS (0,40 m) à la création.
    toit = module["toiture"]
    geo = toiture_geo(toit)   # monopente / deuxpentes / quatrepentes / terrasse
    pignon = bool(toit.get("pignon"))
    pente = float(toit.get("pente") or 0)
    # v2.18 : deux-pentes asymétrique — convention configurateur : versant
    # NORD = pente (pente1), versant SUD = pente2 (défaut = pente).
    pente_sud = pente
    if geo == "deuxpentes":
        try:
            p2 = toit.get("pente2")
            if p2 is not None and float(p2) > 0:
                pente_sud = float(p2)
        except (TypeError, ValueError):
            pass
    angle_nord = round(math.radians(pente), 6)
    angle_sud = round(math.radians(pente_sud), 6)

    def faitage(l_u):
        """v2.18 : (position du faîtage depuis le bord nord, hauteur de faîtage)
        pour une largeur l_u. Symétrique : l/2 et tan(pente)*l/2. Asymétrique
        (C=tan nord, P=tan sud) : x = l*P/(C+P) depuis le nord, hf = x*C."""
        C = math.tan(math.radians(pente))
        P = math.tan(math.radians(pente_sud))
        if geo == "deuxpentes" and C > 0 and P > 0:
            x = l_u * P / (C + P)
            return x, x * C
        return l_u / 2.0, C * l_u / 2.0
    segments_par_unite = [(u, wall_segments(u)) for u in unites]

    # Un mur partagé entre deux modules accolés est la même ligne tracée deux
    # fois (sens opposés) : on ne la crée qu'une fois, en fusionnant les
    # ouvertures des deux côtés.
    canon = {}   # clé de ligne -> segment canonique
    alias = {}   # (uid, face) -> clé de ligne canonique
    unites_par_cle = {}   # clé de mur -> {uid des modules auxquels il appartient}
    for unite, segments in segments_par_unite:
        uid = unite.get("id", "m0")
        for face_key in ("sud", "est", "nord", "ouest"):
            seg = segments.get(face_key)
            if not seg:
                continue
            cle = cle_mur(face_key, seg)
            alias[(uid, face_key)] = cle
            unites_par_cle.setdefault(cle, set()).add(uid)
            if cle in canon:
                canon[cle]["ouvertures"] = canon[cle]["ouvertures"] + seg["ouvertures"]
            else:
                canon[cle] = {**seg, "ouvertures": list(seg["ouvertures"])}

    # Nombre d'instances partageant chaque mur (murs accolés = comptés 2x)
    cle_count = {}
    for _u, _segs in segments_par_unite:
        for _f, _seg in _segs.items():
            _c = cle_mur(_f, _seg)
            cle_count[_c] = cle_count.get(_c, 0) + 1

    # Pignons (deux pentes à pignon) PAR MODULE : chaque côté est/ouest monte
    # jusqu'au faîtage de SA toiture — y compris un mur est/ouest PARTAGÉ entre
    # deux modules accolés (v2.18 : c'est un pignon intérieur, mur central
    # entre les deux modules) ; la couverture le découpe en triangle (opération
    # solide SEO en section 3b, comme tous les murs). Côté "charpente" : pas de
    # mur, un cadre poteaux + poutres (section 1b).
    pignon_cles = {}   # uid -> [clés de murs pignons de ce module]
    # v2.18 : côtés en charpente sur LES 4 faces (pas seulement est/ouest)
    charpente_faces = []   # (unite, face_key) des côtés en charpente
    for unite, _segments in segments_par_unite:
        for face_key in ("nord", "est", "sud", "ouest"):
            face_mur = unite.get("murs", {}).get(face_key) or {}
            if str(face_mur.get("nature") or "").lower() == "charpente":
                charpente_faces.append((unite, face_key))
    if geo == "deuxpentes" and pignon:
        for unite, segments in segments_par_unite:
            uid = unite.get("id", "m0")
            dims_u = unite["dimensions"]
            L_u = float(dims_u["longueur"])
            l_u = float(dims_u["largeur"])
            H_u = float(dims_u["hauteur"])
            hf_u = faitage(l_u)[1]
            bx = float(unite.get("x", 0.0))
            by = float(unite.get("y", 0.0))
            for face_key, x in (("ouest", bx), ("est", bx + L_u)):
                seg = segments.get(face_key)
                face_mur = unite.get("murs", {}).get(face_key) or {}
                if seg is not None:
                    cle = alias[(uid, face_key)]
                    # v2.18 : relevé au faîtage même si partagé (max des deux
                    # faîtages possibles si les modules diffèrent).
                    h_pig = H_u + hf_u
                    if canon[cle].get("hauteur", 0.0) < h_pig:
                        canon[cle]["hauteur"] = h_pig
                    canon[cle]["pignon"] = True
                    pignon_cles.setdefault(uid, []).append(cle)
                elif str(face_mur.get("nature") or "").lower() == "charpente":
                    pass   # déjà collecté globalement ci-dessus (pas de mur)
                else:
                    # rive inactive sans charpente : mur de pignon à fond
                    ref = next((segments[f] for f in ("nord", "sud")
                                if segments.get(f)), None)
                    ep = ref["epaisseur"] if ref else 0.14
                    type_mur = (ref or {}).get("type") or next(
                        (f.get("type", "") for f in module.get("murs", {}).values()
                         if isinstance(f, dict) and f.get("actif")), "Mur")
                    if face_key == "est":
                        beg, end = (x, by + l_u), (x, by)
                    else:
                        beg, end = (x, by), (x, by + l_u)
                    pseg = {"face": face_key, "beg": beg, "end": end,
                            "hauteur": H_u + hf_u, "epaisseur": ep,
                            "type": type_mur, "ouvertures": [], "pignon": True}
                    pcle = cle_mur(face_key, pseg)
                    canon[pcle] = pseg
                    pignon_cles.setdefault(uid, []).append(pcle)
    # Mur pignon créé en rive inactive : rattaché aussi à son module pour
    # la découpe SEO (section 3b).
    for uid, cles in pignon_cles.items():
        for c in cles:
            unites_par_cle.setdefault(c, set()).add(uid)

    walls_data = []
    types_sans_favori = set()

    def axes_envoi(seg):
        """v2.22 : AC30 / Tapir 2.0 — beg<->end échangés à l'envoi, combiné à
        referenceLineLocation="Inside" (v2.23) : la ligne directrice reste aux
        mêmes coordonnées, le corps du mur part vers l'EXTÉRIEUR et la face
        extérieure (côté « soleil » repris par les fenêtres/portes) est sur la
        face opposée à la ligne."""
        return seg["end"], seg["beg"]

    print(f"Création de {len(canon)} mur(s) sur {len(unites)} module(s)…")
    # Un mur par appel CreateWalls : l'elementId retourné est ainsi reliably
    # associé à sa ligne (pas de décalage d'index si un mur échoue).
    wall_ids = {}
    fav_a_appliquer = []   # (elementId, favori, keepFields) -> ApplyFavoritesToElements (section 5)
    for cle, seg in canon.items():
        beg_e, end_e = axes_envoi(seg)
        item = {
            # v2.23 : AC30/Tapir >= 2.0 — axes beg<->end échangés + "Inside" :
            # ligne en place, corps vers l'EXTÉRIEUR, face extérieure (soleil
            # des ouvrants) sur la face opposée à la ligne.
            "begCoordinate": tr(beg_e),
            "endCoordinate": tr(end_e),
            # v2.18 : tous les murs montent de SURHAUSSE_MURS au-dessus de leur
            # hauteur nominale (pignons : au-dessus du faîtage) ; la couverture
            # les rognera ensuite en opération solide (section 3b).
            "height": seg["hauteur"] + SURHAUSSE_MURS,
            "thickness": seg["epaisseur"],
            "referenceLineLocation": WALL_REFERENCE_LINE_LOCATION,
        }
        favori = favori_de(seg, FAVORIS_MURS, seg["type"])
        comp_id = resoudre_composite(favori) if favori else None
        if comp_id:
            # v2.19 : composite de mur appliqué à la création — JAMAIS le
            # favori (écraserait l'orientation du mur)
            item["structureType"] = "Composite"
            item["compositeId"] = comp_id
        elif not favori and seg["type"] not in types_sans_favori:
            types_sans_favori.add(seg["type"])
            print(f"  ! Pas de référence Archicad pour « {seg['type']} » : "
                  f"réglages par défaut de l'outil Mur.")
        walls_data.append((cle, item))
        # Repli automatique si Tapir refuse un champ optionnel
        # (additionalProperties) : tapir_cree le retire et réessaie.
        resp = bridge.tapir_cree("CreateWalls", {"wallsData": [item]})
        el = (resp.get("elements") or [{}])[0]
        if el.get("elementId") is not None:
            wall_ids[cle] = el["elementId"]
        elif el.get("error"):
            print(f"  ! Mur {seg['face']} non créé : {el['error']}")

    # --- 1b. Charpentes (nature="charpente") : poteaux + poutre, pas de mur ---
    # Un côté en charpente = cadre ouvert : 2 poteaux aux extrémités (hauteur H)
    # + 1 poutre sablière en tête (niveau H). Section = charpente.epaisseur,
    # favori = charpente.favori (outils Poteau / Poutre).
    if charpente_faces:
        ch = module.get("charpente") if isinstance(module.get("charpente"), dict) else {}
        ep_ch = float(ch.get("epaisseur") or 0.20)
        fav_ch = favori_de(ch, FAVORIS_CHARPENTE, "")
        cols_data, beams_data = [], []
        for unite, face_key in charpente_faces:
            uid = unite.get("id", "m0")
            dims_u = unite["dimensions"]
            L_u = float(dims_u["longueur"])
            l_u = float(dims_u["largeur"])
            H_u = float(dims_u["hauteur"])
            bx = float(unite.get("x", 0.0))
            by = float(unite.get("y", 0.0))
            # v2.18 : charpente possible sur les 4 côtés
            if face_key in ("est", "ouest"):
                x = bx if face_key == "ouest" else bx + L_u
                extremites = [(x, by), (x, by + l_u)]
            else:
                y = by if face_key == "nord" else by + l_u
                extremites = [(bx, y), (bx + L_u, y)]
            for pt in extremites:
                p = tr(pt)
                cols_data.append({"coordinates": {"x": p["x"], "y": p["y"], "z": 0.0},
                                  "height": H_u, "width": ep_ch, "depth": ep_ch})
            beams_data.append({"begCoordinate": tr(extremites[0]),
                               "endCoordinate": tr(extremites[1]),
                               "zCoordinate": H_u, "width": ep_ch, "height": ep_ch})
            # v2.18 : plus de poutre faîtière (doublon au niveau du toit) :
            # le cadre charpente = 2 poteaux + 1 sablière en tête de mur (H).
        if fav_ch:
            for c in cols_data:
                c["favoriteName"] = fav_ch
            for b in beams_data:
                b["favoriteName"] = fav_ch
        print(f"Création de la charpente ({len(cols_data)} poteau(x), "
              f"{len(beams_data)} poutre(s))…")
        for cmd, key, data in (("CreateColumns", "columnsData", cols_data),
                               ("CreateBeams", "beamsData", beams_data)):
            try:
                resp = bridge.tapir_cree(cmd, {key: data})
                if fav_ch:
                    for e in resp.get("elements", []):
                        if e.get("elementId") is not None:
                            fav_a_appliquer.append((e["elementId"], fav_ch, None))
            except Exception as exc:
                print(f"  ! {cmd} en échec ({exc}) : charpente non créée.")

    # --- 2. Planchers (UN par module, avec débord) --------------------------
    nom_plancher = plancher_nom(module)
    pl_obj = module.get("plancher") if isinstance(module.get("plancher"), dict) else {}
    favori_pl = favori_de(pl_obj, FAVORIS_PLANCHER, nom_plancher)
    dL, dl = debord_plancher(module)
    slabs_data = []
    for unite in unites:
        dims_u = unite["dimensions"]
        L, l = float(dims_u["longueur"]), float(dims_u["largeur"])
        bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
        item = {
            "level": 0.0,   # RDC : étage d'implantation 0, altitude 0
            "polygonCoordinates": [
                tr((bx - dL, by - dl)), tr((bx + L + dL, by - dl)),
                tr((bx + L + dL, by + l + dl)), tr((bx - dL, by + l + dl)),
            ],
        }
        comp_pl = resoudre_composite(favori_pl) if favori_pl else None
        if comp_pl:
            # v2.19 : composite de plancher à la création, jamais le favori
            item["structureType"] = "Composite"
            item["compositeId"] = comp_pl
        slabs_data.append(item)
    print(f"Création de {len(slabs_data)} plancher(s) ({nom_plancher})…")
    slab_response = bridge.tapir_cree("CreateSlabs", {"slabsData": slabs_data})
    errs = [e.get("error") for e in slab_response.get("elements", [])
            if e.get("error")]
    if errs:
        print(f"  ! Plancher(s) non créé(s) : {errs}")

    # --- 3. Toitures (PAR module, superposées : complexe + couverture) ------
    # - complexe de toiture : empreinte sur la LIGNE DIRECTRICE, niveau H ;
    # - couverture (toit avec débords) : empreinte élargie, au-dessus (niveau
    #   H + épaisseur du complexe). Le débord est compté depuis la face
    #   EXTÉRIEURE du mur (v2.7 : débord + épaisseur de mur) ; pas de débord
    #   sur les côtés communs à deux modules accolés.
    angle = round(math.radians(pente), 6)   # pente en RADIANS (convention API)
    ep_toit = float(toit.get("epaisseur") or 0.30)
    deb = float(toit.get("depassee") or ep_toit)   # débord de toiture (m)
    print(f"Création des toitures ({toit.get('type', geo)} / {geo}"
          f"{', pignon' if pignon else ''}, {len(unites)} module(s), "
          f"complexe + couverture, débord {deb:.2f} m + épaisseur de mur)…")

    roofs_data = []
    roof_meta = []   # parallèle de roofs_data : (uid, level, est_couverture, versant)
    # liste pour pouvoir désactiver le favori en cours de route si CreateRoofs
    # le refuse (certaines versions de Tapir : additionalProperties)
    fav_toit_nom = favori_de(toit, FAVORIS_TOITURE, toit.get("type") or "")
    # v2.19 : composite de toiture appliqué à la création — JAMAIS de favori
    # de toit (écraserait la pente et le niveau)
    toit_comp_id = resoudre_composite(fav_toit_nom) if fav_toit_nom else None
    fav_toit = [None]

    def build_roofs(use_multi):
        """Construit roofs_data / roof_meta.
        use_multi (deux pentes, Tapir >= 2.0) : UN toit multi-plans par niveau,
        polygone = LIGNE DIRECTRICE, débords définis par arête via pivotEdges
        -> Archicad calcule le contour sans déplacer la ligne de référence.
        Sinon : versants monoplanes (v2.9), pivot sur la ligne directrice et
        polygone étendu du débord."""
        roofs_data.clear()
        roof_meta.clear()
        for unite, segments in segments_par_unite:
            uid = unite.get("id", "m0")
            dims_u = unite["dimensions"]
            L = float(dims_u["longueur"])
            l = float(dims_u["largeur"])
            H = float(dims_u["hauteur"])
            bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))

            def cote(face_key, segments=segments):
                """Élargissement de la couverture sur ce côté : débord compté
                depuis la face extérieure du mur = depassee + épaisseur du mur.
                Côté partagé entre deux modules accolés (v2.18) : la moitié de
                l'épaisseur du mur — les deux couvertures se rejoignent ainsi
                au milieu du mur partagé et passent AU-DESSUS (découpe SEO)."""
                seg = segments.get(face_key)
                if seg is None:
                    return deb + 0.255      # rive en charpente : débord + ép. mur
                if cle_count.get(cle_mur(face_key, seg), 0) > 1:
                    return float(seg["epaisseur"]) / 2.0
                return deb + float(seg["epaisseur"])

            dS, dN, dE, dO = cote("sud"), cote("nord"), cote("est"), cote("ouest")
            # coordonnées EXPORT (miroir Y appliqué par tr) : nord en y=by, sud en y=by+l
            emp_c = [tr((bx, by)), tr((bx + L, by)),
                     tr((bx + L, by + l)), tr((bx, by + l))]
            x0, x1 = bx - dO, bx + L + dE
            y0, y1 = by - dN, by + l + dS
            emp_v = [tr((x0, y0)), tr((x1, y0)), tr((x1, y1)), tr((x0, y1))]

            def add_roof(level, poly, with_angle, pivot=None, est_couv=False,
                         multi=None, versant=None, angle_rad=None):
                r = {"level": level, "polygonCoordinates": poly}
                if toit_comp_id:
                    r["structureType"] = "Composite"
                    r["compositeId"] = toit_comp_id
                if multi is not None:
                    r["levels"] = multi["levels"]
                    r["pivotEdges"] = multi["pivotEdges"]
                else:
                    if pivot is not None:
                        r["pivotLine"] = pivot
                    if with_angle:
                        # le miroir Y inverse le sens de rotation
                        r["angle"] = -(angle_rad if angle_rad is not None else angle)
                roofs_data.append(r)
                roof_meta.append((uid, level, est_couv, versant))

            if geo == "deuxpentes" and use_multi:
                # v2.12 : un toit multi-plans par niveau. Le polygone reste la
                # LIGNE DIRECTRICE ; les débords sont des débords d'arête
                # (pivotEdges) -> la ligne de référence ne bouge pas, donc la
                # hauteur au droit des murs est la même avec ou sans débord,
                # y compris aux jonctions entre modules (côté partagé = 0).
                # Niveau de la couverture = H + épaisseur du complexe de
                # toiture lue dans le configurateur (toit.epaisseur).
                # Arêtes du polygone pivot : 0=nord, 1=est, 2=sud, 3=ouest.
                for lvl, ovs, couv in ((H, (0.0, 0.0, 0.0, 0.0), False),
                                       (H + ep_toit, (dN, dE, dS, dO), True)):
                    pe = []
                    for i, ov in enumerate(ovs):
                        li = {"eavesOverhang": ov}
                        if pignon and i in (1, 3):   # arêtes est/ouest = pignon
                            li["angleType"] = "Gable"
                        pe.append({"levels": [li]})
                    add_roof(lvl, emp_c, False, est_couv=couv,
                             multi={"levels": [{"levelHeight": 0.0,
                                                "levelAngle": angle}],
                                    "pivotEdges": pe})
            else:
                # v2.9 : pivot des versants posé sur la LIGNE DIRECTRICE (bord du
                # rectangle de base), jamais sur le polygone étendu ; le débord
                # prolonge seulement le polygone, la pente continue au-delà du
                # mur -> hauteurs identiques au droit des murs, même aux
                # jonctions entre modules.
                piv_n = {"begCoordinate": tr((bx, by)),
                         "endCoordinate": tr((bx + L, by))}
                piv_s = {"begCoordinate": tr((bx + L, by + l)),
                         "endCoordinate": tr((bx, by + l))}
                if geo == "monopente":
                    for lvl, emp, couv in ((H, emp_c, False), (H + ep_toit, emp_v, True)):
                        add_roof(lvl, emp, True, pivot=piv_s, est_couv=couv)
                elif geo == "deuxpentes" and pignon:
                    # v2.18 : faîtage possiblement excentré (pentes asymétriques)
                    x_fait, _hf = faitage(l)
                    ydemi = tr((0.0, by + x_fait))["y"]
                    for lvl, emp, couv in ((H, emp_c, False), (H + ep_toit, emp_v, True)):
                        add_roof(lvl, [emp[0], emp[1],
                                       {"x": emp[1]["x"], "y": ydemi},
                                       {"x": emp[0]["x"], "y": ydemi}],
                                 True, pivot=piv_n, est_couv=couv, versant="nord",
                                 angle_rad=angle_nord)
                        add_roof(lvl, [{"x": emp[0]["x"], "y": ydemi},
                                       {"x": emp[1]["x"], "y": ydemi}, emp[2], emp[3]],
                                 True, pivot=piv_s, est_couv=couv, versant="sud",
                                 angle_rad=angle_sud)
                else:
                    for lvl, emp, couv in ((H, emp_c, False), (H + ep_toit, emp_v, True)):
                        add_roof(lvl, emp, geo == "deuxpentes", est_couv=couv)

    build_roofs(use_multi=(geo == "deuxpentes"))
    # Boucle de replis CreateRoofs (v2.18) : selon la version de Tapir, on
    # peut tomber successivement sur : favoriteName refusé, levels/pivotEdges
    # refusés (-> repli versants v2.9), 'angle' refusé. Chaque repli enlève
    # le champ concerné de TOUS les toits et réessaie ; on s'arrête dès que
    # la commande passe.
    roof_response = None
    for _tentative in range(5):
        try:
            roof_response = bridge.tapir("CreateRoofs",
                                         {"roofsData": roofs_data})
            break
        except Exception as exc_roof:
            msg = str(exc_roof)
            if fav_toit[0] and "favoriteName" in msg:
                fav_toit[0] = None
                for r in roofs_data:
                    r.pop("favoriteName", None)
                print("  ! favoriteName refusé par CreateRoofs : toitures "
                      "créées avec les réglages par défaut de l'outil Toiture.")
                continue
            if any("levels" in r or "pivotEdges" in r for r in roofs_data):
                # CreateRoofs refuse levels/pivotEdges (schéma Tapir 2.0.0)
                # -> repli versants monoplanes, pivot sur la ligne directrice.
                print("  ! Toits multi-plans avec pivotEdges refusés par ce "
                      "Tapir : repli sur versants monoplanes (pivot sur la "
                      "ligne directrice).")
                build_roofs(use_multi=False)
                continue
            if any("compositeId" in r or "structureType" in r for r in roofs_data) \
                    and ("compositeId" in msg or "structureType" in msg):
                for r in roofs_data:
                    r.pop("compositeId", None)
                    r.pop("structureType", None)
                print("  ! structureType/compositeId refusés par CreateRoofs : "
                      "toitures créées sans composite.")
                toit_comp_id = None
                continue
            if any("angle" in r for r in roofs_data) and "angle" in msg:
                for r in roofs_data:
                    r.pop("angle", None)
                print("  ! Champ 'angle' refusé : toitures créées avec la "
                      "pente par défaut de l'outil.")
                continue
            if fav_toit[0] and any("favoriteName" in r for r in roofs_data):
                # repli versants retombé sur favoriteName (message générique)
                fav_toit[0] = None
                for r in roofs_data:
                    r.pop("favoriteName", None)
                print("  ! favoriteName refusé par CreateRoofs (repli) : "
                      "toitures créées sans favori.")
                continue
            raise
    errs = [e.get("error") for e in roof_response.get("elements", [])
            if e.get("error")]
    if errs:
        print(f"  ! Toiture(s) non créée(s) : {errs}")
    else:
        print(f"  Toitures créées ({len(roofs_data)} plans : complexe + couverture par module).")
    # --- 3b. Découpe des murs par la couverture (opération solide SEO) -------
    # v2.18 : TOUS les murs sont surhaussés de SURHAUSSE_MURS (section 1) et
    # découpés par la couverture de chaque module auquel ils appartiennent
    # (un mur partagé entre deux modules accolés est rogné par les deux
    # couvertures). Mur = cible (targetId), toit de couverture = opérateur
    # (operatorId), opération "SubtractionUpwards" (soustraction avec extrusion
    # vers le haut) : le toit extrudé vers le haut rogne le mur au-dessus de sa
    # face inférieure -> on garde la partie SOUS la toiture (triangle de
    # pignon avec débord, rives propres).
    roof_elements = roof_response.get("elements", [])
    couv_par_uid = {}          # uid -> [elementId des toits de COUVERTURE]
    couv_par_uid_versant = {}  # uid -> {versant (ou None en multi-plans): elementId}
    if len(roof_elements) == len(roofs_data):
        for (uid, level, couv, vers), rel in zip(roof_meta, roof_elements):
            if couv and not rel.get("error") and rel.get("elementId") is not None:
                couv_par_uid.setdefault(uid, []).append(rel["elementId"])
                couv_par_uid_versant.setdefault(uid, {})[vers] = rel["elementId"]
    if wall_ids and couv_par_uid:
        links = []
        for cle, wid in wall_ids.items():
            for uid in unites_par_cle.get(cle, ()):
                for roof_id in couv_par_uid.get(uid, ()):
                    links.append({
                        "targetId": wid,
                        "operatorId": roof_id,
                        "operation": SEO_OPERATION,
                    })
        if links:
            try:
                bridge.tapir("CreateSolidElementLinks", {"solidLinks": links})
                print(f"  Murs découpés par la couverture en opération solide "
                      f"({len(links)} lien(s) SEO {SEO_OPERATION}, mur=cible / toit=opérateur).")
            except Exception as exc:
                print(f"  ! CreateSolidElementLinks indisponible ({exc}) : murs "
                      f"laissés à hauteur +{SURHAUSSE_MURS:.2f} m, à découper manuellement.")
    else:
        print("  ! IDs de murs ou de toitures de couverture manquants : "
              "découpe SEO ignorée.")

    # --- 3c. Fenêtres de toit (CreateSkylights sur la couverture) ------------
    # Chaque pente de l'export (toiture.pents[]) a un n° de module (1-based) et
    # un versant (nord/sud) ; ses fenêtres sont posées sur la couverture du
    # module. Position mesurée le long du bas de pente depuis le coin ouest ;
    # l'ancre est placée au centre de la fenêtre en projection plan (la
    # profondeur projetée tient compte de la pente : hauteur * cos(pente)).
    pents = toit.get("pents") or []
    if pents and couv_par_uid_versant:
        skylights_data = []
        skylights_favs = []   # favori d'origine de chaque skylight (le repli peut vider item)
        for pent in pents:
            idx = pent.get("module")
            uid = None
            if isinstance(idx, int) and 1 <= idx <= len(unites):
                uid = unites[idx - 1].get("id", "m0")
            if pent.get("instId"):
                uid = pent["instId"]
            unite = next((u for u in unites if u.get("id", "m0") == uid), None)
            d_couv = couv_par_uid_versant.get(uid, {})
            if unite is None or not d_couv:
                continue
            versant = str(pent.get("versant") or "").lower()
            owner = d_couv.get(versant) or d_couv.get(None) \
                or next(iter(d_couv.values()))
            dims_u = unite["dimensions"]
            l_u = float(dims_u["largeur"])
            bx = float(unite.get("x", 0.0))
            by = float(unite.get("y", 0.0))
            for fen in pent.get("fenetres") or []:
                pr = float(fen.get("position", 0.0))
                w = float(fen.get("largeur", 0.0))
                h = float(fen.get("hauteur", 0.0))
                proj = h * math.cos(math.radians(pente)) / 2.0
                if versant == "sud":
                    y_exp = by + l_u - proj    # eave sud, vers le faîtage (-Y export)
                else:
                    y_exp = by + proj          # eave nord, vers le faîtage (+Y export)
                item = {"ownerId": owner,
                        "anchorPosition": tr((bx + pr + w / 2.0, y_exp)),
                        "width": w, "height": h}
                fv = str(fen.get("favori") or "").strip()
                if fv:
                    item["favoriteName"] = fv
                skylights_data.append(item)
                skylights_favs.append(fv)
        if skylights_data:
            try:
                resp = bridge.tapir_cree("CreateSkylights", {"skylightsData": skylights_data})
                print(f"  Fenêtres de toit placées ({len(skylights_data)} skylight(s) "
                      f"sur la couverture).")
                for fv, e in zip(skylights_favs, resp.get("elements", [])):
                    if fv and e.get("elementId") is not None:
                        fav_a_appliquer.append((e["elementId"], fv, None))
            except Exception as exc:
                print(f"  ! CreateSkylights indisponible ({exc}) : fenêtres "
                      f"de toit non placées.")

    # --- 4. Ouvertures (de chaque instance, sur le mur canonique) ----------
    # v2.18 : le type d'outil (fenêtre vs porte) est résolu via le favori quand
    # il est renseigné (GetFavoritesByType) — l'export peut mettre type="porte"
    # pour une porte-fenêtre dont le favori est un favori FENÊTRE. Repli sur le
    # champ type de l'export sinon.
    fav_noms_fenetre, fav_noms_porte = set(), set()
    try:
        for etype, dest in (("Window", fav_noms_fenetre), ("Door", fav_noms_porte)):
            rep = bridge.tapir("GetFavoritesByType", {"elementType": etype})
            for f in rep.get("favorites", []):
                dest.add(f.get("name") if isinstance(f, dict) else f)
    except Exception:
        pass
    n_ok, n_err = 0, 0
    for unite, segments in segments_par_unite:
        uid = unite.get("id", "m0")
        for face_key in ("sud", "est", "nord", "ouest"):
            seg = segments.get(face_key)
            cle = alias.get((uid, face_key))
            wall_id = wall_ids.get(cle) if cle else None
            if not seg or wall_id is None:
                continue
            cseg = canon[cle]
            for ouverture in seg["ouvertures"]:
                favori_ouv = favori_de(ouverture, FAVORIS_OUVERTURES, ouverture["type"])
                # Centre de l'ouverture en coordonnées absolues, puis
                # centerOffset = distance SUR L'AXE du mur depuis le
                # begCoordinate du mur créé (projection, pas distance euclidienne :
                # les directrices de deux modules accolés sont à une épaisseur
                # d'écart, le mur physique est le même).
                cx, cy = ouverture_centre(unite, face_key, ouverture)
                # v2.22 : axes telles qu'envoyées à CreateWalls (beg<->end
                # échangés) : le centerOffset est mesuré depuis le begCoordinate
                # du mur créé = l'ancien END du segment.
                beg_e, end_e = axes_envoi(cseg)
                if abs(beg_e[0] - end_e[0]) < 1e-9:         # mur vertical
                    centre = abs(cy - beg_e[1])
                else:                                       # mur horizontal
                    centre = abs(cx - beg_e[0])
                item = {
                    "ownerWallId": wall_id,
                    "centerOffset": centre,
                    "width": ouverture["largeur"],
                    "height": ouverture["hauteur"],
                    # v2.24 : refSide=true -> côté soleil (extérieur) de
                    # l'ouverture sur la face EXTÉRIEURE du mur (murs envoyés
                    # beg<->end échangés : à droite de beg->end = intérieur,
                    # donc refSide=false mettrait le soleil du mauvais côté).
                    "refSide": True,
                }
                if favori_ouv:
                    item["favoriteName"] = favori_ouv
                # Routage fenêtre/porte : le favori prime sur le champ type.
                if favori_ouv in fav_noms_fenetre:
                    est_porte = False
                elif favori_ouv in fav_noms_porte:
                    est_porte = True
                else:
                    est_porte = ouverture["type"] == "porte"
                command = "CreateDoors" if est_porte else "CreateWindows"
                key = "doorsData" if est_porte else "windowsData"
                try:
                    resp = bridge.tapir_cree(command, {key: [item]})
                    el = (resp.get("elements") or [{}])[0]
                    if el.get("error"):
                        raise RuntimeError(str(el["error"]))
                    n_ok += 1
                    if favori_ouv and el.get("elementId") is not None:
                        fav_a_appliquer.append((el["elementId"], favori_ouv, None))
                except Exception as exc:
                    n_err += 1
                    print(f"  ! Ouverture {ouverture.get('id', '?')} non placée "
                          f"sur le mur {face_key} du module {uid} : {exc}")

    # --- 5. Favoris (repli ApplyFavoritesToElements) + zoom ------------------
    # v2.19 : les favoris ne concernent plus que les OUVRANTS, la charpente
    # (poteaux/poutres) et les fenêtres de toit — jamais murs/plancher/toitures
    # (un favori écraserait l'orientation du mur et la pente/niveau du toit).
    # Ils sont envoyés en favoriteName à la création, mais Tapir 2.0.0 peut
    # les refuser selon la commande -> on les réapplique ici sur les éléments
    # créés (commande disponible depuis Tapir 1.8).
    if fav_a_appliquer:
        groupes = {}
        for eid, fav, kf in fav_a_appliquer:
            groupes.setdefault(tuple(kf) if kf else (), []).append(
                {"elementId": eid, "favorite": fav})
        for kf, items in groupes.items():
            params = {"favoritesToApply": items,
                      "applySettings": True, "applyClassifications": True,
                      "applyCategories": True, "applyProperties": False}
            if kf:
                params["keepFields"] = list(kf)
            try:
                rep = bridge.tapir("ApplyFavoritesToElements", params)
                res = rep.get("executionResults", [])
                nko = sum(1 for r in res if isinstance(r, dict) and not r.get("success"))
                msg = f"  Favoris appliqués ({len(items) - nko}/{len(items)} OK)."
                if nko:
                    msg += f" {nko} refusé(s) — favori absent du gabarit Archicad ?"
                print(msg)
            except Exception as exc:
                print(f"  ! ApplyFavoritesToElements indisponible ({exc}) : "
                      f"favoris non appliqués.")
    if wall_ids:
        try:
            bridge.tapir("FitInWindow",
                         {"elements": [{"elementId": wid}
                                       for wid in wall_ids.values()]})
        except Exception:
            pass

    print("-" * 60)
    print(f"Module « {name} » importé :")
    print(f"  - {len(walls_data)} murs sur {len(unites)} module(s), "
          f"{len(slabs_data)} plancher(s), {len(roofs_data)} élément(s) de toiture")
    print(f"  - {n_ok} ouverture(s) placée(s), {n_err} échec(s)")
    print("Terminé. Vérifiez le résultat dans la fenêtre 3D.")


def main():
    parser = argparse.ArgumentParser(
        description="Importe un module Baracca (JSON du configurateur web) "
                    "dans le projet Archicad ouvert.")
    print("BARACCA-IMPORT v2.24 — Archicad 30 / Tapir >= 2.0 uniquement ; "
          "enveloppe déballée, toutes les instances, murs partagés dédoublonnés "
          "(arrondi cm), miroir Y (Nord correct), murs beg<->end échangés + "
          "Inside (corps vers l'extérieur, face extérieure sur la face opposée "
          "à la ligne), ouvertures refSide=true (soleil côté extérieur), "
          "composites via Référence Archicad "
          "listés par GetAttributesByType et résolus par nom insensible à la "
          "casse/accents/dossier BARACCA, compositeId envoyé en objet {guid} "
          "(murs/plancher/toitures, jamais de favori sur ces éléments), "
          "pentes asymétriques (pente/pente2), "
          "favoris pour ouvrants/charpente/skylights (ApplyFavoritesToElements), "
          "charpentes en poteaux+sablière, mur est/ouest partagé = pignon, "
          "débord couverture sur mur partagé = ép/2, fenêtres de toit "
          "(CreateSkylights), murs +0,40 m découpés par la couverture en opération "
          "solide (SEO SubtractionUpwards), plancher par module, toitures "
          "superposées complexe + couverture (versants avec pivot sur la ligne "
          "directrice)")
    parser.add_argument("fichier", nargs="?", help="Chemin du JSON du module")
    parser.add_argument("--pick", action="store_true",
                        help="Choisir l'origine du module en cliquant")
    parser.add_argument("--probe", action="store_true",
                        help="Valider les commandes Tapir avec des éléments "
                             "de test (supprimables via Ctrl+Z)")
    args = parser.parse_args()

    if args.probe:
        probe()
        return
    if not args.fichier:
        parser.error("Fichier JSON requis (ou --probe)")

    with open(args.fichier, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Fichier téléchargé depuis le back-office = enveloppe de soumission
    # {soumis_le, utilisateur, configuration: {...}} : on déballe.
    if "module" not in data and isinstance(data.get("configuration"), dict):
        data = data["configuration"]
        print("Enveloppe de soumission détectée : lecture de « configuration »…")
    if "module" not in data:
        sys.exit("JSON invalide : clé 'module' absente.")
    import_module(data, pick_origin=args.pick)


if __name__ == "__main__":
    main()
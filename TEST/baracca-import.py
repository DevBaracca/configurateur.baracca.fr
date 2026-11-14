#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BARACCA-IMPORT v2.10 — vérifiez la présence de cette ligne : elle prouve
# que vous exécutez bien la dernière version du script.
# v2.10 : toitures en multi-plans par niveau avec débords d'arête natifs
# (pivotEdges, Tapir >= 2.0) : le polygone reste la LIGNE DIRECTRICE et
# Archicad calcule le contour -> hauteur identique au droit des murs, même
# aux jonctions entre modules ; niveau couverture = H + épaisseur du complexe
# (toit.epaisseur du configurateur). Repli v2.9 (versants monoplanes, angle
# = -angle car le miroir Y inverse le sens de rotation, pivot sur la ligne
# directrice, polygone étendu) si CreateRoofs refuse levels/pivotEdges.
# Pignons : murs est/ouest libres montés au faîtage, taillés par la couverture
# (TrimElements, section 3b).
# v2.9 : ligne de référence = face INTÉRIEURE, compatible Tapir 1.7.2 :
# CreateWalls y refuse le champ "flipped", donc on inverse le SENS de tracé
# de chaque mur (beg<->end) + referenceLineLocation "Inside" — avec la
# convention Archicad (face extérieure d'un mur non flippé = DROITE du sens
# beg->end), ce couple pose la ligne sur la face intérieure tout en gardant
# le corps vers l'extérieur.
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

Méthode : les murs sont créés à partir de FAVORIS du gabarit Baracca
(un favori de l'outil Mur par type de mur) : le script n'envoie que la
géométrie, Archicad applique composite, calque et attributs du favori.
"""

import argparse
import json
import math
import sys

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

LAYER = "BARACCA_Modules"

# Orientation des murs (v2.9). Convention configurateur : la ligne directrice
# tracée = la face INTÉRIEURE du mur, le corps s'étend vers l'EXTÉRIEUR.
# Dans Archicad, pour un mur non flippé, la face EXTÉRIEURE est à DROITE du
# sens beg->end. On envoie referenceLineLocation="Inside" (la ligne est posée
# sur la face intérieure -> le corps part à droite du sens de tracé) et les
# sens de wall_segments sont inversés (beg<->end) pour que ce "droite" soit
# l'EXTÉRIEUR du bâtiment. Pas de champ "flipped" : refusé par le schéma
# CreateWalls de Tapir 1.7.2 (additionalProperties).
WALL_REFERENCE_LINE_LOCATION = "Inside"

# Découpe des pignons par la couverture :
# - TRIM_TYPE = None (défaut) : TrimElements SANS trimmingElement, le toit de
#   couverture dans "elements" -> ACAPI_Element_Trim_Elements, trim standard
#   "tailler sous toiture" qui élimine ce qui est HORS du toit, donc garde la
#   partie du mur SOUS les pans -> triangle de pignon.
# - TRIM_TYPE = "KeepInside"/"KeepOutside" : forme manuelle avec
#   trimmingElement + trimType (à n'utiliser que si le trim auto ne convient pas).
TRIM_TYPE = None

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
            print(f"Tapir détecté : v{version.get('version', '?')}")
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
    sud en y=by+l. Sens de tracé (v2.9, inversés par rapport à v2.7) choisis
    pour qu'avec referenceLineLocation "Inside" — la ligne posée sur la face
    intérieure, donc le corps à DROITE du sens beg->end dans Archicad, la
    face extérieure non flippée étant à droite — le corps soit vers l'EXTÉRIEUR.

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
        beg, end = axes[face_key]
        segments[face_key] = {
            "face": face_key,
            "beg": beg, "end": end,
            "hauteur": H,
            "epaisseur": face.get("epaisseur", 0.14),
            "type": face.get("type", ""),
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
    # du mur va vers l'EXTÉRIEUR) ; les sens de tracé de wall_segments sont
    # inversés en conséquence. AUCUN décalage de demi-épaisseur à appliquer.
    toit = module["toiture"]
    geo = toiture_geo(toit)   # monopente / deuxpentes / quatrepentes / terrasse
    pignon = bool(toit.get("pignon"))
    pente = float(toit.get("pente") or 0)
    segments_par_unite = [(u, wall_segments(u)) for u in unites]

    # Un mur partagé entre deux modules accolés est la même ligne tracée deux
    # fois (sens opposés) : on ne la crée qu'une fois, en fusionnant les
    # ouvertures des deux côtés.
    canon = {}   # clé de ligne -> segment canonique
    alias = {}   # (uid, face) -> clé de ligne canonique
    for unite, segments in segments_par_unite:
        uid = unite.get("id", "m0")
        for face_key in ("sud", "est", "nord", "ouest"):
            seg = segments.get(face_key)
            if not seg:
                continue
            cle = cle_mur(face_key, seg)
            alias[(uid, face_key)] = cle
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

    # Pignons (deux pentes à pignon) PAR MODULE : chaque côté est/ouest
    # LIBRE d'un module (mur non partagé, ou rive en charpente) monte jusqu'au
    # faîtage de SA toiture ; la couverture le taille en triangle (découpe
    # TrimElements en section 3b).
    pignon_cles = {}   # uid -> [clés de murs pignons de ce module]
    if geo == "deuxpentes" and pignon:
        for unite, segments in segments_par_unite:
            uid = unite.get("id", "m0")
            dims_u = unite["dimensions"]
            L_u = float(dims_u["longueur"])
            l_u = float(dims_u["largeur"])
            H_u = float(dims_u["hauteur"])
            hf_u = math.tan(math.radians(pente)) * l_u / 2.0
            bx = float(unite.get("x", 0.0))
            by = float(unite.get("y", 0.0))
            for face_key, x in (("ouest", bx), ("est", bx + L_u)):
                seg = segments.get(face_key)
                if seg is not None:
                    cle = alias[(uid, face_key)]
                    if cle_count.get(cle, 0) > 1:
                        continue          # mur partagé : pas de pignon
                    canon[cle]["hauteur"] = H_u + hf_u
                    canon[cle]["pignon"] = True
                    pignon_cles.setdefault(uid, []).append(cle)
                else:
                    # rive en charpente : on crée le mur de pignon à fond
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

    walls_data = []
    types_sans_favori = set()

    print(f"Création de {len(canon)} mur(s) sur {len(unites)} module(s)…")
    # Un mur par appel CreateWalls : l'elementId retourné est ainsi reliably
    # associé à sa ligne (pas de décalage d'index si un mur échoue).
    wall_ids = {}
    for cle, seg in canon.items():
        item = {
            "begCoordinate": tr(seg["beg"]),
            "endCoordinate": tr(seg["end"]),
            "height": seg["hauteur"],
            "thickness": seg["epaisseur"],
            # Ligne de référence = face INTÉRIEURE (convention configurateur).
            # v2.9 : "Inside" seul (Tapir 1.7.2 refuse "flipped" dans
            # CreateWalls) + sens de tracé inversés dans wall_segments : la
            # face extérieure non flippée étant à droite du sens beg->end,
            # le corps part bien vers l'extérieur et la ligne est posée sur
            # la face intérieure.
            "referenceLineLocation": WALL_REFERENCE_LINE_LOCATION,
        }
        favori = FAVORIS_MURS.get(seg["type"])
        if favori:
            item["favoriteName"] = favori
        elif seg["type"] not in types_sans_favori:
            types_sans_favori.add(seg["type"])
            print(f"  ! Pas de favori pour « {seg['type']} » : réglages par "
                  f"défaut de l'outil Mur (renseignez FAVORIS_MURS).")
        walls_data.append((cle, item))
        try:
            resp = bridge.tapir("CreateWalls", {"wallsData": [item]})
        except Exception:
            # Tapir ancien sans referenceLineLocation : repli sans le champ
            # (la ligne de référence retombe sur le réglage par défaut).
            item.pop("referenceLineLocation", None)
            print("  ! Champ referenceLineLocation refusé : mur créé "
                  "avec les réglages par défaut.")
            resp = bridge.tapir("CreateWalls", {"wallsData": [item]})
        el = (resp.get("elements") or [{}])[0]
        if el.get("elementId") is not None:
            wall_ids[cle] = el["elementId"]
        elif el.get("error"):
            print(f"  ! Mur {seg['face']} non créé : {el['error']}")

    # --- 2. Planchers (UN par module, avec débord) --------------------------
    nom_plancher = plancher_nom(module)
    favori_pl = FAVORIS_PLANCHER.get(nom_plancher)
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
        if favori_pl:
            item["favoriteName"] = favori_pl
        slabs_data.append(item)
    print(f"Création de {len(slabs_data)} plancher(s) ({nom_plancher})…")
    slab_response = bridge.tapir("CreateSlabs", {"slabsData": slabs_data})
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
    roof_meta = []   # parallèle de roofs_data : (uid, level, est_couverture)

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
                Côté partagé entre deux modules accolés : 0 (pas de débord)."""
                seg = segments.get(face_key)
                if seg is None:
                    return deb + 0.255      # rive en charpente : débord + ép. mur
                if cle_count.get(cle_mur(face_key, seg), 0) > 1:
                    return 0.0
                return deb + float(seg["epaisseur"])

            dS, dN, dE, dO = cote("sud"), cote("nord"), cote("est"), cote("ouest")
            # coordonnées EXPORT (miroir Y appliqué par tr) : nord en y=by, sud en y=by+l
            emp_c = [tr((bx, by)), tr((bx + L, by)),
                     tr((bx + L, by + l)), tr((bx, by + l))]
            x0, x1 = bx - dO, bx + L + dE
            y0, y1 = by - dN, by + l + dS
            emp_v = [tr((x0, y0)), tr((x1, y0)), tr((x1, y1)), tr((x0, y1))]

            def add_roof(level, poly, with_angle, pivot=None, est_couv=False,
                         multi=None):
                r = {"level": level, "polygonCoordinates": poly}
                if multi is not None:
                    r["levels"] = multi["levels"]
                    r["pivotEdges"] = multi["pivotEdges"]
                else:
                    if pivot is not None:
                        r["pivotLine"] = pivot
                    if with_angle:
                        # v2.7/v2.10 : le miroir Y inverse le sens de rotation
                        r["angle"] = -angle
                roofs_data.append(r)
                roof_meta.append((uid, level, est_couv))

            if geo == "deuxpentes" and use_multi:
                # v2.10 : un toit multi-plans par niveau. Le polygone reste la
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
                    ydemi = tr((0.0, by + l / 2.0))["y"]
                    for lvl, emp, couv in ((H, emp_c, False), (H + ep_toit, emp_v, True)):
                        add_roof(lvl, [emp[0], emp[1],
                                       {"x": emp[1]["x"], "y": ydemi},
                                       {"x": emp[0]["x"], "y": ydemi}],
                                 True, pivot=piv_n, est_couv=couv)
                        add_roof(lvl, [{"x": emp[0]["x"], "y": ydemi},
                                       {"x": emp[1]["x"], "y": ydemi}, emp[2], emp[3]],
                                 True, pivot=piv_s, est_couv=couv)
                else:
                    for lvl, emp, couv in ((H, emp_c, False), (H + ep_toit, emp_v, True)):
                        add_roof(lvl, emp, geo == "deuxpentes", est_couv=couv)

    build_roofs(use_multi=(geo == "deuxpentes"))
    try:
        roof_response = bridge.tapir("CreateRoofs",
                                     {"roofsData": roofs_data})
    except Exception:
        if any("levels" in r or "pivotEdges" in r for r in roofs_data):
            # Tapir < 2.0 : CreateRoofs refuse levels/pivotEdges -> repli v2.9
            # (versants monoplanes, pivot sur la ligne directrice).
            print("  ! Toits multi-plans avec pivotEdges refusés par ce Tapir : "
                  "repli sur versants monoplanes (pivot sur la ligne directrice).")
            build_roofs(use_multi=False)
            roof_response = bridge.tapir("CreateRoofs",
                                         {"roofsData": roofs_data})
        elif any("angle" in r for r in roofs_data):
            # Repli : cette version de Tapir n'accepte pas 'angle' en
            # multi-plans -> pente par défaut de l'outil Toiture.
            for r in roofs_data:
                r.pop("angle", None)
            print("  ! Champ 'angle' refusé en multi-plans : toitures "
                  "créées avec la pente par défaut de l'outil.")
            roof_response = bridge.tapir("CreateRoofs",
                                         {"roofsData": roofs_data})
        else:
            raise
    errs = [e.get("error") for e in roof_response.get("elements", [])
            if e.get("error")]
    if errs:
        print(f"  ! Toiture(s) non créée(s) : {errs}")
    else:
        print(f"  Toitures créées ({len(roofs_data)} plans : complexe + couverture par module).")

    # --- 3b. Découpe des pignons par la couverture ---------------------------
    # Trim par défaut (TRIM_TYPE = None) : le toit de couverture est mis dans
    # "elements" avec les murs pignons -> ACAPI_Element_Trim_Elements, qui
    # élimine la partie HORS du toit : on garde le mur SOUS les pans ->
    # triangle de pignon avec débord.
    roof_elements = roof_response.get("elements", [])
    if pignon_cles and len(roof_elements) == len(roofs_data):
        n_trim = 0
        try:
            for (uid, level, couv), rel in zip(roof_meta, roof_elements):
                if not couv or rel.get("error") or rel.get("elementId") is None:
                    continue
                cles = [c for c in pignon_cles.get(uid, []) if c in wall_ids]
                if not cles:
                    continue
                if TRIM_TYPE:
                    bridge.tapir("TrimElements", {
                        "elements": [{"elementId": wall_ids[c]} for c in cles],
                        "trimmingElement": {"guid": guid_of(rel["elementId"])},
                        "trimType": TRIM_TYPE,
                    })
                else:
                    bridge.tapir("TrimElements", {
                        "elements": ([{"elementId": wall_ids[c]} for c in cles]
                                     + [{"elementId": rel["elementId"]}]),
                    })
                n_trim += 1
            if n_trim:
                print(f"  Pignons taillés sous la couverture ({n_trim} appel(s) TrimElements).")
        except Exception as exc:
            print(f"  ! TrimElements indisponible ({exc}) : pignons laissés "
                  f"à hauteur de faîtage, à tailler manuellement sous la toiture.")
    elif pignon_cles:
        print("  ! Toitures sans elementId retourné : découpe des pignons ignorée.")

    # --- 4. Ouvertures (de chaque instance, sur le mur canonique) ----------
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
                favori_ouv = FAVORIS_OUVERTURES.get(ouverture["type"])
                # Centre de l'ouverture en coordonnées absolues, puis
                # centerOffset = distance SUR L'AXE du mur depuis le
                # begCoordinate du mur créé (projection, pas distance euclidienne :
                # les directrices de deux modules accolés sont à une épaisseur
                # d'écart, le mur physique est le même).
                cx, cy = ouverture_centre(unite, face_key, ouverture)
                beg = cseg["beg"]
                if abs(beg[0] - cseg["end"][0]) < 1e-9:   # mur vertical
                    centre = abs(cy - beg[1])
                else:                                      # mur horizontal
                    centre = abs(cx - beg[0])
                item = {
                    "ownerWallId": wall_id,
                    "centerOffset": centre,
                    "width": ouverture["largeur"],
                    "height": ouverture["hauteur"],
                }
                if favori_ouv:
                    item["favoriteName"] = favori_ouv
                command = ("CreateDoors" if ouverture["type"] == "porte"
                           else "CreateWindows")
                key = "doorsData" if ouverture["type"] == "porte" \
                    else "windowsData"
                try:
                    bridge.tapir(command, {key: [item]})
                    n_ok += 1
                except Exception:
                    n_err += 1
                    print(f"  ! Ouverture {ouverture.get('id', '?')} non placée "
                          f"sur le mur {face_key} du module {uid}")

    # --- 5. Zoom -------------------------------------------------------------
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
    print("BARACCA-IMPORT v2.10 — enveloppe déballée, toutes les instances, "
          "murs partagés dédoublonnés (arrondi cm), miroir Y (Nord correct), "
          "pignons par module taillés par la couverture (TrimElements), "
          "plancher par module, toitures superposées complexe + couverture "
          "(débords par arête pivotEdges si Tapir >= 2.0, sinon versants avec "
          "pivot sur la ligne directrice) ; ligne de référence sur la face "
          "intérieure (Inside, sens inversés)")
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
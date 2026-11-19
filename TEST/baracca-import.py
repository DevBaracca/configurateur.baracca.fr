#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BARACCA-IMPORT v2.59 — vérifiez la présence de cette ligne : elle prouve
# que vous exécutez bien la dernière version du script.
# v2.59 : avec allège, favori (ouvrant ET BAIELIBRE) envoyé À LA CRÉATION avec
#   sillHeight (champs explicites > favori) et PLUS réappliqué après coup.
#   Probes 5d/5e : favori+sillHeight à la création, favori sans keepFields.
# v2.58 : la liste des 177 composites n'est plus dumpée dans la console (count only).
# v2.57 : log « allège ... envoyée (sillHeight) » par ouverture concernée.
#   Probe v2.56 : sillHeight EFFECTIF (relecture 0.9) et CONSERVÉ après favori
#   + keepFields -> si l'allège reste à 0, le JSON exporté ne contenait pas
#   « allege » (bundle client pas déployé) ou script < v2.54.
# v2.56 : probe 5c — sillHeight effectif ? (relecture details complète) et favori
#   réappliqué avec keepFields conserve-t-il l'allège ?
# v2.55 : « positionHauteur » des fenêtres de toit (distance au bas de pente le
#   long du rampant, exportée par le configurateur) -> ancre décalée en plan de
#   ph*cos(pente) vers le faîtage ; les trous suivent via l'anchorLevel relu.
# v2.54 : CHAMP_ALLEGE = "sillHeight" (probe v2.53 : anchorLevel/anchorPosition
#   refusés, sillHeight accepté). Ouvertures AVEC allège : favori appliqué APRÈS
#   création via ApplyFavoritesToElements + keepFields (width/height/centerOffset/
#   sillHeight/refSide) pour ne pas réinitialiser l'allège ; idem baies libres.
# v2.53 : champ « allège » (hauteur d'implantation) des ouvertures exporté par
#   le configurateur et envoyé à CreateWindows/CreateDoors (CHAMP_ALLEGE,
#   repli gracieux sur l'appui du favori si refusé) + mêmes champs aux baies
#   libres des revêtements ; probe 5b pour trouver le champ accepté/effectif.
# v2.52 : dy = sin(p)cos(p)(al_fen - al_trou) SANS dénominateur. Le résidu v2.51
#   (+0,8 / -2,72 cm = 0,2 x B) prouve pos_Y(trou) = anchor_y + B avec
#   B = sin(p)cos(p)(al_trou@fen - al_fen) : pente 1, pas de facteur 1+sin^2.
#   Ex. pente 30 : dy couv -4,0 cm (y=5,0351), dy inf +13,6 cm (y=5,2111).
# v2.51 : dy = sin(p)cos(p)(al_fen - al_trou)/(1+s*sin^2) -> facteur 1+sin^2 en trop.
# v2.50 : alignait les anchorLevel -> faux, car déplacer y déplace le trou en plan.
# v2.49 : trous au même (x, y) que la fenêtre (alignement en plan, plus de
# décalage le long de la pente), sans favori LUCARNEVIDE (fixMode=Horizontal).
# v2.48 : trous créés SANS favori LUCARNEVIDE (qui force fixMode=Horizontal et
# décale les trous) + ancre décalée le long de la pente ; favori non réappliqué
# ensuite pour préserver la géométrie.
# v2.47 : trous de lucarnes alignés EN PLAN : anchorLevel non réglable sur
# Tapir 2.0.0 (CreateSkylights refuse le champ, SetDetailsOfElements refuse tous
# les payloads) -> on décale l'ancre du trou le long de la pente de
# dy = (E - niveau_couche)/tan(pente), avec E = niveau_complexe + anchorLevel_fenêtre.
# v2.46 : anchorLevel de la FENÊTRE fixé à 0,60 m par défaut (SetDetailsOfElements,
# sinon valeur lue du favori) ; les trous en découlent.
# v2.45 : tout se règle par anchorLevel (ancre x,y = celle de la fenêtre) :
# rotation de la pente Y' = X·sinθ + e·cosθ, X commun ->
# anchorLevel_couche = anchorLevel_fenêtre + (e_couche - e_complexe)·cos(pente).
# v2.44 : ligne de référence (anchorLevel) des trous réglée par SetDetailsOfElements
# (plusieurs formes de payload testées + vérif par relecture) :
# anchorLevel_cible = anchorLevel_fenêtre - delta_couche. Repli : delete+recréation
# avec z corrigé.
# v2.43 : réapplication des favoris de skylights en fin d'import AVEC
# keepFields = width, height, anchorLevel, anchorPosition — sinon le favori
# remet sa propre ligne de référence et les fenêtres de toit se décalent à la
# toute fin du script (constaté : placement OK pendant l'import, saut à la fin).
# v2.42 : diag compact — une ligne par skylight lu (id, owner, anchor x/y,
# anchorLevel, fixMode) + niveaux des toitures, pour lire la position réelle
# des trous après correction.
# v2.41 : la ligne de référence (anchorLevel) des TROUS est modifiée APRÈS
# création via SetDetailsOfElements (CreateSkylights la refuse à la création) :
# anchorLevel_cible = anchorLevel_fenêtre - delta_couche. Repli : delete+recréation
# avec z corrigé (v2.40).
# v2.40 : CreateSkylights refuse anchorLevel (additionalProperties) MAIS le z de
# anchorPosition alimente anchorLevel (anchorLevel = favori + z - niveau toiture).
# Trous en deux passes : passe 1 z = H+delta -> lecture anchorLevel réel ->
# suppression (DeleteElements) -> passe 2 avec z_final = H + anchorLevel_fenêtre
# - anchorLevel_trou = même cote absolue que la fenêtre.
# v2.39 : skylights en DEUX PHASES — l'ancre est 2D (x,y), la hauteur passe par
# anchorLevel (fixMode "Vertical", relatif au niveau de la toiture propriétaire ;
# le z d'anchorPosition est ignoré). Phase 1 : fenêtres seules + lecture réelle de
# leur anchorLevel (GetDetailsOfElements). Phase 2 : trous au même (x,y) que la
# fenêtre, anchorLevel = anchorLevel_fenêtre - delta_niveau_couche.
# v2.38 : DIAGNOSTIC — GetDetailsOfElements appelé avec {"elements":
# [{"elementId": ...}]} (sinon « elementId is missing ») : affiche ancre envoyée
# + position réelle lue pour chaque skylight (calibration ancre Tapir ->
# placement Archicad ; la ligne de référence affichée vient du favori, pas de
# l'ancre).
# v2.37 : DIAGNOSTIC — après CreateSkylights, relit GetDetailsOfElements des
# skylights créés et affiche ancre envoyée + position lue (calibration ancre
# Tapir -> placement réel, la ligne de référence venant du favori).
# v2.36 : trous de lucarnes alignés en 3D avec la fenêtre par décalage EN PLAN
# le long de la pente : dy = (lvl_cplx - lvl_role)/tan(pente) (vers le faîtage
# si la couche est au-dessus du complexe), z = niveau de la couche — la ligne
# de référence affichée venant du favori, le z envoyé est sans effet.
# v2.35 : trous de lucarnes : X (position le long de la pente) COMMUN avec la
# fenêtre -> même (x, y) ; seule la ligne de référence z varie selon l'épaisseur
# de la couche : dz_couv = -(ep_cplx+ep_couv)·cos(pente), dz_inf = -(ep_cplx-ep_inf)·cos(pente).
# v2.34 : trous de lucarnes calés LE LONG DE LA PENTE (dy = ±(ep_cplx+ep_rev)·
# sin(pente)·cos(pente), dz = ±(ep_cplx+ep_rev)·sin²(pente) ; sous-face vers le
# faîtage, couverture vers la rive ; x = axe de la fenêtre) ; anti-doublon des
# skylights renforcé : favoris skylights validés item par item contre le gabarit
# (GetFavoritesByType Skylight) et repli sans favori ITEM PAR ITEM (plus de
# recréation du lot entier -> plus de fenêtre de toit en double).
# v2.33 : jonctions -> les couvertures se rejoignent à l'AXE (milieu de l'écart,
# des deux côtés est/ouest comme nord/sud), comme les murs ; trous de lucarnes
# (couverture / sous-face) au même x,y que la fenêtre mais z calé sur le PLAN DU
# TOIT de la couche propriétaire ; anti-doublon final des skylights envoyés
# (aucun doublon même si l'export répète un pent/une fenêtre).
# v2.32 : extrémités des murs (mur + revêtements int./ext.) placées à l'AXE du
# mur commun aux jonctions avec un voisin (mur/mur ou charpente, ex. modules qui
# se prolongent par les pignons est/ouest) — même système que les toitures ;
# anti-doublon des fenêtres de toit au niveau du pent.
# v2.31 : baies libres des lucarnes calées sur l'ANCRE EXACTE de la fenêtre dans
# le complexe (même x, y, z) — plus de décalage de hauteur ; extrémités des murs
# rognées au centre du mur commun (jonction mur/mur) pour que seule la toiture du
# module découpe le mur (retour à un opérateur SEO par module, plus de toitures
# voisines).
# v2.30 : fenêtres de toit alignées PAR LE BAS (ancre = bas de la fenêtre sur la
# rive, z sur le plan de chaque couche, dérivé de l'ancre du complexe), anti-
# doublon ; poutre de charpente rallongée jusqu'aux extrémités des poteaux ;
# revêtements intérieurs (murs) et sous-face de toiture rejoignent l'axe des
# jonctions charpente (milieu de l'écart).
# v2.29 : baies libres des fenêtres de toit calées sur l'ancre de la fenêtre du
# complexe (même axe de fenêtre, z dérivé du plan de chaque couche de toiture) ;
# dimensions width/height conservées lors du repli de favori (le trou
# BARACCA-LUCARNEVIDE prend la taille réelle de la fenêtre) ; découpage SEO des
# murs prenant aussi les toitures des modules voisins (parties communes).
# v2.28 : jonction des toitures entre modules accolés détectée par l'ÉCART entre
# lignes directrices (comme la 3D), est/ouest = amont recouvre l'écart / aval à
# 0, nord/sud = moitié chacun ; baies libres dans les revêtements mesurées depuis
# l'axe propre de la couche (plus de décalage d'épaisseur de mur) ; revêtement
# INTÉRIEUR non rallongé aux angles (seul l'extérieur l'est) ; ancres des fenêtres
# de toit calées en z sur le plan de chaque couche (plus de décalage de hauteur
# entre complexe et revêtements) ; charpente dédoublonnée aux intersections.
# v2.27 : favoris trous BARACCA-BAIELIBRE / BARACCA-LUCARNEVIDE ; hauteurs de
# toiture selon le plan d'inclinaison (delta / cos(pente)) ; dalle de
# revêtement de plancher au niveau de sa propre épaisseur (level = face
# haute) ; revêtements de mur prolongés d'une épaisseur de mur aux angles ;
# option « pas de revêtement » (id "none" -> couche non créée).
# v2.26 : la géométrie de référence = couche MUR / COMPLEXE / PLANCHER.
# Revêtement intérieur décalé d'ep vers l'INTÉRIEUR de la ligne ; revêtement
# extérieur au-delà de ligne + épaisseur mur/complexe ; revêtement de plancher
# au-dessus du plancher ; toiture : complexe à H, sous-face à H-ep, couverture
# à H+ep_complexe (seule avec débord). Ouvertures (fenêtres/portes, fenêtres de
# toit) sur l'élément de référence + BAIES LIBRES équivalentes dans les couches
# de revêtement (FAVORI_BAIE_LIBRE).
# v2.25 : éléments en PILES DE COUCHES (champ « couches » de l'export, chaque
# couche = {role, favori, epaisseur}) : mur = 3 murs décalés [rev. intérieur,
# mur catalogue, rev. extérieur] ; plancher = 2 dalles [rev. supérieur sur
# plancher] + bandes de chant créées (v2.27, champ « chantsFaces ») ; toiture = 3 toits [couverture AVEC débord,
# complexe, sous-face]. Débord uniquement sur la couche couverture. SEO : toutes
# les couches de mur découpées par la couverture. Repli : sans « couches »,
# ancien comportement (1 mur / 1 dalle / 2 toits).
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
# Favori Archicad « baie libre » (ouverture sans menuiserie) utilisé pour les
# ouvertures équivalentes créées dans les couches de revêtement de MUR (v2.26),
# et « lucarne vide » pour les fenêtres de toit dans les revêtements de TOITURE.
# Laissez '' pour utiliser le réglage par défaut de l'outil.
FAVORI_BAIE_LIBRE = "BARACCA-BAIELIBRE"
FAVORI_LUCARNE_VIDE = "BARACCA-LUCARNEVIDE"
FAVORIS_CHARPENTE = {}    # idem pour poteaux/poutres
# v2.53 : champ de hauteur d'implantation (allège) envoyé à CreateWindows /
# CreateDoors. Probe v2.53 : anchorLevel et anchorPosition REFUSÉS (4002),
# sillHeight ACCEPTÉ -> v2.54 : CHAMP_ALLEGE = "sillHeight".
# Si le champ est refusé (additionalProperties), tapir_cree le retire et
# retombe sur l'appui du favori. Mettre '' pour ne rien envoyer.
CHAMP_ALLEGE = "sillHeight"
# Champs protégés par keepFields quand un favori est (ré)appliqué sur une
# ouverture avec allège (sinon le favori réinitialise la hauteur d'implantation).
KEEP_FIELDS_OUVERTURE = ("width", "height", "centerOffset", "sillHeight", "refSide")


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
                 "refSide", "oSide", "reflected",
                 "anchorLevel", "sillHeight")   # v2.53 : allège (si refusé -> appui du favori)
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

        # 5b. v2.53 : quel champ de hauteur d'implantation (allège) CreateWindows
        # accepte-t-il, et est-il effectif ? (relecture GetDetailsOfElements)
        for fld, val in (("anchorLevel", 0.9), ("sillHeight", 0.9),
                         ("anchorPosition", {"x": 0.0, "y": 0.0, "z": 0.9})):
            try:
                r = bridge.tapir("CreateWindows", {"windowsData": [{
                    "ownerWallId": wall_id,
                    "centerOffset": 1.6,
                    "width": 0.8,
                    "height": 1.2,
                    fld: val,
                }]})
                eid = (r.get("elements") or [{}])[0].get("elementId")
                det = {}
                if eid is not None:
                    try:
                        d = bridge.tapir("GetDetailsOfElements",
                                         {"elements": [{"elementId": eid}]})
                        det = (d.get("detailsOfElements") or [{}])[0].get("details") or {}
                    except Exception:
                        pass
                sill = {k: v for k, v in det.items()
                        if any(t in str(k).lower() for t in ("sill", "height", "level", "anchor"))}
                print(f"CreateWindows+{fld:<15} ACCEPTE, hauteur lue={json.dumps(sill, default=str)[:200]}")
            except Exception as exc:
                print(f"CreateWindows+{fld:<15} REFUSE : {str(exc)[:130]}")

        # 5c. v2.56 : sillHeight est-il EFFECTIF ? relecture complète des details,
        # puis réapplication d'un favori avec keepFields (l'allège est-il conservé ?)
        try:
            r = bridge.tapir("CreateWindows", {"windowsData": [{
                "ownerWallId": wall_id, "centerOffset": 2.6, "width": 0.8,
                "height": 1.2, "sillHeight": 0.9,
            }]})
            eid = (r.get("elements") or [{}])[0].get("elementId")
            d = bridge.tapir("GetDetailsOfElements", {"elements": [{"elementId": eid}]})
            det = (d.get("detailsOfElements") or [{}])[0].get("details") or {}
            print(f"  sillHeight=0.9 creation -> details : {json.dumps(det, default=str)[:500]}")
            favs = bridge.tapir("GetFavoritesByType", {"elementType": "Window"}).get("favorites", [])
            if favs and eid is not None:
                fn = favs[0].get("name") if isinstance(favs[0], dict) else favs[0]
                bridge.tapir("ApplyFavoritesToElements", {
                    "favoritesToApply": [{"elementId": eid, "favorite": fn}],
                    "applySettings": True, "applyClassifications": True,
                    "applyCategories": True, "applyProperties": False,
                    "keepFields": ["width", "height", "centerOffset", "sillHeight", "refSide"]})
                d2 = bridge.tapir("GetDetailsOfElements", {"elements": [{"elementId": eid}]})
                det2 = (d2.get("detailsOfElements") or [{}])[0].get("details") or {}
                print(f"  après favori « {fn} » + keepFields -> details : {json.dumps(det2, default=str)[:500]}")
        except Exception as exc:
            print(f"  test sillHeight échoué : {str(exc)[:150]}")

        # 5d. v2.59 : favoriteName + sillHeight ENSEMBLE à la création :
        # le favori s'applique-t-il (libPart) et sillHeight est-il conservé ?
        try:
            favs = bridge.tapir("GetFavoritesByType", {"elementType": "Window"}).get("favorites", [])
            if favs:
                fn = favs[0].get("name") if isinstance(favs[0], dict) else favs[0]
                r = bridge.tapir("CreateWindows", {"windowsData": [{
                    "ownerWallId": wall_id, "centerOffset": 0.4, "width": 0.9,
                    "height": 1.2, "sillHeight": 0.9, "favoriteName": fn,
                }]})
                eid = (r.get("elements") or [{}])[0].get("elementId")
                d = bridge.tapir("GetDetailsOfElements", {"elements": [{"elementId": eid}]})
                det = (d.get("detailsOfElements") or [{}])[0].get("details") or {}
                lp = (det.get("libPart") or {}).get("name")
                print(f"  5d favori+sillHeight creation -> libPart={lp!r}, sillHeight={det.get('sillHeight')}")
        except Exception as exc:
            print(f"  5d échoué : {str(exc)[:150]}")
        # 5e. v2.59 : favori réappliqué SANS keepFields : sillHeight est-il réinitialisé ?
        try:
            r = bridge.tapir("CreateWindows", {"windowsData": [{
                "ownerWallId": wall_id, "centerOffset": 2.9, "width": 0.8,
                "height": 1.2, "sillHeight": 0.9,
            }]})
            eid = (r.get("elements") or [{}])[0].get("elementId")
            favs = bridge.tapir("GetFavoritesByType", {"elementType": "Window"}).get("favorites", [])
            if favs and eid is not None:
                fn = favs[0].get("name") if isinstance(favs[0], dict) else favs[0]
                bridge.tapir("ApplyFavoritesToElements", {
                    "favoritesToApply": [{"elementId": eid, "favorite": fn}],
                    "applySettings": True, "applyClassifications": True,
                    "applyCategories": True, "applyProperties": False})
                d2 = bridge.tapir("GetDetailsOfElements", {"elements": [{"elementId": eid}]})
                det2 = (d2.get("detailsOfElements") or [{}])[0].get("details") or {}
                lp2 = (det2.get("libPart") or {}).get("name")
                print(f"  5e favori SANS keepFields -> libPart={lp2!r}, sillHeight={det2.get('sillHeight')}")
        except Exception as exc:
            print(f"  5e échoué : {str(exc)[:150]}")

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
        # v2.25 : pile de couches du mur (intérieur -> extérieur), chacune avec
        # sa référence Archicad et son épaisseur. Repli : un seul mur catalogue.
        couches = [c for c in (face.get("couches") or []) if isinstance(c, dict)]
        if not couches:
            couches = [{"role": "mur", "favori": face.get("favori", ""),
                        "epaisseur": face.get("epaisseur", 0.14)}]
        ep_mur = next((float(c.get("epaisseur") or 0.0) for c in couches
                       if c.get("role") == "mur"), float(face.get("epaisseur", 0.14)))
        segments[face_key] = {
            "face": face_key,
            "beg": beg, "end": end,
            "hauteur": H,
            "epaisseur": face.get("epaisseur", 0.14),
            "couches": couches,
            "epaisseur_mur": ep_mur,
            "epaisseur_totale": sum(float(c.get("epaisseur") or 0.0) for c in couches),
            "type": face.get("type", ""),
            "favori": face.get("favori", ""),   # v2.18 : référence Archicad du mur
            "ouvertures": face.get("ouvertures", []),
            "L": L, "l": l,  # dimensions du module : calcul des centerOffset
        }
    return segments


# Normales EXTÉRIEURES des faces en coordonnées EXPORT (+Y = Sud, v2.7) :
# le corps du mur s'étend vers l'extérieur de chaque module. Utilisées pour
# décaler chaque couche du mur perpendiculairement à la ligne directrice (v2.25).
NORMALES_EXT = {"sud": (0.0, 1.0), "nord": (0.0, -1.0),
                "est": (1.0, 0.0), "ouest": (-1.0, 0.0)}


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
    physique -> même clé, le mur partagé n'est créé qu'une fois.
    v2.25 : l'épaisseur prise en compte est celle de la couche MUR (et non de
    toute la pile) : deux modules accolés ont leurs directrices distantes d'une
    épaisseur de MUR, et c'est la couche mur qui est partagée."""
    ep = float(seg.get("epaisseur_mur") or seg.get("epaisseur", 0.0))
    # normales EXTÉRIEURES en coordonnées EXPORT (+Y = Sud, v2.7)
    nx, ny = NORMALES_EXT.get(face_key, (0.0, 0.0))
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
    en objet) ; défaut 0,157 m (constante PLANCHER_DEPASSEMENT du configurateur)."""
    pl = module.get("plancher")
    dims = module.get("dimensions", {})
    if isinstance(pl, dict) and pl.get("longueur") and pl.get("largeur"):
        return (max(0.0, (float(pl["longueur"]) - float(dims.get("longueur", 0.0))) / 2.0),
                max(0.0, (float(pl["largeur"]) - float(dims.get("largeur", 0.0))) / 2.0))
    return (0.157, 0.157)


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
        # v2.58 : liste des composites retirée de la console (trop verbeuse) —
        # seul le compte est affiché ; les résolutions restent loguées une par une.
        print(f"  {len(noms_lus)} composite(s) lu(s) dans le gabarit Archicad.")
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
    # v2.60 : décalage vertical de la rive de chaque versant en deux-pentes
    # asymétrique (shed) — comme dans le configurateur (deltaRiveDm) : on remonte
    # le versant dont la sous-face du complexe serait la plus basse, pour que les
    # deux sous-faces rencontrent les murs intérieurs AU MÊME NIVEAU.
    # δ = ep_complexe · (1/cos p − 1/cos p_min) ; nul si pentes égales.
    _ep_toit0 = float(toit.get("epaisseur") or 0.30)
    _pmin = min(pente, pente_sud)
    _cm = math.cos(math.radians(_pmin))
    d_rive_nord = _ep_toit0 * (1.0 / math.cos(math.radians(pente)) - 1.0 / _cm)
    d_rive_sud = _ep_toit0 * (1.0 / math.cos(math.radians(pente_sud)) - 1.0 / _cm)

    def faitage(l_u):
        """v2.60 : (position du faîtage depuis le bord nord, hauteur de faîtage)
        pour une largeur l_u. Symétrique : l/2 et tan(pente)*l/2. Asymétrique
        (C=tan nord, P=tan sud) : x = l*P/(C+P) depuis le nord, hf = x*C.
        v2.60 : en shed, les rives des versants sont remontées de δ (d_rive_nord /
        d_rive_sud, alignement des sous-faces en rive comme dans le configurateur) :
        le faîtage commun s'ajuste -> hf = (l + δN/C + δS/P)/(1/C + 1/P) et
        x = (hf − δN)/C. Pentes égales : δ = 0, formules v2.18 inchangées."""
        C = math.tan(math.radians(pente))
        P = math.tan(math.radians(pente_sud))
        if geo == "deuxpentes" and C > 0 and P > 0:
            if d_rive_nord or d_rive_sud:
                hf = (l_u + d_rive_nord / C + d_rive_sud / P) / (1.0 / C + 1.0 / P)
                return (hf - d_rive_nord) / C, hf
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

    # v2.30 : jonctions « séparées par une charpente » — pour chaque côté d'une
    # unité, l'écart (m) avec un voisin accolé dont le côté commun est en
    # charpente (nature="charpente" d'un côté ou de l'autre), 0 sinon.
    # Sert à faire rejoindre les revêtements intérieurs à l'axe de la charpente
    # (milieu de l'écart), comme le revêtement de plancher.
    _sep_cache = {}

    def separation(unite, charpente_only):
        """Écarts (m) avec les voisins accolés, par côté : charpente_only=True ->
        seulement si le côté commun est en charpente (jonction charpente) ;
        False -> seulement si le côté commun est un MUR (jonction mur/mur)."""
        key0 = (unite.get("id", "m0"), charpente_only)
        if key0 in _sep_cache:
            return _sep_cache[key0]
        du = unite.get("dimensions") or {}
        bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
        L0, l0 = float(du.get("longueur", 0.0)), float(du.get("largeur", 0.0))
        out = {"nord": 0.0, "sud": 0.0, "est": 0.0, "ouest": 0.0}
        opp = {"nord": "sud", "sud": "nord", "est": "ouest", "ouest": "est"}
        for side in ("nord", "sud", "est", "ouest"):
            fU = (unite.get("murs") or {}).get(side) or {}
            for V in unites:
                if V is unite:
                    continue
                dv = V.get("dimensions") or {}
                vx, vy = float(V.get("x", 0.0)), float(V.get("y", 0.0))
                vL, vl = float(dv.get("longueur", 0.0)), float(dv.get("largeur", 0.0))
                fV = (V.get("murs") or {}).get(opp[side]) or {}
                carU = str(fU.get("nature") or "").lower() == "charpente"
                carV = str(fV.get("nature") or "").lower() == "charpente"
                if charpente_only and not (carU or carV):
                    continue
                if not charpente_only and (carU or carV):
                    continue
                ovY = vy < by + l0 - 1e-6 and vy + vl > by + 1e-6
                ovX = vx < bx + L0 - 1e-6 and vx + vL > bx + 1e-6
                if side == "est":
                    g = vx - (bx + L0)
                    if 0 < g <= 0.6 and ovY:
                        out[side] = g
                elif side == "ouest":
                    g = bx - (vx + vL)
                    if 0 < g <= 0.6 and ovY:
                        out[side] = g
                elif side == "sud":
                    g = vy - (by + l0)
                    if 0 < g <= 0.6 and ovX:
                        out[side] = g
                else:
                    g = by - (vy + vl)
                    if 0 < g <= 0.6 and ovX:
                        out[side] = g
        _sep_cache[key0] = out
        return out

    # v2.32 : extrémités des murs placées à l'AXE du mur commun (milieu de
    # l'écart avec le voisin) quand l'angle à cette extrémité est une jonction
    # (mur/mur ou charpente) — comme le système des toitures aux jonctions :
    # murs, revêtements intérieurs ET extérieurs se rejoignent à l'axe.
    # (ex. deux modules qui se prolongent par les pignons est/ouest.)
    COINS = {"nord": ("est", "ouest"), "sud": ("ouest", "est"),
             "est": ("sud", "nord"), "ouest": ("nord", "sud")}
    axe_par_cle = {}   # cle -> (beg, end, shared_beg, shared_end)
    for unite, segments in segments_par_unite:
        uid = unite.get("id", "m0")
        sepC = separation(unite, True)
        sepM = separation(unite, False)
        sep = {s: max(sepC[s], sepM[s]) for s in ("nord", "sud", "est", "ouest")}
        du = unite.get("dimensions") or {}
        bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
        L0, l0 = float(du.get("longueur", 0.0)), float(du.get("largeur", 0.0))
        for face_key, seg in segments.items():
            cle = alias.get((uid, face_key))
            if cle is None:
                continue
            beg, end = seg["beg"], seg["end"]
            sb = se = False
            if face_key == "nord":
                if sep["est"] > 0:
                    beg = (bx + L0 + sep["est"] / 2.0, by); sb = True
                if sep["ouest"] > 0:
                    end = (bx - sep["ouest"] / 2.0, by); se = True
            elif face_key == "sud":
                if sep["ouest"] > 0:
                    beg = (bx - sep["ouest"] / 2.0, by + l0); sb = True
                if sep["est"] > 0:
                    end = (bx + L0 + sep["est"] / 2.0, by + l0); se = True
            elif face_key == "est":
                if sep["sud"] > 0:
                    beg = (bx + L0, by + l0 + sep["sud"] / 2.0); sb = True
                if sep["nord"] > 0:
                    end = (bx + L0, by - sep["nord"] / 2.0); se = True
            else:  # ouest
                if sep["nord"] > 0:
                    beg = (bx, by - sep["nord"] / 2.0); sb = True
                if sep["sud"] > 0:
                    end = (bx, by + l0 + sep["sud"] / 2.0); se = True
            # mur partagé : on fusionne (une extrémité partagée suffit)
            prev = axe_par_cle.get(cle)
            if prev is None:
                axe_par_cle[cle] = (beg, end, sb, se)
            else:
                axe_par_cle[cle] = (
                    beg if sb else prev[0], end if se else prev[1],
                    sb or prev[2], se or prev[3])

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

    def axes_envoi_pt(beg, end):
        """v2.22 : AC30 / Tapir 2.0 — beg<->end échangés à l'envoi, combiné à
        referenceLineLocation="Inside" (v2.23) : la ligne directrice reste aux
        mêmes coordonnées, le corps du mur part vers l'EXTÉRIEUR et la face
        extérieure (côté « soleil » repris par les fenêtres/portes) est sur la
        face opposée à la ligne."""
        return end, beg

    def axes_envoi(seg):
        return axes_envoi_pt(seg["beg"], seg["end"])

    _avec_couches = sum(1 for s in canon.values() if len(s.get("couches") or []) > 1)
    print(f"Création de {len(canon)} mur(s) sur {len(unites)} module(s)… "
          f"({_avec_couches} avec pile de couches, "
          f"{len(canon) - _avec_couches} sans champ « couches » -> 1 couche)")
    # Un mur par appel CreateWalls : l'elementId retourné est ainsi reliably
    # associé à sa ligne (pas de décalage d'index si un mur échoue).
    wall_ids = {}          # cle -> elementId de la couche MUR (ouvertures)
    wall_layer_ids = {}    # cle -> [elementId de chaque couche] (découpe SEO)
    wall_role_ids = {}     # cle -> {role: elementId} (baies libres dans les revêtements)
    wall_role_axes = {}    # cle -> {role: (beg, end)} axe de chaque couche, coord. EXPORT
    mur_axes = {}          # cle -> (beg, end) de la couche mur, coord. EXPORT
    fav_a_appliquer = []   # (elementId, favori, keepFields) -> ApplyFavoritesToElements (section 5)
    for cle, seg in canon.items():
        # v2.25/v2.26 : le mur est une pile de couches superposées. La LIGNE
        # DIRECTRICE est la couche MUR (géométrie de référence) :
        # - revêtement intérieur : décalé de son épaisseur vers l'INTÉRIEUR
        # - mur catalogue : sur la ligne
        # - revêtement extérieur : au-delà de la ligne + épaisseur du mur
        couches = seg.get("couches") or [{"role": "mur", "favori": seg.get("favori", ""),
                                          "epaisseur": seg["epaisseur"]}]
        nx, ny = NORMALES_EXT.get(seg["face"], (0.0, 0.0))
        # v2.32 : extrémités à l'AXE du mur commun aux jonctions avec un voisin
        # (mur/mur ou charpente) — mur, revêtement intérieur et extérieur
        # se rejoignent à l'axe, comme les toitures.
        ab, ae, sb, se = axe_par_cle.get(cle, (seg["beg"], seg["end"], False, False))
        favori_seg = favori_de(seg, FAVORIS_MURS, seg["type"])
        ep_int = next((float(c.get("epaisseur") or 0.0) for c in couches
                       if c.get("role") == "interieur"), 0.0)
        ep_mur = next((float(c.get("epaisseur") or 0.0) for c in couches
                       if c.get("role") == "mur"), float(seg.get("epaisseur", 0.14)))
        decalage = {"interieur": -ep_int, "mur": 0.0, "exterieur": ep_mur}
        roles_ids = {}
        for couche in couches:
            ep = float(couche.get("epaisseur") or 0.0)
            if ep <= 0 or str(couche.get("id") or "") == "none":
                continue   # « pas de revêtement » ou épaisseur nulle : rien créé
            role = str(couche.get("role") or "mur")
            d = decalage.get(role, 0.0)
            beg_l = (ab[0] + nx * d, ab[1] + ny * d)
            end_l = (ae[0] + nx * d, ae[1] + ny * d)
            if role == "exterieur":
                # v2.26/v2.32 : aux extrémités LIBRES, le revêtement EXTÉRIEUR dépasse
                # d'une épaisseur de MUR (angle extérieur) ; aux extrémités en
                # JONCTION, il est déjà à l'axe du mur commun (rien de plus).
                dx, dy = end_l[0] - beg_l[0], end_l[1] - beg_l[1]
                ln = math.hypot(dx, dy) or 1.0
                ux, uy = dx / ln, dy / ln
                if not sb:
                    beg_l = (beg_l[0] - ux * ep_mur, beg_l[1] - uy * ep_mur)
                if not se:
                    end_l = (end_l[0] + ux * ep_mur, end_l[1] + uy * ep_mur)
            # mur et revêtement intérieur : aux jonctions l'extrémité est déjà à
            # l'axe (ab/ae) ; aux coins libres, le coin = la ligne directrice.
            wall_role_axes.setdefault(cle, {})[role] = (beg_l, end_l)
            beg_e, end_e = axes_envoi_pt(beg_l, end_l)
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
                "thickness": ep,
                "referenceLineLocation": WALL_REFERENCE_LINE_LOCATION,
            }
            favori_c = str(couche.get("favori") or "").strip() or favori_seg
            comp_id = resoudre_composite(favori_c) if favori_c else None
            if comp_id:
                # composite de la couche appliqué à la création — JAMAIS le
                # favori (écraserait l'orientation du mur)
                item["structureType"] = "Composite"
                item["compositeId"] = comp_id
            elif not favori_c and seg["type"] not in types_sans_favori:
                types_sans_favori.add(seg["type"])
                print(f"  ! Pas de référence Archicad pour « {seg['type']} » : "
                      f"réglages par défaut de l'outil Mur.")
            walls_data.append((cle, item))
            # Repli automatique si Tapir refuse un champ optionnel
            # (additionalProperties) : tapir_cree le retire et réessaie.
            resp = bridge.tapir_cree("CreateWalls", {"wallsData": [item]})
            el = (resp.get("elements") or [{}])[0]
            if el.get("elementId") is not None:
                wall_layer_ids.setdefault(cle, []).append(el["elementId"])
                roles_ids[role] = el["elementId"]
                if role == "mur":
                    wall_ids[cle] = el["elementId"]      # ouvertures sur le mur
                    mur_axes[cle] = (beg_l, end_l)        # axe de la couche mur
            elif el.get("error"):
                print(f"  ! Mur {seg['face']} (couche {role}) non créé : {el['error']}")
        wall_role_ids[cle] = roles_ids

    # --- 1b. Charpentes (nature="charpente") : poteaux + poutre, pas de mur ---
    # Un côté en charpente = cadre ouvert : 2 poteaux aux extrémités (hauteur H)
    # + 1 poutre sablière en tête (niveau H). Section = charpente.epaisseur,
    # favori = charpente.favori (outils Poteau / Poutre).
    if charpente_faces:
        ch = module.get("charpente") if isinstance(module.get("charpente"), dict) else {}
        ep_ch = float(ch.get("epaisseur") or 0.20)
        fav_ch = favori_de(ch, FAVORIS_CHARPENTE, "")
        cols_data, beams_data = [], []
        # v2.28 : dédoublonnage — à l'intersection de deux modules accolés (côté
        # commun en charpente des DEUX côtés), un seul cadre est créé, posé au
        # MILIEU de l'écart entre les deux lignes directrices (comme le mur
        # partagé) ; les poteaux d'angle communs à deux côtés charpente ne sont
        # créés qu'une fois (clé = point arrondi au cm / ligne normalisée).
        col_vus, poutre_vues = set(), set()

        def voisin_charpente(unite, face_key):
            """Si le voisin accolé a aussi ce côté commun en charpente : écart (m)
            entre les deux lignes directrices, sinon 0."""
            dims_u = unite["dimensions"]
            bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
            L_u, l_u = float(dims_u["longueur"]), float(dims_u["largeur"])
            opp = {"nord": "sud", "sud": "nord", "est": "ouest", "ouest": "est"}[face_key]
            for V in unites:
                if V is unite:
                    continue
                dv = V.get("dimensions") or {}
                vx, vy = float(V.get("x", 0.0)), float(V.get("y", 0.0))
                vL, vl = float(dv.get("longueur", 0.0)), float(dv.get("largeur", 0.0))
                fv = (V.get("murs") or {}).get(opp) or {}
                if str(fv.get("nature") or "").lower() != "charpente":
                    continue
                ovY = vy < by + l_u - 1e-6 and vy + vl > by + 1e-6
                ovX = vx < bx + L_u - 1e-6 and vx + vL > bx + 1e-6
                if face_key == "est":
                    g = vx - (bx + L_u)
                    if 0 < g <= 0.6 and ovY:
                        return g
                elif face_key == "ouest":
                    g = bx - (vx + vL)
                    if 0 < g <= 0.6 and ovY:
                        return g
                elif face_key == "sud":
                    g = vy - (by + l_u)
                    if 0 < g <= 0.6 and ovX:
                        return g
                else:
                    g = by - (vy + vl)
                    if 0 < g <= 0.6 and ovX:
                        return g
            return 0.0

        for unite, face_key in charpente_faces:
            uid = unite.get("id", "m0")
            dims_u = unite["dimensions"]
            L_u = float(dims_u["longueur"])
            l_u = float(dims_u["largeur"])
            H_u = float(dims_u["hauteur"])
            bx = float(unite.get("x", 0.0))
            by = float(unite.get("y", 0.0))
            # v2.18 : charpente possible sur les 4 côtés ; v2.28 : côté commun
            # charpente des deux côtés -> cadre unique au milieu de l'écart,
            # dessiné par le module amont (est/sud) uniquement.
            g = voisin_charpente(unite, face_key)
            if g > 0:
                if face_key in ("ouest", "nord"):
                    continue      # c'est le module opposé (est/sud) qui dessine
                if face_key == "est":
                    x = bx + L_u + g / 2.0
                    extremites = [(x, by), (x, by + l_u)]
                else:  # sud
                    y = by + l_u + g / 2.0
                    extremites = [(bx, y), (bx + L_u, y)]
            elif face_key in ("est", "ouest"):
                x = bx if face_key == "ouest" else bx + L_u
                extremites = [(x, by), (x, by + l_u)]
            else:
                y = by if face_key == "nord" else by + l_u
                extremites = [(bx, y), (bx + L_u, y)]
            bkey = cle_ligne(extremites[0], extremites[1])
            if bkey not in poutre_vues:
                poutre_vues.add(bkey)
                # v2.30 : la poutre arrive aux EXTRÉMITÉS des poteaux (leurs bords
                # extérieurs), pas à leur axe : rallongée de ep_ch/2 à chaque bout.
                bdx, bdy = extremites[1][0] - extremites[0][0], extremites[1][1] - extremites[0][1]
                bln = math.hypot(bdx, bdy) or 1.0
                bux, buy = bdx / bln, bdy / bln
                b0 = (extremites[0][0] - bux * ep_ch / 2.0, extremites[0][1] - buy * ep_ch / 2.0)
                b1 = (extremites[1][0] + bux * ep_ch / 2.0, extremites[1][1] + buy * ep_ch / 2.0)
                beams_data.append({"begCoordinate": tr(b0),
                                   "endCoordinate": tr(b1),
                                   "zCoordinate": H_u, "width": ep_ch, "height": ep_ch})
            for pt in extremites:
                ckey = (round(pt[0], 2), round(pt[1], 2))
                if ckey in col_vus:
                    continue
                col_vus.add(ckey)
                p = tr(pt)
                cols_data.append({"coordinates": {"x": p["x"], "y": p["y"], "z": 0.0},
                                  "height": H_u, "width": ep_ch, "depth": ep_ch})
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

    # --- 2. Planchers (par module, avec débord) -----------------------------
    # v2.25 : plancher = 2 dalles superposées [revêtement supérieur, plancher
    # catalogue]. v2.27 : + bandes de chant créées (section 2b, chantsFaces).
    # Repli : une seule dalle.
    nom_plancher = plancher_nom(module)
    pl_obj = module.get("plancher") if isinstance(module.get("plancher"), dict) else {}
    favori_pl = favori_de(pl_obj, FAVORIS_PLANCHER, nom_plancher)
    pl_couches = [c for c in (pl_obj.get("couches") or []) if isinstance(c, dict)]
    ep_plancher = float(pl_obj.get("epaisseur") or 0.20)
    c_sup = next((c for c in pl_couches if c.get("role") == "superieur"), None)
    dL, dl = debord_plancher(module)
    slabs_data = []
    for unite in unites:
        dims_u = unite["dimensions"]
        L, l = float(dims_u["longueur"]), float(dims_u["largeur"])
        bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
        poly = [
            tr((bx - dL, by - dl)), tr((bx + L + dL, by - dl)),
            tr((bx + L + dL, by + l + dl)), tr((bx - dL, by + l + dl)),
        ]
        # dalle du plancher catalogue, niveau 0 (RDC)
        item = {"level": 0.0, "polygonCoordinates": poly}
        comp_pl = resoudre_composite(favori_pl) if favori_pl else None
        if comp_pl:
            item["structureType"] = "Composite"
            item["compositeId"] = comp_pl
        slabs_data.append(item)
        # dalle du revêtement supérieur, posée sur le plancher
        # v2.26 : « level » d'une dalle = sa FACE HAUTE -> le revêtement
        # supérieur est à la hauteur de SA PROPRE épaisseur au-dessus de la
        # position de base (le dessus du plancher est à 0), pas à +ép. plancher.
        if c_sup is not None and float(c_sup.get("epaisseur") or 0.0) > 0:
            item_sup = {"level": float(c_sup.get("epaisseur") or 0.0), "polygonCoordinates": poly}
            fav_sup = str(c_sup.get("favori") or "").strip()
            comp_sup = resoudre_composite(fav_sup) if fav_sup else None
            if comp_sup:
                item_sup["structureType"] = "Composite"
                item_sup["compositeId"] = comp_sup
            slabs_data.append(item_sup)
    print(f"Création de {len(slabs_data)} dalle(s) de plancher ({nom_plancher})… "
          f"({'pile de couches' if pl_couches else 'sans champ « couches » -> 1 dalle'})")
    slab_response = bridge.tapir_cree("CreateSlabs", {"slabsData": slabs_data})
    errs = [e.get("error") for e in slab_response.get("elements", [])
            if e.get("error")]
    if errs:
        print(f"  ! Plancher(s) non créé(s) : {errs}")

    # --- 2b. Bandes de chant du plancher (champ « chantsFaces » de l'export) --
    # v2.27 : une bande PAR FACE de module (les côtés communs à deux modules
    # accolés sont déjà exclus côté export). Chaque bande est créée comme un
    # poteau allongé : section = longueur du bord x épaisseur du revêtement de
    # chant choisi, hauteur = épaisseur du plancher, base à -ep_plancher (la
    # bande couvre exactement la tranche de la dalle, de -ep à 0).
    chants_faces = [c for c in (pl_obj.get("chantsFaces") or []) if isinstance(c, dict)]
    if chants_faces:
        unites_par_id = {(u.get("id") or "m0"): u for u in unites}
        cols_chant = []
        for cf in chants_faces:
            unite = unites_par_id.get(cf.get("instId")) or unites[0]
            dims_u = unite["dimensions"]
            L, l = float(dims_u["longueur"]), float(dims_u["largeur"])
            bx, by = float(unite.get("x", 0.0)), float(unite.get("y", 0.0))
            rev = cf.get("revetement") if isinstance(cf.get("revetement"), dict) else {}
            ep_ch = float(rev.get("epaisseur") or 0.0)
            if ep_ch <= 0:
                continue
            face = str(cf.get("face") or "")
            # bord EXTÉRIEUR de la dalle (ligne directrice + débord dL/dl) ;
            # le poteau étant centré sur son point, on décale d'une
            # demi-épaisseur de revêtement vers l'extérieur (coord. EXPORT, +Y = Sud)
            if face == "nord":
                cx, cy, w, d = bx + L / 2, by - dl - ep_ch / 2, L + 2 * dL, ep_ch
            elif face == "sud":
                cx, cy, w, d = bx + L / 2, by + l + dl + ep_ch / 2, L + 2 * dL, ep_ch
            elif face == "ouest":
                cx, cy, w, d = bx - dL - ep_ch / 2, by + l / 2, ep_ch, l + 2 * dl
            elif face == "est":
                cx, cy, w, d = bx + L + dL + ep_ch / 2, by + l / 2, ep_ch, l + 2 * dl
            else:
                continue
            p = tr((cx, cy))
            item = {"coordinates": {"x": p["x"], "y": p["y"], "z": -ep_plancher},
                    "height": ep_plancher, "width": w, "depth": d}
            fav_ch = str(rev.get("favori") or "").strip()
            if fav_ch:
                item["favoriteName"] = fav_ch
            cols_chant.append((item, fav_ch))
        if cols_chant:
            print(f"Création de {len(cols_chant)} bande(s) de chant de plancher…")
            try:
                resp = bridge.tapir_cree("CreateColumns",
                                        {"columnsData": [it for it, _ in cols_chant]})
                for (it, fav), e in zip(cols_chant, resp.get("elements", [])):
                    if e.get("elementId") is not None and fav:
                        fav_a_appliquer.append((e["elementId"], fav, None))
                n_ok = sum(1 for e in resp.get("elements", []) if e.get("elementId") is not None)
                print(f"  -> {n_ok}/{len(cols_chant)} bande(s) créée(s).")
            except Exception as exc:
                print(f"  ! CreateColumns (chants) en échec ({exc}) : bandes non créées.")

    # --- 3. Toitures (PAR module, superposées : complexe + couverture) ------
    # - complexe de toiture : empreinte sur la LIGNE DIRECTRICE, niveau H ;
    # - couverture (toit avec débords) : empreinte élargie, au-dessus (niveau
    #   H + épaisseur du complexe). Le débord est compté depuis la face
    #   EXTÉRIEURE du mur (v2.7 : débord + épaisseur de mur) ; pas de débord
    #   sur les côtés communs à deux modules accolés.
    angle = round(math.radians(pente), 6)   # pente en RADIANS (convention API)
    ep_toit = float(toit.get("epaisseur") or 0.30)
    deb = float(toit.get("depassee") or ep_toit)   # débord de toiture (m)
    # v2.25 : toiture = pile de 3 couches superposées [revêtement toiture
    # (couverture, SEULE avec débord), complexe de toiture, revêtement
    # inférieur (sous-face)]. Chaque couche a sa référence Archicad (composite)
    # et son épaisseur. Repli : ancien schéma à 2 niveaux.
    couches_toit = [c for c in (toit.get("couches") or []) if isinstance(c, dict)]

    def couche_toit(role):
        return next((c for c in couches_toit if c.get("role") == role), {})

    c_couv, c_comp, c_inf = (couche_toit("couverture"), couche_toit("complexe"),
                             couche_toit("inferieur"))
    ep_inf = float(c_inf.get("epaisseur") or 0.0)
    ep_comp = float(c_comp.get("epaisseur") or ep_toit)
    comp_inf = resoudre_composite(str(c_inf.get("favori") or "").strip()) \
        if str(c_inf.get("favori") or "").strip() else None
    comp_comp = resoudre_composite(str(c_comp.get("favori") or "").strip()) \
        if str(c_comp.get("favori") or "").strip() else None
    comp_couv = resoudre_composite(str(c_couv.get("favori") or "").strip()) \
        if str(c_couv.get("favori") or "").strip() else None
    if couches_toit:
        # le débord ne concerne QUE le revêtement de toiture (couche couverture)
        deb = float(c_couv.get("depassee") or toit.get("depassee") or ep_comp)
    print(f"Création des toitures ({toit.get('type', geo)} / {geo}"
          f"{' — pile de 3 couches' if couches_toit else ' — sans champ « couches » -> 2 niveaux'}, "
          f"{len(unites)} module(s), complexe + couverture, débord {deb:.2f} m + épaisseur de mur)…")

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

            # Jonction entre deux modules accolés : détectée par l'ÉCART entre
            # lignes directrices (0 < écart <= épaisseur max + marge), comme dans
            # la 3D du configurateur — indépendamment du mur/charpente de chaque
            # côté et de l'épaisseur courante (l'écart réel peut différer de
            # l'épaisseur au moment de l'ajout du module).
            epMax = max([0.2] + [float(f.get("epaisseur") or 0.0)
                                 for u2 in unites
                                 for f in (u2.get("murs") or {}).values()
                                 if isinstance(f, dict)]) + 0.05

            def voisin_gap(face_key):
                """Écart (m) avec le voisin accolé sur ce côté, 0 si aucun."""
                for V in unites:
                    if V is unite:
                        continue
                    dv = V.get("dimensions") or {}
                    vx, vy = float(V.get("x", 0.0)), float(V.get("y", 0.0))
                    vL, vl = float(dv.get("longueur", 0.0)), float(dv.get("largeur", 0.0))
                    ovY = vy < by + l - 1e-6 and vy + vl > by + 1e-6
                    ovX = vx < bx + L - 1e-6 and vx + vL > bx + 1e-6
                    if face_key == "est":
                        g = vx - (bx + L)
                        if 0 < g <= epMax and ovY:
                            return g
                    elif face_key == "ouest":
                        g = bx - (vx + vL)
                        if 0 < g <= epMax and ovY:
                            return g
                    elif face_key == "sud":
                        g = vy - (by + l)
                        if 0 < g <= epMax and ovX:
                            return g
                    else:  # nord
                        g = by - (vy + vl)
                        if 0 < g <= epMax and ovX:
                            return g
                return 0.0

            def cote(face_key, segments=segments):
                """Élargissement de la couverture sur ce côté : débord compté
                depuis la face extérieure du mur = depassee + épaisseur TOTALE
                du mur (pile de couches, v2.25). Côté partagé entre deux modules
                accolés (v2.33) : chacun prolonge de la moitié de l'écart, les
                deux couvertures se rejoignent à l'AXE (milieu du mur partagé),
                comme les murs découpés à l'axe (v2.32)."""
                seg = segments.get(face_key)
                ep_tot = float(seg.get("epaisseur_totale") or seg.get("epaisseur") or 0.255) if seg else 0.255
                g = 0.0 if (geo == "monopente" and face_key == "nord") else voisin_gap(face_key)
                if g > 0:
                    # v2.60 : jonction SUD/NORD en deux-pentes -> NOUE : chaque versant
                    # est prolongé jusqu'au point où les deux plans de couverture se
                    # coupent au-dessus du mur commun (comme dans la 3D du
                    # configurateur) : d = (δS − δN + g·tan pN)/(tan pN + tan pS),
                    # mesuré depuis la ligne directrice SUD du module au nord.
                    # -> les toitures se rejoignent sans marche, même en shed.
                    # Est/ouest et pentes égales : milieu de l'écart (v2.33).
                    if face_key in ("sud", "nord") and geo == "deuxpentes":
                        C = math.tan(math.radians(pente))
                        P = math.tan(math.radians(pente_sud))
                        if C > 0 and P > 0:
                            raw = (d_rive_sud - d_rive_nord + g * C) / (C + P)
                            d = min(max(raw, -g), 2 * g)
                            return d if face_key == "sud" else g - d
                    return g / 2.0
                if seg is None:
                    return deb + 0.255      # rive en charpente : débord + ép. mur
                return deb + ep_tot

            dS, dN, dE, dO = cote("sud"), cote("nord"), cote("est"), cote("ouest")
            # coordonnées EXPORT (miroir Y appliqué par tr) : nord en y=by, sud en y=by+l
            emp_c = [tr((bx, by)), tr((bx + L, by)),
                     tr((bx + L, by + l)), tr((bx, by + l))]
            x0, x1 = bx - dO, bx + L + dE
            y0, y1 = by - dN, by + l + dS
            emp_v = [tr((x0, y0)), tr((x1, y0)), tr((x1, y1)), tr((x0, y1))]
            # v2.30 : sous-face (revêtement inférieur) — sur un côté séparé d'un
            # voisin par une CHARPENTE, elle est élargie de la moitié de l'écart :
            # les sous-faces de deux modules séparés par une charpente se
            # rejoignent à l'axe (comme les revêtements intérieurs des murs).
            sepC = separation(unite, True)
            ex0 = bx - sepC["ouest"] / 2.0
            ex1 = bx + L + sepC["est"] / 2.0
            ey0 = by - sepC["nord"] / 2.0
            ey1 = by + l + sepC["sud"] / 2.0
            emp_inf = [tr((ex0, ey0)), tr((ex1, ey0)), tr((ex1, ey1)), tr((ex0, ey1))]

            # v2.26 : la LIGNE DIRECTRICE (niveau H) = couche COMPLEXE (référence).
            # Niveaux exprimés en DELTA vertical depuis H ; l'épaisseur d'une
            # couche de toiture est mesurée SELON LE PLAN D'INCLINAISON, donc le
            # delta vertical vaut ep / cos(pente du versant) :
            # - revêtement inférieur (sous-face) : delta -ep_inf
            # - couverture (revêtement toiture) : delta +ep_comp — SEULE couche
            #   avec débord.
            # Sans champ couches : ancien schéma à 2 niveaux.
            if couches_toit:
                niveaux = [(0.0, emp_c, "complexe", comp_comp)]
                if ep_inf > 0 or comp_inf:
                    niveaux.append((-ep_inf, emp_inf, "inferieur", comp_inf))
                niveaux.append((ep_comp, emp_v, "couverture", comp_couv))
            else:
                niveaux = [(0.0, emp_c, "complexe", toit_comp_id),
                           (ep_toit, emp_v, "couverture", toit_comp_id)]

            def add_roof(delta, poly, with_angle, pivot=None, role="complexe",
                         multi=None, versant=None, angle_rad=None, comp=None, dr=0.0):
                # v2.26 : épaisseur selon le plan d'inclinaison -> delta vertical
                pr = angle_rad if angle_rad is not None else (angle if with_angle else 0.0)
                # v2.60 : dr = remontée de la rive du versant en shed (δ), pour
                # aligner les sous-faces du complexe en rive comme dans le configurateur
                level = H + delta / max(math.cos(pr), 0.2) + dr
                r = {"level": round(level, 6), "polygonCoordinates": poly}
                cid = comp or toit_comp_id
                if cid:
                    r["structureType"] = "Composite"
                    r["compositeId"] = cid
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
                roof_meta.append((uid, level, role, versant))

            if geo == "deuxpentes" and use_multi:
                # v2.12 : un toit multi-plans par niveau. Le polygone reste la
                # LIGNE DIRECTRICE ; les débords sont des débords d'arête
                # (pivotEdges) -> la ligne de référence ne bouge pas, donc la
                # hauteur au droit des murs est la même avec ou sans débord,
                # y compris aux jonctions entre modules (côté partagé = 0).
                # Niveau de la couverture = H + épaisseur du complexe de
                # toiture lue dans le configurateur (toit.epaisseur).
                # Arêtes du polygone pivot : 0=nord, 1=est, 2=sud, 3=ouest.
                # v2.25 : niveaux = pile de couches ; seul le revêtement de
                # toiture (couverture) a des débords d'arête.
                for delta, emp, role, comp in niveaux:
                    ovs = (dN, dE, dS, dO) if role == "couverture" else (0.0, 0.0, 0.0, 0.0)
                    pe = []
                    for i, ov in enumerate(ovs):
                        li = {"eavesOverhang": ov}
                        if pignon and i in (1, 3):   # arêtes est/ouest = pignon
                            li["angleType"] = "Gable"
                        pe.append({"levels": [li]})
                    # v2.30 : la couverture garde le polygone de la ligne directrice
                    # (débords via pivotEdges) ; la sous-face prend son polygone élargi
                    # (emp_inf) sur les jonctions charpente.
                    poly = emp_c if role == "couverture" else emp
                    add_roof(delta, poly, False, role=role, comp=comp,
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
                    for delta, emp, role, comp in niveaux:
                        add_roof(delta, emp, True, pivot=piv_s, role=role, comp=comp)
                elif geo == "deuxpentes" and pignon:
                    # v2.18 : faîtage possiblement excentré (pentes asymétriques)
                    x_fait, _hf = faitage(l)
                    ydemi = tr((0.0, by + x_fait))["y"]
                    for delta, emp, role, comp in niveaux:
                        add_roof(delta, [emp[0], emp[1],
                                       {"x": emp[1]["x"], "y": ydemi},
                                       {"x": emp[0]["x"], "y": ydemi}],
                                 True, pivot=piv_n, role=role, versant="nord",
                                 angle_rad=angle_nord, comp=comp, dr=d_rive_nord)
                        add_roof(delta, [{"x": emp[0]["x"], "y": ydemi},
                                       {"x": emp[1]["x"], "y": ydemi}, emp[2], emp[3]],
                                 True, pivot=piv_s, role=role, versant="sud",
                                 angle_rad=angle_sud, comp=comp, dr=d_rive_sud)
                else:
                    for delta, emp, role, comp in niveaux:
                        add_roof(delta, emp, geo == "deuxpentes", role=role, comp=comp)

    # v2.60 : en shed (deux-pentes asymétrique avec épaisseur de complexe), on
    # passe en versants monoplanes : c'est le seul mode où chaque versant peut
    # porter sa propre remontée δ (d_rive_nord/sud) — en multi-plans Archicad
    # calculerait un faîtage sans δ, incohérent avec le configurateur.
    _shed = geo == "deuxpentes" and abs(angle_nord - angle_sud) > 1e-9 and _ep_toit0 > 0
    if _shed:
        print("  … deux-pentes asymétrique (shed) : versants monoplanes avec δ "
              f"(δN={d_rive_nord:.4f} m, δS={d_rive_sud:.4f} m) pour coller au configurateur.")
    build_roofs(use_multi=(geo == "deuxpentes" and not _shed))
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
        print(f"  Toitures créées ({len(roofs_data)} plans : pile de couches par module — "
              f"couverture (débord) + complexe + sous-face si couches exportées).")
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
    couv_par_uid = {}          # uid -> [elementId des toits de COUVERTURE] (opérateurs SEO)
    toit_par_uid_versant = {}  # uid -> {role: {versant (ou None): elementId}}
    toit_niveau = {}           # (uid, role, versant) -> level (cote z de la couche)
    if len(roof_elements) == len(roofs_data):
        for (uid, level, role, vers), rel in zip(roof_meta, roof_elements):
            if rel.get("error") or rel.get("elementId") is None:
                continue
            toit_par_uid_versant.setdefault(uid, {}).setdefault(role, {})[vers] = rel["elementId"]
            toit_niveau[(uid, role, vers)] = level
            if role == "couverture":
                couv_par_uid.setdefault(uid, []).append(rel["elementId"])
    if wall_layer_ids and couv_par_uid:
        links = []
        for cle, wids in wall_layer_ids.items():
            # v2.31 : seule la toiture du (des) module(s) auquel appartient le mur
            # sert de découpe — les extrémités des murs étant rognées au centre des
            # parties communes (v2.30), la toiture du module couvre tout le mur.
            uids = set(unites_par_cle.get(cle, ()))
            for wid in wids:   # v2.25 : chaque COUCHE du mur est découpée
                for uid in uids:
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

    # --- 3c. Fenêtres de toit -------------------------------------------------
    # v2.26 : les fenêtres de toit sont posées sur l'élément de RÉFÉRENCE (la
    # couche COMPLEXE de la toiture), et des ouvertures équivalentes (baie
    # libre) sont créées dans les couches de revêtement (couverture et
    # sous-face). Chaque pente de l'export (toiture.pents[]) a un n° de module
    # (1-based) et un versant (nord/sud). Position mesurée le long du bas de
    # pente depuis le coin ouest ; v2.30 : ancre au BAS de la fenêtre (axe en x),
    # alignement par le bas de toutes les fenêtres d'un pent.
    pents = toit.get("pents") or []
    if pents and toit_par_uid_versant:
        skylights_data = []
        skylights_favs = []   # favori d'origine de chaque skylight (le repli peut vider item)
        trous_spec = []       # v2.39 : specs des trous, créés en phase 2 (anchorLevel)
        skylight_vus = set()  # v2.30 : anti-doublon (uid, versant, fenêtre)
        pent_vus = set()      # v2.32 : anti-doublon au niveau du pent (uid, versant)
        # v2.34 : favoris de skylights du gabarit — un favori inconnu (faute de
        # frappe, ex. « BARRAC-FENTOIT114 ») est retiré ITEM PAR ITEM avant envoi :
        # le repli par lot de tapir_cree recréerait TOUT le lot -> doublons.
        fav_noms_skylight = set()
        try:
            rep = bridge.tapir("GetFavoritesByType", {"elementType": "Skylight"})
            for f in rep.get("favorites", []):
                fav_noms_skylight.add(f.get("name") if isinstance(f, dict) else f)
        except Exception:
            pass
        for pent in pents:
            idx = pent.get("module")
            uid = None
            if isinstance(idx, int) and 1 <= idx <= len(unites):
                uid = unites[idx - 1].get("id", "m0")
            if pent.get("instId"):
                uid = pent["instId"]
            unite = next((u for u in unites if u.get("id", "m0") == uid), None)
            d_toits = toit_par_uid_versant.get(uid, {})
            if unite is None or not d_toits:
                continue
            versant = str(pent.get("versant") or "").lower()
            # v2.32 : un même pent n'est traité qu'une seule fois, même s'il
            # apparaît en double dans l'export (pas de fenêtre de toit en doublon)
            pent_key = (uid, versant)
            if pent_key in pent_vus:
                continue
            pent_vus.add(pent_key)
            dims_u = unite["dimensions"]
            l_u = float(dims_u["largeur"])
            bx = float(unite.get("x", 0.0))
            by = float(unite.get("y", 0.0))

            def toit_de(role):
                d = d_toits.get(role, {})
                return d.get(versant) or d.get(None) or next(iter(d.values()), None)

            owner = toit_de("complexe")   # élément de référence
            if owner is None:
                continue
            angle_v = angle_sud if versant == "sud" else angle_nord
            # v2.30 : RÉFÉRENCE = la fenêtre dans le COMPLEXE, avec ALIGNEMENT PAR
            # LE BAS : l'ancre est le bas de la fenêtre (axe de la fenêtre en x =
            # centre, y = rive/bas de pente de la ligne directrice), posé sur le plan
            # de la toiture (z = niveau de la couche à la rive). Toutes les fenêtres
            # d'un pent sont ainsi à la même hauteur, et les baies libres des
            # revêtements au même endroit (z dérivé de l'ancre complexe par le seul
            # écart vertical entre les plans des couches).
            H_u = float(dims_u.get("hauteur", 0.0))
            lvl_cplx = toit_niveau.get((uid, "complexe", versant))
            if lvl_cplx is None:
                lvl_cplx = toit_niveau.get((uid, "complexe", None), H_u)

            def ancre(role, x_exp, y_exp):
                """Anchor (x, y, z) — bas de la fenêtre (axe en x), z sur le plan
                de la couche role à la rive, dérivé de l'ancre de la fenêtre du
                complexe (référence)."""
                ap = tr((x_exp, y_exp))
                d = d_toits.get(role, {})
                vers = versant if versant in d else (None if None in d else next(iter(d), None))
                lvl = toit_niveau.get((uid, role, vers))
                if lvl is None:
                    lvl = toit_niveau.get((uid, role, None), lvl_cplx)
                ap["z"] = lvl_cplx + (lvl - lvl_cplx)   # plan de la couche, à la rive
                return ap

            for fen in pent.get("fenetres") or []:
                pr = float(fen.get("position", 0.0))
                w = float(fen.get("largeur", 0.0))
                h = float(fen.get("hauteur", 0.0))
                # v2.30 : anti-doublon (un même pent ne doit pas recréer la fenêtre)
                fen_key = (uid, versant, str(fen.get("id") or "%.3f:%.3f:%.3f" % (pr, w, h)))
                if fen_key in skylight_vus:
                    continue
                skylight_vus.add(fen_key)
                # alignement par le bas : ancre au bas de la fenêtre, sur la rive
                y_exp = by + l_u if versant == "sud" else by
                fv = str(fen.get("favori") or "").strip()
                x_exp = bx + pr + w / 2.0
                # v2.55 : position en hauteur sur le versant (distance au bas de
                # pente, mesurée le long du rampant) -> décalage en plan de
                # ph*cos(pente) vers le faîtage. Les trous des revêtements suivent
                # seuls : la phase 2 relit l'anchorLevel réel de chaque fenêtre.
                ph = float(fen.get("positionHauteur") or 0.0)
                if ph and versant in ("nord", "sud"):
                    dp = ph * math.cos(angle_v)
                    y_exp = (y_exp - dp) if versant == "sud" else (y_exp + dp)
                # v2.31 : RÉFÉRENCE = la position de la fenêtre dans le COMPLEXE
                # (axe de la fenêtre, bas de la fenêtre sur le plan de la toiture).
                # Les baies libres des revêtements reprennent EXACTEMENT cette ancre :
                # plus de décalage de hauteur entre la fenêtre et les trous.
                ap_ref = ancre("complexe", x_exp, y_exp)
                # fenêtre de toit sur le complexe (référence) : favori d'origine
                item = {"ownerId": owner,
                        "anchorPosition": dict(ap_ref),
                        "width": w, "height": h}
                if fv:
                    if fav_noms_skylight and fv not in fav_noms_skylight:
                        print(f"  ! Favori skylight « {fv} » introuvable dans le "
                              f"gabarit : fenêtre créée SANS favori (pas de doublon).")
                        fv = ""
                    else:
                        item["favoriteName"] = fv
                skylights_data.append(item)
                skylights_favs.append(fv)
                # v2.39 : les trous (baies libres des revêtements) ne sont pas
                # créés ici : on mémorise leur spec ; ils seront créés en phase 2
                # avec le anchorLevel réellement lu sur la fenêtre (l'ancre d'un
                # skylight est 2D : x, y — la hauteur passe par anchorLevel).
                trous_spec.append({"item": item, "owner": owner, "angle": angle_v,
                                   "versant": versant, "lvl_cplx": lvl_cplx,
                                   "roles": {"couverture": (toit_de("couverture"),
                                                           float(c_couv.get("epaisseur") or 0.0),
                                                           toit_niveau.get((uid, "couverture", versant)) or toit_niveau.get((uid, "couverture", None)) or 0.0),
                                             "inferieur": (toit_de("inferieur"), ep_inf,
                                                           toit_niveau.get((uid, "inferieur", versant)) or toit_niveau.get((uid, "inferieur", None)) or 0.0)},
                                   "x": ap_ref["x"], "y": ap_ref["y"],
                                   "w": w, "h": h, "H_u": H_u})
        # v2.39 : création EN DEUX PHASES + anti-doublon.
        # L'ancre d'un skylight est 2D (x, y) : la hauteur passe par anchorLevel
        # (fixMode "Vertical", relatif au niveau de la toiture propriétaire) —
        # le z d'anchorPosition est ignoré par Archicad (constaté en v2.38).
        # Phase 1 : fenêtres seules, puis lecture de leur anchorLevel réel.
        # Phase 2 : trous au même (x, y) que la fenêtre, avec
        # anchorLevel = anchorLevel_fenêtre - delta_niveau_couche
        # (niveau stocké d'une couche = H + delta ; delta = +ep_cplx pour la
        # couverture, -ep_inf pour la sous-face).
        def dedup_skylights(data, favs):
            out_d, out_f, vus = [], [], set()
            for item, fv in zip(data, favs):
                ap = item.get("anchorPosition") or {}
                cle = (str(item.get("ownerId")),
                       round(float(ap.get("x", 0.0)), 6),
                       round(float(ap.get("y", 0.0)), 6),
                       round(float(ap.get("z", 0.0)), 6),
                       round(float(item.get("width", 0.0)), 6),
                       round(float(item.get("height", 0.0)), 6))
                if cle in vus:
                    continue
                vus.add(cle)
                out_d.append(item)
                out_f.append(fv)
            return out_d, out_f

        def envoi_skylights(data, favs, etiquette):
            """Envoi direct (PAS de repli par lot : un favori inconnu ne doit
            jamais recréer tout le lot -> doublons). Repli item par item si un
            item est refusé. Retourne (data dédupliquée, favs, elems)."""
            data, favs = dedup_skylights(data, favs)
            if not data:
                return data, favs, []
            resp = None
            try:
                resp = bridge.tapir("CreateSkylights", {"skylightsData": data})
            except Exception as exc:
                if any("anchorLevel" in d for d in data):
                    for d in data:
                        d.pop("anchorLevel", None)
                        d.pop("fixMode", None)
                        d.pop("anchorPoint", None)
                    print(f"  ! anchorLevel/fixMode refusé par CreateSkylights ({exc}) : "
                          f"repli sans ces champs (z seul).")
                    try:
                        resp = bridge.tapir("CreateSkylights", {"skylightsData": data})
                    except Exception as exc2:
                        print(f"  ! CreateSkylights indisponible ({exc2}) : "
                              f"{etiquette} non placés.")
                        return data, favs, []
                else:
                    print(f"  ! CreateSkylights indisponible ({exc}) : "
                          f"{etiquette} non placés.")
                    return data, favs, []
            elems = list(resp.get("elements", [])) if isinstance(resp, dict) else []
            # repli ITEM PAR ITEM : seuls les items refusés (favori inconnu)
            # sont recréés, sans favori — jamais le lot entier.
            if elems and len(elems) == len(data):
                reprendre = []
                for i, e in enumerate(elems):
                    if isinstance(e, dict) and e.get("error") and data[i].get("favoriteName"):
                        it = dict(data[i])
                        it.pop("favoriteName", None)
                        reprendre.append((i, it))
                if reprendre:
                    try:
                        resp2 = bridge.tapir("CreateSkylights",
                                             {"skylightsData": [it for _, it in reprendre]})
                        e2 = resp2.get("elements", []) if isinstance(resp2, dict) else []
                        for (i, _), ne in zip(reprendre, e2):
                            elems[i] = ne
                            favs[i] = ""
                        print(f"  ! {len(reprendre)} skylight(s) recréé(s) sans favori "
                              f"(favori inconnu du gabarit).")
                    except Exception as exc2:
                        print(f"  ! Repli skylights sans favori impossible ({exc2}).")
            print(f"  {etiquette} : {len(data)} skylight(s) placé(s).")
            return data, favs, elems

        def set_anchor_level(eid, al):
            """Règle la ligne de référence (anchorLevel) d'un skylight — essaie
            plusieurs formes de payload/commandes Tapir, vérifie par relecture."""
            g = guid_de(eid) if isinstance(eid, dict) else str(eid)
            al = round(al, 6)
            candidats = [
                ("SetDetailsOfElements", {"elements": [{"elementId": eid, "details": {"anchorLevel": al}}]}),
                ("SetDetailsOfElements", {"elements": [{"elementId": eid}], "details": {"anchorLevel": al}}),
                ("SetDetailsOfElements", {"elements": [g], "details": {"anchorLevel": al}}),
                ("SetElementDetails", {"elementId": eid, "details": {"anchorLevel": al}}),
            ]
            for cmd, payload in candidats:
                try:
                    bridge.tapir(cmd, payload)
                    det = bridge.tapir("GetDetailsOfElements", {"elements": [{"elementId": eid}]})
                    dl = det.get("detailsOfElements", []) if isinstance(det, dict) else []
                    if dl:
                        lu = (dl[0].get("details") or {}).get("anchorLevel")
                        if lu is not None and abs(float(lu) - al) < 1e-3:
                            return True
                except Exception:
                    continue
            return False

        # --- phase 1 : fenêtres de toit (complexe) ---
        data_fen, skylights_favs, elems_fen = envoi_skylights(
            skylights_data, skylights_favs, "Fenêtres de toit sur le complexe")
        # lecture du anchorLevel réel de chaque fenêtre créée
        al_par_item = {}
        try:
            refs = [{"elementId": e["elementId"]} for e in elems_fen
                    if isinstance(e, dict) and e.get("elementId")]
            if refs and len(refs) == len(data_fen):
                det = bridge.tapir("GetDetailsOfElements", {"elements": refs})
                dl = det.get("detailsOfElements", []) if isinstance(det, dict) else []
                for it, d in zip(data_fen, dl):
                    dd = d.get("details") or {}
                    if dd.get("anchorLevel") is not None:
                        al_par_item[id(it)] = float(dd["anchorLevel"])
        except Exception as exc:
            print(f"  [diag] lecture anchorLevel impossible ({exc})")
        # --- phase 2 : trous dans les revêtements de toiture (v2.52) ---
        # On ne peut envoyer que x,y (anchorLevel non réglable sur Tapir 2.0.0).
        # Passe 1 : trous au même (x, y) que la fenêtre, sans favori (le favori
        # LUCARNEVIDE force fixMode=Horizontal). Lecture de leur anchorLevel.
        # Passe 2 : suppression + recréation avec y décalé pour que le TROU
        # (sa position en plan) tombe sur la fenêtre. Modèle mesuré (v2.49/v2.51) :
        #   pos_Y(trou) = anchor_y + B_role,  B_role = sin(p)cos(p)*(al_trou@fen - al_fen)
        # (résidu v2.51 = 0,2*B -> pente 1 ; le anchorLevel du trou ne joue pas)
        # d'où dy = -B = sin(p)cos(p)*(al_fen - al_trou).
        # (v2.50 alignait les anchorLevel : faux, déplacer y déplace le trou en plan.)
        trous_data, trous_favs, trous_meta = [], [], []
        for spec in trous_spec:
            for role_rev, (rev_id, ep_role, lvl_role) in spec["roles"].items():
                if rev_id is None or rev_id == spec["owner"]:
                    continue
                item_t = {"ownerId": rev_id,
                          "anchorPosition": {"x": spec["x"], "y": spec["y"],
                                             "z": lvl_role},
                          "width": spec["w"], "height": spec["h"]}
                trous_data.append(item_t)
                trous_favs.append("")
                trous_meta.append({"spec": spec, "lvl_role": lvl_role})
        trous_data, trous_favs, elems_trous = envoi_skylights(
            trous_data, trous_favs, "Trous (lucarnes vides) passe 1")
        if trous_data and elems_trous:
            al_trou = {}
            try:
                refs = [{"elementId": e["elementId"]} for e in elems_trous
                        if isinstance(e, dict) and e.get("elementId")]
                if refs and len(refs) == len(trous_data):
                    det = bridge.tapir("GetDetailsOfElements", {"elements": refs})
                    dl = det.get("detailsOfElements", []) if isinstance(det, dict) else []
                    for it, d in zip(trous_data, dl):
                        dd = d.get("details") or {}
                        if dd.get("anchorLevel") is not None:
                            al_trou[id(it)] = float(dd["anchorLevel"])
            except Exception as exc:
                print(f"  [diag] lecture anchorLevel trous impossible ({exc})")
            if al_trou:
                try:
                    bridge.tapir("DeleteElements",
                                 {"elements": [{"elementId": e["elementId"]} for e in elems_trous
                                               if isinstance(e, dict) and e.get("elementId")]})
                    for it, meta in zip(trous_data, trous_meta):
                        al_win = al_par_item.get(id(meta["spec"]["item"])) or 0.60
                        al_t = al_trou.get(id(it))
                        if al_t is not None:
                            p = meta["spec"]["angle"]
                            k = math.sin(p) * math.cos(p)
                            dy = k * (al_win - al_t)
                            it["anchorPosition"]["y"] = round(meta["spec"]["y"] + dy, 6)
                    _, trous_favs, elems_trous = envoi_skylights(
                        trous_data, trous_favs, "Trous passe 2, position alignée sur la fenêtre")
                except Exception as exc:
                    print(f"  ! Recréation des trous impossible ({exc}) : trous laissés en passe 1.")
        # favoris à appliquer (v2.28 : conserver width/height) + diagnostic
        tous_elems = list(elems_fen) + list(elems_trous)
        tous_favs = list(skylights_favs) + list(trous_favs)
        for fv, e in zip(tous_favs, tous_elems):
            if fv and isinstance(e, dict) and e.get("elementId") is not None:
                # v2.43 : on conserve AUSSI anchorLevel/anchorPosition lors de la
                # réapplication du favori en fin d'import — sinon le favori
                # LUCARNEVIDE/FENTOIT remet sa propre ligne de référence et les
                # fenêtres de toit se décalent à la toute fin du script.
                fav_a_appliquer.append((e["elementId"], fv,
                                        ("width", "height", "anchorLevel", "anchorPosition")))
        try:
            refs = [{"elementId": e["elementId"]} for e in tous_elems
                    if isinstance(e, dict) and e.get("elementId")]
            if refs:
                det = bridge.tapir("GetDetailsOfElements", {"elements": refs})
                dl = det.get("detailsOfElements", []) if isinstance(det, dict) else []
                print("  [diag v2.42] niveaux toitures :",
                      {str(k): round(v, 4) for k, v in toit_niveau.items()})
                print("  [diag v2.42] skylights lus (id, owner, anchor x/y, anchorLevel) :")
                for d in dl:
                    dd = d.get("details") or {}
                    ap = dd.get("anchorPosition") or {}
                    ow = dd.get("ownerElementId") or {}
                    g = ow.get("guid") if isinstance(ow, dict) else str(ow)
                    print("    id=%s owner=%s anchor=(%.4f, %.4f) anchorLevel=%.6f fixMode=%s"
                          % (d.get("id"), str(g)[-6:], ap.get("x", 0.0), ap.get("y", 0.0),
                             dd.get("anchorLevel") or 0.0, dd.get("fixMode")))
        except Exception as exc:
            print(f"  [diag v2.42] lecture impossible ({exc})")

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
    n_ok, n_err, n_baies = 0, 0, 0
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
                # v2.25 : axe de la couche MUR (et non du revêtement intérieur) :
                # le centerOffset est mesuré depuis le begCoordinate envoyé de la
                # couche mur (beg<->end échangés : l'ancien END de son axe).
                beg_l, end_l = mur_axes.get(cle) or (cseg["beg"], cseg["end"])
                beg_e, end_e = axes_envoi_pt(beg_l, end_l)
                if abs(beg_e[0] - end_e[0]) < 1e-9:         # mur vertical
                    centre = abs(cy - beg_e[1])
                else:                                       # mur horizontal
                    centre = abs(cx - beg_e[0])
                # v2.53 : allège (hauteur d'implantation depuis le bas du mur),
                # envoyée aussi aux baies libres des revêtements pour que le
                # trou suive la même hauteur que l'ouvrant.
                allege = float(ouverture.get("allege") or 0.0)
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
                if CHAMP_ALLEGE and allege:
                    item[CHAMP_ALLEGE] = allege
                    print(f"  Ouverture {ouverture.get('id', '?')} : allège {allege:.3f} m "
                          f"envoyée ({CHAMP_ALLEGE}) — favori appliqué après coup avec keepFields.")
                # v2.59 : favori envoyé à la création AVEC sillHeight quand allège
                # (les champs explicites priment sur le favori, comme pour les
                # skylights) ; n'est plus réappliqué après coup dans ce cas.
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
                    if favori_ouv and el.get("elementId") is not None and not (CHAMP_ALLEGE and allege):
                        fav_a_appliquer.append((el["elementId"], favori_ouv, None))
                except Exception as exc:
                    n_err += 1
                    print(f"  ! Ouverture {ouverture.get('id', '?')} non placée "
                          f"sur le mur {face_key} du module {uid} : {exc}")
                # v2.26 : ouvertures équivalentes (baie libre) dans les couches
                # de revêtement intérieur / extérieur du même mur. Le centerOffset
                # est mesuré depuis l'axe PROPRE du revêtement (qui peut être
                # rallongé aux extrémités) : la baie libre tombe ainsi à la même
                # position absolue que la fenêtre dans la couche mur.
                for role_rev in ("interieur", "exterieur"):
                    rev_id = (wall_role_ids.get(cle) or {}).get(role_rev)
                    if rev_id is None or rev_id == wall_id:
                        continue
                    rb, re_ = (wall_role_axes.get(cle) or {}).get(role_rev) or (beg_l, end_l)
                    rb_e, re_e = axes_envoi_pt(rb, re_)
                    if abs(rb_e[0] - re_e[0]) < 1e-9:      # mur vertical
                        centre_rev = abs(cy - rb_e[1])
                    else:                                  # mur horizontal
                        centre_rev = abs(cx - rb_e[0])
                    item_rev = {
                        "ownerWallId": rev_id,
                        "centerOffset": centre_rev,
                        "width": ouverture["largeur"],
                        "height": ouverture["hauteur"],
                        "refSide": True,
                    }
                    if CHAMP_ALLEGE and allege:
                        item_rev[CHAMP_ALLEGE] = allege
                    # v2.59 : BAIELIBRE envoyé à la création avec sillHeight (idem ouvrant)
                    if FAVORI_BAIE_LIBRE:
                        item_rev["favoriteName"] = FAVORI_BAIE_LIBRE
                    try:
                        resp_rev = bridge.tapir_cree("CreateWindows", {"windowsData": [item_rev]})
                        n_baies += 1
                        el_rev = (resp_rev.get("elements") or [{}])[0]
                        if (FAVORI_BAIE_LIBRE and el_rev.get("elementId") is not None
                                and not (CHAMP_ALLEGE and allege)):
                            fav_a_appliquer.append((el_rev["elementId"], FAVORI_BAIE_LIBRE, None))
                    except Exception as exc:
                        print(f"  ! Baie libre {ouverture.get('id', '?')} non placée "
                              f"dans le revêtement {role_rev} ({face_key}/{uid}) : {exc}")

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
    print(f"  - {len(walls_data)} couche(s) de mur ({len(canon)} mur(s) physique(s)) sur {len(unites)} module(s), "
          f"{len(slabs_data)} plancher(s), {len(roofs_data)} élément(s) de toiture")
    print(f"  - {n_ok} ouverture(s) placée(s) sur les éléments de référence, "
          f"{n_err} échec(s), {n_baies} baie(s) libre(s) dans les revêtements")
    print("Terminé. Vérifiez le résultat dans la fenêtre 3D.")


def main():
    parser = argparse.ArgumentParser(
        description="Importe un module Baracca (JSON du configurateur web) "
                    "dans le projet Archicad ouvert.")
    print("BARACCA-IMPORT v2.59 — Archicad 30 / Tapir >= 2.0 uniquement ; "
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
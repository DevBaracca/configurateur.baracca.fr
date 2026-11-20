import React, { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  bboxOf, dimsOf, epaisseurPlancher, toitureDefOf, formeDefOf, toitTypeOf,
  pente1Of, pente2Of, hauteurFaitageDm, deltaRiveDm, runFaitageDm, basPenteOf, penteOfPent, fenetresOfPent,
  couvListOf, couvIdOf, intListOf, intIdOf, plancherListOf, plancherIdOf, chantListOf, revIdOf,
  rgbHex, mixHex, SOL_SOUS_PLANCHER, toitVisOf,
  PLANCHER_DEPASSEMENT,
} from "./App.jsx";

/* Vue 3D en lecture seule du configurateur (Three.js) : on reconstruit la scène
   à chaque changement de configuration. Repère : plan (x, y) -> 3D (x, z), Y vers
   le haut ; le bâtiment est centré sur la bbox de l'ensemble des modules.
   Nord = -Z, Sud = +Z, Est = +X, Ouest = -X. */

const css = (rgb, fb) => `rgb(${rgb?.[0] ?? fb[0]},${rgb?.[1] ?? fb[1]},${rgb?.[2] ?? fb[2]})`;
const rad = (deg) => (deg * Math.PI) / 180;
const TEX_MUR = 2; // échelle réelle des textures murales : répétition tous les 2 m (comme la toiture)

/* Normale unitaire « vers le haut » d'un polygone de versant */
function upNormal(poly) {
  const n = new THREE.Vector3().subVectors(poly[1], poly[0]).cross(new THREE.Vector3().subVectors(poly[2], poly[0])).normalize();
  return n.y >= 0 ? n : n.negate();
}

/* Dalle de toiture : à partir des polygones de la face SUPÉRIEURE (Vector3),
   construit une dalle d'épaisseur th vers le bas. Par défaut la sous-face est
   décalée VERTICALEMENT (jupes verticales, pour suivre les murs en rive) ;
   si `bots` est fourni, on l'utilise comme sous-face explicite (ex. couverture
   posée exactement sur le dessus du complexe). */
function roofSlabGeometry(polys, th, bots) {
  const pos = [], uvs = [];
  const TEX = 2; // la texture se répète tous les 2 m (projection au sol)
  const tri = (a, b, c) => {
    pos.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
    uvs.push(a.x / TEX, a.z / TEX, b.x / TEX, b.z / TEX, c.x / TEX, c.z / TEX);
  };
  const g = new THREE.BufferGeometry();
  for (let pi = 0; pi < polys.length; pi++) {
    const poly = polys[pi];
    const n = poly.length;
    const bot = bots ? bots[pi] : poly.map((p) => new THREE.Vector3(p.x, p.y - th, p.z)); // dessous
    const g0 = pos.length / 3; // groupe 0 : dessus + jupes (chant)
    for (let i = 1; i < n - 1; i++) tri(poly[0], poly[i], poly[i + 1]); // dessus
    for (let i = 0; i < n; i++) { // jupes sur chaque arête
      const a = poly[i], b = poly[(i + 1) % n];
      const aB = bot[i], bB = bot[(i + 1) % n];
      tri(a, b, bB); tri(a, bB, aB);
    }
    const g1 = pos.length / 3; // groupe 1 : dessous (sous-face, matériau à part)
    for (let i = 1; i < n - 1; i++) tri(bot[0], bot[i + 1], bot[i]); // dessous (inversé)
    g.addGroup(g0, g1 - g0, 0);
    g.addGroup(g1, pos.length / 3 - g1, 1);
  }
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  g.computeVertexNormals();
  return g;
}

/* Construit la scène complète à partir de la configuration d et des catalogues env */
function buildScene(d, env) {
  const scene = new THREE.Scene();

  const insts = d.instances?.length
    ? d.instances
    : [{ id: "m0", x: 0, y: 0, moduleId: d.moduleId, murs: null }];
  const b = bboxOf(d, (i) => dimsOf(d, env, i));
  const cx = (b.minX + b.maxX) / 2, cz = (b.minY + b.maxY) / 2;

  const murDef = env.murs.find((m) => m.id === d.murType) || env.murs[0];
  const ep = +(murDef?.epaisseur ?? 0.14);
  const toitDef = toitureDefOf(d, env);
  const tt = toitTypeOf(d, env);
  const p1 = pente1Of(d), p2 = pente2Of(d);
  const epToit = +(toitDef.epaisseur ?? 0.30);
  const epToitV = epToit; // épaisseur réelle du complexe de toiture (définie dans le back-office) ; la sous-face reste à H
  const dep = Math.max(0, +(d.depassee ?? formeDefOf(d, env)?.depassee ?? epToit * 100) / 100);
  const epP = epaisseurPlancher(d, env.planchers);
  const plancherDef = env.planchers.find((p) => p.id === d.plancher) || env.planchers[0];

  // lumière
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8378, 1.0));
  const dir = new THREE.DirectionalLight(0xffffff, 1.8);
  dir.position.set(6, 12, 8);
  scene.add(dir);

  // sol + plancher (dépasse de 15,7 cm de la ligne directrice des murs)
  const sol = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.MeshLambertMaterial({ color: 0xf3f1ee }));
  sol.rotation.x = -Math.PI / 2;
  sol.position.y = -epP - SOL_SOUS_PLANCHER;
  scene.add(sol);
  const plancherMat = new THREE.MeshLambertMaterial({ color: 0xd6d3d1 });

  const wallMat = new THREE.MeshLambertMaterial({ color: new THREE.Color(css(murDef?.rgb, [140, 107, 89])) });
  const roofMat = new THREE.MeshLambertMaterial({ color: new THREE.Color(css(toitDef?.rgb, [120, 113, 108])), side: THREE.DoubleSide });
  const ouvMatPorte = new THREE.MeshLambertMaterial({ color: 0x7c2d12 });
  const ouvMatFen = new THREE.MeshLambertMaterial({ color: 0x0284c7 });
  const fenMat = new THREE.MeshLambertMaterial({ color: 0xbfdbfe });
  // charpente sélectionnée (épaisseur = section des poteaux/sablières)
  const charpenteDef = env.charpentes?.find((c) => c.id === d.charpente) || env.charpentes?.[0];
  const epC = +(charpenteDef?.epaisseur ?? 0.20);
  const charpMat = new THREE.MeshLambertMaterial({ color: new THREE.Color(css(charpenteDef?.rgb, [140, 107, 89])) });

  // textures des revêtements (catalogue « Extérieur » sur les murs, « Toiture » sur le toit)
  const textures = [];
  const textureFor = (url) => {
    const t = new THREE.TextureLoader().load(url);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping; // tuilage
    textures.push(t);
    return t;
  };
  if (charpenteDef?.image) { charpMat.map = textureFor(charpenteDef.image); charpMat.color.set(0xffffff); } // visuel charpente sur poteaux/sablières
  const surfItemOf = (inst, face) => env.facades.find((f) => f.id === revIdOf(env.facades, inst?.murs?.[face]?.surface, murDef?.surface));
  // revêtement INTÉRIEUR de la face (catalogue « Intérieur », sous-face des murs côté 3D)
  const intItemOf = (inst, face) => intListOf(env).find((f) => f.id === intIdOf(env, inst?.murs?.[face]?.surfaceInt, murDef?.interieur));
  const matWithMap = (url, base) => {
    const m = base.clone();
    m.map = textureFor(url);
    m.color.set(0xffffff);
    return m;
  };
  // matériau uni : couleur du revêtement s'il en a une, sinon la couleur de repli
  const matCouleur = (base, rgb, fb) => {
    const m = base.clone();
    m.color = new THREE.Color(css(rgb, fb));
    return m;
  };
  const couvItemOf = (inst, versant) => {
    const vis = dimsOf(d, env, inst).visibilite;
    if (vis && vis.couverture === false) return null; // couverture masquée pour ce module
    const cid = couvIdOf(env, d.surfacesToiture?.[inst.id]?.[versant], toitDef?.couverture ?? toitDef?.surface);
    return couvListOf(env).find((c) => c.id === cid) || null;
  };
  // épaisseur réelle de la couche de couverture d'un pent (catalogue « Toiture »)
  const epCouvVOf = (inst, versant) => Math.max(0.02, +(couvItemOf(inst, versant)?.epaisseur ?? epToit / 2));
  // complexe de toiture : chant/dessus = couleur du complexe (back-office) ;
  // sous-face = revêtement INFÉRIEUR (catalogue « Intérieur » de la toiture) — image
  // si visuel, sinon sa couleur, sinon la couleur du toit
  const intToitItem = intListOf(env).find((f) => f.id === intIdOf(env, null, toitDef?.interieur));
  const cplxEdgeMat = matCouleur(roofMat, toitDef?.rgb, [120, 113, 108]);
  const sousFaceMat = intToitItem?.image
    ? matWithMap(intToitItem.image, roofMat)
    : matCouleur(roofMat, intToitItem?.rgb, toitDef?.rgb || [120, 113, 108]);

  let maxTop = 0;
  const postSeen = new Set(); // dédoublonne les poteaux d'angle entre modules accolés

  // Débords effectifs par module et par côté : quand deux modules sont accolés
  // (espacés de l'épaisseur du mur commun), le débord est supprimé sur le côté
  // commun — que ce soit un côté pignon (est/ouest) ou une façade nord/sud.
  // Le module amont recouvre le mur commun (débord = épaisseur du mur), l'autre
  // démarre à sa ligne directrice : les deux rives de toit se rejoignent exactement.
  const exDef = ep + dep;
  const dimsList = insts.map((inst) => ({ inst, dm: dimsOf(d, env, inst) }));
  const over = {};
  const shared = {}; // côtés communs avec un voisin (pour le plancher)
  const jointMur = {}; // côté commun : true si un mur occupe le joint (propre ou voisin), false si charpente des deux côtés, null si pas de joint
  const jointOver = {}; // débord de rive AU JOINT (m) : côté commun nord/sud = position de la noue ; est/ouest = ep/2
  for (const { inst } of dimsList) {
    over[inst.id] = { nord: exDef, sud: exDef, est: exDef, ouest: exDef };
    shared[inst.id] = { nord: false, sud: false, est: false, ouest: false };
    jointMur[inst.id] = { nord: null, sud: null, est: null, ouest: null };
    jointOver[inst.id] = { nord: 0, sud: 0, est: 0, ouest: 0 };
  }
  // Mur commun entre deux modules accolés (écart = épaisseur du mur, murs actifs
  // des deux côtés) : dessiné UNE SEULE FOIS, par le module propriétaire de
  // l'arête (le premier dans insts, comme eachEdge en plan/export) — sinon les
  // deux murs se superposent. wallMerge : ouvertures du voisin à reporter sur
  // le mur du propriétaire (décalées dans son repère).
  const instIdx = {};
  insts.forEach((i, k) => { instIdx[i.id] = k; });
  const wallSkip = {};
  const wallMerge = {};
  for (const { inst } of dimsList) wallSkip[inst.id] = { nord: false, sud: false, est: false, ouest: false };
  const markJointWall = (A, faceA, B, faceB, gap) => {
    const aActif = A.inst.murs?.[faceA]?.actif !== false, bActif = B.inst.murs?.[faceB]?.actif !== false;
    const aVis = A.dm.visibilite?.murs !== false, bVis = B.dm.visibilite?.murs !== false;
    if (!(aActif && bActif && aVis && bVis)) return; // charpente d'un côté : le mur de l'autre suffit
    if (gap > ep + 0.02) return; // murs non confondus (écart > épaisseur du mur) : on garde les deux
    const ownFirst = instIdx[A.inst.id] < instIdx[B.inst.id];
    const owner = ownFirst ? A : B, ownFace = ownFirst ? faceA : faceB;
    const loser = ownFirst ? B : A, loseFace = ownFirst ? faceB : faceA;
    wallSkip[loser.inst.id][loseFace] = true;
    const horiz = ownFace === "nord" || ownFace === "sud";
    wallMerge[owner.inst.id + ":" + ownFace] = { nb: loser.inst, nface: loseFace, off: horiz ? loser.inst.x - owner.inst.x : loser.inst.y - owner.inst.y };
  };
  // Anti-doublon des coins : un carré de coin (ep x ep) n'est prolongé qu'une seule
  // fois — la première prolongation arrivée le couvre (avec le revêtement sur sa
  // tranche), les suivantes sont annulées ou réduites pour se rejoindre à l'axe du
  // joint sans chevauchement. Sinon deux murs prolongés se superposent dans le même
  // carré (angle de murs, jonction entre deux modules) et le revêtement apparaît en double.
  const r100 = (v) => Math.round(v * 100) / 100;
  const cornerClaim = new Map(); // clé du carré -> { xW, xE, zN, zS } : couverture déjà prise par côté
  const claimCorner = (key, axis, side, p) => {
    if (p <= 1e-6) return 0;
    let c = cornerClaim.get(key);
    if (!c) { c = { xW: 0, xE: 0, zN: 0, zS: 0 }; cornerClaim.set(key, c); }
    // déjà couvert par un mur perpendiculaire (autre axe) ou du même côté : rien
    if (axis === "x" ? (c.zN + c.zS > 0) : (c.xW + c.xE > 0)) return 0;
    if (c[axis + side] > 0) return 0;
    // même axe, côté opposé : on se rejoint à l'axe du joint sans chevaucher
    const opp = axis === "x" ? c[side === "W" ? "xE" : "xW"] : c[side === "N" ? "zS" : "zN"];
    const allowed = Math.min(p, Math.max(0, ep - opp));
    if (allowed <= 1e-6) return 0;
    c[axis + side] += allowed;
    return allowed;
  };
  // Noue au joint nord/sud entre deux modules : point où les deux plans de versants
  // (sud du module nord, pente p2, cote Hr+δ2 ; nord du module sud, pente p1, cote
  // Hr+δ1) se coupent au-dessus du mur commun. d = distance depuis la ligne directrice
  // sud du module nord ; pentes égales -> d = gap/2 (milieu du mur, comme avant).
  const t1g = Math.tan(rad(p1)), t2g = Math.tan(rad(p2));
  const dl1 = deltaRiveDm(p1, p2, p1, epToitV), dl2 = deltaRiveDm(p1, p2, p2, epToitV);
  // pas de clamp à [0, gap] : l'arête de jonction peut tomber légèrement au-delà du
  // mur commun (un versant recouvre alors tout le joint) — jamais de marche verticale
  const noueSN = (gap) => Math.min(Math.max((dl2 - dl1 + gap * t1g) / (t1g + t2g), -gap), 2 * gap);
  const epsC = 1e-6;
  // Les positions des modules sont enregistrées avec l'épaisseur de mur en vigueur à
  // l'ajout : si l'isolation change ensuite, l'écart réel entre lignes directrices
  // diffère de l'épaisseur courante. On détecte donc les jonctions par l'écart
  // (0 < écart <= épaisseur max du catalogue + marge), pas par égalité à ep.
  const epMax = Math.max(0.2, ...env.murs.map((m) => +m.epaisseur || 0)) + 0.05;
  const overlap = (a0, a1, b0, b1) => a0 < b1 - epsC && b0 < a1 - epsC;
  for (const A of dimsList) {
    for (const B of dimsList) {
      if (A === B) continue;
      // pas de règles de débord de toiture entre un module et un module sans toit
      // visible (complexe de toiture ET couverture décochés dans le back-office)
      if (!toitVisOf(A.dm.visibilite) || !toitVisOf(B.dm.visibilite)) continue;
      const ovY = overlap(A.inst.y, A.inst.y + A.dm.largeur, B.inst.y, B.inst.y + B.dm.largeur);
      const ovX = overlap(A.inst.x, A.inst.x + A.dm.longueur, B.inst.x, B.inst.x + B.dm.longueur);
      const gapE = B.inst.x - (A.inst.x + A.dm.longueur); // écart lignes directrices, côté est de A
      const gapW = A.inst.x - (B.inst.x + B.dm.longueur);
      const gapS = B.inst.y - (A.inst.y + A.dm.largeur);
      const gapN = A.inst.y - (B.inst.y + B.dm.largeur);
      if (gapE > epsC && gapE <= epMax && ovY) { over[A.inst.id].est = ep; over[B.inst.id].ouest = 0; shared[A.inst.id].est = shared[B.inst.id].ouest = true; jointOver[A.inst.id].est = ep / 2; jointOver[B.inst.id].ouest = ep / 2; const jm = (A.inst.murs?.est?.actif !== false) || (B.inst.murs?.ouest?.actif !== false); jointMur[A.inst.id].est = jm; jointMur[B.inst.id].ouest = jm; markJointWall(A, "est", B, "ouest", gapE); }
      if (gapW > epsC && gapW <= epMax && ovY) { over[B.inst.id].est = ep; over[A.inst.id].ouest = 0; shared[B.inst.id].est = shared[A.inst.id].ouest = true; jointOver[B.inst.id].est = ep / 2; jointOver[A.inst.id].ouest = ep / 2; const jm = (B.inst.murs?.est?.actif !== false) || (A.inst.murs?.ouest?.actif !== false); jointMur[B.inst.id].est = jm; jointMur[A.inst.id].ouest = jm; markJointWall(B, "est", A, "ouest", gapW); }
      // Jonction sud/nord : noue — chaque versant est prolongé jusqu'au point où les
      // deux plans de couverture se coupent au-dessus du mur commun (pas forcément le
      // milieu en shed) -> les toitures se rejoignent sans marche, en bas de pente aussi
      if (gapS > epsC && gapS <= epMax && ovX) { const d = noueSN(gapS); over[A.inst.id].sud = d; over[B.inst.id].nord = gapS - d; jointOver[A.inst.id].sud = d; jointOver[B.inst.id].nord = gapS - d; shared[A.inst.id].sud = shared[B.inst.id].nord = true; const jm = (A.inst.murs?.sud?.actif !== false) || (B.inst.murs?.nord?.actif !== false); jointMur[A.inst.id].sud = jm; jointMur[B.inst.id].nord = jm; markJointWall(A, "sud", B, "nord", gapS); }
      if (gapN > epsC && gapN <= epMax && ovX) { const d = noueSN(gapN); over[B.inst.id].sud = d; over[A.inst.id].nord = gapN - d; jointOver[B.inst.id].sud = d; jointOver[A.inst.id].nord = gapN - d; shared[B.inst.id].sud = shared[A.inst.id].nord = true; const jm = (B.inst.murs?.sud?.actif !== false) || (A.inst.murs?.nord?.actif !== false); jointMur[B.inst.id].sud = jm; jointMur[A.inst.id].nord = jm; markJointWall(B, "sud", A, "nord", gapN); }
    }
  }
  // En monopente, le nord est le haut du toit (mur nord montant jusqu'au toit) :
  // on ne supprime JAMAIS le débord au nord, même sur un côté commun
  if (tt === "monopente") for (const k of Object.keys(over)) over[k].nord = exDef;

  for (const inst of insts) {
    const dm = dimsOf(d, env, inst);
    const X0 = inst.x - cx, Z0 = inst.y - cz;       // coin haut-gauche (nord-ouest) en 3D
    const X1 = X0 + dm.longueur, Z1 = Z0 + dm.largeur;
    const H = dm.hauteur;

    // empreinte du toit : débord par défaut, supprimé sur les côtés communs (mur seul)
    const ov = over[inst.id] || { nord: exDef, sud: exDef, est: exDef, ouest: exDef };
    const rx0 = X0 - ov.ouest, rx1 = X1 + ov.est, rz0 = Z0 - ov.nord, rz1 = Z1 + ov.sud;

    // plancher sous le module UNIQUEMENT (pas dans la zone vide d'un L) : la dalle
    // dépasse de 15,7 cm (PLANCHER_DEPASSEMENT) au-delà de la ligne directrice des murs ;
    // côté commun à un module accolé : jonction au milieu du mur commun (ep/2)
    // visibilité des constituants (définie dans le back-office, partie « Modules »)
    const vis = dm.visibilite || { murs: true, complexe_toiture: true, plancher: true, couverture: true };
    const sh0 = shared[inst.id] || {};
    const pN = sh0.nord ? ep / 2 : PLANCHER_DEPASSEMENT, pS = sh0.sud ? ep / 2 : PLANCHER_DEPASSEMENT;
    const pE = sh0.est ? ep / 2 : PLANCHER_DEPASSEMENT, pW = sh0.ouest ? ep / 2 : PLANCHER_DEPASSEMENT;
    if (vis.plancher) {
      // dessus du plancher = revêtement « Plancher » choisi ; chants (bords) =
      // même revêtement par défaut (étoile de l'onglet « Plancher »)
      const hautItem = plancherListOf(env).find((f) => f.id === plancherIdOf(env, d.revetementPlancher, plancherDef?.revetement_sup));
      const chantItem = chantListOf(env).find((f) => f.id === revIdOf(chantListOf(env), d.revetementChantPlancher, plancherDef?.revetement_chants ?? murDef?.surface));
      // sans visuel : couleur du revêtement, sinon gris clair
      const matTop = hautItem?.image ? matWithMap(hautItem.image, plancherMat) : matCouleur(plancherMat, hautItem?.rgb, [214, 211, 209]);
      const matSide = chantItem?.image ? matWithMap(chantItem.image, plancherMat) : matCouleur(plancherMat, chantItem?.rgb, [214, 211, 209]);
      const Lx = dm.longueur + pW + pE, Lz = dm.largeur + pN + pS;
      // BoxGeometry : [+x, -x, +y(dessus), -y, +z, -z] — côtés = dalle nue,
      // le dessus reçoit le revêtement supérieur choisi
      const pl = new THREE.Mesh(
        new THREE.BoxGeometry(Lx, epP, Lz),
        [plancherMat, plancherMat, matTop, plancherMat, plancherMat, plancherMat]
      );
      pl.position.set(X0 + dm.longueur / 2, -epP / 2, Z0 + dm.largeur / 2);
      scene.add(pl);
      // revêtement des chants (bords) : un élément rajouté sur chaque face du
      // plancher, d'épaisseur = épaisseur du revêtement de chant choisi ;
      // PAS de bande sur un côté commun à un module accolé (sh0)
      const epRev = Math.max(0, +(chantItem?.epaisseur ?? 0));
      if (epRev > 0) {
        const cx = X0 + dm.longueur / 2, cz = Z0 + dm.largeur / 2;
        const bandes = [];
        if (!sh0.nord) bandes.push({ w: Lx, d: epRev, x: cx, z: Z0 - pN - epRev / 2 });            // nord
        if (!sh0.sud) bandes.push({ w: Lx, d: epRev, x: cx, z: Z1 + pS + epRev / 2 });              // sud
        if (!sh0.ouest) bandes.push({ w: epRev, d: Lz - 2 * epRev, x: X0 - pW - epRev / 2, z: cz }); // ouest
        if (!sh0.est) bandes.push({ w: epRev, d: Lz - 2 * epRev, x: X1 + pE + epRev / 2, z: cz });   // est
        for (const b of bandes) {
          const bande = new THREE.Mesh(new THREE.BoxGeometry(b.w, epP, b.d), matSide);
          bande.position.set(b.x, -epP / 2, b.z);
          scene.add(bande);
        }
      }
    }
    const t1 = Math.tan(rad(p1)), t2 = Math.tan(rad(p2));
    const Hr = H + epToitV; // dessus de la dalle au droit de la ligne directrice (sous-face à H = dessus des murs)
    // Hauteurs de toit calculées sur la LIGNE DIRECTRICE, indépendamment des débords :
    // deux modules de mêmes dimensions ont exactement le même faîtage / bas de pente.
    let hF = 0, zr = (Z0 + Z1) / 2;
    // shed (deux pentes différentes) : chaque versant est remonté de δ_i =
    // ep·(1/cos p_i − 1/cos p_min) pour que les sous-faces du complexe rencontrent
    // les murs intérieurs AU MÊME NIVEAU (parallélisme conservé, simple translation)
    const dN = deltaRiveDm(p1, p2, p1, epToitV), dS = deltaRiveDm(p1, p2, p2, epToitV);
    if (tt === "monopente") hF = t1 * (Z1 - Z0);
    else if (tt === "deuxpentes") {
      hF = hauteurFaitageDm(dm, p1, p2, tt, epToitV);
      zr = Z0 + runFaitageDm(dm, p1, p2, tt, epToitV);
    } else if (tt === "quatrepentes") { hF = t1 * (Z1 - Z0) / 2; zr = (Z0 + Z1) / 2; }

    /* ----- toiture : face supérieure par versant -----
       Le plan de chaque versant passe par la LIGNE DIRECTRICE à hauteur Hr ; le débord
       prolonge la pente au-delà (la rive extérieure descend sous Hr côté gouttière). */
    const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
    // Polygones de la face supérieure par versant, pour un contour donné :
    // (rx0,rx1,rz0,rz1) avec les débords = couverture ; (X0,X1,Z0,Z1) avec ov nul
    // = empreinte seule (ligne directrice) = complexe de toiture.
    const polysOf = (ox0, ox1, oz0, oz1, ovv) => {
      if (tt === "monopente") {
        // versant sud : rive basse au sud, haut du toit au nord ; pente constante p1
        const yN = Hr + (Z1 - oz0) * t1, yS = Hr + (Z1 - oz1) * t1;
        return [{ versant: "sud", poly: [V3(ox0, yN, oz0), V3(ox1, yN, oz0), V3(ox1, yS, oz1), V3(ox0, yS, oz1)] }];
      }
      if (tt === "deuxpentes") {
        const yN = Hr + dN - ovv.nord * t1, yS = Hr + dS - ovv.sud * t2; // rives remontées de δ + débords qui prolongent la pente
        return [
          { versant: "nord", poly: [V3(ox0, yN, oz0), V3(ox1, yN, oz0), V3(ox1, Hr + hF, zr), V3(ox0, Hr + hF, zr)] },
          { versant: "sud", poly: [V3(ox0, yS, oz1), V3(ox1, yS, oz1), V3(ox1, Hr + hF, zr), V3(ox0, Hr + hF, zr)] },
        ];
      }
      if (tt === "quatrepentes") {
        const run = (oz1 - oz0) / 2;
        const yN = Hr - ovv.nord * t1, yS = Hr - ovv.sud * t1, yE = Hr - ovv.est * t1, yW = Hr - ovv.ouest * t1;
        return [
          { versant: "nord", poly: [V3(ox0, yN, oz0), V3(ox1, yN, oz0), V3(ox1 - run, Hr + hF, zr), V3(ox0 + run, Hr + hF, zr)] },
          { versant: "sud", poly: [V3(ox0, yS, oz1), V3(ox1, yS, oz1), V3(ox1 - run, Hr + hF, zr), V3(ox0 + run, Hr + hF, zr)] },
          { versant: "est", poly: [V3(ox1, yE, oz0), V3(ox1, yE, oz1), V3(ox1 - run, Hr + hF, zr)] },
          { versant: "ouest", poly: [V3(ox0, yW, oz0), V3(ox0, yW, oz1), V3(ox0 + run, Hr + hF, zr)] },
        ];
      }
      return null;
    };
    const roofPolysV = polysOf(rx0, rx1, rz0, rz1, ov); // couverture : empreinte AVEC débords
    // complexe : empreinte sur la LIGNE DIRECTRICE (face INTÉRIEURE des murs, sans
    // débord), prolongée de ep/2 sur les côtés communs à un module accolé -> les deux
    // complexes se rejoignent à l'AXE du joint (charpente centrale comprise), comme
    // les murs et comme à l'export Archicad ; la rive verticale descend contre le mur
    // en intérieur aux vrais bords (X0/X1/Z0/Z1), la pente = celle de la couverture
    const jO = jointOver[inst.id] || { nord: 0, sud: 0, est: 0, ouest: 0 };
    const cx0 = X0 - jO.ouest, cx1 = X1 + jO.est;
    const cz0 = Z0 - jO.nord, cz1 = Z1 + jO.sud;
    // le complexe prolonge AUSSI sa pente jusqu'à la noue du joint (ovv = jO) :
    // couverture et complexe se rejoignent au même point, sans marche en bas de pente
    const cplxPolysV = polysOf(cx0, cx1, cz0, cz1, jO);
    const roofPolys = roofPolysV ? roofPolysV.map((r) => r.poly) : null;
    if (roofPolys) for (const poly of roofPolys) for (const p of poly) maxTop = Math.max(maxTop, p.y);

    /* ----- plans de coupe = surface de la toiture, par versant -----
       Les murs sont construits en pleine hauteur puis « coupés » par la toiture :
       ils montent jusqu'à la toiture (1 cm sous la surface pour éviter le
       z-fighting avec la dalle) — plus de vide en haut de mur sous la couverture. */
    const clipPlanes = (tt === "terrasse" || !toitVisOf(vis))
      ? [new THREE.Plane(new THREE.Vector3(0, -1, 0), H)] // terrasse ou pas de toit : murs à H
      : roofPolys.map((poly) => {
          const q = poly.map((p) => new THREE.Vector3(p.x, p.y - 0.01, p.z)); // surface du toit, 1 cm en dessous
          const n = new THREE.Vector3().subVectors(q[1], q[0]).cross(new THREE.Vector3().subVectors(q[2], q[0])).normalize();
          if (n.y > 0) n.negate(); // normale vers le bas : on garde le côté SOUS la dalle
          return new THREE.Plane(n, -n.dot(q[0]));
        });
    const wallMatI = wallMat.clone();
    wallMatI.clippingPlanes = clipPlanes;
    const yMax = H + hF + epToitV + 0.5; // murs construits en pleine hauteur, au-dessus du toit

    /* ----- murs : un segment plein par portion entre ouvertures (+ linteau) ----- */
    for (const face of (vis.murs ? ["nord", "est", "sud", "ouest"] : [])) {
      const f = inst.murs?.[face] ?? { actif: true, ouvertures: [] };
      if (!f.actif) continue; // charpente : pas de mur
      if (wallSkip[inst.id]?.[face]) continue; // mur commun : dessiné une seule fois, par le module propriétaire de l'arête
      // revêtements de cette face : EXTÉRIEUR (face externe du mur) et INTÉRIEUR (face interne)
      const wItem = surfItemOf(inst, face);
      const iItem = intItemOf(inst, face);
      const wImg = wItem?.image || "";
      const iImg = iItem?.image || "";
      const matSide = wallMatI; // dessus/dessous/petits côtés : couleur pleine
      // sans visuel : couleur du revêtement, sinon celle du mur
      const matOuter = wImg ? matWithMap(wImg, wallMatI) : matCouleur(wallMatI, wItem?.rgb, murDef?.rgb || [140, 107, 89]);
      const innerBase = wallMatI.clone();
      innerBase.color = new THREE.Color(rgbHex(iItem?.rgb ?? murDef?.rgb)); // face intérieure : couleur exacte du revêtement intérieur
      const matInner = iImg ? matWithMap(iImg, wallMatI) : innerBase;
      // BoxGeometry : matériaux dans l'ordre [+x, -x, +y, -y, +z, -z]
      const mats = face === "nord" ? [matSide, matSide, matSide, matSide, matInner, matOuter]
        : face === "sud" ? [matSide, matSide, matSide, matSide, matOuter, matInner]
        : face === "ouest" ? [matInner, matOuter, matSide, matSide, matSide, matSide]
        : [matOuter, matInner, matSide, matSide, matSide, matSide];
      const Lface = face === "nord" || face === "sud" ? dm.longueur : dm.largeur;
      // mur commun : les ouvertures du module voisin (côté non dessiné) sont
      // reportées sur ce mur, décalées dans le repère de ce module
      const wmerge = wallMerge[inst.id + ":" + face];
      const extra = wmerge
        ? (wmerge.nb.murs?.[wmerge.nface]?.ouvertures || [])
            .map((o) => ({ ...o, position: o.position + wmerge.off }))
            .filter((o) => o.position + o.largeur > 1e-6 && o.position < Lface - 1e-6)
        : [];
      const ops = [...(f.ouvertures || []), ...extra].sort((a, c) => a.position - c.position);
      const segs = [];
      let cursor = 0;
      for (const o of ops) {
        const a0 = o.allege ?? 0; // allège : partie pleine sous l'ouverture
        if (o.position > cursor + 1e-6) segs.push([cursor, o.position, 0, yMax]);
        if (a0 > 1e-6) segs.push([o.position, o.position + o.largeur, 0, a0]); // allège sous l'ouverture
        if (a0 + o.hauteur < yMax - 1e-6) segs.push([o.position, o.position + o.largeur, a0 + o.hauteur, yMax]); // linteau au-dessus
        cursor = Math.max(cursor, o.position + o.largeur);
      }
      if (cursor < Lface - 1e-6) segs.push([cursor, Lface, 0, yMax]);
      // jonction des angles : les murs prolongés de l'épaisseur dans les coins couvrent
      // les carrés d'angle — seulement si le côté perpendiculaire est un mur ; sinon
      // c'est le poteau de charpente qui occupe le coin (il ne doit pas être recouvert).
      // Un coin prolongé (deux murs en angle) porte le revêtement EXTÉRIEUR sur sa tranche,
      // pour que le revêtement soit continu à l'angle au lieu de la couleur par défaut.
      // Charpente MAIS module accolé de l'autre côté du joint -> prolongation de ep/2 :
      // le mur rejoint l'AXE de la charpente (le voisin prolonge l'autre moitié), comme
      // à l'export Archicad. S'applique aux 4 faces (pignons est/ouest compris).
      if (segs.length) {
        const jm = jointMur[inst.id] || {};
        let pW = inst.murs?.ouest?.actif !== false ? ep : (sh0.ouest ? (jm.ouest === true ? ep : ep / 2) : 0);
        let pE = inst.murs?.est?.actif !== false ? ep : (sh0.est ? (jm.est === true ? ep : ep / 2) : 0);
        let pN = inst.murs?.nord?.actif !== false ? ep : (sh0.nord ? (jm.nord === true ? ep : ep / 2) : 0);
        let pS = inst.murs?.sud?.actif !== false ? ep : (sh0.sud ? (jm.sud === true ? ep : ep / 2) : 0);
        // chaque carré de coin n'est prolongé qu'une fois (voir claimCorner)
        if (face === "nord" || face === "sud") {
          const zc = face === "nord" ? Z0 - ep : Z1;
          pW = claimCorner(`c${r100(X0 - ep)},${r100(zc)}`, "x", "E", pW);
          pE = claimCorner(`c${r100(X1)},${r100(zc)}`, "x", "W", pE);
          if (pW > 0) { segs[0][0] -= pW; segs[0][4] = true; } // coin ouest, tranche -x (index 1)
          if (pE > 0) { segs[segs.length - 1][1] += pE; segs[segs.length - 1][5] = true; } // coin est, tranche +x (index 0)
        } else {
          const xc = face === "ouest" ? X0 - ep : X1;
          pN = claimCorner(`c${r100(xc)},${r100(Z0 - ep)}`, "z", "S", pN);
          pS = claimCorner(`c${r100(xc)},${r100(Z1)}`, "z", "N", pS);
          if (pN > 0) { segs[0][0] -= pN; segs[0][6] = true; } // coin nord, tranche -z (index 5)
          if (pS > 0) { segs[segs.length - 1][1] += pS; segs[segs.length - 1][7] = true; } // coin sud, tranche +z (index 4)
        }
      }

      for (const [u0, u1, y0, y1, coinO, coinE, coinN, coinS] of segs) {
        const wSeg = u1 - u0, hSeg = y1 - y0;
        if (wSeg <= 1e-6 || hSeg <= 1e-6) continue;
        // BoxGeometry : [+x, -x, +y, -y, +z, -z] — murs nord/sud : tranche ouest = -x (1), est = +x (0) ;
        // murs est/ouest : tranche nord = -z (5), sud = +z (4). Coin prolongé -> revêtement EXTÉRIEUR.
        const matsSeg = (face === "nord" || face === "sud")
          ? ((coinO || coinE) ? mats.map((m, k) => ((k === 1 && coinO) || (k === 0 && coinE) ? matOuter : m)) : mats)
          : ((coinN || coinS) ? mats.map((m, k) => ((k === 5 && coinN) || (k === 4 && coinS) ? matOuter : m)) : mats);
        let mesh;
        if (face === "nord") mesh = new THREE.Mesh(new THREE.BoxGeometry(wSeg, hSeg, ep), matsSeg),
          mesh.position.set(X0 + (u0 + u1) / 2, (y0 + y1) / 2, Z0 - ep / 2);
        else if (face === "sud") mesh = new THREE.Mesh(new THREE.BoxGeometry(wSeg, hSeg, ep), matsSeg),
          mesh.position.set(X0 + (u0 + u1) / 2, (y0 + y1) / 2, Z1 + ep / 2);
        else if (face === "ouest") mesh = new THREE.Mesh(new THREE.BoxGeometry(ep, hSeg, wSeg), matsSeg),
          mesh.position.set(X0 - ep / 2, (y0 + y1) / 2, Z0 + (u0 + u1) / 2);
        else mesh = new THREE.Mesh(new THREE.BoxGeometry(ep, hSeg, wSeg), matsSeg),
          mesh.position.set(X1 + ep / 2, (y0 + y1) / 2, Z0 + (u0 + u1) / 2);
        // Tranche d'un coin prolongé : UV à l'échelle réelle (texture répétée tous les
        // 2 m selon les coordonnées monde, comme la toiture) — sinon les UV 0..1 de la
        // BoxGeometry écrasent l'image sur la largeur de la tranche (ep) et la déforment.
        if (coinO || coinE || coinN || coinS) {
          const pos = mesh.geometry.attributes.position, uv = mesh.geometry.attributes.uv;
          const mx = mesh.position.x, my = mesh.position.y, mz = mesh.position.z;
          // BoxGeometry : faces dans l'ordre [+x, -x, +y, -y, +z, -z], 4 sommets chacune
          const tranches = face === "nord" || face === "sud"
            ? [...(coinO ? [1] : []), ...(coinE ? [0] : [])]   // tranches -x / +x
            : [...(coinN ? [5] : []), ...(coinS ? [4] : [])];  // tranches -z / +z
          for (const fi of tranches) {
            for (let i = fi * 4; i < fi * 4 + 4; i++) {
              const wx = pos.getX(i) + mx, wy = pos.getY(i) + my, wz = pos.getZ(i) + mz;
              if (face === "nord" || face === "sud") uv.setXY(i, wz / TEX_MUR, wy / TEX_MUR);
              else uv.setXY(i, wx / TEX_MUR, wy / TEX_MUR);
            }
          }
        }
        scene.add(mesh);
      }

      // ouvertures : panneau sombre posé sur la face extérieure du mur, sur l'allège
      for (const o of ops) {
        const m = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), o.type === "porte" ? ouvMatPorte : ouvMatFen);
        const yOuv = (o.allege ?? 0) + o.hauteur / 2;
        if (face === "nord") { m.scale.set(o.largeur, o.hauteur, 0.05); m.position.set(X0 + o.position + o.largeur / 2, yOuv, Z0 - ep - 0.02); }
        else if (face === "sud") { m.scale.set(o.largeur, o.hauteur, 0.05); m.position.set(X0 + o.position + o.largeur / 2, yOuv, Z1 + ep + 0.02); }
        else if (face === "ouest") { m.scale.set(0.05, o.hauteur, o.largeur); m.position.set(X0 - ep - 0.02, yOuv, Z0 + o.position + o.largeur / 2); }
        else { m.scale.set(0.05, o.hauteur, o.largeur); m.position.set(X1 + ep + 0.02, yOuv, Z0 + o.position + o.largeur / 2); }
        scene.add(m);
      }
    }

    /* ----- charpente : poteaux aux angles des côtés sans mur + sablière en
       sous-face de toiture (section = épaisseur de la charpente choisie) ----- */
    if (vis.murs) {
      const charpMatI = charpMat.clone();
      charpMatI.clippingPlanes = clipPlanes; // poteaux coupés sous la toiture comme les murs
      const actif = {
        nord: inst.murs?.nord?.actif ?? true, est: inst.murs?.est?.actif ?? true,
        sud: inst.murs?.sud?.actif ?? true, ouest: inst.murs?.ouest?.actif ?? true,
      };
      // sablière en sous-face de toiture : son axe = axe des poteaux, décalé de
      // (section du poteau / 2) + 1,2 cm vers l'EXTÉRIEUR de la ligne directrice des murs
      const beamY = H - epC / 2; // sous-face de la sablière à H, au droit de la ligne directrice
      const off = epC / 2 + 0.012; // décalage de l'axe poteau/poutre vers l'extérieur (m)
      // poteaux d'angle : axe à ±off de la ligne directrice ; ils s'arrêtent SOUS la
      // sablière (hauteur = beamY - epC/2 = H - epC) ; angles partagés entre deux
      // modules accolés coïncident -> un seul poteau (postSeen)
      const postH = H - epC; // le poteau s'arrête sous la poutre
      for (const [px, pz, need] of [
        [X0 - off, Z0 - off, !actif.nord || !actif.ouest], [X1 + off, Z0 - off, !actif.nord || !actif.est],
        [X1 + off, Z1 + off, !actif.sud || !actif.est], [X0 - off, Z1 + off, !actif.sud || !actif.ouest],
      ]) {
        if (!need) continue;
        const key = `${Math.round(px * 100)}:${Math.round(pz * 100)}`;
        if (postSeen.has(key)) continue; // angle déjà pourvu par un module voisin
        postSeen.add(key);
        const post = new THREE.Mesh(new THREE.BoxGeometry(epC, postH, epC), charpMatI);
        post.position.set(px, postH / 2, pz);
        scene.add(post);
      }
      // sablières : une seule par côté charpente, DANS LE MÊME AXE que les poteaux (±off) ;
      // sur un mur commun, elle est au milieu du mur (ep/2) et dessinée par le module
      // propriétaire (plus petite coordonnée)
      const sh = shared[inst.id] || {};
      // la sablière va jusqu'aux bords EXTÉRIEURS des poteaux (axe ± off, section epC),
      // pas seulement jusqu'à leur axe : longueur = cote + 2*off + epC
      if (!actif.nord && !sh.nord) { const b = new THREE.Mesh(new THREE.BoxGeometry(dm.longueur + 2 * off + epC, epC, epC), charpMatI); b.position.set(X0 + dm.longueur / 2, beamY, Z0 - off); scene.add(b); }
      if (!actif.sud) { const b = new THREE.Mesh(new THREE.BoxGeometry(dm.longueur + 2 * off + epC, epC, epC), charpMatI); b.position.set(X0 + dm.longueur / 2, beamY, sh.sud ? Z1 + ep / 2 : Z1 + off); scene.add(b); }
      if (!actif.ouest && !sh.ouest) { const b = new THREE.Mesh(new THREE.BoxGeometry(epC, epC, dm.largeur + 2 * off + epC), charpMatI); b.position.set(X0 - off, beamY, Z0 + dm.largeur / 2); scene.add(b); }
      if (!actif.est) { const b = new THREE.Mesh(new THREE.BoxGeometry(epC, epC, dm.largeur + 2 * off + epC), charpMatI); b.position.set(sh.est ? X1 + ep / 2 : X1 + off, beamY, Z0 + dm.largeur / 2); scene.add(b); }
    }

    /* ----- toiture en DEUX couches superposées (comme dans Archicad) -----
       - complexe de toiture : dalle sur l'empreinte du module (SANS débord), de H à Hr,
         couleur de la toiture — affiché si vis.complexe_toiture
       - couverture : dalle AVEC débords, posée sur le complexe (sa sous-face = roofPolys
         passe par Hr au droit de la ligne directrice), visuel/couleur du revêtement de
         couverture de chaque pent — affiché si vis.couverture
       (les murs, eux, sont coupés par la sous-face de la dalle via clipPlanes) */
    if (toitVisOf(vis)) {
      if (tt === "terrasse") {
        if (vis.complexe_toiture) {
          // complexe : dalle sur l'empreinte (ligne directrice), de H à Hr
          // BoxGeometry : [+x, -x, +y, -y, +z, -z] — sous-face (-y) = revêtement inférieur, le reste = couleur du complexe
          const cplx = new THREE.Mesh(new THREE.BoxGeometry(X1 - X0, epToitV, Z1 - Z0),
            [cplxEdgeMat, cplxEdgeMat, cplxEdgeMat, sousFaceMat, cplxEdgeMat, cplxEdgeMat]);
          cplx.position.set((X0 + X1) / 2, H + epToitV / 2, (Z0 + Z1) / 2);
          scene.add(cplx);
        }
        if (vis.couverture) {
          const tItem = couvItemOf(inst, "toit"); // terrasse : revêtement du pent « toit »
          const tImg = tItem?.image || "";
          // sans visuel : couleur de la couverture, sinon celle de la toiture
          const tMat = tImg ? matWithMap(tImg, roofMat) : matCouleur(roofMat, tItem?.rgb, toitDef?.rgb || [120, 113, 108]);
          const epCV = epCouvVOf(inst, "toit");
          const roof = new THREE.Mesh(new THREE.BoxGeometry(rx1 - rx0, epCV, rz1 - rz0), tMat);
          roof.position.set((rx0 + rx1) / 2, H + epToitV + epCV / 2, (rz0 + rz1) / 2);
          scene.add(roof);
          maxTop = Math.max(maxTop, H + epToitV + epCV);
        }
      } else {
        // complexe : mêmes versants mais sur l'empreinte seule (ligne directrice = face
        // intérieure des murs, sans débord). Sous-face = dessus décalé VERTICALEMENT de
        // epToitV / un.y (= epToitV / cos pente) : c'est exactement le plan PARALLÈLE au
        // versant à distance normale epToitV (faces sup/inf parallèles, épaisseur
        // constante, shed OK) — et comme le décalage est purement vertical, toutes les
        // jupes sont verticales : la rive du bas de complexe suit le mur (non coupée
        // perpendiculairement au versant).
        if (vis.complexe_toiture && cplxPolysV) {
          for (const { poly } of cplxPolysV) {
            const un = upNormal(poly);
            const isNS = Math.abs(un.z) >= Math.abs(un.x);
            const dy = epToitV / Math.max(un.y, 1e-6); // = epToitV / cos(pente) : reste sur le plan parallèle
            const bots = [poly.map((p) => {
              // rive = bord MUR (Z0/Z1 si versant nord/sud, X0/X1 sinon) ; le reste = faîtage/croupe
              const onRive = isNS
                ? Math.abs(p.z - Z0) < 1e-6 || Math.abs(p.z - Z1) < 1e-6
                : Math.abs(p.x - X0) < 1e-6 || Math.abs(p.x - X1) < 1e-6;
              return onRive
                ? new THREE.Vector3(p.x, p.y - dy, p.z) // rive : jupe VERTICALE, suit le mur (même plan parallèle)
                : new THREE.Vector3(p.x - un.x * epToitV, p.y - un.y * epToitV, p.z - un.z * epToitV); // faîtage : normale propre du versant (jonction par interpénétration)
            })];
            // groupe 0 = dessus + jupes, groupe 1 (sous-face, plane et parallèle au dessus) = revêtement inférieur
            scene.add(new THREE.Mesh(roofSlabGeometry([poly], epToitV, bots), [cplxEdgeMat, sousFaceMat]));
          }
        }
        // couverture : un mesh par versant (avec débords), posé sur le complexe :
        // sa sous-face = roofPolys (qui passe par Hr au droit de la ligne directrice,
        // comme le dessus du complexe) ; le dessus est relevé de l'épaisseur de la
        // couverture mesurée SELON LA NORMALE du versant (épaisseur réelle le long
        // du plan de toit), la dalle restant à jupes verticales
        if (vis.couverture && roofPolysV) {
          for (const { poly, versant } of roofPolysV) {
            const cItem = couvItemOf(inst, versant);
            const cImg = cItem?.image || "";
            // sans visuel : couleur de la couverture du pent, sinon celle de la toiture
            const cMat = cImg ? matWithMap(cImg, roofMat) : matCouleur(roofMat, cItem?.rgb, toitDef?.rgb || [120, 113, 108]);
            const epCV = epCouvVOf(inst, versant);
            const un = upNormal(poly);
            const isNS = Math.abs(un.z) >= Math.abs(un.x);
            const dyC = epCV / Math.max(un.y, 1e-6);
            const top = poly.map((p) => {
              // rive = bord EXTÉRIEUR du toit (avec débords) ; le reste = faîtage/croupe
              const onRive = isNS
                ? Math.abs(p.z - rz0) < 1e-6 || Math.abs(p.z - rz1) < 1e-6
                : Math.abs(p.x - rx0) < 1e-6 || Math.abs(p.x - rx1) < 1e-6;
              return onRive
                ? new THREE.Vector3(p.x, p.y + dyC, p.z) // jupe verticale en rive
                : new THREE.Vector3(p.x + un.x * epCV, p.y + un.y * epCV, p.z + un.z * epCV); // faîtage : normale propre du versant
            });
            // sous-face explicite = poly : la couverture repose exactement sur le dessus
            // du complexe (pas de décalage vers l'extérieur, pas d'écart au faîtage)
            scene.add(new THREE.Mesh(roofSlabGeometry([top], epCV, [poly]), [cMat, cMat]));
            for (const p of top) maxTop = Math.max(maxTop, p.y);
          }
        }
      }
    }

    /* ----- fenêtres de toit : cadre posé sur le versant, à 20 cm du bas de pente ----- */
    if (tt !== "terrasse" && toitVisOf(vis)) {
      for (const [versant, list] of Object.entries(d.fenetresToit?.[inst.id] || {})) {
        const edge = basPenteOf(tt, versant);
        const p = penteOfPent(d, tt, versant);
        const sin = Math.sin(rad(p)), cos = Math.cos(rad(p));
        for (const f of list || []) {
          // bas de pente = ligne directrice du mur (comme en plan/élévation 2D) ;
          // le dessus de la couverture y vaut Hr + épaisseur de couverture selon la
          // verticale (épaisseur le long du plan × cos pente), quel que soit le débord
          const yEave = H + epToitV + (vis.couverture ? epCouvVOf(inst, versant) * cos : 0);
          let E0, s, u;
          if (edge === "nord") { E0 = new THREE.Vector3(X0 + f.position + f.largeur / 2, yEave, Z0); s = new THREE.Vector3(0, sin, cos); u = new THREE.Vector3(1, 0, 0); }
          else if (edge === "sud") { E0 = new THREE.Vector3(X0 + f.position + f.largeur / 2, yEave, Z1); s = new THREE.Vector3(0, sin, -cos); u = new THREE.Vector3(1, 0, 0); }
          else if (edge === "ouest") { E0 = new THREE.Vector3(X0, yEave, Z0 + f.position + f.largeur / 2); s = new THREE.Vector3(cos, sin, 0); u = new THREE.Vector3(0, 0, 1); }
          else { E0 = new THREE.Vector3(X1, yEave, Z0 + f.position + f.largeur / 2); s = new THREE.Vector3(-cos, sin, 0); u = new THREE.Vector3(0, 0, 1); }
          // base orthonormée DIRECTE (u x s = n) sinon le quaternion est invalide ;
          // la normale "sortante" (vers le haut) sert uniquement au décollement
          const n = new THREE.Vector3().crossVectors(u, s).normalize();
          const out = n.y >= 0 ? n : n.clone().negate();
          const sc = (f.positionHauteur ?? 0) + f.hauteur / 2; // distance le long du rampant depuis le bas de pente (0 = contre le mur)
          const m = new THREE.Mesh(new THREE.BoxGeometry(f.largeur, f.hauteur, 0.06), fenMat);
          m.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(u, s, n));
          m.position.copy(E0).addScaledVector(s, sc).addScaledVector(out, 0.05);
          scene.add(m);
        }
      }
    }
  }

  return { scene, maxTop, span: Math.max(b.maxX - b.minX, b.maxY - b.minY, 4), textures };
}

export default function Vue3D({ d, env, w, h }) {
  const mountRef = useRef(null);
  // clé sérialisée : toute modification de la config ou des catalogues reconstruit la scène
  const key = useMemo(() => JSON.stringify({
    d,
    murs: env.murs, toitures: env.toitures, formes: env.formes,
    planchers: env.planchers, modules: env.modules,
  }), [d, env]);

  // env est recréé à chaque rendu du parent : on le lit via une ref pour ne
  // reconstruire la scène que quand la clé (config + catalogues) change
  const envRef = useRef(env);
  envRef.current = env;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount || !envRef.current?.murs?.length) return;

    const W = mount.clientWidth || w || 600;
    const H = mount.clientHeight || h || 380;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.localClippingEnabled = true; // coupe des murs par la sous-face de la toiture
    renderer.setClearColor(0x000000, 0); // fond transparent : la page transparaît
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(W, H);
    mount.appendChild(renderer.domElement);

    const dConf = JSON.parse(key).d;
    const { scene, maxTop, span, textures } = buildScene(dConf, envRef.current);

    const camera = new THREE.PerspectiveCamera(45, W / H, 0.1, 500);
    // Vue par défaut plus large (module entièrement visible) et plus rasante (axonométrie proche du sol)
    const target = new THREE.Vector3(0, maxTop / 2, 0);
    const camPos = new THREE.Vector3(span * 1.25, Math.max(span * 0.42, maxTop * 0.85), span * 1.6);
    // Zoom réduit de 50% : on double la distance caméra-cible (le module paraît deux fois plus petit)
    camera.position.copy(target).add(new THREE.Vector3().subVectors(camPos, target).multiplyScalar(2));

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.copy(target);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.update();

    let raf = 0;
    const loop = () => { raf = requestAnimationFrame(loop); controls.update(); renderer.render(scene, camera); };
    loop();

    const ro = new ResizeObserver(() => {
      const w2 = mount.clientWidth, h2 = mount.clientHeight;
      if (!w2 || !h2) return;
      camera.aspect = w2 / h2;
      camera.updateProjectionMatrix();
      renderer.setSize(w2, h2);
    });
    ro.observe(mount);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      controls.dispose();
      scene.traverse((o) => { o.geometry?.dispose?.(); if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.map?.dispose?.(); m.dispose?.(); }); });
      (textures || []).forEach((t) => t.dispose?.());
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, w, h]);

  return <div ref={mountRef} style={{ width: "100%", height: "100%", touchAction: "none" }} title="Vue 3D — lecture seule (glisser : orbite, molette : zoom, clic droit : panoramique)" />;
}

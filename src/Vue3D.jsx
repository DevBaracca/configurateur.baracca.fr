import React, { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  bboxOf, dimsOf, epaisseurPlancher, toitureDefOf, formeDefOf, toitTypeOf,
  pente1Of, pente2Of, hauteurFaitageDm, basPenteOf, penteOfPent, fenetresOfPent,
  couvListOf, couvIdOf, intListOf, intIdOf, rgbHex, mixHex, SOL_SOUS_PLANCHER, toitVisOf,
  PLANCHER_DEPASSEMENT,
} from "./App.jsx";

/* Vue 3D en lecture seule du configurateur (Three.js) : on reconstruit la scène
   à chaque changement de configuration. Repère : plan (x, y) -> 3D (x, z), Y vers
   le haut ; le bâtiment est centré sur la bbox de l'ensemble des modules.
   Nord = -Z, Sud = +Z, Est = +X, Ouest = -X. */

const css = (rgb, fb) => `rgb(${rgb?.[0] ?? fb[0]},${rgb?.[1] ?? fb[1]},${rgb?.[2] ?? fb[2]})`;
const rad = (deg) => (deg * Math.PI) / 180;

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
  const surfItemOf = (inst, face) => env.facades.find((f) => f.id === (inst?.murs?.[face]?.surface ?? murDef?.surface));
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
  for (const { inst } of dimsList) {
    over[inst.id] = { nord: exDef, sud: exDef, est: exDef, ouest: exDef };
    shared[inst.id] = { nord: false, sud: false, est: false, ouest: false };
  }
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
      if (gapE > epsC && gapE <= epMax && ovY) { over[A.inst.id].est = ep; over[B.inst.id].ouest = 0; shared[A.inst.id].est = shared[B.inst.id].ouest = true; }
      if (gapW > epsC && gapW <= epMax && ovY) { over[B.inst.id].est = ep; over[A.inst.id].ouest = 0; shared[B.inst.id].est = shared[A.inst.id].ouest = true; }
      // Jonction sud/nord : les deux modules se décalent d'une MOITIÉ du mur commun
      // (chacun prolonge sa pente de ep/2) -> les toits se rejoignent au milieu du mur
      if (gapS > epsC && gapS <= epMax && ovX) { over[A.inst.id].sud = ep / 2; over[B.inst.id].nord = ep / 2; shared[A.inst.id].sud = shared[B.inst.id].nord = true; }
      if (gapN > epsC && gapN <= epMax && ovX) { over[B.inst.id].sud = ep / 2; over[A.inst.id].nord = ep / 2; shared[B.inst.id].sud = shared[A.inst.id].nord = true; }
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
      // dessus du plancher = revêtement Intérieur choisi ; chants = revêtement Extérieur choisi
      const hautItem = intListOf(env).find((f) => f.id === intIdOf(env, d.revetementPlancher, plancherDef?.revetement_sup));
      const chantItem = env.facades.find((f) => f.id === (d.revetementChantPlancher ?? plancherDef?.revetement_chants ?? murDef?.surface));
      // sans visuel : couleur du revêtement, sinon gris clair
      const matTop = hautItem?.image ? matWithMap(hautItem.image, plancherMat) : matCouleur(plancherMat, hautItem?.rgb, [214, 211, 209]);
      const matSide = chantItem?.image ? matWithMap(chantItem.image, plancherMat) : matCouleur(plancherMat, chantItem?.rgb, [214, 211, 209]);
      // BoxGeometry : [+x, -x, +y(dessus), -y, +z, -z]
      const pl = new THREE.Mesh(
        new THREE.BoxGeometry(dm.longueur + pW + pE, epP, dm.largeur + pN + pS),
        [matSide, matSide, matTop, plancherMat, matSide, matSide]
      );
      pl.position.set(X0 + dm.longueur / 2, -epP / 2, Z0 + dm.largeur / 2);
      scene.add(pl);
    }
    const t1 = Math.tan(rad(p1)), t2 = Math.tan(rad(p2));
    const Hr = H + epToitV; // dessus de la dalle au droit de la ligne directrice (sous-face à H = dessus des murs)
    // Hauteurs de toit calculées sur la LIGNE DIRECTRICE, indépendamment des débords :
    // deux modules de mêmes dimensions ont exactement le même faîtage / bas de pente.
    let hF = 0, zr = (Z0 + Z1) / 2;
    if (tt === "monopente") hF = t1 * (Z1 - Z0);
    else if (tt === "deuxpentes") {
      hF = hauteurFaitageDm(dm, p1, p2, tt);
      zr = Z0 + (t1 > 0 ? Math.min(Math.max(hF / t1, 0), Z1 - Z0) : (Z1 - Z0) / 2);
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
        const yN = Hr - ovv.nord * t1, yS = Hr - ovv.sud * t2; // débords qui prolongent la pente
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
    // complexe : empreinte sur la LIGNE DIRECTRICE seule (sans débord) — la pente du
    // complexe et celle de la couverture sont alors strictement identiques
    const cplxPolysV = polysOf(X0, X1, Z0, Z1, { nord: 0, sud: 0, est: 0, ouest: 0 });
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
      const ops = [...(f.ouvertures || [])].sort((a, c) => a.position - c.position);
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
      // jonction des angles : les murs nord/sud prolongés de l'épaisseur dans les coins
      // couvrent les carrés d'angle — seulement si le côté perpendiculaire est un mur ;
      // sinon c'est le poteau de charpente qui occupe le coin (il ne doit pas être recouvert)
      if (segs.length && (face === "nord" || face === "sud")) {
        if (inst.murs?.ouest?.actif !== false) segs[0][0] -= ep;
        if (inst.murs?.est?.actif !== false) segs[segs.length - 1][1] += ep;
      }

      for (const [u0, u1, y0, y1] of segs) {
        const wSeg = u1 - u0, hSeg = y1 - y0;
        if (wSeg <= 1e-6 || hSeg <= 1e-6) continue;
        let mesh;
        if (face === "nord") mesh = new THREE.Mesh(new THREE.BoxGeometry(wSeg, hSeg, ep), mats),
          mesh.position.set(X0 + (u0 + u1) / 2, (y0 + y1) / 2, Z0 - ep / 2);
        else if (face === "sud") mesh = new THREE.Mesh(new THREE.BoxGeometry(wSeg, hSeg, ep), mats),
          mesh.position.set(X0 + (u0 + u1) / 2, (y0 + y1) / 2, Z1 + ep / 2);
        else if (face === "ouest") mesh = new THREE.Mesh(new THREE.BoxGeometry(ep, hSeg, wSeg), mats),
          mesh.position.set(X0 - ep / 2, (y0 + y1) / 2, Z0 + (u0 + u1) / 2);
        else mesh = new THREE.Mesh(new THREE.BoxGeometry(ep, hSeg, wSeg), mats),
          mesh.position.set(X1 + ep / 2, (y0 + y1) / 2, Z0 + (u0 + u1) / 2);
        scene.add(mesh);
      }

      // ouvertures : panneau sombre posé sur la face extérieure du mur, sur l'allège
      for (const o of f.ouvertures || []) {
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
        // complexe : mêmes versants mais sur l'empreinte seule (ligne directrice, sans débord)
        if (vis.complexe_toiture && cplxPolysV) {
          // groupe 0 (dessus + jupes/chant) = couleur du complexe ; groupe 1 (sous-face) = revêtement inférieur
          for (const { poly } of cplxPolysV) scene.add(new THREE.Mesh(roofSlabGeometry([poly], epToitV), [cplxEdgeMat, sousFaceMat]));
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
            const top = poly.map((p) => new THREE.Vector3(p.x + un.x * epCV, p.y + un.y * epCV, p.z + un.z * epCV));
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
          const sc = 0.20 / cos + (f.positionHauteur ?? 0) + f.hauteur / 2; // distance le long du rampant depuis le bas de pente
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
    camera.position.set(span * 0.9, Math.max(span * 0.75, maxTop * 1.2), span * 1.15);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, maxTop / 2, 0);
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

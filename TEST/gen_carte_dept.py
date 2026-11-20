import json, math, os
from xml.sax.saxutils import escape

SRC = r'C:\Users\conta\AppData\Local\Temp\dept.geojson'
OUT = r'assets/cartes/departements-france.svg'

d = json.load(open(SRC, encoding='utf-8'))
feats = [f for f in d['features'] if not str(f['properties']['code']).startswith('97')]

minlon = minlat = 1e9
maxlon = maxlat = -1e9
for f in feats:
    polys = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
    for poly in polys:
        for lon, lat in poly[0]:
            minlon = min(minlon, lon); maxlon = max(maxlon, lon)
            minlat = min(minlat, lat); maxlat = max(maxlat, lat)

meanlat = (minlat + maxlat) / 2
kx = math.cos(math.radians(meanlat))
W = 480
sx = W / ((maxlon - minlon) * kx)
sy = sx
H = math.ceil((maxlat - minlat) * sy)


def proj(lon, lat):
    return (round((lon - minlon) * kx * sx, 1), round((maxlat - lat) * sy, 1))


def ring_path(ring):
    pts = [proj(lon, lat) for lon, lat in ring]
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    if len(out) < 3:
        return ''
    return 'M' + 'L'.join(f'{x:g},{y:g}' for x, y in out) + 'Z'


def poly_area_centroid(ring):
    pts = [proj(lon, lat) for lon, lat in ring]
    n = len(pts)
    a = 0.0; cx = 0.0; cy = 0.0
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross; cx += (x0 + x1) * cross; cy += (y0 + y1) * cross
    a *= 0.5
    if abs(a) < 1e-9:
        return 0.0, (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
    return abs(a), (cx / (6 * a), cy / (6 * a))


parts = []
for f in sorted(feats, key=lambda f: str(f['properties']['code'])):
    code = str(f['properties']['code'])
    nom = str(f['properties']['nom'])
    geom = f['geometry']
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    dpath = ''.join(ring_path(ring) for poly in polys for ring in poly)
    big = max(polys, key=lambda p: poly_area_centroid(p[0])[0])
    area, (lx, ly) = poly_area_centroid(big[0])
    label = f'<text x="{lx:g}" y="{ly:g}">{code}</text>' if area >= 140 else ''
    parts.append(f'<g class="dept-g" data-dept="{code}"><path d="{dpath}"/><title>{escape(nom)} ({code})</title>{label}</g>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" class="dept-france" '
       f'role="img" aria-label="Carte des departements de France metropolitaine">'
       + ''.join(parts) + '</svg>')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(svg)
print('features:', len(feats), 'viewBox:', W, H, 'svg size:', len(svg), 'bytes')
print('codes:', ' '.join(str(f['properties']['code']) for f in sorted(feats, key=lambda f: str(f['properties']['code']))))

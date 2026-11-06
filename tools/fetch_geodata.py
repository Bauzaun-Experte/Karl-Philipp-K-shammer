#!/usr/bin/env python3
"""Holt die Fachdaten für die Jagdkarte und schreibt sie als GeoJSON nach data/:

  data/schutzgebiete.geojson    NSG- und FFH-Grenzen um Kerpen (LANUV NRW, LINFOS-WFS)
  data/parrig_osm.geojson       Umriss "Parrig" aus OpenStreetMap (Nominatim)
  data/jagdbezirke.geojson      Jagdbezirke aus der Jagdbezirkskarte des Rhein-Erft-Kreises (ArcGIS REST)
  data/teilverpachtungen.geojson

  python3 tools/fetch_geodata.py
"""
import json, math, re, pathlib, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'; DATA.mkdir(exist_ok=True)
BBOX = (50.85, 6.64, 50.94, 6.77)  # lat_min, lon_min, lat_max, lon_max


def get(url, timeout=120):
    req = urllib.request.Request(url, headers={'User-Agent': 'jagdkarte-parrig (github.com/bauzaun-experte)'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8')


def linfos(typename, kind):
    url = ('https://www.wfs.nrw.de/umwelt/linfos?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=wfs_linfos:' + typename +
           '&SRSNAME=urn:ogc:def:crs:EPSG::4326&BBOX=%s,%s,%s,%s,urn:ogc:def:crs:EPSG::4326&COUNT=50' % BBOX)
    t = get(url); feats = []
    for m in re.finditer(r'<wfs_linfos:(%s)[^>]*>(.*?)</wfs_linfos:\1>' % typename, t, re.S):
        body = m.group(2)
        name = re.search(r'<wfs_linfos:gebietsname>([^<]*)<', body); kenn = re.search(r'<wfs_linfos:kennung>([^<]*)<', body)
        polys = []
        for pm in re.finditer(r'<gml:Polygon[^>]*>(.*?)</gml:Polygon>', body, re.S):
            rings = []
            for rm in re.finditer(r'<gml:(exterior|interior)>.*?<gml:posList[^>]*>([^<]*)</gml:posList>', pm.group(1), re.S):
                nums = [float(v) for v in rm.group(2).split()]
                rings.append([[round(nums[i + 1], 6), round(nums[i], 6)] for i in range(0, len(nums), 2)])
            if rings:
                polys.append(rings)
        if polys:
            geom = {'type': 'Polygon', 'coordinates': polys[0]} if len(polys) == 1 else {'type': 'MultiPolygon', 'coordinates': polys}
            feats.append({'type': 'Feature', 'properties': {'typ': kind, 'name': name.group(1) if name else '', 'kennung': kenn.group(1) if kenn else ''}, 'geometry': geom})
    return feats


def simplify(ring, tol):
    if len(ring) < 5:
        return ring
    def dist(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if dx == 0 and dy == 0:
            return math.hypot(p[0] - a[0], p[1] - a[1])
        t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
        return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))
    keep = [False] * len(ring); keep[0] = keep[-1] = True; stack = [(0, len(ring) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        dmax, idx = 0, -1
        for k in range(i + 1, j):
            d = dist(ring[k], ring[i], ring[j])
            if d > dmax:
                dmax, idx = d, k
        if dmax > tol:
            keep[idx] = True; stack += [(i, idx), (idx, j)]
    out = [p for p, k in zip(ring, keep) if k]
    return out if len(out) >= 4 else ring


def arcgis(layer, fields, out, tol=0.000015):
    geometry = json.dumps({'xmin': BBOX[1], 'ymin': BBOX[0], 'xmax': BBOX[3], 'ymax': BBOX[2], 'spatialReference': {'wkid': 4326}})
    url = ('https://geo.rhein-erft-kreis.de/arcgis/rest/services/WMS/WMS_REK_Jagdbezirkskarte/MapServer/%d/query?' % layer +
           urllib.parse.urlencode({'where': '1=1', 'geometry': geometry, 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
                                   'spatialRel': 'esriSpatialRelIntersects', 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'f': 'geojson'}))
    d = json.loads(get(url)); feats = []
    for f in d.get('features', []):
        g = f['geometry']; props = {k: f['properties'].get(k) for k in fields}
        if props.get('NAME'):
            props['NAME'] = props['NAME'].strip()
        clean = lambda r: simplify([[round(x, 6), round(y, 6)] for x, y in r], tol)
        if g['type'] == 'Polygon':
            g['coordinates'] = [clean(r) for r in g['coordinates']]
        elif g['type'] == 'MultiPolygon':
            g['coordinates'] = [[clean(r) for r in poly] for poly in g['coordinates']]
        feats.append({'type': 'Feature', 'properties': props, 'geometry': g})
    (DATA / out).write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(out, len(feats), 'Objekte')


def main():
    feats = linfos('nsg_polygon', 'NSG') + linfos('ffh_polygon', 'FFH')
    (DATA / 'schutzgebiete.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False), encoding='utf-8')
    print('schutzgebiete.geojson', len(feats), 'Objekte')
    nom = json.loads(get('https://nominatim.openstreetmap.org/search?q=Parrig,+Kerpen&format=json&polygon_geojson=1&limit=5'))
    rel = [x for x in nom if x.get('osm_type') == 'relation']
    if rel:
        fc = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'name': 'Parrig (OSM nature_reserve)', 'osm_id': rel[0]['osm_id'], 'source': 'OpenStreetMap, ODbL'}, 'geometry': rel[0]['geojson']}]}
        (DATA / 'parrig_osm.geojson').write_text(json.dumps(fc), encoding='utf-8'); print('parrig_osm.geojson 1 Objekt')
    arcgis(7, ['NAME', 'TSN_NEU', 'TSN_REV_NR', 'lfdNr', 'DAT_ERST', 'Shape_Area'], 'jagdbezirke.geojson')
    arcgis(8, ['NAME', 'TVP_AN', 'SONSTIGES', 'Beschriftung', 'Shape_Area'], 'teilverpachtungen.geojson')


if __name__ == '__main__':
    main()

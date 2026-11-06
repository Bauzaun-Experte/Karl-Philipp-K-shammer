#!/usr/bin/env python3
"""Lädt Luftbild- (DOP), Topokarten- (DTK) und Flurstücks-Kacheln (ALKIS) von Geobasis NRW
für den Parrig-Ausschnitt als 1024-px-Kacheln im Web-Mercator-Raster (für die Offline-/Artefakt-Variante).

  python3 tools/fetch_tiles.py tiles/

Lizenz der Daten: Land NRW, Datenlizenz Deutschland – Namensnennung 2.0 (dl-de/by-2-0).
"""
import math, os, sys, time, urllib.request, urllib.parse, concurrent.futures

R = 20037508.342789244
OUT = sys.argv[1] if len(sys.argv) > 1 else 'tiles'
BBOX = (6.680, 50.880, 6.730, 50.918)  # lon_min, lat_min, lon_max, lat_max
LAYERS = {
    'dop':   dict(url='https://www.wms.nrw.de/geobasis/wms_nw_dop', layer='nw_dop_rgb', fmt='image/jpeg', ext='jpg', zooms=range(12, 17), transparent='FALSE'),
    'dtk':   dict(url='https://www.wms.nrw.de/geobasis/wms_nw_dtk', layer='nw_dtk_col', fmt='image/jpeg', ext='jpg', zooms=range(12, 16), transparent='FALSE'),
    'alkis': dict(url='https://www.wms.nrw.de/geobasis/wms_nw_alkis', layer='adv_alkis_flurstuecke', fmt='image/png', ext='png', zooms=range(15, 17), transparent='TRUE'),
}


def merc(lon, lat):
    return lon * R / 180.0, math.log(math.tan((90 + lat) * math.pi / 360.0)) / (math.pi / 180.0) * R / 180.0


def tiles_for(z):
    n = 2 ** z; size = 2 * R / n
    x0, y1 = merc(BBOX[0], BBOX[3]); x1, y0 = merc(BBOX[2], BBOX[1])
    for tx in range(int((x0 + R) / size), int((x1 + R) / size) + 1):
        for ty in range(int((R - y1) / size), int((R - y0) / size) + 1):
            minx = -R + tx * size; maxy = R - ty * size
            yield tx, ty, (minx, maxy - size, minx + size, maxy)


def fetch(name, cfg, z, tx, ty, bbox):
    path = os.path.join(OUT, name, str(z), str(tx), f'{ty}.{cfg["ext"]}')
    if os.path.exists(path) and os.path.getsize(path) > 500:
        return 'skip'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    q = dict(SERVICE='WMS', VERSION='1.3.0', REQUEST='GetMap', LAYERS=cfg['layer'], STYLES='', CRS='EPSG:3857',
             BBOX=','.join(f'{v:.3f}' for v in bbox), WIDTH='1024', HEIGHT='1024', FORMAT=cfg['fmt'], TRANSPARENT=cfg['transparent'])
    url = cfg['url'] + '?' + urllib.parse.urlencode(q)
    err = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = r.read(); ct = r.headers.get('Content-Type', '')
            if not ct.startswith('image/'):
                raise RuntimeError('keine Bildantwort: ' + data[:200].decode('utf8', 'replace'))
            with open(path, 'wb') as f:
                f.write(data)
            return 'ok'
        except Exception as e:
            err = e; time.sleep(2 * (attempt + 1))
    return f'FEHLER {name}/{z}/{tx}/{ty}: {err}'


jobs = [(name, cfg, z, tx, ty, bbox) for name, cfg in LAYERS.items() for z in cfg['zooms'] for tx, ty, bbox in tiles_for(z)]
print('Kacheln:', len(jobs), {n: sum(1 for j in jobs if j[0] == n) for n in LAYERS}, flush=True)
done = 0; fails = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    for res in ex.map(lambda j: fetch(*j), jobs):
        done += 1
        if res.startswith('FEHLER'):
            fails.append(res); print(res, flush=True)
        if done % 20 == 0:
            print('Fortschritt', done, '/', len(jobs), flush=True)
print('Fertig:', done, 'Kacheln,', len(fails), 'Fehler')

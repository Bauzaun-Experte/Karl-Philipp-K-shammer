#!/usr/bin/env python3
"""Baut die Jagdkarte aus der Vorlage und den Daten in data/.

  python3 tools/build.py                 -> index.html (Live-Dienste: WMS Geobasis NRW, OSM)
  python3 tools/build.py --artifact OUT  -> Seite für ein Claude-Artefakt mit lokalen Kacheln (tiles/)
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TPL = ROOT / 'src' / 'jagdkarte.template.html'
LEAFLET_CSS = ROOT / 'src' / 'vendor' / 'leaflet-1.9.4.css'

# Kartenausschnitt, für den Kacheln vorliegen (lon_min, lat_min, lon_max, lat_max)
TILE_BBOX = (6.680, 50.880, 6.730, 50.918)
CENTER = [50.8934, 6.7072]


def load_json(name):
    p = ROOT / 'data' / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def js_json(obj):
    # JSON innerhalb von <script>: "</" maskieren, damit kein </script> entstehen kann
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def render(mode, tiles_base='tiles/'):
    tpl = TPL.read_text(encoding='utf-8')
    css = LEAFLET_CSS.read_text(encoding='utf-8')
    css = re.sub(r'url\([^)]*\)', 'none', css)  # Leaflet-Bilddateien werden nicht verwendet
    css = '/* Leaflet 1.9.4 - BSD-2-Clause, (c) 2010-2023 Volodymyr Agafonkin */\n' + css
    data = {
        'schutzgebiete': load_json('schutzgebiete.geojson'),
        'parrig_osm': load_json('parrig_osm.geojson'),
        'jagdbezirke': load_json('jagdbezirke.geojson'),
        'teilverpachtungen': load_json('teilverpachtungen.geojson'),
        'fotos': load_json('fotos.geojson'),
    }
    cfg = {
        'mode': mode, 'tilesBase': tiles_base, 'center': CENTER, 'zoom': 15,
        'bounds': [[TILE_BBOX[1], TILE_BBOX[0]], [TILE_BBOX[3], TILE_BBOX[2]]],
    }
    html = tpl.replace('/*__LEAFLET_CSS__*/', css)
    html = html.replace('/*__CONFIG__*/{}', js_json(cfg)).replace('/*__DATA__*/{}', js_json(data))
    return html


def main(argv):
    if len(argv) >= 2 and argv[0] == '--artifact':
        out = pathlib.Path(argv[1])
        html = render('local').replace('<!--__BODY__-->', '')
        out.write_text(html, encoding='utf-8')
        print('Artefakt-Seite:', out, round(len(html.encode()) / 1024), 'KB')
        return
    html = render('wms')
    head, body = html.split('<!--__BODY__-->')
    doc = ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
           + head + '</head>\n<body>\n' + body + '\n</body>\n</html>\n')
    out = ROOT / 'index.html'
    out.write_text(doc, encoding='utf-8')
    print('index.html:', round(len(doc.encode()) / 1024), 'KB')


if __name__ == '__main__':
    main(sys.argv[1:])

#!/usr/bin/env python3
"""Liest einen Ordner mit exportierten Fotos, holt Aufnahmeort und -zeit aus den EXIF-Daten,
erzeugt Vorschaubilder und schreibt data/fotos.geojson für die Jagdkarte.

  python3 tools/build_photo_index.py ~/Desktop/Parrig-Fotos [--alle]

Standardmäßig werden nur Fotos übernommen, deren Aufnahmeort im Parrig-Rechteck liegt
(--alle übernimmt alle Fotos mit GPS-Daten). Vorschaubilder landen in fotos/thumbs und fotos/web.

Voraussetzung: pip3 install pillow   (für HEIC zusätzlich: pip3 install pillow-heif)
"""
import sys, json, pathlib, hashlib
from datetime import datetime

try:
    from PIL import Image, ImageOps, ExifTags
except ImportError:
    sys.exit('Pillow fehlt: pip3 install pillow')
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
BBOX = (50.877, 6.688, 50.914, 6.722)  # lat_min, lon_min, lat_max, lon_max
EXTS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.heic', '.heif'}


def to_deg(v, ref):
    try:
        d = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
    except Exception:
        return None
    return -d if ref in ('S', 'W') else d


def read_exif(im):
    lat = lon = None; when = None
    try:
        exif = im.getexif()
        dt = exif.get(306) or exif.get(36867)
        ifd = exif.get_ifd(0x8769)
        dt = ifd.get(36867) or dt
        if dt:
            try:
                when = datetime.strptime(str(dt), '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M')
            except ValueError:
                when = str(dt)
        gps = exif.get_ifd(0x8825)
        if gps:
            lat = to_deg(gps.get(2), gps.get(1)); lon = to_deg(gps.get(4), gps.get(3))
    except Exception:
        pass
    return lat, lon, when


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    src = pathlib.Path(args[0]).expanduser()
    alle = '--alle' in sys.argv
    thumbs = ROOT / 'fotos' / 'thumbs'; web = ROOT / 'fotos' / 'web'
    thumbs.mkdir(parents=True, exist_ok=True); web.mkdir(parents=True, exist_ok=True)
    feats = []; skipped = 0
    for p in sorted(src.rglob('*')):
        if p.suffix.lower() not in EXTS or not p.is_file():
            continue
        try:
            im = Image.open(p)
        except Exception as e:
            print('übersprungen (nicht lesbar):', p.name, e); skipped += 1; continue
        lat, lon, when = read_exif(im)
        if lat is None or lon is None:
            print('ohne GPS:', p.name); skipped += 1; continue
        in_box = BBOX[0] <= lat <= BBOX[2] and BBOX[1] <= lon <= BBOX[3]
        if not in_box and not alle:
            skipped += 1; continue
        pid = hashlib.sha1(str(p.resolve()).encode()).hexdigest()[:12]
        try:
            im = ImageOps.exif_transpose(im).convert('RGB')
            t = im.copy(); t.thumbnail((240, 240)); t.save(thumbs / f'{pid}.jpg', 'JPEG', quality=72, optimize=True)
            w = im.copy(); w.thumbnail((1600, 1600)); w.save(web / f'{pid}.jpg', 'JPEG', quality=85, optimize=True)
        except Exception as e:
            print('Vorschau fehlgeschlagen:', p.name, e)
        feats.append({'type': 'Feature', 'properties': {'id': pid, 'name': p.name, 'date': when, 'im_parrig': in_box,
                                                         'thumb': f'fotos/thumbs/{pid}.jpg', 'web': f'fotos/web/{pid}.jpg'},
                      'geometry': {'type': 'Point', 'coordinates': [round(lon, 6), round(lat, 6)]}})
        print('ok:', p.name, round(lat, 5), round(lon, 5), when or '', 'im Parrig' if in_box else 'außerhalb')
    out = ROOT / 'data' / 'fotos.geojson'
    out.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{len(feats)} Fotos in {out} geschrieben, {skipped} übersprungen. Jetzt: python3 tools/build.py')


if __name__ == '__main__':
    main()

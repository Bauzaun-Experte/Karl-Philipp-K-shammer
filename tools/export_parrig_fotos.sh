#!/usr/bin/env bash
# Exportiert alle Fotos aus der Apple-Fotos-Mediathek (macOS), deren Aufnahmeort im Parrig liegt.
#
# Voraussetzung: osxphotos  ->  brew install pipx && pipx install osxphotos   (oder: pip3 install osxphotos)
# Aufruf:        tools/export_parrig_fotos.sh [Zielordner]      (Standard: ~/Desktop/Parrig-Fotos)
#
# Das Rechteck entspricht dem Eigenjagdbezirk "Kerpener Parrig" und dem NSG Parrig (BM-004)
# mit rund 300 m Rand. Die Ortsangabe wird aus den GPS-Daten der Fotos gelesen.
set -euo pipefail

OUT="${1:-$HOME/Desktop/Parrig-Fotos}"
LAT_MIN=50.877; LAT_MAX=50.914
LON_MIN=6.688;  LON_MAX=6.722

if ! command -v osxphotos >/dev/null 2>&1; then
  echo "osxphotos ist nicht installiert. Installation: pipx install osxphotos" >&2
  echo "Alternative ohne Zusatzsoftware: Fotos-App -> Suche 'Parrig' -> alle markieren -> Ablage -> Exportieren" >&2
  echo "-> 'Unverändertes Original exportieren' (behält die GPS-Daten)." >&2
  exit 1
fi

mkdir -p "$OUT"
echo "Exportiere Fotos mit Aufnahmeort zwischen $LAT_MIN..$LAT_MAX N und $LON_MIN..$LON_MAX O nach: $OUT"

osxphotos export "$OUT" \
  --query-eval "photo.location[0] is not None and $LAT_MIN <= photo.location[0] <= $LAT_MAX and $LON_MIN <= photo.location[1] <= $LON_MAX" \
  --download-missing \
  --convert-to-jpeg --jpeg-quality 0.9 \
  --skip-live \
  --filename "{created.year}-{created.mm}-{created.dd}_{created.hh}{created.min}_{original_name}" \
  --report "$OUT/export-bericht.csv" \
  --verbose

echo
echo "Fertig. Danach den Foto-Index für die Karte bauen:"
echo "  python3 tools/build_photo_index.py \"$OUT\""
echo "  python3 tools/build.py"

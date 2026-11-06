# Jagdkarte Parrig

Digitale Jagdkarte für den **Eigenjagdbezirk Kerpener Parrig** (Kerpen, Rhein-Erft-Kreis) mit Luftbild,
topographischer Karte, Jagdbezirks- und Schutzgebietsgrenzen, eigenen Revier-Einträgen und Fotos mit Aufnahmeort.

Die Karte gibt es in zwei Ausführungen aus derselben Vorlage:

| Ausführung | Wo | Grundkarten | Speicherung |
|---|---|---|---|
| **Claude-Artefakt** | <https://claude.ai/artifact/7bCXtTazwMFizmYGfmYhH2> | eingebettete Kacheln (Luftbild, DTK, Flurstücke) für den Parrig-Ausschnitt | im Artefakt, auf allen Geräten, Fotos als Anhänge |
| **`index.html`** | lokal öffnen oder per GitHub Pages | Live-Dienste von Geobasis NRW (ganz NRW) und OpenStreetMap | im Browser (localStorage), Export als Sicherung |

## Was die Karte kann

- **Grundkarten:** Luftbild (DOP, 10 cm), Topographische Karte (DTK), OpenStreetMap (nur `index.html`).
- **Fachebenen:** Jagdbezirke und Teilverpachtungen aus der Jagdbezirkskarte des Rhein-Erft-Kreises
  (der EJB Kerpener Parrig ist hervorgehoben), NSG Parrig (BM-004), FFH-Gebiet „Kerpener Bruch und Parrig“,
  weitere NSG der Umgebung, Flurstücke (ALKIS), Parrig-Umriss aus OpenStreetMap.
- **Eigene Einträge:** Hochsitz, Kanzel, Drückjagdbock, Kirrung, Salzlecke, Wildkamera, Suhle, Sammelplatz,
  Parkplatz, Gefahrenstelle, Wildunfall-Punkt, Notiz (Punkte); Wildwechsel, Pirschpfad, Reviergrenze (Linien);
  Einstand, Wildacker, Treiben (Flächen). Jeweils mit Name, Datum und Notiz; Länge und Fläche werden berechnet.
- **Fotos:** Bilder per Drag & Drop oder Dateiauswahl ablegen. Aufnahmeort und -zeit werden aus den EXIF-Daten gelesen
  (JPEG, HEIC, PNG, TIFF), die Bilder erscheinen als Bildmarker. Filter „Nur Fotos im Parrig“. Fotos ohne GPS lassen
  sich von Hand platzieren.
- **Werkzeuge:** Entfernung messen, eigener Standort, Koordinaten (WGS84 und UTM 32), Sonnenauf-/-untergang und
  bürgerliche Dämmerung für den Parrig.
- **Import/Export:** GPX und GeoJSON (z. B. für Garmin, Locus, QGIS), vollständige Sicherung als JSON.

## Fotos aus Apple Fotos mit Standort Parrig exportieren

Ohne Zusatzsoftware: Fotos-App → Suche „Parrig“ (oder Ansicht „Orte“, Karte auf den Parrig ziehen) → alle markieren →
**Ablage → Exportieren → Unverändertes Original exportieren** (behält die GPS-Daten). Beim normalen „Exportieren“ unter
„Einschließen“ den Haken bei **Ortsinformationen** setzen. Die Dateien anschließend in der Karte ablegen.

Automatisiert über das Rechteck des Parrig (Terminal auf dem Mac, benötigt [osxphotos](https://github.com/RhetTbull/osxphotos)):

```bash
pipx install osxphotos            # einmalig
tools/export_parrig_fotos.sh      # exportiert nach ~/Desktop/Parrig-Fotos
python3 tools/build_photo_index.py ~/Desktop/Parrig-Fotos   # Vorschaubilder + data/fotos.geojson
python3 tools/build.py            # index.html neu bauen, Fotos sind dann fest eingebaut
```

## Aufbau

```
index.html                      fertige Karte (Live-Dienste), wird von tools/build.py erzeugt
src/jagdkarte.template.html     Vorlage (Layout, Logik)
src/vendor/leaflet-1.9.4.css    Leaflet-Stylesheet (wird eingebettet)
data/schutzgebiete.geojson      NSG- und FFH-Grenzen um Kerpen (LANUV NRW)
data/jagdbezirke.geojson        Jagdbezirke (Rhein-Erft-Kreis), vereinfacht auf ca. 1,5 m
data/teilverpachtungen.geojson  Teilverpachtungen (Rhein-Erft-Kreis)
data/parrig_osm.geojson         Parrig-Umriss aus OpenStreetMap
tools/build.py                  baut index.html bzw. die Artefakt-Seite (--artifact)
tools/fetch_geodata.py          lädt die Fachdaten neu (WFS LANUV, ArcGIS REST des Kreises, Nominatim)
tools/fetch_tiles.py            lädt Luftbild-/DTK-/ALKIS-Kacheln für die Offline-/Artefakt-Variante
tools/export_parrig_fotos.sh    Export aus Apple Fotos nach Aufnahmeort
tools/build_photo_index.py      erzeugt Vorschaubilder und data/fotos.geojson
```

Neu bauen: `python3 tools/build.py`. Artefakt-Variante: `python3 tools/fetch_tiles.py tiles/` und
`python3 tools/build.py --artifact dist/jagdkarte.html`.

## Datenquellen und Lizenzen

- Luftbild (DOP), Topographische Karte (DTK), Flurstücke (ALKIS): © Geobasis NRW,
  [Datenlizenz Deutschland – Namensnennung – Version 2.0](https://www.govdata.de/dl-de/by-2-0).
  Dienste: `www.wms.nrw.de/geobasis/wms_nw_dop`, `wms_nw_dtk`, `wms_nw_alkis`.
- Jagdbezirke: Jagdbezirkskarte des Rhein-Erft-Kreises, Geodatenportal des Kreises
  (<https://www.rhein-erft-kreis.de/infrastruktur/bauen/inhaltsseiten/geodaten-portale.php>), Abfrage am 06.11.2026
  über den Kartendienst `WMS/WMS_REK_Jagdbezirkskarte`. Ohne Gewähr; rechtsverbindlich ist die Untere Jagdbehörde.
- Schutzgebiete: LANUV NRW, LINFOS-WFS (`www.wfs.nrw.de/umwelt/linfos`).
- Parrig-Umriss: © OpenStreetMap-Mitwirkende, ODbL.
- Karte: [Leaflet](https://leafletjs.com) (BSD-2-Clause). EXIF: [exifr](https://github.com/MikeKovarik/exifr) (MIT).

Die Kacheln für die Artefakt-Variante decken den Bereich 50,880–50,918 N / 6,680–6,730 O ab (ca. 3,5 × 4,2 km).

# Offene-Posten-Listen Mieter

Stand der Daten: Immocloud, gelesen am 07.11.2026 (Bestandsaufnahme `NAS/alle/Immocloud_Export_2026-11-07`).
Erstellt am 12.11.2026.

| Datei | Inhalt |
|---|---|
| `Offene-Posten_Mieter_2026-11-12.xlsx` | Arbeitsmappe: Übersicht nach Gesellschaft und Haus, ein Blatt je Gesellschaft mit allen Mietern, Rohdaten (`Daten`), Hinweise |
| `OP-Listen_Gesamt_2026-11-12.pdf` | Alle Gesellschaften, Übersicht plus eine Seite je Haus |
| `OP-Liste_eGbR_2026-11-12.pdf` | Käshammer und Penkhues Immobilien eGbR (7 Häuser) |
| `OP-Liste_KPK-Grundbesitz-GmbH_2026-11-12.pdf` | KPK Grundbesitz GmbH (3 Häuser) |
| `OP-Liste_PK-Immo-Verwaltungs-GmbH_2026-11-12.pdf` | PK Immo Verwaltungs GmbH (2 Häuser) |

## Aktualisieren

Werte in `tools/daten.json` anpassen (Saldo, Soll-Miete, offene Novembermiete je Einheit), dann:

```bash
python3 tools/build_xlsx.py tools/daten.json Offene-Posten_Mieter_<Datum>.xlsx
python3 tools/build_pdf.py  tools/daten.json .
```

Die Excel-Datei danach einmal in Excel oder LibreOffice öffnen und speichern, damit die Formeln berechnet sind
(in der Cloud-Sitzung übernimmt das `recalc.py` der xlsx-Fähigkeit).

Lesart und Vorbehalte stehen im Blatt `Hinweise` der Arbeitsmappe und auf Seite 1 der PDFs.

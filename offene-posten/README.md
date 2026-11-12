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

## Zahlungsabgleich (Pilot, 12.11.2026)

`Zahlungsabgleich_Pilot_Adenau_Velbert_2026-11-12.xlsx` gleicht die tatsächlichen Mieteingänge mit dem Soll ab:

- Adenau (Konto …4404): aus dem Kassenbuch `NAS/alle/Kassenbuch GbR BH neu.xlsx`, Blatt Adenau (vollständig bis 10.11.2026).
- Velbert (Konto …4401): aus den Volksbank-Kontoauszügen 12/2025 und 02–09/2026 (`NAS/alle/Rechnungen/Käshammer und Penkhues Immobilien GbR/Umsätze VB`).

Die übrigen sieben Konten konnten noch nicht ausgewertet werden: Die Kassenbuch-Blätter sind über die
Microsoft-365-Schnittstelle nur bis ca. Zeile 1.000 lesbar (Krefeld bis 05/2023, Bickernstr bis 04/2023,
Wilhelmstr bis 08/2024, Lenaustr bis 01/2026, Gelsenkirchen Breilstr bis 12/2024, Gymnich bis 2022/2025),
und Kontoauszüge liegen auf der NAS nur für Velbert vor. Datenbasis und Skript: `tools/zahlungsabgleich/`.

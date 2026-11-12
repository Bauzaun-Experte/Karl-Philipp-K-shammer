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

## Zahlungsabgleich mit Bankkonten (12.11.2026)

`Zahlungsabgleich_2026_2026-11-12.xlsx` stellt die tatsächlichen Mieteingänge je Mieter und Monat (Januar bis
September 2026) dem Soll gegenüber. Die Ergebnisse stehen auch in den OP-Listen (Excel-Spalten
`Bankbefund` und `Rückstand lt. Bank`, in den PDFs unter `Bank:` in der Spalte Hinweis).

| Haus (Konto) | Quelle | Zeitraum |
|---|---|---|
| Adenau Haus 17 + 19 (…4404) | Kassenbuch `NAS/alle/Kassenbuch GbR BH neu.xlsx`, Blatt Adenau | bis 10.11.2026 |
| Velbert Haus 17 + 19 (…4401) | Volksbank-Kontoauszüge (`NAS/alle/Rechnungen/Käshammer und Penkhues Immobilien GbR/Umsätze VB`) | 12/2025–09/2026 |
| Krefeld Ritterstr 295 (…5000) | Volksbank-Kontoauszüge PK Immo Verwaltungs GmbH (NAS/alle) | 12/2025–09/2026 |
| Gelsenkirchen Bickernstr 102 (…5001) | Volksbank-Kontoauszüge PK Immo Verwaltungs GmbH (NAS/alle) | 12/2025–09/2026 |
| Breilstr, Gymnich 2/3, Duisburg, Lenaustr | nur Zahlerübersicht Juli–September 2026 aus dem Projekt „Vermietung“ | 07–09/2026 |

Jeder Kontoauszug wurde beim Einlesen über die Saldenprüfung (alter Kontostand + Buchungen = neuer Kontostand)
kontrolliert; alle 30 Auszüge stimmen. `Rückstand lt. Bank` = Soll Januar–September 2026 (9 Monate, Immocloud-Soll
bzw. Dauerzahlung) minus Mieteingänge für diese Monate; negativ = Guthaben. Oktober und November 2026 sind nicht
enthalten, weil die Auszüge dafür noch nicht auf der NAS liegen. Für Breilstr, Gymnich, Duisburg und Lenaustr fehlen die
Auszüge ganz (NAS-Freigabe `intern`, noch nicht in OneDrive kopiert).

Ablauf (Skripte in `tools/zahlungsabgleich/`):

1. `parse_vb.py` liest die Kontoauszug-Texte (Volksbank-PDF als Text) in eine Buchungsliste je Konto
   (`<Konto>_buchungen.json`, nicht im Repository, enthält Bankdaten Dritter).
2. `mapping.json` ordnet Zahler (Muster auf den Verwendungszweck) den Einheiten und dem Soll zu.
3. `bankregeln.py` enthält die gemeinsamen Regeln: Leistungsmonat (Nennung im Verwendungszweck, sonst Buchungstag,
   ab dem 25. = Folgemonat), Erkennung von Mietzahlungen (keine Umbuchungen, Kautionen, Versicherungen,
   Nebenkosten-Nachzahlungen) und die Auffüll-Zuordnung für unregelmäßige Zahler.
4. `konsolidieren.py <op-verzeichnis> <ausgabe.xlsx>` erzeugt die Arbeitsmappe; `befunde.py <op-verzeichnis>` schreibt
   die Befunde je Einheit (`konsolidiert_befunde.json`); `../bankbefund.py <op-verzeichnis>` überträgt sie in `daten.json`.
5. Danach `build_xlsx.py` und `build_pdf.py` wie oben.

Der frühere Pilot (`Zahlungsabgleich_Pilot_Adenau_Velbert_2026-11-12.xlsx`, `tools/zahlungsabgleich/build_pilot.py`) bleibt
als Quelle für das Adenau-Blatt erhalten.

#!/usr/bin/env python3
"""Bankbefunde je Einheit für Krefeld (18375000) und Bickernstr (18375001) aus den Kontoauszügen 12/2025–09/2026.
Schreibt konsolidiert_befunde.json mit Schlüssel 'Objekt||Einheit' (wie daten.json): {"text": ..., "rest": Rückstand bis 09/2026 (negativ = Guthaben) oder null}.
Aufruf: befunde.py <scratch-op-dir>"""
import sys, json, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bankregeln import is_rent_credit, zuordnen, nk_zahlung, anteile_umlegen
S = sys.argv[1]
KONTEN = ["18375000", "18375001"]
MONTHS = [f"2026-{m:02d}" for m in range(1, 10)]
def fmt(x): return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def dd(datum): return datum[:6]  # dd.mm.
# Ergänzende Hinweise je Einheit (Erkenntnisse aus den Auszügen und Abgleich mit Immocloud)
NOTES = {
 ("MFH Krefeld Ritterstr 295", "1.OG hinten"): "Zahlt 500 € per Dauerauftrag ‚Miete und Nebenkosten‘; darin 10 € Anteil am Hof-Stellplatz (Zusatzvereinbarung 28.09.2020), bleiben 490 € für die Wohnung gegenüber Immocloud-Soll 460 € (ob die 10 € dort enthalten sind, ist nicht erkennbar – Mietvertrag nur als Scan). Immocloud führt 11/2026 als offen, obwohl die Zahlungen regelmäßig eingehen – Soll und Zuordnung prüfen.",
 ("MFH Krefeld Ritterstr 295", "EG vorne"): "380 € per Dauerauftrag ‚Miete und Stellplatz‘ = 370 € Wohnung + 10 € Anteil am Hof-Stellplatz (Zusatzvereinbarung 28.09.2020).",
 ("MFH Krefeld Ritterstr 295", "Stellplatz Hof"): "Zusatzvereinbarung vom 28.09.2020: PKW-Stellplatz im Hof, 30 €/Monat ab 01.10.2020, je 1/3 (10 €) für Olaf Schlieper, Ramona Lenz und Ralf Francki. Lenz und Francki zahlen ihren Anteil mit der Miete (in 380 € bzw. 500 € enthalten). Schlieper ist in Immocloud nicht mehr als Mieter geführt und zahlt 2026 nichts – sein Drittel (10 €/Monat) ist unbesetzt; laut Vereinbarung können die übrigen Mieter den Anteil übernehmen, sonst Kündigungsrecht des Vermieters. Der Stellplatz ist in Immocloud nicht angelegt (keine Sollstellung).",
 ("MFH Krefeld Ritterstr 295", "1.OG mitte"): "Mietvertrag vom 22.05.2020: 360 € warm (270 + 55 + 35), kein Stellplatz. Zahlt 410 € statt Immocloud-Soll 380 €; NKA-Guthaben 2024/25 von 226,49 € am 30.03.2026 ausgezahlt. Immocloud-Saldo −190 € passt nicht zu den Eingängen – Soll und Zuordnung prüfen.",
 ("MFH Krefeld Ritterstr 295", "1.OG vorne"): "Jobcenter zahlte die Miete (735 €) nur für 01–04/2026 (zuletzt 31.03.2026); daneben ‚Tilgung Mietschulden‘ 110 €/Monat für 01–06/2026 und 105 € am 17.07.2026 (Altschulden, im Ist enthalten). Seit 08/2026 kein Eingang. Mietende/Auszug lt. NAS-Fotos (‚Wohnung ehemals Hilgers‘) in Immocloud nachtragen und Soll ab Auszug stornieren.",
 ("MFH Krefeld Ritterstr 295", "2.OG mitte"): "Jobcenter zahlte 01–04/2026 875 €, seit 05/2026 840 €.",
 ("MFH Krefeld Ritterstr 295", "2.OG vorne"): "Zahlungen 700 € (29.12., 30.01., 27.02., 29.04., 28.05.), 1.400 € (19.06.) und 750 € (02.07., 31.07., 31.08., 30.09.); für 04/2026 keine eigene Zahlung, 06/2026 Doppelzahlung. Immocloud-Soll 665 € liegt unter den gezahlten 700/750 € und Immocloud zeigt −290 € – Soll und Zuordnung prüfen.",
 ("MFH Krefeld Ritterstr 295", "DG vorne"): "01–03/2026 745 €, seit 04/2026 695 €.",
 ("MFH Krefeld Ritterstr 295", "EG mitte"): "Kein Eingang seit mindestens 12/2025. Forderung 02–09/2026 (8 × 303,45 = 2.427,60 €) liegt beim Anwalt (OP-Liste Projekt MI-09).",
 ("MFH Krefeld Ritterstr 295", "Glas WS"): "01–03/2026 362 €, seit 04/2026 427 € (Dauerauftrag zum Monatsende für den Folgemonat). NK-Nachzahlungen 130,83 € (23.02.) und 858,77 € (02.03.2026) zusätzlich eingegangen. Immocloud-Saldo −545 € – Herkunft prüfen; aus den Auszügen ergeben sich nur 3 × 65 € = 195 €, falls das Soll 427 € schon ab 01/2026 galt.",
 ("MFH Krefeld Ritterstr 295", "Schreinerei"): "01–03/2026 882,75 €, seit 04/2026 1.011,50 € (07/2026 in zwei Teilen: 11,50 € + 1.000 €). NK-Nachzahlungen 139,71 € (16.01.) und 1.570,66 € (30.03.2026) zusätzlich eingegangen. Immocloud-Saldo −726,65 € – Herkunft prüfen; aus den Auszügen ergeben sich nur 3 × 128,75 € = 386,25 €, falls das Soll 1.011,50 € schon ab 01/2026 galt.",
 ("MFH Krefeld Ritterstr 295", "WS OG hinten"): "01–02/2026 458,15 €, seit 03/2026 464,10 € statt Soll 505,75 €.",
 ("MFH Gelsenkirchen Bickernstr 102", "1.OG"): "Stadt Gelsenkirchen zahlt für 01–06/2026 1.415 € (1.212,86 + 202,14), seit 07/2026 1.505 € (1.290 + 215); gegenüber Immocloud-Soll 1.605 € fehlen 190 bzw. 100 €/Monat (Eigenanteil). Oktober (1.505 €) bereits am 30.09. eingegangen. Zusätzlich BKA 2024/2025 und NK-Nachzahlungen der Stadtkasse 4.645,17 € am 15./17.06.2026 (keine Miete).",
 ("MFH Gelsenkirchen Bickernstr 102", "2.OG lks"): "Zahlt 758,47 € für die Wohnung (Soll 788,47 € → 30 €/Monat zu wenig) plus 50 € Garage 15; 08/2026 nur 250 € (508,47 € fehlen). NK-Raten 95,52 € (22.01.), 117,58 € (27.01.), 58,79 € (22.05.) und 58,79 € (06.07.) zusätzlich. Immocloud-Saldo −838,47 € passt zu den Auszügen.",
 ("MFH Gelsenkirchen Bickernstr 102", "2.OG rts"): "Jobcenter 460 € für 01–02/2026, 504 € seit 03/2026 (jeweils am Monatsende für den Folgemonat), dazu Edelgard Dahms 85 €/Monat (‚Mietdifferenz‘). Immocloud zeigt dagegen Guthaben 181 €.",
 ("MFH Gelsenkirchen Bickernstr 102", "DG Hof"): "Jobcenter zahlt 415 € jeweils am Monatsende für den Folgemonat (01/2026: 395 € am 30.12.2025 + 20 € am 08.01.2026); 10/2026 bereits am 30.09. eingegangen. Immocloud-Saldo −415 € und ‚11/2026 offen‘ beruhen vermutlich auf der Zuordnung der Monatsende-Zahlung zum laufenden Monat – prüfen.",
 ("MFH Gelsenkirchen Bickernstr 102", "DG lks"): "05/2026 nur 312,76 €: 20,54 € lt. Mieter mit NK-Guthaben verrechnet (Immocloud-Saldo 0) – daher kein Rückstand ausgewiesen.",
 ("MFH Gelsenkirchen Bickernstr 102", "DG rts"): "442,40 € = 392,40 € Wohnung + 50 € Garage 14; Heiz-/NK-Nachzahlung 2024 von 223,86 € am 22.12.2025.",
 ("MFH Gelsenkirchen Bickernstr 102", "EG Gewerbe"): "Acht Zahlungen à 1.695,75 € für 01–09/2026 (28.01., 23.02., 27.03., 22.04., 26.05., 24.06., 24.07., 01.09.) → eine Monatsmiete fehlt. NK-Raten 3 × 240 € (07.04., 15.05., 05.08.) zusätzlich. Immocloud-Saldo −357 € – prüfen.",
 ("MFH Gelsenkirchen Bickernstr 102", "Garage 1"): "Dauerauftrag (90 + 86,50 €) lief nur noch 01/2026, danach bis 07/2026 kein Eingang; am 05.08.2026 2 × 90 €. Immocloud zeigt nur −265,50/−267 € (Garage 1/16), die Auszüge deutlich mehr.",
 ("MFH Gelsenkirchen Bickernstr 102", "Garage 3"): "180 € monatlich für die Garagen 3, 7 und 9 (Soll 3 × 59,50 = 178,50 €).",
 ("MFH Gelsenkirchen Bickernstr 102", "Garage 6"): "Zahlt 60 € monatlich (Soll 59,50 €). Immocloud-Saldo −104 € widerspricht den Auszügen – prüfen.",
 ("MFH Gelsenkirchen Bickernstr 102", "Garage 8"): "179,30 € monatlich für die Garagen 8, 10 und 11 (Soll 3 × 59,50 = 178,50 €). Immocloud-Saldo −119 € je Garage widerspricht den Auszügen – prüfen.",
 ("MFH Gelsenkirchen Bickernstr 102", "Fläche Hauswand Plakatwerbung 1"): "Vierteljährliche Zahlung; nächste Rate 10/2026 nicht mehr in den vorliegenden Auszügen.",
 ("MFH Gelsenkirchen Bickernstr 102", "Fläche Hauswand Plakatwerbung 2"): "Vierteljährliche Zahlung; nächste Rate 10/2026 nicht mehr in den vorliegenden Auszügen.",
}
REST_OVERRIDE = {("MFH Gelsenkirchen Bickernstr 102", "DG lks"): 0.0}
# Einheiten, deren Zahlung in einer anderen Einheit enthalten ist
ENTHALTEN = {
 ("MFH Gelsenkirchen Bickernstr 102", "Garage 14"): "In der Zahlung für DG rts (Serowiak, 442,40 €) enthalten: 50 €/Monat, 01–09/2026 vollständig.",
 ("MFH Gelsenkirchen Bickernstr 102", "Stellplatz 1"): "In der Gewerbemiete Maik Keller (1.695,75 € = 1.636,25 + 2 × 29,75) enthalten – siehe EG Gewerbe.",
 ("MFH Gelsenkirchen Bickernstr 102", "Stellplatz 2"): "In der Gewerbemiete Maik Keller (1.695,75 € = 1.636,25 + 2 × 29,75) enthalten – siehe EG Gewerbe.",
}
mapping = json.load(open(f"{S}/bank/mapping.json", encoding="utf-8"))
out = {}
for konto in KONTEN:
    cfg = mapping[konto]; obj = cfg["objekt"]
    bk = json.load(open(f"{S}/bank/{konto}_buchungen.json", encoding="utf-8"))
    PER = {}
    for r in cfg["regeln"]:
        hits = [b for b in bk if b["betrag"] > 0 and re.search(r["muster"], b["text"], re.I)]
        PER[r["einheit"]] = zuordnen([b for b in hits if is_rent_credit(b)], r["soll"], r.get("verteilung"))
    anteile_umlegen(PER, cfg["regeln"])
    for r in cfg["regeln"]:
        per = PER[r["einheit"]]
        inwin = [(d, a) for m in MONTHS for d, a, _, _ in per.get(m, [])]
        ist = round(sum(a for _, a in inwin), 2)
        # Monatsbeträge als Läufe zusammenfassen: "01–04: 875,00; 05–09: 840,00; 04: –"
        mon = [(m[5:], round(sum(a for _, a, _, _ in per.get(m, [])), 2) if per.get(m) else None) for m in MONTHS]
        runs = []
        for mm, v in mon:
            if runs and runs[-1][2] == v: runs[-1][1] = mm
            else: runs.append([mm, mm, v])
        zahl = "kein Eingang" if not inwin else "; ".join((f"{a}–{b}" if a != b else a) + ": " + (fmt(v) if v is not None else "–") for a, b, v in runs)
        last = max(inwin, key=lambda x: (x[0][6:10], x[0][3:5], x[0][:2]))[0] if inwin else None
        parts = [f"Auszüge 01–09/2026: Ist {fmt(ist)} € (Monat: {zahl})" + (f", letzte Zahlung {last}" if last and (last[6:10], last[3:5]) < ("2026", "08") else "")]
        if r["soll"]:
            soll = round(r["soll"] * 9, 2); rest = round(soll - ist, 2)
            parts.append(f"Soll 9 × {fmt(r['soll'])} = {fmt(soll)} € ({r['soll_quelle']})")
            if rest > 0.005: parts.append(f"→ Rückstand {fmt(rest)} € bis 09/2026")
            elif rest < -0.005: parts.append(f"→ Guthaben {fmt(-rest)} € bis 09/2026")
            else: parts.append("→ ausgeglichen bis 09/2026")
        else:
            rest = None; parts.append(f"kein monatliches Soll ({r['soll_quelle']})")
        text = "; ".join(parts) + "."
        einheiten = r["einheit"].split(" + ")
        if len(einheiten) > 1: einheiten = [einheiten[0]] + ["Garage " + x if x.isdigit() else x for x in einheiten[1:]]
        for i, e in enumerate(einheiten):
            key = (obj, e)
            if i == 0:
                t = text + ((" " + NOTES[key]) if key in NOTES else "")
                rr = REST_OVERRIDE.get(key, rest)
            else:
                t = f"Gemeinsame Zahlung mit {einheiten[0]} ({r['mieter']}) – Befund und Rückstand dort ausgewiesen."; rr = 0.0 if rest is not None else None
            out[f"{obj}||{e}"] = {"text": t, "rest": rr}
for (obj, e), t in ENTHALTEN.items(): out[f"{obj}||{e}"] = {"text": t, "rest": 0.0}
json.dump(out, open(f"{S}/bank/konsolidiert_befunde.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in out.items(): print(f"{k.split('||')[1][:24]:24s} | Rest {str(v['rest']):>8} | {v['text'][:170]}")

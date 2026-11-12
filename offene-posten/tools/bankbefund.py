#!/usr/bin/env python3
"""Ergänzt daten.json je Einheit um 'bank' (Text) und 'bank_rest' (Zahl) aus (a) Projekt-Zahlerdaten Jul–Sep 2026,
(b) eigenen Auszugs-/Kassenbuch-Auswertungen (Velbert, Adenau; Krefeld/Bickernstr aus Konsolidierung, falls vorhanden)."""
import json, re, sys, os, unicodedata
from collections import defaultdict
S = sys.argv[1]
d = json.load(open(f"{S}/daten.json", encoding="utf-8"))
zahler = json.load(open(f"{S}/dashboard/assets/fcd7d1cac4c33db5f0691d163778a7c2.json", encoding="utf-8"))
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", " ", s)
OBJ_ID = {"MFH Adenau Haus 17": "adenau", "MFH Adenau Haus 19": "adenau", "MFH Gelsenkirchen Breilstr 16": "breil", "MFH Gymnich 2": "kerpener", "MFH Gymnich 3": "burgweg",
          "MFH Velbert Haus 17": "velbert", "MFH Velbert Haus 19": "velbert", "MFH Duisburg Wilhelmstr 4": "duisburg", "MFH Gelsenkirchen Lenaustr 10": "lenau",
          "MFH Gelsenkirchen Lenaustr 12": "lenau", "MFH Gelsenkirchen Bickernstr 102": "bickern", "MFH Krefeld Ritterstr 295": "krefeld"}
ALIAS = {"nurova": "murodov", "mossati": "amagtir", "schmale": "hartmann", "sulejmani": "suleymani", "jorg keller": "jorg keller", "pufe": "puffe", "kleibomer": "kleiblomer",
         "moennig": "monnig", "loulla": "sideritaki", "petrovics": "petrovic", "doenmez": "doenmez", "sabanovski": "suleymani", "blomer": "blomer", "hubeker": "hubeker", "huth": "skotz", "specht": "skotz"}
def fmt(x): return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
# (a) Projektzahler je Objekt-ID
by_id = defaultdict(list)
for z in zahler: by_id[z["id"]].append(z)
def match_units(z, units):
    zn = norm(z["zahler"])
    for a, b in ALIAS.items():
        if a in zn: zn = zn + " " + b
    hits = []
    for e in units:
        if e["status"] == "Leerstand": continue
        toks = [t for t in norm(e["mieter"]).split() if len(t) >= 4 and t not in ("und", "familie", "gmbh")]
        if any(t in zn for t in toks): hits.append(e)
    # Spezialfälle
    if "keller" in zn:
        if "maik" in zn or "gewerbe" in norm(z["verwendungszweck"]): hits = [e for e in hits if "Maik" in e["mieter"]]
        elif "jorg" in zn: hits = [e for e in hits if "Jörg" in e["mieter"]]
    if "dahms" in zn: hits = [e for e in units if "Dahms" in e["mieter"]]
    return hits
for g in d["gesellschaften"]:
    for o in g["objekte"]:
        oid = OBJ_ID[o["objekt"]]
        units = o["einheiten"]
        found = defaultdict(list)
        for z in by_id.get(oid, []):
            # Objekt Adenau/Velbert/Lenau umfasst mehrere Immocloud-Objekte: nur Einheiten dieses Objekts
            for e in match_units(z, units):
                found[id(e)].append(z)
        for e in units:
            zs = found.get(id(e), [])
            if not zs: continue
            parts = []
            for z in zs:
                n = int(z["monate_gezahlt"]); amt = float(z["miete_monat"])
                parts.append(f"{z['zahler']}: {n} von 3 Monaten je {fmt(amt)} €, zuletzt {z['letzte_zahlung'][8:10]}.{z['letzte_zahlung'][5:7]}.{z['letzte_zahlung'][:4]}")
            e["bank"] = "Projekt-Bankdaten Jul–Sep 2026: " + "; ".join(parts)
            if any(int(z["monate_gezahlt"]) < 3 for z in zs): e["bank"] += " – nicht in allen drei Monaten gezahlt"
# Zahler ohne Immocloud-Einheit (z. B. Briefkasten Schiemann) als Hinweis am Objekt
d.setdefault("bank_hinweise", [])
# (b) eigene Auswertungen
EIGEN = {
 ("MFH Adenau Haus 19", "1.OG"): ("Kassenbuch bis 10.11.2026: 01–11/2026 jeden Monat 520 € (inkl. Stellplatz) bezahlt, zuletzt 28.10.2026 für 11/2026. Immocloud führt 11/2026 fälschlich als offen.", 0.0),
 ("MFH Adenau Haus 19", "Stellplatz"): ("Kassenbuch bis 10.11.2026: in den 520 € monatlich enthalten, 01–11/2026 bezahlt.", 0.0),
 ("MFH Adenau Haus 19", "EG rts"): ("Kassenbuch bis 10.11.2026: 01–11/2026 je 465 € statt 470 € Soll, zuletzt 02.11.2026; NKA 2024 in vier Raten à 142,75 € beglichen. Rückstand 11 × 5 € = 55 €.", 55.0),
 ("MFH Adenau Haus 19", "Garage 2"): ("Kassenbuch bis 10.11.2026: bezahlt bis 09/2026 (07.09.2026 für 07–09/2026); 10/2026 und 11/2026 offen.", 120.0),
 ("MFH Adenau Haus 19", "Garage 3"): ("Kassenbuch bis 10.11.2026: nur 50 € (04/2026 für 05/2026) und 40 € (07.09.2026 für 09/2026) als zweite Garagenzahlung; Soll 30 €/Monat und Zuordnung klären.", None),
 ("MFH Adenau Haus 19", "Garage 1"): ("Kassenbuch: Christoph Büntgens zahlte bis 03/2026 30 €/Monat für die Garage gegenüber Haus 19, seitdem nichts; in Immocloud nicht geführt (OP-Liste Projekt AL-04).", None),
 ("MFH Adenau Haus 17", "EG lks"): ("Kassenbuch: Renate Schulz zahlte bis 07/2026 (ab 02/2026 465 €), Auszug 31.07.2026; Kaution 504 € offen zu verrechnen (OP-Liste Projekt AL-01).", None),
 ("MFH Velbert Haus 19", "EG"): ("Auszüge 01–09/2026: je 1.000 € per Dauerauftrag zum Monatsersten.", 0.0),
 ("MFH Velbert Haus 19", "1.OG"): ("Auszüge 01–09/2026: 01/2026 650 €, 02–09/2026 je 670 € (Immocloud-Soll 674 €); Differenz 24 + 8 × 4 = 56 € bis 09/2026.", 56.0),
 ("MFH Velbert Haus 19", "DG"): ("Auszüge: 08/2026 1.135 € (03.08.), 09/2026 1.135 € (02.09., Umbuchung vom eGbR-Hauptkonto).", 0.0),
 ("MFH Velbert Haus 19", "EG hinten"): ("Auszüge 01–09/2026: je 540 € per Dauerauftrag; NKA 2024 163,45 € am 05.01.2026 nachgezahlt.", 0.0),
 ("MFH Velbert Haus 17", "EG"): ("Auszüge 01–09/2026: je 662 € per Dauerauftrag.", 0.0),
 ("MFH Velbert Haus 17", "DG"): ("Auszüge: Miete 01–10/2026 je 701,93 € per Dauerauftrag, jeweils am 28. des Vormonats.", 0.0),
 ("MFH Velbert Haus 17", "Surterrain"): ("Auszüge 01–09/2026: je 435 € per Dauerauftrag (Immocloud-Soll 440 €); Differenz 9 × 5 = 45 € bis 09/2026.", 45.0),
}
# Krefeld / Bickernstr aus Konsolidierung (falls vorhanden)
KONS = set()
kons = f"{S}/bank/konsolidiert_befunde.json"
if os.path.exists(kons):
    for k, v in json.load(open(kons, encoding="utf-8")).items():
        obj, einheit = k.split("||"); EIGEN[(obj, einheit)] = (v["text"], v.get("rest")); KONS.add((obj, einheit))
for g in d["gesellschaften"]:
    for o in g["objekte"]:
        for e in o["einheiten"]:
            k = (o["objekt"], e["einheit"])
            if k in EIGEN:
                txt, rest = EIGEN[k]
                e["bank"] = txt + ((" | " + e["bank"]) if e.get("bank") and "Projekt" in e["bank"] and k not in KONS else "")
                e["bank_rest"] = rest
json.dump(d, open(f"{S}/daten.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = sum(1 for g in d["gesellschaften"] for o in g["objekte"] for e in o["einheiten"] if e.get("bank"))
print("Einheiten mit Bankbefund:", n)
for g in d["gesellschaften"]:
    for o in g["objekte"]:
        for e in o["einheiten"]:
            if e["status"] != "Leerstand" and not e.get("bank"): print("  ohne Befund:", o["objekt"], "|", e["einheit"], "|", e["mieter"])

#!/usr/bin/env python3
"""Parst den Text von Volksbank-Kontoauszügen (read_resource-Ausgabe) in Buchungen.
Aufruf: parse_vb.py <txt-Datei> [...]  -> JSON-Liste auf stdout, Saldenprüfung je Datei auf stderr"""
import sys, re, json
KINDS = r"Dauerauftragsgutschr|Überweisungsgutschr\.|Umbuchung|Basislastschrift|Überweisungsauftrag|Dauerauftragsbelast|Darlehenstilgung|Abschluss|Gutschrift|Lastschrift|Bareinzahlung|Barauszahlung|Scheck|Zinsen/Entgelt|Firmenlastschrift|Echtzeit-Überweisung|Echtzeitüberweisung|Sammelüberweisung|Rücküberweisung|Retoure|Storno|Kartenzahlung|Zahlungseingang|Gutschr\.|Belastung|Entgeltabschluss|Überweisung"
START = r"(\d\d\.\d\d\.)\s+(\d\d\.\d\d\.)\s+(" + KINDS + r")(?:\s+lt\.\s+Anlage\s+\d+)?\s+([\d\.]+,\d\d)\s+(H|S)"
START_NC = r"\d\d\.\d\d\.\s+\d\d\.\d\d\.\s+(?:" + KINDS + r")(?:\s+lt\.\s+Anlage\s+\d+)?\s+[\d\.]+,\d\d\s+(?:H|S)"
ENTRY = re.compile(START + r"\s*(.*?)(?=" + START_NC + r"|Übertrag\s+auf|neuer\s+Kontostand|──|Anlage\s+1\s+(?:\d\d\.\d\d\.\d{4}|Buchungstag|Wert)|$)", re.S)
def amt(s): return float(s.replace(".", "").replace(",", "."))
def parse_file(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"\s+", " ", t)
    m = re.search(r"(\d{8})\s+(\d{1,2})/(\d{4})", t)
    konto, mon, year = (m.group(1), int(m.group(2)), int(m.group(3))) if m else ("?", 0, 0)
    alt = re.search(r"alter\s+Kontostand\s+vom\s+(\d\d\.\d\d\.\d{4})\s+(?:Wert\s+Vorgang\s+)?([\d\.]+,\d\d)\s+(H|S)", t)
    neu = re.search(r"neuer\s+Kontostand\s+v(?:om|\.)\s+(\d\d\.\d\d\.\d{4})\s+([\d\.]+,\d\d)\s+(H|S)", t)
    out = []
    for e in ENTRY.finditer(t):
        bu, wert, kind, a, hs, rest = e.groups()
        rest = re.split(r"\s+(?:erstellt am Blatt|Übertrag von Blatt)", rest.strip())[0].strip()
        val = amt(a) if hs == "H" else -amt(a)
        bm = int(bu[3:5]); y = year
        if mon == 1 and bm == 12: y = year - 1
        out.append({"konto": konto, "auszug": f"{mon:02d}/{year}", "datum": f"{bu}{y}", "valuta": wert, "art": kind,
                    "betrag": round(val, 2), "text": rest[:300], "datei": path.split("/")[-1]})
    name = path.split("/")[-1]
    if alt and neu:
        a0 = amt(alt.group(2)) * (1 if alt.group(3) == "H" else -1)
        n0 = amt(neu.group(2)) * (1 if neu.group(3) == "H" else -1)
        s = sum(x["betrag"] for x in out)
        ok = abs(a0 + s - n0) < 0.01
        print(f"{'OK      ' if ok else 'MISMATCH'} {name}: alt {a0:.2f} + Buchungen {s:.2f} = {a0+s:.2f} | neu lt. Auszug {n0:.2f} | {len(out)} Buchungen", file=sys.stderr)
    else:
        print(f"KEIN SALDO GEFUNDEN {name}: {len(out)} Buchungen", file=sys.stderr)
    return out
if __name__ == "__main__":
    res = []
    for p in sys.argv[1:]: res.extend(parse_file(p))
    json.dump(res, sys.stdout, ensure_ascii=False, indent=1)

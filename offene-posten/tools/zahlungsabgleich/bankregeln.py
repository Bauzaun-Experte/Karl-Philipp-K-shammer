"""Gemeinsame Regeln für den Zahlungsabgleich: Leistungsmonat einer Gutschrift und Erkennung von Mietzahlungen."""
import re
MONNAMES = {r"\bjanuar\b":1, r"\bfebruar\b":2, r"\bm(ä|ae|a)rz\b":3, r"\bapril\b":4, r"\bmai\b":5, r"\bjuni\b":6, r"\bjuli\b":7, r"\baugust\b":8,
            r"\bseptember\b":9, r"\boktober\b":10, r"\bnovember\b":11, r"\bdezember\b":12,
            r"\bjan\b":1, r"\bfeb\b":2, r"\bmrz\b":3, r"\bapr\b":4, r"\bjun\b":6, r"\bjul\b":7, r"\baug\b":8, r"\bsep\b":9, r"\bsept\b":9, r"\bokt\b":10, r"\bnov\b":11, r"\bdez\b":12}
def leistungsmonat(datum, text):
    """Monat, für den eine Mietzahlung bestimmt ist: Monatsnennung im Text (L-Code, MM/JJJJ, Monatsname), sonst Buchungstag >= 25 -> Folgemonat."""
    d, m, y = int(datum[:2]), int(datum[3:5]), int(datum[6:10])
    t = text.lower()
    mm = re.search(r"\bL(\d\d)\.(\d\d)\b", text)                    # Stadt Gelsenkirchen: L10.26 = Leistungsmonat 10/2026
    if mm: return f"20{mm.group(2)}-{mm.group(1)}", "Text (L-Code)"
    mm = re.search(r"\b(0?[1-9]|1[0-2])[./](20(2[5-7]))\b", t)       # 10/2026, 10.2026
    if mm: return f"{mm.group(2)}-{int(mm.group(1)):02d}", "Text (MM/JJJJ)"
    for name, num in MONNAMES.items():
        if re.search(name, t):
            yy = y
            if num == 12 and m == 1: yy = y - 1
            if num == 1 and m == 12: yy = y + 1
            return f"{yy}-{num:02d}", "Text (Monatsname)"
    if d >= 25:
        m2, y2 = m + 1, y
        if m2 == 13: m2, y2 = 1, y + 1
        return f"{y2}-{m2:02d}", "Buchungstag ≥ 25. → Folgemonat"
    return f"{y}-{m:02d}", "Buchungsmonat"
# keine Miete: eigene Umbuchungen, Erstattungen, Kautionen, Versicherungen, Versorger, eigene Gesellschaften
EXCL_RE = re.compile(r"umbuchung|erstattung|r(ü|ue)ckzahlung|kaution|umsatzsteuer|versicherung|gutschrift nr|rechnungs?\s*nr|rechnung vom|serienrechnung|\bzins|darlehen|entsch(ä|ae)dig|stadtwerke|gelsenwasser|e\.on|\beon\b|vattenfall|\bele\b|\bista\b|techem|brunata|maingau|immobilien egbr|immo verwaltungs|kpk grundbesitz|kp immobilien|pk dienstleistungs|pk immo", re.I)
# Nebenkosten-Nachzahlungen/-Raten und Betriebskostenabrechnungen sind keine Miete – außer der Text nennt ausdrücklich die Miete (z. B. "Miete und Nebenkosten", "Miete 462 + NK 200")
NK_RE = re.compile(r"nebenkosten|\bnbk|\bnk\b|\bnka\b|\bbka\b|heiz|betriebskosten|abrechnung|nachzahl|ratenzahlung", re.I)
MIETE_RE = re.compile(r"\bmiete\b|wohnungsmiete|garagenmiete|garagemiete|mietdiffer", re.I)
def nk_zahlung(text):
    return bool(NK_RE.search(text)) and not MIETE_RE.search(text)
def is_rent_credit(b):
    if b["betrag"] <= 0: return False
    t = b["text"]
    # Umbuchungen von eigenen Konten mit Mieterbezug ("Umbuchung Miete Braun") zählen als Mieteingang
    if re.search(r"umbuchung.*miete|miete.*umbuchung", t, re.I) and not re.search(r"kaution|verrechnung", t, re.I): return True
    if EXCL_RE.search(t): return False
    if nk_zahlung(t): return False
    return True
def zuordnen(buchungen, soll, modus=None):
    """Ordnet Mietgutschriften (chronologisch) Leistungsmonaten zu. Standard: leistungsmonat(); modus 'auffuellen':
    Zahlungen ohne Monatsnennung füllen ab 01/2026 (bzw. 12/2025) den jeweils ältesten Monat auf, der noch unter 90 % des Solls liegt."""
    from collections import defaultdict
    per = defaultdict(list)
    for b in sorted(buchungen, key=lambda x: (x["datum"][6:10], x["datum"][3:5], x["datum"][:2])):
        lm, how = leistungsmonat(b["datum"], b["text"])
        if modus == "auffuellen" and soll and not how.startswith("Text"):
            start = "2026-01" if (b["datum"][6:10], b["datum"][3:5]) >= ("2025", "12") and (b["datum"][6:10] > "2025" or int(b["datum"][:2]) >= 25) else b["datum"][6:10] + "-" + b["datum"][3:5]
            y, m = int(start[:4]), int(start[5:])
            for _ in range(24):
                key = f"{y}-{m:02d}"
                if sum(a for _, a, _, _ in per[key]) < 0.9 * soll: lm, how = key, "Auffüllen (ältester offener Monat)"; break
                m += 1
                if m == 13: m, y = 1, y + 1
        per[lm].append((b["datum"], b["betrag"], b["text"][:90], how))
    return per

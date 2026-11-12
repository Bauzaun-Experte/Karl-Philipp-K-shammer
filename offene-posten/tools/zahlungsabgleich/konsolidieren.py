#!/usr/bin/env python3
"""Zahlungsabgleich 2026: Bankbuchungen (parse_vb.py-JSON) je Mieter/Monat gegen Soll und Immocloud.
Aufruf: konsolidieren.py <scratch-op-dir> <out.xlsx>"""
import sys, json, re, os
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
S, OUT = sys.argv[1], sys.argv[2]
mapping = json.load(open(f"{S}/bank/mapping.json", encoding="utf-8"))
immo = json.load(open(f"{S}/daten.json", encoding="utf-8"))
projekt_zahler = json.load(open(f"{S}/dashboard/assets/fcd7d1cac4c33db5f0691d163778a7c2.json", encoding="utf-8"))
MONTHS = [f"2026-{m:02d}" for m in range(1, 12)]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bankregeln import leistungsmonat, is_rent_credit, zuordnen, anteile_umlegen
F = "Arial"; f_n=Font(name=F,size=9); f_b=Font(name=F,size=9,bold=True); f_t=Font(name=F,size=14,bold=True); f_s=Font(name=F,size=9,italic=True,color="555555")
f_h=Font(name=F,size=9,bold=True,color="FFFFFF"); fill_h=PatternFill("solid",fgColor="1F3864"); fill_sub=PatternFill("solid",fgColor="F2F2F2"); fill_warn=PatternFill("solid",fgColor="FCE4D6")
EUR='#,##0.00 "€";[Red]-#,##0.00 "€";"–"'; wrap=Alignment(wrap_text=True,vertical="top"); thin=Side(style="thin",color="999999")
immo_idx = {}
for g in immo["gesellschaften"]:
    for o in g["objekte"]:
        for e in o["einheiten"]:
            immo_idx[(o["objekt"], e["mieter"])] = (g["name"], o, e)
wb = Workbook(); wb.remove(wb.active)
raw_rows = []
for konto, cfg in mapping.items():
    if konto.startswith("_"): continue
    path = f"{S}/bank/{konto}_buchungen.json"
    if not os.path.exists(path): print("fehlt:", path); continue
    bk = json.load(open(path, encoding="utf-8"))
    rules = cfg["regeln"]
    treffer = {r["einheit"]: [] for r in rules}; other = []
    for b in bk:
        hit = None
        for r in rules:
            if re.search(r["muster"], b["text"], re.I): hit = r; break
        if not is_rent_credit(b):
            if b["betrag"] > 0: other.append(b)
            continue
        if hit is None: other.append(b); continue
        treffer[hit["einheit"]].append(b)
    per = {}
    for r_ in rules:
        per[r_["einheit"]] = zuordnen(treffer[r_["einheit"]], r_["soll"], r_.get("verteilung"))
    anteile_umlegen(per, rules)
    for r_ in rules:
        for lm, lst in per[r_["einheit"]].items():
            for d_, a_, t_, how in lst:
                raw_rows.append([konto, cfg["objekt"], d_, "Gutschrift", a_, r_["mieter"], r_["einheit"], lm, how, t_])
    for b in other:
        raw_rows.append([konto, cfg["objekt"], b["datum"], b["art"], b["betrag"], "", "(nicht Miete / nicht zugeordnet)", "", "", b["text"][:200]])
    ws = wb.create_sheet(cfg["objekt"].replace("MFH ", "").replace("Gelsenkirchen ", "GE ")[:31])
    ws["A1"] = f"Zahlungsabgleich 2026 – {cfg['objekt']} (Konto {konto})"; ws["A1"].font = f_t
    ws["A2"] = "Ist: Volksbank-Kontoauszüge 12/2025–09/2026 (NAS), Leistungsmonat aus Verwendungszweck, sonst Buchungstag (ab 25. = Folgemonat). Soll: Immocloud 11/2026 bzw. aus Dauerzahlung abgeleitet. 10/2026 und 11/2026: Auszüge noch nicht auf der NAS."; ws["A2"].font = f_s
    hdr = ["Einheit", "Mieter", "Soll/Monat", "Soll-Quelle"] + [f"Ist {m[5:]}/26" for m in MONTHS] + ["Ist 01–09/2026", "Soll 01–09/2026", "Differenz 01–09 (−=Rückstand)", "Immocloud Saldo 07.11.", "Zahlungen (Datum Betrag)"]
    r = 4
    for c, h in enumerate(hdr, 1):
        cell = ws.cell(row=r, column=c, value=h); cell.font = f_h; cell.fill = fill_h; cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[r].height = 36; r += 1
    first = r
    for rule in rules:
        pay = per[rule["einheit"]]
        ws.cell(row=r, column=1, value=rule["einheit"]).font = f_n
        ws.cell(row=r, column=2, value=rule["mieter"]).font = f_n
        c3 = ws.cell(row=r, column=3, value=rule["soll"]); c3.number_format = EUR; c3.font = Font(name=F, size=9, color="0000FF")
        ws.cell(row=r, column=4, value=rule["soll_quelle"]).font = Font(name=F, size=8); ws.cell(row=r, column=4).alignment = wrap
        for j, mth in enumerate(MONTHS):
            tot = round(sum(a for _, a, _, _ in pay.get(mth, [])), 2)
            c = ws.cell(row=r, column=5 + j, value=tot if pay.get(mth) else None); c.number_format = EUR; c.font = f_n
            if mth in ("2026-10", "2026-11") and not pay.get(mth): c.value = "k.A."; c.font = f_s; c.alignment = Alignment(horizontal="center")
        L0, L1 = get_column_letter(5), get_column_letter(5 + 8)   # Jan..Sep
        cI = 5 + len(MONTHS); ws.cell(row=r, column=cI, value=f"=SUM({L0}{r}:{L1}{r})").number_format = EUR
        if rule["soll"]:
            ws.cell(row=r, column=cI + 1, value=f"=C{r}*9").number_format = EUR
            ws.cell(row=r, column=cI + 2, value=f"={get_column_letter(cI)}{r}-{get_column_letter(cI+1)}{r}").number_format = EUR
        # Immocloud-Saldo
        key_obj = cfg["objekt"]
        saldo = None
        for (ob, mi), (gname, o, e) in immo_idx.items():
            if ob.startswith(key_obj.split(" Haus")[0]) and (mi == rule["mieter"] or rule["mieter"].split()[-1] in mi):
                saldo = (saldo or 0) + (e.get("saldo") or 0)
        ws.cell(row=r, column=cI + 3, value=saldo).number_format = EUR
        txt = "; ".join(f"{m[5:]}/{m[2:4]}: " + ", ".join(f"{d} {a:.2f}" for d, a, _, _ in v) for m, v in sorted(pay.items()))
        ws.cell(row=r, column=cI + 4, value=txt).font = Font(name=F, size=7); ws.cell(row=r, column=cI + 4).alignment = wrap
        ws.row_dimensions[r].height = 40; r += 1
    last = r - 1
    ws.cell(row=r, column=1, value="Summe").font = f_b
    for c in range(5, 5 + len(MONTHS) + 3):
        col = get_column_letter(c); cell = ws.cell(row=r, column=c, value=f"=SUM({col}{first}:{col}{last})"); cell.number_format = EUR; cell.font = f_b; cell.fill = fill_sub
    r += 2
    ws.cell(row=r, column=1, value="Sonstige Gutschriften auf dem Konto (keine Mieten oder nicht zugeordnet):").font = f_b; r += 1
    for b in other:
        ws.cell(row=r, column=1, value=b["datum"]).font = f_n; ws.cell(row=r, column=2, value=b["betrag"]).number_format = EUR
        ws.cell(row=r, column=3, value=b["text"][:160]).font = Font(name=F, size=8); ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=12); r += 1
    for i, w in enumerate([22, 26, 11, 30] + [10]*len(MONTHS) + [13, 13, 14, 13, 70], 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "E5"
# Blatt: Projekt-Zahlerübersicht Q3 2026 für alle Objekte
ws = wb.create_sheet("Q3-2026 Zahler (Projekt)")
ws["A1"] = "Mieteingänge Juli–September 2026 je Zahler (Projektdatensatz ‚Mieter und Zahler‘, Stand 26.10.2026) gegen Immocloud 07.11.2026"; ws["A1"].font = f_t
hdr = ["Objekt", "Zahler", "Betrag/Monat (Median)", "Monate gezahlt (von 3)", "letzte Zahlung", "Verwendungszweck", "Hinweis"]
for c, h in enumerate(hdr, 1):
    cell = ws.cell(row=3, column=c, value=h); cell.font = f_h; cell.fill = fill_h; cell.alignment = Alignment(wrap_text=True, vertical="center")
r = 4
for z in projekt_zahler:
    if z["id"] == "hilden": continue
    vals = [z["objekt"], z["zahler"], float(z["miete_monat"]), int(z["monate_gezahlt"]), z["letzte_zahlung"], z["verwendungszweck"], "" if int(z["monate_gezahlt"]) == 3 else "nicht in allen drei Monaten gezahlt – prüfen"]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(row=r, column=c, value=v); cell.font = f_n
        if c == 3: cell.number_format = EUR
    if int(z["monate_gezahlt"]) < 3:
        for c in range(1, 8): ws.cell(row=r, column=c).fill = fill_warn
    r += 1
for i, w in enumerate([34, 36, 14, 12, 13, 44, 40], 1): ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A4"; ws.auto_filter.ref = f"A3:G{r-1}"
# Blatt: Rohbuchungen
ws = wb.create_sheet("Bankbuchungen 2026")
hdr = ["Konto", "Objekt", "Datum", "Art", "Betrag", "Mieter", "Einheit", "Leistungsmonat", "Zuordnung", "Buchungstext"]
for c, h in enumerate(hdr, 1):
    cell = ws.cell(row=1, column=c, value=h); cell.font = f_h; cell.fill = fill_h
for row in sorted(raw_rows, key=lambda x: (x[0], x[2][6:10], x[2][3:5], x[2][0:2])):
    ws.append(row)
for row in ws.iter_rows(min_row=2):
    row[4].number_format = EUR
    for c in row: c.font = f_n
for i, w in enumerate([10, 30, 11, 20, 11, 24, 22, 13, 24, 90], 1): ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"; ws.auto_filter.ref = f"A1:J{ws.max_row}"
# Adenau-Blatt aus dem Pilot (Kassenbuch) übernehmen
PILOT = f"{S}/../../../../../../workspace/Karl-Philipp-K-shammer/offene-posten/Zahlungsabgleich_Pilot_Adenau_Velbert_2026-11-12.xlsx"
PILOT = "/workspace/Karl-Philipp-K-shammer/offene-posten/Zahlungsabgleich_Pilot_Adenau_Velbert_2026-11-12.xlsx"
if os.path.exists(PILOT):
    from openpyxl import load_workbook
    from copy import copy
    src = load_workbook(PILOT)["Adenau"]
    dst = wb.create_sheet("MFH Adenau Haus 17 + 19 (KB)", 0)
    for row in src.iter_rows():
        for c in row:
            n = dst.cell(row=c.row, column=c.column, value=c.value)
            if c.has_style:
                n.font = copy(c.font); n.fill = copy(c.fill); n.number_format = c.number_format; n.alignment = copy(c.alignment); n.border = copy(c.border)
    for k, dim in src.column_dimensions.items(): dst.column_dimensions[k].width = dim.width
    for k, dim in src.row_dimensions.items(): dst.row_dimensions[k].height = dim.height
    for m in src.merged_cells.ranges: dst.merge_cells(str(m))
    dst.freeze_panes = src.freeze_panes
    dst["A2"] = "Ist: Kassenbuch GbR BH neu.xlsx, Blatt Adenau (vollständig bis 10.11.2026) · Soll: Immocloud 11/2026 · Monatszuordnung lt. Buchungstext im Kassenbuch"
# Blattreihenfolge: Adenau, Velbert, Krefeld, Bickernstr, Q3, Roh
order = ["MFH Adenau Haus 17 + 19 (KB)", "Velbert Haus 17 + 19", "Krefeld Ritterstr 295", "GE Bickernstr 102", "Q3-2026 Zahler (Projekt)", "Bankbuchungen 2026"]
wb._sheets = [wb[n] for n in order if n in wb.sheetnames] + [s for s in wb._sheets if s.title not in order]
wb.save(OUT); print("saved", OUT, "Rohbuchungen:", len(raw_rows))

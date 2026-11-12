import json, re, sys
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
S = sys.argv[1]; OUT = sys.argv[2]
ad = json.load(open(f"{S}/bank/adenau_2026.json", encoding="utf-8"))
ve = json.load(open(f"{S}/bank/velbert_2026.json", encoding="utf-8"))
MONTHS = [f"{m:02d}-2026" for m in range(1, 12)]
F="Arial"; f_n=Font(name=F,size=10); f_b=Font(name=F,size=10,bold=True); f_t=Font(name=F,size=14,bold=True); f_s=Font(name=F,size=9,italic=True,color="555555")
f_h=Font(name=F,size=10,bold=True,color="FFFFFF"); fill_h=PatternFill("solid",fgColor="1F3864"); fill_sec=PatternFill("solid",fgColor="D9E1F2"); fill_sub=PatternFill("solid",fgColor="F2F2F2")
EUR='#,##0.00 "€";[Red]-#,##0.00 "€";"–"'; thin=Side(style="thin",color="999999")
wrap=Alignment(wrap_text=True,vertical="top")

# ---------- Adenau: Soll je Einheit (Immocloud 07.11.2026) und Zuordnung der Kassenbuch-Zeilen
AD_UNITS = [  # (Mieter, Einheit, Soll/Monat 2026, Zuordnungs-Regex auf Buchungstext/Name, Monat-Regex-Quelle)
 ("Bastian Nelles", "Haus 19, 1.OG + Stellplatz", 520.00, r"Nelles"),
 ("Peter Wagener", "Haus 19, EG rts", 470.00, r"Wagener"),
 ("Gerhard Weber", "Haus 19, Garage 2 (Mitte)", 60.00, r"Weber"),
 ("Gerhard Weber", "Haus 19, Garage 3", 30.00, r"Weber"),
 ("Christoph Büntgens", "Haus 19, Garage gegenüber (Immocloud: Garage 1 Leerstand)", 30.00, r"Büntgens"),
 ("Renate Schulz", "Haus 17, EG, ausgezogen ca. 07/2026 (Immocloud: Leerstand)", 465.00, r"Schulz"),
]
def month_of(ref):
    m = re.search(r"(\d\d)-(20\d\d)", ref or "")
    return f"{m.group(1)}-{m.group(2)}" if m else None

wb = Workbook(); ws = wb.active; ws.title = "Adenau"
ws["A1"] = "Zahlungsabgleich Adenau, Lohmühlenstr. 17 + 19 (Konto …4404) – Jahr 2026"; ws["A1"].font = f_t
ws["A2"] = "Ist: " + ad["quelle"] + " · Soll: Immocloud-Sollstellung 11/2026 · Monatszuordnung lt. Buchungstext im Kassenbuch"; ws["A2"].font = f_s
r = 4
hdr = ["Mieter / Einheit", "Soll/Monat"] + [f"Ist {m[:2]}/26" for m in MONTHS] + ["Ist 2026 gesamt", "Soll 2026 gesamt", "Differenz 2026 (−=Rückstand)", "Immocloud Saldo 07.11.", "Zahlungen / Bemerkung"]
for c, h in enumerate(hdr, 1):
    cell = ws.cell(row=r, column=c, value=h); cell.font = f_h; cell.fill = fill_h; cell.alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[r].height = 32; r += 1
IMMO = {"Bastian Nelles": -520.00, "Peter Wagener": -55.00, "Gerhard Weber|Haus 19, Garage 2 (Mitte)": -120.00, "Gerhard Weber|Haus 19, Garage 3": -60.00, "Christoph Büntgens": None, "Renate Schulz": None}
used = set(); g2seen = {}
for mieter, einheit, soll, rx in AD_UNITS:
    pay = defaultdict(list); notes = []
    for i, z in enumerate(ad["zahlungen"]):
        d, who, txt, amt, ref, kost = z
        key = who + " " + txt
        if not re.search(rx, key): continue
        if mieter == "Gerhard Weber" and "Garage 3" in einheit:
            # Garage 3 erhält je Monat nur das, was über die 60 € der Garage 2 hinausgeht
            mo0 = month_of(ref) or month_of(txt)
            seen = g2seen.setdefault(mo0, 0.0)
            if seen < 60 - 0.01 and "Garage 2 Mitte" not in txt:
                g2seen[mo0] = seen + amt; continue
        if kost == "Kaution": notes.append(f"{d} Kaution {amt:.2f}"); continue
        if "NKA" in txt or "Nachzahlung" in txt or "Rate" in txt: notes.append(f"{d} {txt} {amt:.2f}"); continue
        mo = month_of(ref) or month_of(txt)
        bmo = f"{d[3:5]}-{d[6:10]}"
        if mo and soll and mo < bmo[3:] + "-" + bmo[:2] and False: pass
        if mo and soll and (mo[3:] + mo[:2]) < (bmo[3:] + bmo[:2]) and sum(a for _, a in pay.get(mo, [])) >= soll * 0.9:
            notes.append(f"{d}: Referenz ‚{ref}‘, dem Buchungsmonat {bmo} zugeordnet (Monat {mo} war bereits bezahlt)"); mo = bmo
        if mieter == "Gerhard Weber" and "Garage 2 (Mitte)" in einheit and mo and sum(a for _, a in pay.get(mo, [])) >= 60 - 0.01:
            continue  # zweite Garagenzahlung im selben Monat gehört zu Garage 3
        if mieter == "Gerhard Weber" and "Garage 3" in einheit and "Garage 2 Mitte" not in txt:
            # nur Zahlungen, die über die 60 € von Garage 2 hinausgehen
            pass
        if mo and mo.endswith("2026"): pay[mo].append((d, amt))
        elif mo: pass
        else: notes.append(f"{d} ohne Monatsbezug {amt:.2f}")
    ws.cell(row=r, column=1, value=f"{mieter}\n{einheit}").font = f_n; ws.cell(row=r, column=1).alignment = wrap
    ws.cell(row=r, column=2, value=soll).number_format = EUR
    first_ist = 3
    for j, m in enumerate(MONTHS):
        tot = sum(a for _, a in pay.get(m, []))
        c = ws.cell(row=r, column=first_ist + j, value=tot if pay.get(m) else None); c.number_format = EUR; c.font = f_n
        if pay.get(m): c.comment = None
    cI = first_ist + len(MONTHS); cS = cI + 1; cD = cI + 2; cIm = cI + 3; cN = cI + 4
    L0 = get_column_letter(first_ist); L1 = get_column_letter(first_ist + len(MONTHS) - 1)
    ws.cell(row=r, column=cI, value=f"=SUM({L0}{r}:{L1}{r})").number_format = EUR
    if soll is not None and "Schulz" not in mieter:
        ws.cell(row=r, column=cS, value=f"=B{r}*11").number_format = EUR
        ws.cell(row=r, column=cD, value=f"={get_column_letter(cI)}{r}-{get_column_letter(cS)}{r}").number_format = EUR
    im = IMMO.get(mieter + "|" + einheit, IMMO.get(mieter))
    ws.cell(row=r, column=cIm, value=im).number_format = EUR
    paylist = "; ".join(f"{m[:2]}/26: " + ", ".join(f"{d} {a:.0f}" for d, a in v) for m, v in sorted(pay.items()))
    ws.cell(row=r, column=cN, value=(paylist + ("  |  " if notes else "") + "; ".join(notes))).font = Font(name=F, size=8); ws.cell(row=r, column=cN).alignment = wrap
    ws.row_dimensions[r].height = 48
    r += 1
ws.cell(row=r+1, column=1, value="Befund Adenau (Stand Kassenbuch 10.11.2026):").font = f_b
bef = ["Nelles: alle Monate 01–11/2026 bezahlt (jeweils am 28. des Vormonats, 520 € = 500 € Wohnung + 20 € Stellplatz). Immocloud zeigt 11/2026 als offen (520 €) – die Zahlung vom 28.10.2026 ist dort offenbar nicht zugeordnet. Rückstand lt. Bank: 0 €.",
       "Wagener: zahlt 465 € statt 470 € Soll, 01–11/2026 jeweils 5 € zu wenig = 55 € Rückstand. Deckt sich mit Immocloud (−55 €). Zusätzlich NKA 2024 in Raten zu 142,75 € (02., 03., 04., 05.2026) gezahlt; Rest aus 05/2025 (50 €) am 09.04.2026 nachgezahlt.",
       "Weber Garage 2 (60 €): bezahlt bis 09/2026 (zuletzt 07.09.2026 für 07–09/2026) → 10/2026 und 11/2026 offen = 120 €. Deckt sich mit Immocloud. Garage 3 (Soll lt. Immocloud 30 €): im Kassenbuch nur zwei zusätzliche Garagenzahlungen (50 € für 05/2026, 40 € ‚Garage 2 Mitte‘ für 09/2026) – Soll und Zuordnung bitte prüfen; Immocloud −60 €.",
       "Büntgens (Garage gegenüber, 30 €): bezahlt bis 03/2026, danach keine Zahlung mehr. In Immocloud nicht als Mieter geführt (Garage 1 = Leerstand). Klären, ob das Mietverhältnis 03/2026 endete.",
       "Schulz (Haus 17 EG): bezahlt bis 07/2026 (ab 02/2026 465 € statt 525 €), danach Auszug (Immocloud: Leerstand). NKA 2024 in Raten (200 + 207,88) bezahlt."]
for b in bef:
    r += 1; ws.cell(row=r, column=1, value="• " + b).font = f_n; ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=18); ws.cell(row=r, column=1).alignment = wrap; ws.row_dimensions[r].height = 42
ws.column_dimensions["A"].width = 34; ws.column_dimensions["B"].width = 11
for j in range(len(MONTHS)): ws.column_dimensions[get_column_letter(3 + j)].width = 10
for c in range(cI, cN): ws.column_dimensions[get_column_letter(c)].width = 13
ws.column_dimensions[get_column_letter(cN)].width = 80
ws.freeze_panes = "C5"

# ---------- Velbert
ws = wb.create_sheet("Velbert")
ws["A1"] = "Zahlungsabgleich Velbert, Bonsfelder Str. 17 + 19 (Konto …4401) – Jahr 2026"; ws["A1"].font = f_t
ws["A2"] = "Ist: " + ve["quelle"] + " · Soll: Immocloud 11/2026 · Zuordnung zum Monat nach Buchungstag (Dauerauftrag zum 1.; Meschede zahlt am 28. des Vormonats)"; ws["A2"].font = f_s
VE_UNITS = [
 ("Surinder Singh", "Haus 19, EG Gewerbe", 1000.00, 8.60),
 ("Mathias Siehl", "Haus 19, 1.OG", 674.00, -59.00),
 ("Braun (Leonard)", "Haus 19, DG (ab 01.08.2026)", 1135.00, 0.00),
 ("Marion Blömer", "Haus 19, EG hinten", 540.00, 0.00),
 ("Rolf und Marie-Luise Weiler", "Haus 17, EG", 662.00, 0.00),
 ("Angelika Meschede", "Haus 17, DG", 701.93, 0.00),
 ("Hubert Gatzka", "Haus 17, Surterrain", 440.00, -15.00),
 ("Shamsa Ismaeel (Vormieterin)", "Haus 19, DG (bis 2025)", None, None),
]
r = 4
hdr = ["Mieter / Einheit", "Soll/Monat (Immocloud)"] + [f"Ist {m[:2]}/26" for m in MONTHS] + ["Ist 02–09/2026 (bekannte Monate)", "Soll 02–09/2026 (bekannte Monate)", "Differenz 02–09/2026", "Immocloud Saldo 07.11.", "Bemerkung"]
for c, h in enumerate(hdr, 1):
    cell = ws.cell(row=r, column=c, value=h); cell.font = f_h; cell.fill = fill_h; cell.alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[r].height = 32; r += 1
def ve_month(d, who):
    dd, mm, yy = d.split("."); mm = int(mm); yy = int(yy)
    if "Meschede" in who and int(dd) >= 25:   # zahlt Ende des Vormonats
        mm += 1
        if mm == 13: mm = 1; yy += 1
    return f"{mm:02d}-{yy}"
for mieter, einheit, soll, immo in VE_UNITS:
    pay = defaultdict(list); notes = []
    key = mieter.split(" (")[0].split(" ")[-1] if "Braun" not in mieter else "Braun"
    for d, who, unit, amt, txt in ve["zahlungen"]:
        if key not in who: continue
        if "Nachzahlung" in txt or "Rate" in txt or "Verrechnung" in txt: notes.append(f"{d} {txt} {amt:.2f}"); continue
        mo = ve_month(d, who)
        if mo.endswith("2026"): pay[mo].append((d, amt))
        else: notes.append(f"{d} {amt:.2f} ({txt})")
    ws.cell(row=r, column=1, value=f"{mieter}\n{einheit}").font = f_n; ws.cell(row=r, column=1).alignment = wrap
    ws.cell(row=r, column=2, value=soll).number_format = EUR
    for j, m in enumerate(MONTHS):
        tot = sum(a for _, a in pay.get(m, []))
        c = ws.cell(row=r, column=3 + j, value=tot if pay.get(m) else None); c.number_format = EUR
        if (m in ("01-2026", "10-2026", "11-2026") or ("Meschede" in mieter and m == "02-2026")) and not pay.get(m): c.value = "k.A."; c.font = f_s; c.alignment = Alignment(horizontal="center")
    cI = 3 + len(MONTHS); cS = cI + 1; cD = cI + 2; cIm = cI + 3; cN = cI + 4
    ws.cell(row=r, column=cI, value=f"=SUM(D{r}:K{r})").number_format = EUR   # Feb..Sep = Spalten D..K
    if soll is not None:
        months_due = 2 if "Braun" in mieter else (7 if "Meschede" in mieter else 8)
        ws.cell(row=r, column=cS, value=f"=B{r}*{months_due}").number_format = EUR
        ws.cell(row=r, column=cD, value=f"={get_column_letter(cI)}{r}-{get_column_letter(cS)}{r}").number_format = EUR
    ws.cell(row=r, column=cIm, value=immo).number_format = EUR
    paylist = "; ".join(f"{m[:2]}/26: " + ", ".join(f"{d} {a:.2f}" for d, a in v) for m, v in sorted(pay.items()))
    ws.cell(row=r, column=cN, value=(paylist + ("  |  " if notes else "") + "; ".join(notes))).font = Font(name=F, size=8); ws.cell(row=r, column=cN).alignment = wrap
    ws.row_dimensions[r].height = 48; r += 1
ws.cell(row=r+1, column=1, value="Befund Velbert (Kontoauszüge bis 30.09.2026; Januar und Oktober 2026 fehlen auf der NAS):").font = f_b
bef = ["Alle sieben Mietverhältnisse zahlen per Dauerauftrag pünktlich zum Monatsanfang (Meschede am 28. des Vormonats). Für 02–09/2026 gibt es keine fehlende Monatsmiete.",
       "Siehl zahlt 670 € statt 674 € Soll (4 €/Monat zu wenig), Gatzka 435 € statt 440 € (5 €/Monat). Daraus ergeben sich die kleinen Rückstände in Immocloud (Siehl −59 €, Gatzka −15 €). Ob die Soll-Erhöhung auf 674/440 € wirksam vereinbart ist, bitte am Mieterhöhungsschreiben prüfen; die Dauerauftragsbeträge wurden im Dezember 2025 zuletzt angepasst (Siehl 650→670, Gatzka 430→435, Blömer 530→540, Singh 994→1.000).",
       "Braun (DG Haus 19, Einzug 01.08.2026): 08/2026 direkt bezahlt (03.08.), 09/2026 kam auf dem eGbR-Hauptkonto an und wurde am 02.09.2026 umgebucht. Für 10/2026 und 11/2026 liegen keine Auszüge vor.",
       "Vormieterin DG Haus 19 (Shamsa Ismaeel): Restmiete Dezember 2025 in vier Raten bezahlt (200 + 216 + 300 € bis 30.03.2026; die 1. Rate liegt im fehlenden Januar-Auszug), dazu Verrechnung Miete mit Kaution 1.890 € am 20.03.2026. Kein laufendes Mietverhältnis mehr.",
       "Singh: Nachzahlung 2024 (457,25 €) am 18.12.2025, Siehl: Nachzahlung 171,69 € am 30.12.2025 – vermutlich NKA 2024, in Immocloud als Guthaben/Verrechnung prüfen."]
for b in bef:
    r += 1; ws.cell(row=r, column=1, value="• " + b).font = f_n; ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=18); ws.cell(row=r, column=1).alignment = wrap; ws.row_dimensions[r].height = 42
ws.column_dimensions["A"].width = 34; ws.column_dimensions["B"].width = 11
for j in range(len(MONTHS)): ws.column_dimensions[get_column_letter(3 + j)].width = 10
for c in range(cI, cN): ws.column_dimensions[get_column_letter(c)].width = 13
ws.column_dimensions[get_column_letter(cN)].width = 80
ws.freeze_panes = "C5"

# ---------- Zahlungen roh
ws = wb.create_sheet("Zahlungen roh")
ws.append(["Konto", "Datum", "Zahler", "Einheit / Buchungstext", "Betrag", "Referenz / Bemerkung", "Kostenart"])
for c in range(1, 8): ws.cell(row=1, column=c).font = f_h; ws.cell(row=1, column=c).fill = fill_h
for d, who, txt, amt, ref, kost in ad["zahlungen"]: ws.append(["Adenau …4404", d, who, txt, amt, ref, kost])
for d, who, unit, amt, txt in ve["zahlungen"]: ws.append(["Velbert …4401", d, who, unit, amt, txt, "Miete"])
for row in ws.iter_rows(min_row=2): row[4].number_format = EUR
for i, w in enumerate([16, 12, 36, 48, 12, 40, 14], 1): ws.column_dimensions[get_column_letter(i)].width = w
ws.auto_filter.ref = f"A1:G{ws.max_row}"; ws.freeze_panes = "A2"
for s in wb.worksheets:
    for row in s.iter_rows():
        for c in row:
            if c.font.name != F: c.font = Font(name=F, size=c.font.size or 10, bold=c.font.bold, italic=c.font.italic, color=c.font.color)
wb.save(OUT); print("saved", OUT)

import json, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from openpyxl.worksheet.page import PageMargins

SRC, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding="utf-8"))
STAND, ERSTELLT = d["stand_immocloud"], d["erstellt"]

F = "Arial"
f_norm = Font(name=F, size=10)
f_bold = Font(name=F, size=10, bold=True)
f_title = Font(name=F, size=14, bold=True)
f_sub = Font(name=F, size=10, italic=True, color="555555")
f_head = Font(name=F, size=10, bold=True, color="FFFFFF")
f_input = Font(name=F, size=10, color="0000FF")
f_link = Font(name=F, size=10, color="008000")
f_link_b = Font(name=F, size=10, color="008000", bold=True)
fill_head = PatternFill("solid", fgColor="1F3864")
fill_sec = PatternFill("solid", fgColor="D9E1F2")
fill_sub = PatternFill("solid", fgColor="F2F2F2")
fill_tot = PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="999999")
med = Side(style="medium", color="1F3864")
b_top = Border(top=thin)
b_tot = Border(top=med, bottom=med)
EUR = '#,##0.00 "€";-#,##0.00 "€";"–"'
EURS = '#,##0.00 "€";[Red]-#,##0.00 "€";"–"'
wrap = Alignment(wrap_text=True, vertical="top")
center = Alignment(horizontal="center", vertical="top")
right = Alignment(horizontal="right", vertical="top")
red_rule = lambda: CellIsRule(operator="greaterThan", formula=["0"], font=Font(name=F, size=10, color="C00000", bold=True))

wb = Workbook()
# ---------------------------------------------------------------- Daten
ws = wb.active; ws.title = "Daten"
hdr = ["Gesellschaft", "Objekt", "Adresse", "Bankkonto", "Einheit", "Mieter", "Status",
       "Soll-Miete 11/2026 (€)", "Nov 2026 Status", "Nov 2026 offen, überfällig (€)", "Nov 2026 offen, noch nicht fällig (€)",
       f"Saldo lt. Immocloud {STAND} (€)", "Rückstand Vormonate bis 10/2026 (€)", "Guthaben aus Vormonaten (€)",
       "Rückstand gesamt, fällig (€)", "Offen gesamt inkl. noch nicht fällig (€)", "Hinweis", "Bankbefund (Kontoauszüge/Kassenbuch, Stand 12.11.2026)", "Rückstand lt. Bank (€; negativ = Guthaben)"]
ws.append(hdr)
for c in range(1, len(hdr)+1):
    cell = ws.cell(row=1, column=c); cell.font = f_head; cell.fill = fill_head; cell.alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[1].height = 45
rows_by_obj = {}   # objekt -> (first_row, last_row)
row_index = []     # list of dicts with row numbers for later linking
r = 2
for g in d["gesellschaften"]:
    for o in g["objekte"]:
        first = r
        for e in o["einheiten"]:
            saldo = e.get("saldo")
            nov = e.get("nov_offen")
            j = nov if (nov is not None and e.get("nov_faellig")) else None
            k = nov if (nov is not None and not e.get("nov_faellig")) else None
            hinweis = e.get("hinweis", "")
            if saldo is not None and j:
                vor = saldo + j
                if vor > 0:
                    extra = f"Guthaben aus Vormonaten {vor:,.2f} €, Novembermiete noch offen – Verrechnung in Immocloud prüfen".replace(",", "X").replace(".", ",").replace("X", ".")
                    hinweis = (hinweis + ". " if hinweis else "") + extra
            if saldo is None and e["status"] != "Leerstand":
                raise SystemExit(f"Saldo fehlt: {e}")
            vals = [g["name"], o["objekt"], o["adresse"], o["konto"], e["einheit"], e["mieter"], e["status"],
                    e.get("soll"), e.get("nov_status") or ("–" if e["status"] != "Leerstand" else ""), j, k, saldo]
            for c, v in enumerate(vals, start=1):
                cell = ws.cell(row=r, column=c, value=v); cell.font = f_norm; cell.alignment = wrap
            for c in (8, 10, 11, 12):
                ws.cell(row=r, column=c).font = f_input; ws.cell(row=r, column=c).number_format = EUR if c != 12 else EURS
            L = f"L{r}"; J = f"J{r}"; K = f"K{r}"; M = f"M{r}"; N = f"N{r}"
            ws[f"M{r}"] = f'=IF({L}="","",MAX(0,-({L}+{J})))'
            ws[f"N{r}"] = f'=IF({L}="","",MAX(0,{L}+{J}))'
            ws[f"O{r}"] = f'=IF({L}="","",MAX(0,{J}+{M}-{N}))'
            ws[f"P{r}"] = f'=IF({L}="","",MAX(0,{J}+{M}-{N}+{K}))'
            for c in (13, 14, 15, 16):
                ws.cell(row=r, column=c).font = f_norm; ws.cell(row=r, column=c).number_format = EUR
            ws.cell(row=r, column=17, value=hinweis).font = f_norm; ws.cell(row=r, column=17).alignment = wrap
            ws.cell(row=r, column=18, value=e.get("bank")).font = f_norm; ws.cell(row=r, column=18).alignment = wrap
            cb = ws.cell(row=r, column=19, value=e.get("bank_rest")); cb.font = f_input; cb.number_format = EUR
            row_index.append({"ges": g["name"], "obj": o["objekt"], "row": r, "einheit": e["einheit"], "mieter": e["mieter"], "saldo": saldo, "j": j, "k": k})
            r += 1
        rows_by_obj[o["objekt"]] = (first, r - 1)
LAST = r - 1
widths = [34, 30, 34, 10, 30, 36, 11, 13, 12, 14, 14, 14, 14, 14, 14, 16, 60, 70, 14]
for i, w in enumerate(widths, start=1): ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "G2"; ws.auto_filter.ref = f"A1:S{LAST}"
for col in ("O", "P", "M"): ws.conditional_formatting.add(f"{col}2:{col}{LAST}", red_rule())
ws.page_setup.orientation = "landscape"; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0; ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.print_title_rows = "1:1"
nr = LAST + 2
ws.cell(row=nr, column=1, value="Legende: blaue Zahlen = Eingaben aus Immocloud (Stand " + STAND + "), schwarze Zahlen = Formeln. Saldo: negativ = Rückstand, positiv = Guthaben (Lesart Immocloud). Vormonate = −(Saldo + Nov überfällig), Guthaben = Saldo + Nov überfällig (wenn positiv). ‚Noch nicht fällig‘ = Immocloud-Status ‚Erwartet‘, nicht im Saldo enthalten.").font = f_sub
ws.merge_cells(start_row=nr, start_column=1, end_row=nr, end_column=19); ws.cell(row=nr, column=1).alignment = wrap; ws.row_dimensions[nr].height = 30

# ------------------------------------------------------- Gesellschaft sheets
GS_COLS = ["Einheit", "Mieter", "Status", "Soll-Miete 11/2026", "Nov 2026 offen, überfällig", "Nov 2026 noch nicht fällig",
           "Rückstand Vormonate bis 10/2026", "Guthaben aus Vormonaten", "Rückstand gesamt, fällig", "Offen gesamt inkl. noch nicht fällig", f"Saldo Immocloud {STAND}", "Hinweis", "Bankbefund (Stand 12.11.2026)", "Rückstand lt. Bank (negativ = Guthaben)"]
SRC_COL = ["E", "F", "G", "H", "J", "K", "M", "N", "O", "P", "L", "Q", "R", "S"]   # Daten columns
NUMC = [4, 5, 6, 7, 8, 9, 10, 11, 14]
sheet_names = {}
ges_total_rows = {}
for g in d["gesellschaften"]:
    name = g["name"][:31]
    sn = {"Käshammer und Penkhues Immobilien eGbR": "eGbR", "KPK Grundbesitz GmbH": "KPK Grundbesitz GmbH", "PK Immo Verwaltungs GmbH": "PK Immo Verwaltungs GmbH"}[g["name"]]
    sheet_names[g["name"]] = sn
    s = wb.create_sheet(sn)
    s["A1"] = f"Offene-Posten-Liste Mieter – {g['name']}"; s["A1"].font = f_title
    s["A2"] = f"Datenstand Immocloud {STAND} · erstellt {ERSTELLT} · Beträge in Euro · alle Werte verweisen auf das Blatt ‚Daten‘"; s["A2"].font = f_sub
    r = 4
    sub_rows = []
    for o in g["objekte"]:
        s.cell(row=r, column=1, value=f"{o['objekt']}  ·  {o['adresse']}  ·  Konto {o['konto']}").font = f_bold
        for c in range(1, 15): s.cell(row=r, column=c).fill = fill_sec
        r += 1
        for c, h in enumerate(GS_COLS, start=1):
            cell = s.cell(row=r, column=c, value=h); cell.font = f_head; cell.fill = fill_head; cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center" if c in NUMC else "left")
        s.row_dimensions[r].height = 42
        r += 1
        first, last = rows_by_obj[o["objekt"]]
        f0 = r
        for dr in range(first, last + 1):
            for c, sc in enumerate(SRC_COL, start=1):
                cell = s.cell(row=r, column=c, value=f"=Daten!{sc}{dr}")
                cell.font = f_link; cell.alignment = wrap
                if c in NUMC: cell.number_format = EURS if c == 11 else EUR
            r += 1
        f1 = r - 1
        s.cell(row=r, column=1, value="Summe " + o["objekt"]).font = f_bold
        s.cell(row=r, column=2, value=f'=COUNTIF(I{f0}:I{f1},">0")&" Mieter mit Rückstand"').font = f_bold
        for c in NUMC:
            if c == 4: continue
            col = get_column_letter(c)
            cell = s.cell(row=r, column=c, value=f"=SUM({col}{f0}:{col}{f1})"); cell.font = f_bold; cell.number_format = EURS if c == 11 else EUR
        for c in range(1, 15): s.cell(row=r, column=c).fill = fill_sub; s.cell(row=r, column=c).border = b_top
        sub_rows.append(r)
        r += 2
    s.cell(row=r, column=1, value=f"GESAMT {g['name']}").font = f_bold
    s.cell(row=r, column=2, value='=' + '+'.join(f'VALUE(LEFT(B{x},FIND(" ",B{x})-1))' for x in sub_rows) + '&" Mieter mit Rückstand"').font = f_bold
    for c in NUMC:
        if c == 4: continue
        col = get_column_letter(c)
        cell = s.cell(row=r, column=c, value="=" + "+".join(f"{col}{x}" for x in sub_rows)); cell.font = f_bold; cell.number_format = EURS if c == 11 else EUR
    for c in range(1, 15): s.cell(row=r, column=c).fill = fill_tot; s.cell(row=r, column=c).border = b_tot
    ges_total_rows[g["name"]] = r
    for i, w in enumerate([30, 34, 11, 13, 14, 14, 14, 14, 14, 15, 14, 50, 60, 13], start=1): s.column_dimensions[get_column_letter(i)].width = w
    for col in ("G", "I", "J", "N"): s.conditional_formatting.add(f"{col}5:{col}{r}", red_rule())
    s.freeze_panes = "C4"
    s.page_setup.orientation = "landscape"; s.page_setup.fitToWidth = 1; s.page_setup.fitToHeight = 0; s.sheet_properties.pageSetUpPr.fitToPage = True
    s.page_margins = PageMargins(left=0.4, right=0.4, top=0.5, bottom=0.5)

# ---------------------------------------------------------------- Übersicht
u = wb.create_sheet("Übersicht", 0)
u["A1"] = "Offene Posten Mieter – Übersicht nach Gesellschaft und Haus"; u["A1"].font = f_title
u["A2"] = f"Datenstand Immocloud {STAND} (Konto J. Penkhues) · erstellt {ERSTELLT} · Beträge in Euro · Detail je Mieter auf den Blättern je Gesellschaft, Rohdaten auf ‚Daten‘"; u["A2"].font = f_sub
UH = ["Gesellschaft / Objekt", "Adresse", "Einheiten", "davon vermietet", "Mieter mit Rückstand", "Nov 2026 offen, überfällig", "Nov 2026 noch nicht fällig",
      "Rückstand Vormonate bis 10/2026", "Guthaben aus Vormonaten", "Rückstand gesamt, fällig", "Offen gesamt inkl. noch nicht fällig"]
r = 4
for c, h in enumerate(UH, start=1):
    cell = u.cell(row=r, column=c, value=h); cell.font = f_head; cell.fill = fill_head; cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center" if c > 2 else "left")
u.row_dimensions[r].height = 42
r += 1
ges_sub = []
D = lambda col: f"Daten!${col}$2:${col}${LAST}"
for g in d["gesellschaften"]:
    u.cell(row=r, column=1, value=g["name"]).font = f_bold
    for c in range(1, 12): u.cell(row=r, column=c).fill = fill_sec
    r += 1; f0 = r
    for o in g["objekte"]:
        u.cell(row=r, column=1, value="   " + o["objekt"]).font = f_norm
        u.cell(row=r, column=2, value=o["adresse"]).font = f_norm
        B = f"$A{r}"
        key = f'TRIM({B})'
        u.cell(row=r, column=3, value=f'=COUNTIF({D("B")},{key})')
        u.cell(row=r, column=4, value=f'=COUNTIFS({D("B")},{key},{D("G")},"<>Leerstand")')
        u.cell(row=r, column=5, value=f'=COUNTIFS({D("B")},{key},{D("O")},">0")')
        for c, col in zip(range(6, 12), ["J", "K", "M", "N", "O", "P"]):
            cell = u.cell(row=r, column=c, value=f'=SUMIFS({D(col)},{D("B")},{key})'); cell.number_format = EUR
        for c in range(3, 12): u.cell(row=r, column=c).font = f_norm
        r += 1
    f1 = r - 1
    u.cell(row=r, column=1, value="Summe " + g["name"]).font = f_bold
    for c in range(3, 12):
        col = get_column_letter(c)
        cell = u.cell(row=r, column=c, value=f"=SUM({col}{f0}:{col}{f1})"); cell.font = f_bold
        if c >= 6: cell.number_format = EUR
    for c in range(1, 12): u.cell(row=r, column=c).fill = fill_sub; u.cell(row=r, column=c).border = b_top
    ges_sub.append(r); r += 2
u.cell(row=r, column=1, value="GESAMT alle Gesellschaften").font = f_bold
for c in range(3, 12):
    col = get_column_letter(c)
    cell = u.cell(row=r, column=c, value="=" + "+".join(f"{col}{x}" for x in ges_sub)); cell.font = f_bold
    if c >= 6: cell.number_format = EUR
for c in range(1, 12): u.cell(row=r, column=c).fill = fill_tot; u.cell(row=r, column=c).border = b_tot
TOTAL_ROW = r
r += 2
u.cell(row=r, column=1, value="Kontrolle: Summe der offenen Novemberposten lt. Immocloud-Liste (38 Posten)").font = f_sub
u.cell(row=r, column=6, value=f"=F{TOTAL_ROW}+G{TOTAL_ROW}").number_format = EUR; u.cell(row=r, column=6).font = f_sub
u.cell(row=r, column=7, value="Immocloud: 11.098,85 € (davon 2.930,75 € erwartet)").font = f_sub
r += 2
# Top-Rückstände
u.cell(row=r, column=1, value="Größte Rückstände (fällig, Stand " + STAND + ")").font = f_bold; r += 1
TH = ["Mieter", "Objekt", "Einheit", "Rückstand gesamt, fällig", "davon Nov 2026", "davon Vormonate"]
for c, h in enumerate(TH, start=1):
    cell = u.cell(row=r, column=c, value=h); cell.font = f_head; cell.fill = fill_head; cell.alignment = Alignment(wrap_text=True, vertical="center")
r += 1
def rueck(x): return max(0.0, -(x["saldo"] or 0.0)) if x["saldo"] is not None else 0.0
top = sorted([x for x in row_index if rueck(x) > 0], key=rueck, reverse=True)[:15]
for x in top:
    dr = x["row"]
    for c, sc in enumerate(["F", "B", "E", "O", "J", "M"], start=1):
        cell = u.cell(row=r, column=c, value=f"=Daten!{sc}{dr}"); cell.font = f_link
        if c >= 4: cell.number_format = EUR
    r += 1
for i, w in enumerate([40, 36, 10, 10, 12, 14, 14, 14, 14, 14, 16], start=1): u.column_dimensions[get_column_letter(i)].width = w
u.conditional_formatting.add(f"J5:J{TOTAL_ROW}", red_rule())
u.freeze_panes = "A5"
u.page_setup.orientation = "landscape"; u.page_setup.fitToWidth = 1; u.page_setup.fitToHeight = 0; u.sheet_properties.pageSetUpPr.fitToPage = True

# ---------------------------------------------------------------- Hinweise
h = wb.create_sheet("Hinweise")
notes = [
 ("Quelle", f"Immocloud (Konto Jürgen Penkhues), gelesen am {STAND}; Bestandsaufnahme-Datei ‚Immocloud_Bestandsaufnahme_2026-11-07.md‘ (NAS/alle/Immocloud_Export_2026-11-07). Verwendet: Objektliste mit Eigentümer (A2), Mietverhältnisse mit Saldo (A3) und offene Mieten November 2026 (A6)."),
 ("Stichtag", f"Datenstand {STAND}. Zahlungseingänge zwischen dem {STAND} und dem {ERSTELLT} sind nicht enthalten. Vor einer Mahnung bitte den aktuellen Kontostand in Immocloud bzw. auf dem Bankkonto prüfen."),
 ("Lesart Saldo", "Saldo lt. Immocloud: negativ = Rückstand, positiv = Guthaben/Überzahlung. Der Saldo enthält nur fällige Sollstellungen. Posten mit Immocloud-Status ‚Erwartet‘ (Novembermiete noch nicht fällig) sind nicht im Saldo und werden gesondert ausgewiesen."),
 ("Berechnung", "Nov 2026 offen = Spalte ‚offen‘ der Immocloud-Liste (bei ‚Teilbezahlt‘ der Wert ‚Zu wenig‘). Rückstand Vormonate = −(Saldo + Nov überfällig), wenn positiv. Guthaben aus Vormonaten = Saldo + Nov überfällig, wenn positiv. Rückstand gesamt (fällig) = Nov überfällig + Vormonate − Guthaben, mindestens 0. Offen gesamt inkl. noch nicht fällig = Rückstand gesamt + noch nicht fällige Novembermiete, nach Verrechnung mit Guthaben."),
 ("Nicht zugeordnete Umsätze", "In Immocloud waren am 07.11.2026 insgesamt 1.130 Bankumsätze nicht zugeordnet (387 im Zeitraum 07.05.–07.11.2026, u. a. interne Umbuchungen, Versorger, Rechnungen KP Immobilien GmbH). Mieterzahlungen darunter würden die hier ausgewiesenen Rückstände verringern. Für Ralf Francki (Krefeld) liegt ein Zuordnungsvorschlag vor."),
 ("Abweichung Objektsummen", "Die Summe der Einheitensaldi weicht bei zwei Objekten von der Objektliste in Immocloud ab: Duisburg Wilhelmstr 4 hier 3.509,50 € (Immocloud 3.529,50 €), Bickernstr 102 hier 5.612,60 € (Immocloud 5.665,60 €). Alle anderen Objekte stimmen überein. Ursache unklar, in Immocloud prüfen."),
 ("Sonderfälle", "Monika Hilgers (Krefeld 1.OG vorne, 5.685 €): NAS-Fotos vom 03.11.2026 bezeichnen die Wohnung als ‚ehemals Hilgers‘; das Mietende ist in Immocloud offenbar nicht erfasst. Roni Osman (Breilstr 16): Vertragswerte 765 €/Monat belegt, Zusammensetzung des Rückstands im separaten OP-Projekt noch ungeklärt. Szabolcs Bella (Breilstr 16): Mahnung vom 13.11.2026 über 905 € inkl. 5 € Mahngebühr."),
 ("Nicht enthalten", "Kautionsrückstände, Nebenkostenabrechnungs-Salden, Mahngebühren und Verzugszinsen sind nicht Teil dieser Liste (Kautionshinweise aus der NAS-Mietaufstellung 06/2026 stehen nur in der Spalte Hinweis). Hilden, Ginsterweg 1 (privat) und Kohlstraße 4 (verkauft) sind nicht enthalten."),
 ("Bankbefund", "Spalten R/S: Abgleich der Mieteingänge 2026 mit den Volksbank-Kontoauszügen 12/2025–09/2026 (Velbert 17974401, Krefeld 18375000, Bickernstr 18375001) bzw. dem Kassenbuch (Adenau, bis 10.11.2026). ‚Rückstand lt. Bank‘ = Soll Januar–September 2026 (9 Monate, Immocloud-Soll bzw. Dauerzahlung) minus Mieteingänge für diese Monate; negativ = Guthaben/Überzahlung. Zahlungen für Oktober/November 2026 sind nicht enthalten (Auszüge liegen noch nicht vor). Für Breilstr, Gymnich, Duisburg und Lenaustr liegen nur die Zahlerdaten Juli–September 2026 aus dem Projekt vor. Leistungsmonat: Nennung im Verwendungszweck, sonst Buchungstag (ab dem 25. = Folgemonat); Nebenkosten-Nachzahlungen, Kautionen und Umbuchungen zählen nicht als Miete. Details je Zahlung: Zahlungsabgleich_2026_2026-11-12.xlsx."),
 ("Pflege", "Neue Werte nur im Blatt ‚Daten‘ in den blauen Spalten eintragen (Soll-Miete, Nov offen, Saldo). Die Blätter je Gesellschaft und die Übersicht rechnen automatisch nach."),
]
h["A1"] = "Hinweise und Methodik"; h["A1"].font = f_title
rr = 3
for k, v in notes:
    h.cell(row=rr, column=1, value=k).font = f_bold; h.cell(row=rr, column=1).alignment = wrap
    c = h.cell(row=rr, column=2, value=v); c.font = f_norm; c.alignment = wrap
    h.row_dimensions[rr].height = max(30, 15 * (len(v) // 110 + 1))
    rr += 1
h.column_dimensions["A"].width = 26; h.column_dimensions["B"].width = 120

wb.save(OUT)
print("saved", OUT, "Daten rows", LAST - 1)

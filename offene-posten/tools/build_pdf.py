import json, sys, os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

SRC, OUTDIR = sys.argv[1], sys.argv[2]
d = json.load(open(SRC, encoding="utf-8"))
STAND, ERSTELLT = d["stand_immocloud"], d["erstellt"]
pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont("DVI", '/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf'))
NAVY = colors.HexColor("#1F3864"); SEC = colors.HexColor("#D9E1F2"); SUB = colors.HexColor("#F2F2F2"); TOT = colors.HexColor("#FFF2CC"); RED = colors.HexColor("#C00000"); GREY = colors.HexColor("#555555")
st_title = ParagraphStyle("t", fontName="DVB", fontSize=15, leading=19, spaceAfter=2)
st_sub = ParagraphStyle("s", fontName="DVI", fontSize=8.5, leading=11, textColor=GREY, spaceAfter=8)
st_h2 = ParagraphStyle("h2", fontName="DVB", fontSize=11, leading=14, spaceBefore=6, spaceAfter=4)
st_cell = ParagraphStyle("c", fontName="DV", fontSize=7.6, leading=9.2)
st_cellb = ParagraphStyle("cb", fontName="DVB", fontSize=7.6, leading=9.2)
st_hint = ParagraphStyle("h", fontName="DV", fontSize=6.6, leading=8, textColor=GREY)
st_head = ParagraphStyle("hd", fontName="DVB", fontSize=7.2, leading=8.6, textColor=colors.white)
st_note = ParagraphStyle("n", fontName="DV", fontSize=7.8, leading=10.2, spaceAfter=3)

def eur(x, dash=True):
    if x is None or (dash and abs(x) < 0.005): return "–"
    s = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if x < 0 else "") + s + " €"

def calc(e):
    saldo = e.get("saldo"); nov = e.get("nov_offen")
    j = nov if (nov is not None and e.get("nov_faellig")) else 0.0
    k = nov if (nov is not None and not e.get("nov_faellig")) else 0.0
    if saldo is None: return dict(j=0, k=0, vor=0, gut=0, ges=0, inkl=0, saldo=None)
    vor = max(0.0, -(saldo + j)); gut = max(0.0, saldo + j)
    ges = max(0.0, j + vor - gut); inkl = max(0.0, j + vor - gut + k)
    return dict(j=j, k=k, vor=vor, gut=gut, ges=ges, inkl=inkl, saldo=saldo)

def header_footer(canvas, doc):
    canvas.saveState(); canvas.setFont("DV", 7); canvas.setFillColor(GREY)
    canvas.drawString(12*mm, 8*mm, f"Offene-Posten-Liste Mieter · Datenstand Immocloud {STAND} · erstellt {ERSTELLT} · vertraulich")
    canvas.drawRightString(landscape(A4)[0] - 12*mm, 8*mm, f"Seite {doc.page}")
    canvas.restoreState()

def house_table(o):
    cols = ["Einheit", "Mieter", "Status", "Soll-Miete\n11/2026", "Nov 2026 offen,\nüberfällig", "Nov 2026\nnoch nicht fällig", "Rückstand\nVormonate", "Guthaben\nVormonate", "Rückstand\ngesamt, fällig", "Hinweis"]
    W = [34*mm, 44*mm, 17*mm, 19*mm, 21*mm, 21*mm, 21*mm, 19*mm, 22*mm, 55*mm]
    data = [[Paragraph(c.replace("\n", "<br/>"), st_head) for c in cols]]
    sums = dict(j=0, k=0, vor=0, gut=0, ges=0); n_r = 0
    for e in o["einheiten"]:
        c = calc(e)
        hint = e.get("hinweis", "")
        if c["saldo"] is not None and c["j"] and (c["saldo"] + c["j"]) > 0:
            hint = (hint + ". " if hint else "") + f"Guthaben aus Vormonaten {eur(c['saldo']+c['j'])}, Novembermiete noch offen – Verrechnung prüfen"
        stl = st_cellb if c["ges"] > 0 else st_cell
        nov_txt = eur(c["j"]) if c["j"] else "–"
        if e.get("nov_status") == "Teilbezahlt": nov_txt += "\n(teilbezahlt)"
        row = [Paragraph(e["einheit"], st_cell), Paragraph(e["mieter"], stl), Paragraph(e["status"], st_cell),
               Paragraph(eur(e.get("soll")) if e.get("soll") else "–", st_cell), Paragraph(nov_txt.replace("\n", "<br/>"), st_cell),
               Paragraph(eur(c["k"]) if c["k"] else "–", st_cell), Paragraph(eur(c["vor"]), st_cell), Paragraph(eur(c["gut"]), st_cell),
               Paragraph(f'<font color="#C00000"><b>{eur(c["ges"])}</b></font>' if c["ges"] > 0 else "–", st_cell), Paragraph(hint, st_hint)]
        data.append(row)
        for kk in sums: sums[kk] += c[kk]
        if c["ges"] > 0: n_r += 1
    data.append([Paragraph("Summe " + o["objekt"], st_cellb), Paragraph(f"{n_r} Mieter mit Rückstand", st_cellb), "", "",
                 Paragraph(eur(sums["j"]), st_cellb), Paragraph(eur(sums["k"]), st_cellb), Paragraph(eur(sums["vor"]), st_cellb), Paragraph(eur(sums["gut"]), st_cellb),
                 Paragraph(f'<font color="#C00000">{eur(sums["ges"])}</font>', st_cellb), ""])
    t = Table(data, colWidths=W, repeatRows=1)
    ts = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (3, 1), (8, -1), "RIGHT"),
          ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBBBBB")), ("BACKGROUND", (0, -1), (-1, -1), SUB),
          ("LINEABOVE", (0, -1), (-1, -1), 0.8, NAVY), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    for i in range(1, len(data) - 1):
        if i % 2 == 0: ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAFAFA")))
    t.setStyle(TableStyle(ts))
    for i in range(1, len(data)):
        for ci in range(3, 9):
            if isinstance(data[i][ci], Paragraph): data[i][ci].style = ParagraphStyle("r", parent=data[i][ci].style, alignment=2)
    return t, sums, n_r

def summary_table(gs):
    cols = ["Gesellschaft / Objekt", "Adresse", "Einh.", "verm.", "Mieter m. Rückst.", "Nov 2026 offen, überfällig", "Nov 2026 noch nicht fällig", "Rückstand Vormonate", "Guthaben Vormonate", "Rückstand gesamt, fällig", "Offen inkl. nicht fällig"]
    W = [52*mm, 52*mm, 12*mm, 12*mm, 18*mm, 24*mm, 24*mm, 24*mm, 22*mm, 24*mm, 24*mm]
    data = [[Paragraph(c, st_head) for c in cols]]; styles = []
    G = dict(j=0, k=0, vor=0, gut=0, ges=0, inkl=0, n=0, u=0, v=0)
    for g in gs:
        data.append([Paragraph(g["name"], st_cellb)] + [""] * 10); styles.append(("BACKGROUND", (0, len(data)-1), (-1, len(data)-1), SEC))
        S = dict(j=0, k=0, vor=0, gut=0, ges=0, inkl=0, n=0, u=0, v=0)
        for o in g["objekte"]:
            s = dict(j=0, k=0, vor=0, gut=0, ges=0, inkl=0, n=0, u=0, v=0)
            for e in o["einheiten"]:
                c = calc(e); s["u"] += 1; s["v"] += (e["status"] != "Leerstand"); s["n"] += (c["ges"] > 0)
                for kk in ("j", "k", "vor", "gut", "ges", "inkl"): s[kk] += c[kk]
            for kk in s: S[kk] += s[kk]
            data.append([Paragraph("   " + o["objekt"], st_cell), Paragraph(o["adresse"], st_cell), Paragraph(str(s["u"]), st_cell), Paragraph(str(s["v"]), st_cell), Paragraph(str(s["n"]), st_cell),
                         Paragraph(eur(s["j"]), st_cell), Paragraph(eur(s["k"]), st_cell), Paragraph(eur(s["vor"]), st_cell), Paragraph(eur(s["gut"]), st_cell),
                         Paragraph(f'<font color="#C00000"><b>{eur(s["ges"])}</b></font>' if s["ges"] > 0 else "–", st_cell), Paragraph(eur(s["inkl"]), st_cell)])
        for kk in S: G[kk] += S[kk]
        data.append([Paragraph("Summe " + g["name"], st_cellb), "", Paragraph(str(S["u"]), st_cellb), Paragraph(str(S["v"]), st_cellb), Paragraph(str(S["n"]), st_cellb),
                     Paragraph(eur(S["j"]), st_cellb), Paragraph(eur(S["k"]), st_cellb), Paragraph(eur(S["vor"]), st_cellb), Paragraph(eur(S["gut"]), st_cellb),
                     Paragraph(f'<font color="#C00000">{eur(S["ges"])}</font>', st_cellb), Paragraph(eur(S["inkl"]), st_cellb)])
        styles += [("BACKGROUND", (0, len(data)-1), (-1, len(data)-1), SUB), ("LINEABOVE", (0, len(data)-1), (-1, len(data)-1), 0.8, NAVY)]
    if len(gs) > 1:
        data.append([Paragraph("GESAMT alle Gesellschaften", st_cellb), "", Paragraph(str(G["u"]), st_cellb), Paragraph(str(G["v"]), st_cellb), Paragraph(str(G["n"]), st_cellb),
                     Paragraph(eur(G["j"]), st_cellb), Paragraph(eur(G["k"]), st_cellb), Paragraph(eur(G["vor"]), st_cellb), Paragraph(eur(G["gut"]), st_cellb),
                     Paragraph(f'<font color="#C00000">{eur(G["ges"])}</font>', st_cellb), Paragraph(eur(G["inkl"]), st_cellb)])
        styles += [("BACKGROUND", (0, len(data)-1), (-1, len(data)-1), TOT), ("LINEABOVE", (0, len(data)-1), (-1, len(data)-1), 1.2, NAVY), ("LINEBELOW", (0, len(data)-1), (-1, len(data)-1), 1.2, NAVY)]
    for i in range(1, len(data)):
        for ci in range(2, 11):
            if isinstance(data[i][ci], Paragraph): data[i][ci].style = ParagraphStyle("r", parent=data[i][ci].style, alignment=2)
    t = Table(data, colWidths=W, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBBBBB")),
                           ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)] + styles))
    return t, G

NOTES = [
 f"<b>Quelle und Stichtag:</b> Immocloud (Konto J. Penkhues), gelesen am {STAND}. Zahlungseingänge nach dem {STAND} sind nicht enthalten. Vor einer Mahnung den aktuellen Stand in Immocloud bzw. auf dem Bankkonto prüfen.",
 "<b>Lesart:</b> Saldo lt. Immocloud negativ = Rückstand, positiv = Guthaben. ‚Nov 2026 offen, überfällig‘ ist der offene Betrag der Novembermiete (bei Teilzahlung der Fehlbetrag). ‚Noch nicht fällig‘ = Immocloud-Status ‚Erwartet‘, nicht im Saldo enthalten. Rückstand Vormonate = Saldo zuzüglich offener Novembermiete, wenn daraus ein Rückstand verbleibt; andernfalls Guthaben aus Vormonaten. Rückstand gesamt = Novembermiete + Vormonate − Guthaben.",
 "<b>Vorbehalt:</b> In Immocloud waren am 07.11.2026 insgesamt 1.130 Bankumsätze nicht zugeordnet (387 aus dem Zeitraum 07.05.–07.11.2026). Mieterzahlungen darunter würden die Rückstände verringern. Objektsummen weichen bei Duisburg Wilhelmstr 4 (−20 €) und Bickernstr 102 (−53 €) von der Immocloud-Objektliste ab.",
 "<b>Nicht enthalten:</b> Kautionsrückstände, Nebenkostenabrechnungs-Salden, Mahngebühren und Verzugszinsen (nur als Hinweis). Hilden, Ginsterweg 1 (privat) und Kohlstraße 4 (verkauft) sind nicht Teil der Liste.",
]

def build(gs, title, fname):
    doc = SimpleDocTemplate(os.path.join(OUTDIR, fname), pagesize=landscape(A4), leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=14*mm, title=title, author="Käshammer und Penkhues")
    story = [Paragraph(title, st_title), Paragraph(f"Offene Posten Mieter nach Gesellschaft und Haus · Datenstand Immocloud {STAND} · erstellt {ERSTELLT} · Beträge in Euro", st_sub)]
    t, G = summary_table(gs); story += [t, Spacer(1, 6)]
    for n in NOTES: story.append(Paragraph(n, st_note))
    for g in gs:
        for o in g["objekte"]:
            story.append(PageBreak())
            story.append(Paragraph(f"{g['name']}", st_sub))
            story.append(Paragraph(f"{o['objekt']} · {o['adresse']} · Bankkonto {o['konto']}", st_h2))
            ht, s, n_r = house_table(o)
            story.append(ht)
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print("PDF", fname, "Rückstand gesamt", round(G["ges"], 2))

slug = {"Käshammer und Penkhues Immobilien eGbR": "eGbR", "KPK Grundbesitz GmbH": "KPK-Grundbesitz-GmbH", "PK Immo Verwaltungs GmbH": "PK-Immo-Verwaltungs-GmbH"}
for g in d["gesellschaften"]:
    build([g], f"Offene-Posten-Liste Mieter – {g['name']}", f"OP-Liste_{slug[g['name']]}_{ERSTELLT[6:]}-{ERSTELLT[3:5]}-{ERSTELLT[:2]}.pdf")
build(d["gesellschaften"], "Offene-Posten-Listen Mieter – alle Gesellschaften", f"OP-Listen_Gesamt_{ERSTELLT[6:]}-{ERSTELLT[3:5]}-{ERSTELLT[:2]}.pdf")

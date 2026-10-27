# Lieferscheine aus WhatsApp genauso verarbeiten wie aus der Mail

Stand: 27.10.2026. Verfasst mit Claude für Karl-Philipp Käshammer, Bauzaun-Experte GmbH.

## Kurzfassung

Die Routinen („Rechnungsentwürfe aus Lieferscheinen“, „Scan-Nachkontrolle“, „Mail-Überwachung“)
lesen heute genau drei Quellen: das Postfach info@, Karls Postfach (jeweils alle Ordner) und die
Auftragsordner in SharePoint. Sie schauen sich dort jeden PDF- und Bildanhang selbst an, egal wie
Betreff oder Datei heißen, und lesen die LS-Nummer vom Schein ab.

Der sinnvollste Weg für WhatsApp ist deshalb kein neuer Verarbeitungsweg, sondern eine **Brücke,
die jedes WhatsApp-Foto als Mail an info@ ablegt**. Danach läuft alles wie bei einem per Mail
geschickten Scan: Mail-Überwachung meldet „LS-Scan … → Rechnungsentwurf folgt automatisch“,
Rechnungsentwürfe legt den Entwurf an und hängt den Scan in der Baustellen-App an, die
Scan-Nachkontrolle findet ihn als Nachtrag. **An den Routinen muss nichts geändert werden.**

Drei Stufen, die aufeinander aufbauen:

| Stufe | Was | Aufwand | Laufende Kosten | Automatik | Deckt ab |
|---|---|---|---|---|---|
| 1 | Teilen-Kurzbefehl „Lieferschein ans Büro“ auf dem iPhone | 15 Minuten | 0 € | 2 Tipper je Schein | alles, was auf Karls/Sebastians Handy ankommt |
| 2 | Büro-Handy (Android) mit WhatsApp + OneDrive-Kameraupload + Power-Automate-Flow | 1–2 Stunden | Zweitnummer (eSIM, ca. 2–5 €/Monat), ggf. ein M365-Benutzer | vollautomatisch | alles, was an die Büro-Nummer oder in Gruppen mit ihr geschickt wird |
| 3 | WhatsApp Cloud API (Meta) → Azure Logic App → Mail an info@ | halber Tag + Meta-Freischaltung | Cent-Beträge in Azure, eingehende WhatsApp-Nachrichten kostenlos | vollautomatisch, kein Handy nötig | alles, was an die API-Nummer geschickt wird (bei „Coexistence“ auch Karls bestehende Nummer, aber keine Gruppen) |

**Empfehlung:** Stufe 1 heute einrichten (sofortige Wirkung, kein Risiko). Parallel Stufe 2
aufbauen, weil sie ohne Meta-Freigabe, ohne Azure und ohne Programmierung auskommt und Gruppen
abdeckt. Stufe 3 ist der saubere Endzustand, wenn ein Büro-Handy nicht gewollt ist oder die
Nummer dauerhaft ohne Gerät laufen soll. Die Logic-App-Vorlage liegt fertig bei.

## Warum „Mail an info@“ und nicht „Datei nach SharePoint“ oder „direkt in die App“

- Die Mail ist die einzige Quelle, die **alle** drei Routinen schon heute lesen. Eine Datei in
  SharePoint würde nur gefunden, wenn sie im richtigen Auftragsordner „AB… “ liegt; den kennt die
  Brücke nicht, weil die LS-Nummer erst beim Ansehen des Scans bekannt wird.
- Ein Scan direkt in der Baustellen-App („belege“) bräuchte die LS- und AB-Nummer schon beim
  Hochladen. Das Zuordnen macht heute die Routine aus dem Bild. Das soll so bleiben.
- Dubletten (WhatsApp liefert ein Bild gelegentlich doppelt) sind unkritisch: Die Routinen zählen
  denselben Anhangnamen als einen Scan, deshalb vergibt die Brücke je Bild einen festen Dateinamen
  (Stufe 3: Medien-ID von Meta; Stufe 2: Dateiname aus dem WhatsApp-Ordner).
- Mails an lieferscheine@ und trupp_1@ laufen offenbar auf info@ auf; beides sind keine eigenen
  Postfächer (Graph meldet „invalid user“). Ziel der Brücke ist deshalb immer info@bauzaun-experte.de.

## Was in jeder Stufe gleich ist

1. Betreff beginnt mit „[WhatsApp]“, dazu Absendername oder Nummer und, falls der Sender eine
   Zeile wie „LS262437“ dazuschreibt, dieser Text. Die Routine findet die LS-Nummer sonst auf dem
   Schein; der Betreff hilft nur bei unscharfen Fotos.
2. Das Bild hängt im Original an (kein Link, keine Vorschau). WhatsApp verkleinert Fotos auf etwa
   1600 Pixel Breite; das reicht für die Kopfzeile, aber bitte den Sendern sagen: Foto
   **„Als Dokument senden“** (volle Auflösung) oder „HD“ wählen, Schein flach und ganz im Bild.
3. Die Mail geht von einem Firmenkonto an info@. Die Mail-Überwachung behandelt Mails von
   info@/Karl an info@ als Jobs, die anderen Routinen lesen ohnehin alle Mails mit Bildanhang.

## Nächste Schritte (Vorschlag)

- [ ] Stufe 1: Kurzbefehl nach `stufe-1-kurzbefehl.md` auf Karls iPhone anlegen, einmal testen
      (Foto aus WhatsApp → nach 10 Minuten steht „LS-Scan … von Karl“ in der Übersicht der
      Mail-Überwachung, spätestens beim nächsten Lauf von „Rechnungsentwürfe“ der Entwurf).
- [ ] Entscheiden: Büro-Handy (Stufe 2) oder Cloud API (Stufe 3). Beides kann später nebeneinander laufen.
- [ ] Sender informieren (Monteure, Cteam-Bauleiter): Scheine bitte an die Büro-Nummer bzw. in die
      Gruppe mit dem Büro-Handy, als Dokument/HD, LS-Nummer als Text dazu.
- [ ] Optional, nach 2 Wochen: Routinentexte um einen Satz ergänzen (siehe unten). Nötig ist das nicht.

## Optionale Ergänzung der Routinentexte (nur mit Karls Freigabe, Prüfsummen ändern sich)

In `mail-jobs.txt`, Abschnitt „LIEFERSCHEIN-SCANS (e)“, ein Satz:
„Mails mit Betreff „[WhatsApp] …“ sind automatisch weitergeleitete WhatsApp-Bilder; sie zählen wie
Scan-Mails, Absender ist der WhatsApp-Kontakt im Betreff, nicht das Firmenkonto.“

In `rechnungsentwuerfe.txt` und `scan-nachkontrolle.txt` unter „Quellen“ ein Satz:
„Mails mit Betreff „[WhatsApp] …“ enthalten je ein WhatsApp-Bild im Original; LS-Nummer wie immer
vom Schein lesen, Name und Nummer des WhatsApp-Absenders stehen im Betreff und im Mailtext.“

## Dateien in diesem Ordner

- `stufe-1-kurzbefehl.md` – Teilen-Kurzbefehl fürs iPhone (und der Android-Weg über Outlook).
- `stufe-2-buero-handy.md` – Büro-Handy mit WhatsApp, OneDrive-Kameraupload, Power-Automate-Flow.
- `stufe-3-cloud-api/README.md` – Meta-Einrichtung, Azure-Bereitstellung, Test, Coexistence-Hinweise.
- `stufe-3-cloud-api/logic-app-template.json` – fertige ARM-Vorlage der Logic App „WhatsApp-Mail-Brücke“.

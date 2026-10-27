# Stufe 1: Kurzbefehl „Lieferschein ans Büro“ (iPhone, 15 Minuten, 0 €)

Ziel: Ein WhatsApp-Foto mit zwei Tippern als Mail an info@bauzaun-experte.de schicken, mit
Betreff „[WhatsApp] Lieferschein …“. Ab da verarbeiten die Routinen es wie jeden anderen Scan.

## Einrichten (einmalig, App „Kurzbefehle“)

1. Kurzbefehle öffnen → „+“ (neuer Kurzbefehl) → oben Namen vergeben: **Lieferschein ans Büro**.
2. Auf das Info-Symbol (i) tippen → **„Im Freigabeblatt anzeigen“** einschalten.
   Bei „Freigabeblatt-Typen“ nur **Bilder, PDFs, Dateien** lassen.
3. Aktion 1 hinzufügen: **„Nach Eingabe fragen“** → Eingabetyp *Text*, Frage:
   `LS-Nummer oder Hinweis (kann leer bleiben)`.
4. Aktion 2 hinzufügen: **„E-Mail senden“** (Mail-App):
   - Empfänger: `info@bauzaun-experte.de`
   - Betreff: `[WhatsApp] Lieferschein ` + die Variable *Eingabe* aus Aktion 1 (Variable per
     „Variable auswählen“ in das Betreff-Feld ziehen)
   - Inhalt: die Variable **Kurzbefehl-Eingabe** (das ist das Foto oder die PDF; Mail hängt es an)
   - Pfeil bei „E-Mail senden“ aufklappen: **„Compose-Fenster anzeigen“ ausschalten**,
     Absender: das Firmenkonto (karl.kaeshammer@…). Dann geht die Mail ohne Nachfrage raus.
5. Fertig. Einmal testen: In WhatsApp ein Foto öffnen → Teilen-Symbol → „Lieferschein ans Büro“
   → LS-Nummer eintippen oder leer lassen → fertig.

## Benutzen

- Ein Foto: In WhatsApp das Foto antippen → Teilen → **Lieferschein ans Büro**.
- Mehrere Fotos auf einmal: Nachricht gedrückt halten → „Mehr…“ → alle Fotos anhaken → Teilen
  (Viereck mit Pfeil) → **Lieferschein ans Büro**. Es entsteht eine Mail mit allen Bildern.
- PDFs, die jemand per WhatsApp „als Dokument“ schickt, gehen genauso.

## Android (Sebastian, Trupp-Handys): ohne Kurzbefehl

Foto in WhatsApp antippen → Teilen → **Outlook** → An: info@bauzaun-experte.de,
Betreff: `[WhatsApp] Lieferschein LS…` → Senden. Drei Tipper mehr, gleiches Ergebnis.

## Was die Routinen danach tun

- Mail-Überwachung (alle 2 Stunden): meldet „LS-Scan LS… von Karl → Rechnungsentwurf folgt automatisch“.
- Rechnungsentwürfe aus Lieferscheinen (7:43, 11:43, 15:43): liest den Schein, legt den
  Rechnungsentwurf in Lexware an, hängt den Scan in der Baustellen-App an.
- Scan-Nachkontrolle (8:05, 12:05, 16:05): findet den Scan als Nachtrag, falls er oben durchrutschte.

## Grenzen

- Es bleibt ein Handgriff je Schein. Wer das Weiterleiten vergisst, hat den Schein nur im Chat.
  Deshalb Stufe 2 oder 3 als Dauerlösung.

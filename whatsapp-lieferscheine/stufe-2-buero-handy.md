# Stufe 2: Büro-Handy als WhatsApp-Brücke (ohne Programmierung, vollautomatisch)

Idee: Ein Android-Handy mit WhatsApp (Business) auf einer **Büro-Nummer** empfängt die Scheine.
Die OneDrive-App lädt den WhatsApp-Bilderordner automatisch nach OneDrive. Ein Power-Automate-Flow
(Standard-Konnektoren, in Microsoft 365 enthalten) schickt jede neue Datei als Mail an info@.
Ergebnis für die Routinen: dieselbe Mail wie ein Scan vom Monteur.

Warum ein echtes Handy: WhatsApp-Gruppen (z. B. „Trupp 1“, „Cteam Schutterwald“) werden nur von
einem normalen WhatsApp-Client empfangen. Die Cloud API (Stufe 3) sieht Gruppen nicht.

## Was gebraucht wird

- Ein Android-Handy (ein ausgemustertes reicht; Dauerstrom, WLAN im Büro).
- Eine Nummer für WhatsApp: eSIM oder Prepaid-SIM (2–5 €/Monat). Die Nummer bleibt dauerhaft die
  „Lieferschein-Nummer“ der Firma. Alternativ ein Trupp-Handy, das ohnehin WhatsApp hat
  (das Google-Konto trupp_1@bauzaun-experte.de ist bereits mit WhatsApp verknüpft, siehe
  Google-Hinweismail vom 23.09.2026 in info@).
- Ein Microsoft-365-Benutzer mit OneDrive und Power Automate, z. B. ein neuer Benutzer
  `scan@bauzaun-experte.de` (Business Basic genügt). Shared Mailboxes wie info@ haben kein OneDrive.

## Einrichten

### A) Handy (30 Minuten)

1. WhatsApp Business installieren, mit der Büro-Nummer registrieren. Profilname
   „Bauzaun-Experte Lieferscheine“. Begrüßungsnachricht (Einstellungen → Unternehmenstools):
   „Hier bitte nur ausgefüllte Liefer- und Retourenscheine als Foto oder PDF, am besten
   „Als Dokument senden“. LS-Nummer als Text dazu. Antworten liest hier niemand.“
2. WhatsApp → Einstellungen → Speicher und Daten → **Automatischer Download** für Fotos und
   Dokumente über WLAN und Mobilfunk **ein**. Einstellungen → Chats → **Medien-Sichtbarkeit ein**
   (dann liegen die Bilder im Gerätespeicher, wo OneDrive sie sieht).
3. OneDrive-App installieren, mit dem Benutzer scan@ anmelden. **Ich → Einstellungen →
   Kamera-Upload** einschalten, Upload auch über Mobilfunk erlauben, dann **„Zusätzliche Ordner“**
   öffnen und **WhatsApp Images** (und, falls angeboten, WhatsApp Documents) anhaken.
   Die Bilder landen in OneDrive unter „Bilder“ (Unterordner je Quelle).
   Hinweis: Auf Samsung-Geräten ersetzt „Samsung Gallery Sync“ den Kamera-Upload; dort die
   Verknüpfung in der Galerie-App lösen, dann erscheint der Kamera-Upload wieder.
4. Falls die Liste „Zusätzliche Ordner“ keine WhatsApp-Dokumente (PDF) anbietet: die App
   **Autosync for OneDrive** (MetaCtrl, einmalig wenige Euro) installieren und den Ordner
   `Android/media/com.whatsapp.w4b/WhatsApp Business/Media/WhatsApp Documents` nach
   OneDrive „Bilder/WhatsApp Documents“ synchronisieren lassen (nur Upload).
5. Akku-Optimierung für WhatsApp und OneDrive abschalten (Einstellungen → Apps → … → Akku →
   „Nicht einschränken“), sonst pausiert der Upload nach Stunden.

### B) Power-Automate-Flow (20 Minuten, make.powerautomate.com, angemeldet als scan@)

Erstellen → Automatisierter Cloud-Flow → Name **WhatsApp-Bilder an info@**:

1. Trigger **OneDrive for Business – „Wenn eine Datei erstellt wird“**
   Ordner: `/Bilder` · „Unterordner einschließen“: Ja · „Dateiinhalt abrufen“: Ja.
2. Aktion **Office 365 Outlook – „E-Mail senden (V2)“**
   - An: `info@bauzaun-experte.de`
   - Betreff: `[WhatsApp] Lieferschein ` + dynamischer Inhalt *Dateiname*
   - Text: `Automatisch vom Büro-Handy weitergeleitet. Datei: ` + *Dateipfad* + `, hochgeladen: ` + *Letzte Änderung*
   - Anlagen: Name = *Dateiname*, Inhalt = *Dateiinhalt*
   - (Erweitert) „Von (Senden als)“ leer lassen; die Mail geht dann von scan@. Soll sie von info@
     kommen: scan@ in Exchange die Berechtigung „Senden als“ auf info@ geben und `info@bauzaun-experte.de` eintragen.
3. Speichern. Test: Foto an die Büro-Nummer schicken → nach 1–3 Minuten steht die Mail in info@.

Kosten: Standard-Konnektoren (OneDrive for Business, Office 365 Outlook) sind in der
Microsoft-365-Lizenz des Benutzers enthalten; es braucht keine Premium-Lizenz.

### C) Sender umstellen

- Monteure: Scheine an die Büro-Nummer (oder die Büro-Nummer in die Trupp-Gruppen aufnehmen;
  Bilder aus Gruppen werden genauso heruntergeladen und weitergeleitet).
- Kunden/Bauleiter, die bisher Karl schreiben: einmal die Büro-Nummer mitteilen; was trotzdem
  bei Karl landet, geht weiter über Stufe 1 (Kurzbefehl).

## Variante: Trupp-Handys direkt (noch einen Schritt kürzer)

Wenn die Trupps ihre Scheine mit dem Firmen-Handy fotografieren, kann die OneDrive-App dort mit
dem Trupp-Benutzer angemeldet den **Kamera-Ordner** hochladen. Dann muss niemand mehr etwas
senden: Foto machen genügt, der Flow (auf dem Trupp-Benutzer) schickt es an info@. Dafür landen
alle Fotos des Firmen-Handys in OneDrive, auch Baustellenfotos; die Routinen überspringen Fotos
ohne Schein. Das vorher mit den Monteuren besprechen (Firmen-Gerät, dienstliche Nutzung).

## Was nicht geht

- Karls eigenes iPhone als Brücke: iOS kennt keinen WhatsApp-Ordner; nur „In Aufnahmen sichern“
  je Chat und dann der komplette Foto-Upload von Karls Fotos nach OneDrive. Nicht empfohlen.
- Das Büro-Handy ist ein Gerät, das laufen muss (Strom, WLAN, Updates). Fällt es aus, bleiben
  Scheine im Chat liegen, bis es wieder läuft; verloren geht nichts.

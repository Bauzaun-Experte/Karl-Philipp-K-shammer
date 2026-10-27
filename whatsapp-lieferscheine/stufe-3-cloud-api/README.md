# Stufe 3: WhatsApp Cloud API → Logic App → Mail an info@ (vollautomatisch, ohne Handy)

Meta liefert jede eingehende WhatsApp-Nachricht per Webhook an eine URL. Die beiliegende Azure
Logic App nimmt den Webhook an, lädt Bild oder PDF im Original herunter und schickt es als Mail
an info@bauzaun-experte.de. Eingehende Nachrichten kosten bei Meta nichts; die Logic App kostet
Cent-Beträge je Monat (Verbrauchsplan, ca. 10 Aktionen je Schein).

Die Vorlage `logic-app-template.json` ist vollständig: Verifizierung durch Meta (GET mit
`hub.challenge`), Ereignisse (POST), Medien-Download mit Bearer-Token, Mailversand über den
Office-365-Konnektor, Text-Nachrichten als eigene Mail („[WhatsApp] Nachricht von …“), fester
Dateiname je Medien-ID (Dubletten bei Meta-Wiederholungen fallen in den Routinen zusammen).

## Zwei Wege zur Nummer

**Weg A, neue Büro-Nummer direkt bei Meta (empfohlen, ohne Drittanbieter).**
Eine Nummer, die noch nicht in WhatsApp benutzt wird (eSIM oder Festnetznummer der Firma, die
SMS/Anruf zur Verifizierung empfangen kann). Die Nummer läuft dann nur über die API; es gibt
dafür keine WhatsApp-App. Das ist für einen „Briefkasten“ ideal: Jeder schickt den Schein dorthin,
niemand muss dort Chats lesen. Eine automatische Antwort („Danke, Lieferschein erhalten“) lässt
sich später ergänzen.

**Weg B, Karls bestehende Nummer („Coexistence“).**
Seit 2025 kann eine Nummer gleichzeitig in der WhatsApp-Business-App und an der Cloud API hängen.
Das geht laut Meta-Dokumentation nur über einen Meta-Partner (Solution Partner oder Tech
Provider), nicht mit einer eigenen Meta-App. Einschränkungen: **Gruppenchats werden nicht
übertragen**, Broadcast-Listen werden schreibgeschützt, Windows-/Wear-Clients werden abgemeldet,
Anrufe bleiben in der App. Wer Karl bisher in Einzelchats Scheine schickt, wäre abgedeckt; Gruppen
nicht. Der Partner reicht die Webhooks an unsere Logic-App-URL weiter (Einstellung beim Partner).
Quelle: developers.facebook.com, „Onboard WhatsApp Business app users“.

## Einrichten, Weg A

### 1) Meta (ca. 1 Stunde, business.facebook.com und developers.facebook.com)

1. Business-Portfolio der Bauzaun-Experte GmbH anlegen oder öffnen (Business Manager).
   Unternehmensverifizierung mit Handelsregisterauszug starten; sie dauert einige Tage, der
   Empfang funktioniert schon vorher.
2. developers.facebook.com → „Meine Apps“ → App erstellen → Typ „Business“ → Name
   „Bauzaun-Experte Lieferscheine“ → Produkt **WhatsApp** hinzufügen, Business-Portfolio zuordnen.
3. WhatsApp → API-Einrichtung → **Telefonnummer hinzufügen** (die Büro-Nummer; Verifizierung per
   SMS oder Anruf), Anzeigename „Bauzaun-Experte Lieferscheine“.
4. Dauerhaftes Token: Business-Einstellungen → Benutzer → **Systemnutzer** → neu (Admin) → der
   App zuweisen (vollständige Kontrolle) → „Token generieren“ mit `whatsapp_business_messaging`
   und `whatsapp_business_management`, Ablauf „nie“. Token sicher ablegen (wird gleich
   `metaAccessToken`).
5. Ein Verify-Token ausdenken (beliebige Zeichenkette, z. B. 32 Zufallszeichen). Das wird
   `metaVerifyToken`.

### 2) Azure (ca. 20 Minuten, portal.azure.com)

1. Abonnement (Pay-as-you-go reicht) und Ressourcengruppe `rg-whatsapp-bruecke` in
   Region „Germany West Central“ anlegen.
2. Suche „Benutzerdefinierte Bereitstellung“ → „Eigene Vorlage im Editor erstellen“ →
   Inhalt von `logic-app-template.json` einfügen → Speichern.
3. Parameter: `metaVerifyToken`, `metaAccessToken` (aus Schritt 1), `mailTo` lassen,
   `graphVersion` lassen (v23.0; bei Ablauf in der Meta-Changelog die aktuelle Version eintragen).
   Bereitstellen.
4. Ressource **office365-whatsapp-bruecke** (API-Verbindung) öffnen → „API-Verbindung
   bearbeiten“ → **Autorisieren** → mit dem Konto anmelden, von dem die Mails kommen sollen
   (z. B. karl.kaeshammer@ oder ein Benutzer scan@; Shared Mailboxes können sich nicht anmelden).
   Speichern. Soll „Von“ info@ sein: diesem Konto in Exchange „Senden als“ auf info@ geben und
   in der Aktion „Mail_mit_Anhang“ das Feld „Von (Senden als)“ ergänzen.
5. Logic App öffnen → Übersicht → Ausgabe `callbackUrl` der Bereitstellung kopieren
   (alternativ: Logic-App-Designer → Trigger → „HTTP-URL“). Die URL enthält eine Signatur
   (`sig=`) und ist damit das Geheimnis, das nur Meta kennen darf.

### 3) Webhook bei Meta eintragen (5 Minuten)

developers.facebook.com → App → WhatsApp → **Konfiguration** → Webhook: Callback-URL = die
Logic-App-URL, Verify-Token = `metaVerifyToken` → „Verifizieren und speichern“. Danach beim
Webhook-Feld **messages** auf „Abonnieren“.

Falls Meta die Verifizierung mit „URL couldn't be validated“ ablehnt: Im Logic-App-Designer am
Trigger unter „Erweiterte Parameter“ die **Methode auf GET** stellen, speichern, Verifizierung bei
Meta wiederholen, dann die Methode auf **POST** stellen und speichern. Die URL ändert sich dabei
nicht; Meta verifiziert nur einmal.

### 4) Test

1. Von einem beliebigen Handy ein Foto an die Büro-Nummer schicken, dazu als Text „LS262437“.
2. In der Logic App unter „Ausführungsverlauf“ erscheint ein erfolgreicher Lauf; innerhalb einer
   Minute liegt in info@ die Mail „[WhatsApp] Lieferschein von <Name> (+49…): LS262437“ mit dem
   Bild im Anhang.
3. Beim nächsten Lauf „Mail-Überwachung“ steht „LS-Scan LS262437 von … → Rechnungsentwurf folgt
   automatisch“; „Rechnungsentwürfe aus Lieferscheinen“ legt den Entwurf an und hängt den Scan in
   der Baustellen-App an.

## Betrieb

- Meta wiederholt Zustellungen, wenn die Logic App nicht mit 200 antwortet; die Vorlage antwortet
  sofort und arbeitet danach weiter. Ein doppelt zugestelltes Bild bekommt denselben Dateinamen
  (Medien-ID) und zählt in den Routinen als derselbe Scan.
- Medien-URLs von Meta sind 5 Minuten gültig; der Download folgt direkt auf den Webhook.
- Nicht unterstützte Nachrichtentypen (Sprachnachricht, Standort, Sticker) werden übersprungen;
  Videos ebenfalls (für Lieferscheine nicht nötig).
- Kosten: Logic Apps Verbrauchsplan, integrierte Aktionen etwa 0,00003 € je Aktion, Standard-
  Konnektor (Office 365) etwa 0,0001 € je Aufruf. Bei 300 Scheinen im Monat deutlich unter 1 €.
- Token-Ablauf: Systemnutzer-Token „nie“; bei Rotation nur den Parameter `metaAccessToken` in der
  Logic App ändern.

## Alternative ohne Azure

Dieselbe Kette gibt es als Klick-Lösung bei Make.com („WhatsApp Business Cloud → Watch Events“,
„Download Media“, „Email → Send“), ab etwa 9 €/Monat. Gleiches Ergebnis, dafür ein weiterer
Anbieter mit Zugriff auf die Scheine. Die Azure-Variante bleibt im Microsoft-Tenant der Firma.

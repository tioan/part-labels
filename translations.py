"""German translations, keyed by the English source text used in the code."""

DE = {
    # Shared
    "error: {message}": "Fehler: {message}",
    "must be a whole number of at least 1": "muss eine ganze Zahl von mindestens 1 sein",
    "language of all output: en or de; default from PART_LABELS_LANG, then the system language, then en": (
        "Sprache aller Ausgaben: en oder de; Standard aus PART_LABELS_LANG, dann die Systemsprache, sonst en"
    ),
    # labels.py: messages
    "{dots} dots per module do not fit {tape} mm tape with a full quiet zone": (
        "{dots} Punkte pro Modul passen mit voller Ruhezone nicht auf {tape}-mm-Band"
    ),
    "PT-P900W not found on USB": "PT-P900W per USB nicht gefunden",
    "no status reply from printer": "keine Statusantwort vom Drucker",
    "Tape needed: about {strip} per strip, {total} in total": "Bandbedarf: etwa {strip} pro Streifen, {total} insgesamt",
    "Tape needed: about {total}": "Bandbedarf: etwa {total}",
    "printing {count} labels ...": "drucke {count} Etiketten ...",
    "cancelled; labels already sent may still print, restart the printer if it does not recover": (
        "abgebrochen; bereits gesendete Etiketten können noch gedruckt werden, Drucker bei Bedarf neu starten"
    ),
    "no answer available, stopped": "keine Antwort möglich, abgebrochen",
    "Replace the tape if needed and press the printer's power button briefly to clear the error. Continue? Nothing is printed yet. [Y/n] ": (
        "Band bei Bedarf wechseln und die Power-Taste des Druckers kurz drücken, um den Fehler zu löschen. "
        "Weiter? Es wird noch nichts gedruckt. [J/n] "
    ),
    "stopped, no further labels printed": "abgebrochen, keine weiteren Etiketten gedruckt",
    "printer does not answer, press its power button briefly, or turn it off and on again": (
        "Drucker antwortet nicht, bitte Power-Taste kurz drücken oder aus- und wieder einschalten"
    ),
    "printer still reports: {errors}": "Drucker meldet weiterhin: {errors}",
    "{loaded} mm tape is loaded instead of {needed} mm: module {module} mm, code {code} mm. Continue with it? [Y/n] ": (
        "{loaded}-mm-Band statt {needed} mm eingelegt: Modul {module} mm, Code {code} mm. Damit weitermachen? [J/n] "
    ),
    "printer is ready": "Drucker ist bereit",
    "At least {count} labels are missing. Print them as a new job? [Y/n or a number] ": (
        "Mindestens {count} Etiketten fehlen. Als neuen Auftrag drucken? [J/n oder eine Zahl] "
    ),
    "please answer y, n or a number": "bitte mit j, n oder einer Zahl antworten",
    "at most {reached} of {count} labels reached the printer before it stopped": (
        "höchstens {reached} von {count} Etiketten kamen beim Drucker an, bevor er stoppte"
    ),
    "USB connection to the printer failed: {error}": "USB-Verbindung zum Drucker fehlgeschlagen: {error}",
    "printer stopped accepting data, check the tape and press its power button briefly": (
        "Drucker nimmt keine Daten mehr an, bitte Band prüfen und Power-Taste kurz drücken"
    ),
    "printer error, nothing printed: {errors}": "Druckerfehler, nichts gedruckt: {errors}",
    "{tape} mm: kept": "{tape} mm: beibehalten",
    "{tape} mm: {codes} codes, length {length} mm": "{tape} mm: {codes} Codes, Länge {length} mm",
    "{tape} mm {variant}: {found}/{expected} found": "{tape} mm {variant}: {found}/{expected} gefunden",
    "rotated+blur": "gedreht+unscharf",
    "before:": "vorher:",
    "printer:": "Drucker:",
    "{loaded} mm tape loaded, {needed} mm needed, nothing printed": (
        "{loaded}-mm-Band eingelegt, {needed} mm benötigt, nichts gedruckt"
    ),
    "printer error during printing: {errors}": "Druckerfehler beim Drucken: {errors}",
    "print complete": "Druck abgeschlossen",
    "no completion status within 120 s, check the printer": (
        "keine Fertigmeldung innerhalb von 120 s, bitte den Drucker prüfen"
    ),
    "Detected {tape} mm tape: {count} x {kind}, module {module} mm, code {code} mm": (
        "{tape}-mm-Band erkannt: {count} x {kind}, Modul {module} mm, Code {code} mm"
    ),
    "Is this the tape you want? [Y/n] ": "Ist das das gewünschte Band? [J/n] ",
    "no answer available, nothing printed": "keine Antwort möglich, nichts gedruckt",
    "cancelled, nothing printed": "abgebrochen, nichts gedruckt",
    "no standard label defined for {tape} mm tape": "für {tape}-mm-Band ist kein Standardetikett festgelegt",
    "{loaded} mm tape loaded, {requested} mm requested, nothing printed": (
        "{loaded}-mm-Band eingelegt, {requested} mm angefordert, nichts gedruckt"
    ),
    "{completed} completion reports for {count} labels": "{completed} Fertigmeldungen für {count} Etiketten",
    "no completion status, check the printer": "keine Fertigmeldung, bitte den Drucker prüfen",
    "issued: {value} ({module} mm module)": "ausgegeben: {value} (Modul {module} mm)",
    # labels.py: help
    "Print small Data Matrix ID labels on a Brother PT-P900W connected over USB.": (
        "Druckt kleine Data-Matrix-ID-Etiketten auf einem per USB angeschlossenen Brother PT-P900W."
    ),
    """typical use:
  uv run labels.py status             show the loaded tape, prints nothing
  uv run labels.py labels 20          print 20 new labels for the loaded tape
  uv run labels.py labels 20 --tape 9 same, but stop unless 9 mm tape is loaded

run "uv run labels.py <command> --help" for details on a command.""": """typische Aufrufe:
  uv run labels.py status             eingelegtes Band anzeigen, druckt nichts
  uv run labels.py labels 20          20 neue Etiketten für das eingelegte Band drucken
  uv run labels.py labels 20 --tape 9 ebenso, aber Abbruch ohne eingelegtes 9-mm-Band

"uv run labels.py <befehl> --help" zeigt Details zu einem Befehl.""",
    "<command>": "<befehl>",
    "commands": "Befehle",
    "print new labels with random IDs (main command)": "neue Etiketten mit zufälligen IDs drucken (Hauptbefehl)",
    """Print new labels with random IDs, in the standard size for the tape.

standard sizes (Data Matrix, module / code size):
   6 mm  0.28 mm /  4.0 mm   only if nothing larger fits, needs good light
   9 mm  0.49 mm /  6.9 mm   small parts
  12 mm  0.71 mm /  9.9 mm   default for most parts
  18 mm  1.06 mm / 14.8 mm   larger devices, boxes
  24 mm  1.48 mm / 20.7 mm   cases, crates
  36 mm  2.26 mm / 31.6 mm   shelves, racks

Several labels get half cuts between them and one full cut at the end, which saves tape.
With 5x100 each strip is its own job with new IDs, and a printer problem stops the remaining strips.
Without --tape, the detected tape is shown and you confirm it with [Y/n].""": """Druckt neue Etiketten mit zufälligen IDs in der Standardgröße für das Band.

Standardgrößen (Data Matrix, Modul / Codegröße):
   6 mm  0,28 mm /  4,0 mm   nur wenn nichts Größeres passt, braucht gutes Licht
   9 mm  0,49 mm /  6,9 mm   kleine Teile
  12 mm  0,71 mm /  9,9 mm   Standard für die meisten Teile
  18 mm  1,06 mm / 14,8 mm   größere Geräte, Kartons
  24 mm  1,48 mm / 20,7 mm   Gehäuse, Kisten
  36 mm  2,26 mm / 31,6 mm   Regale, Racks

Mehrere Etiketten erhalten Anschnitte dazwischen und einen vollen Schnitt am Ende, das spart Band.
Bei 5x100 ist jeder Streifen ein eigener Auftrag mit neuen IDs, ein Druckerproblem stoppt die restlichen Streifen.
Ohne --tape wird das erkannte Band angezeigt und mit [J/n] bestätigt.""",
    """examples:
  uv run labels.py labels 20
  uv run labels.py labels 5x100
  uv run labels.py labels 20 --tape 12
  uv run labels.py labels 5 --full-cut""": """Beispiele:
  uv run labels.py labels 20
  uv run labels.py labels 5x100
  uv run labels.py labels 20 --tape 12
  uv run labels.py labels 5 --full-cut""",
    "number of labels, or strips x labels: 5x100 prints 5 separate strips with 100 labels each": (
        "Anzahl der Etiketten oder Streifen x Etiketten: 5x100 druckt 5 einzelne Streifen mit je 100 Etiketten"
    ),
    "must be a number like 100 or strips x labels like 5x100": (
        "muss eine Zahl wie 100 oder Streifen x Etiketten wie 5x100 sein"
    ),
    "{strips} strips with {count} labels each": "{strips} Streifen mit je {count} Etiketten",
    "strip {strip}/{strips} printed": "Streifen {strip}/{strips} gedruckt",
    "printer error, stopped after {done} of {strips} strips: {errors}": (
        "Druckerfehler, Abbruch nach {done} von {strips} Streifen: {errors}"
    ),
    "{loaded} mm tape loaded, {needed} mm needed, stopped after {done} of {strips} strips": (
        "{loaded}-mm-Band eingelegt, {needed} mm benötigt, Abbruch nach {done} von {strips} Streifen"
    ),
    "required tape width in mm; prints without asking, but stops if another tape is loaded": (
        "erforderliche Bandbreite in mm; druckt ohne Rückfrage, bricht aber bei anderem Band ab"
    ),
    "full cut after every label; each cut wastes about 20 mm of tape": (
        "voller Schnitt nach jedem Etikett; jeder Schnitt verschwendet etwa 20 mm Band"
    ),
    "show the loaded tape and printer errors, prints nothing": "eingelegtes Band und Druckerfehler anzeigen, druckt nichts",
    """Show the printer status in plain text, prints nothing.

The explanations come from the tables in docs/brother-pt-p900w-status*.md.""": """Zeigt den Druckerstatus im Klartext, druckt nichts.

Die Erklärungen stammen aus den Tabellen in docs/brother-pt-p900w-status*.md.""",
    """examples:
  uv run labels.py status
  uv run labels.py --lang de status
  uv run labels.py status --raw""": """Beispiele:
  uv run labels.py status
  uv run labels.py --lang en status
  uv run labels.py status --raw""",
    "also show the 32 raw reply bytes": "zusätzlich die 32 Rohbytes der Antwort anzeigen",
    "print one label per module size, to compare sizes": "je ein Etikett pro Modulgröße drucken, um Größen zu vergleichen",
    """Print one label per given module size, to compare sizes on one tape.

A dot is 0.07 mm, so 10 dots per module mean 0.71 mm. Sizes without a full quiet zone are refused.""": (
        """Druckt je ein Etikett pro angegebener Modulgröße, um Größen auf einem Band zu vergleichen.

Ein Punkt misst 0,07 mm, 10 Punkte pro Modul sind also 0,71 mm. Größen ohne volle Ruhezone werden abgelehnt."""
    ),
    """example:
  uv run labels.py probe 36 32 24    two labels on 36 mm tape: 2.26 and 1.69 mm""": """Beispiel:
  uv run labels.py probe 36 32 24    zwei Etiketten auf 36-mm-Band: 2,26 und 1,69 mm""",
    "tape width in mm, must be loaded": "Bandbreite in mm, muss eingelegt sein",
    "dots per module, one value per label": "Punkte pro Modul, ein Wert pro Etikett",
    "print a test strip to compare QR and Data Matrix sizes, not for real labels": (
        "Teststreifen zum Vergleich von QR- und Data-Matrix-Größen drucken, nicht für echte Etiketten"
    ),
    """Print the test strip for a tape: several QR and Data Matrix sizes with captions.

The strip always holds the same test IDs from strips/manifest.json, and there is no confirmation.
Only a full cut at the end; marks on the tape edges show where to cut by hand.""": (
        """Druckt den Teststreifen für ein Band: mehrere QR- und Data-Matrix-Größen mit Beschriftung.

Der Streifen enthält immer dieselben Test-IDs aus strips/manifest.json, und es gibt keine Rückfrage.
Nur ein voller Schnitt am Ende; Markierungen an den Bandkanten zeigen, wo von Hand getrennt werden kann."""
    ),
    """example:
  uv run labels.py print-test-strip 24""": """Beispiel:
  uv run labels.py print-test-strip 24""",
    "create missing test strips in strips/, prints nothing": "fehlende Teststreifen in strips/ erzeugen, druckt nichts",
    "Create missing test strips in strips/. Existing strips keep their IDs. Prints nothing.": (
        "Erzeugt fehlende Teststreifen in strips/. Vorhandene Streifen behalten ihre IDs. Druckt nichts."
    ),
    "check the test strip images with the decoder, prints nothing": (
        "Teststreifen-Bilder mit dem Decoder prüfen, druckt nichts"
    ),
    "Decode the test strip images, also rotated and blurred, and report missing codes. Prints nothing.": (
        "Liest die Teststreifen-Bilder, auch gedreht und unscharf, und meldet fehlende Codes. Druckt nichts."
    ),
    # read_photo.py
    """Find label IDs in photos and print them, without saving anything.

Runs a direct pass, then tiled and preprocessed passes. A large photo takes about 40 seconds.
To index a whole folder and sort its photos by part, use sort_photos.py instead.""": (
        """Sucht Etiketten-IDs in Fotos und gibt sie aus, ohne etwas zu speichern.

Läuft erst direkt, dann über Ausschnitte mit Vorverarbeitung. Ein großes Foto dauert etwa 40 Sekunden.
Um einen ganzen Ordner zu erfassen und Fotos nach Bauteil zu sortieren, nutze sort_photos.py."""
    ),
    """example:
  uv run read_photo.py IMG_1505.HEIC IMG_1506.jpg""": """Beispiel:
  uv run read_photo.py IMG_1505.HEIC IMG_1506.jpg""",
    "photo": "foto",
    "HEIC, JPEG, PNG, TIFF or WebP file": "HEIC-, JPEG-, PNG-, TIFF- oder WebP-Datei",
    "{name}: {width}x{height}, {found} IDs, {direct} direct": "{name}: {width}x{height}, {found} IDs, {direct} direkt",
    "{kind} {dots} dots on {tape} mm": "{kind} {dots} Punkte auf {tape} mm",
    "unknown ID": "unbekannte ID",
    "{px} px/module": "{px} px/Modul",
    "size unknown": "Größe unbekannt",
    # sort_photos.py
    """Index a folder of photos by label ID and link them into one folder per part.

Writes index.csv, parts/<id>/ and unmatched/ with symbolic links, and only reads the originals.
A photo with several labels appears in several folders. Photos already in the index are skipped.""": (
        """Erfasst einen Fotoordner nach Etiketten-ID und verknüpft die Fotos in je einen Ordner pro Bauteil.

Schreibt index.csv, parts/<id>/ und unmatched/ mit Verknüpfungen und liest die Originale nur.
Ein Foto mit mehreren Etiketten erscheint in mehreren Ordnern. Bereits erfasste Fotos werden übersprungen."""
    ),
    """example:
  uv run sort_photos.py ~/Pictures/parts
  uv run sort_photos.py ~/Pictures/parts --out ~/Pictures/parts-index --rescan""": """Beispiele:
  uv run sort_photos.py ~/Pictures/parts
  uv run sort_photos.py ~/Pictures/parts --out ~/Pictures/parts-index --rescan""",
    "folder with photos, not searched recursively": "Ordner mit Fotos, Unterordner werden nicht durchsucht",
    "output folder, default <photos>-sorted next to the photo folder": (
        "Ausgabeordner, Standard ist <photos>-sorted neben dem Fotoordner"
    ),
    "scan photos again that are already in the index": "bereits erfasste Fotos erneut auswerten",
    "photos scanned in parallel": "gleichzeitig ausgewertete Fotos",
    "{path} is not a folder": "{path} ist kein Ordner",
    "{photos} photos, {todo} to scan": "{photos} Fotos, {todo} auszuwerten",
    "[{number}/{total}] {name}: FAILED {error}": "[{number}/{total}] {name}: FEHLGESCHLAGEN {error}",
    "[{number}/{total}] {name}: {count} IDs": "[{number}/{total}] {name}: {count} IDs",
    "{parts} parts, {unmatched} photos without ID, {failed} failed, {unknown} IDs not in the print log": (
        "{parts} Bauteile, {unmatched} Fotos ohne ID, {failed} fehlgeschlagen, {unknown} IDs nicht im Druckprotokoll"
    ),
    "output: {path}": "Ausgabe: {path}",
}

# Texts of Python's argparse module, which uses %-style placeholders.
ARGPARSE_DE = {
    "usage: ": "Aufruf: ",
    "options": "Optionen",
    "positional arguments": "Argumente",
    "show this help message and exit": "diese Hilfe anzeigen und beenden",
    "the following arguments are required: %s": "folgende Argumente fehlen: %s",
    "argument %(argument_name)s: %(message)s": "Argument %(argument_name)s: %(message)s",
    "invalid choice: %(value)r (choose from %(choices)s)": "ungültige Auswahl: %(value)r (möglich: %(choices)s)",
    "invalid %(type)s value: %(value)r": "ungültiger %(type)s-Wert: %(value)r",
    "unrecognized arguments: %s": "unbekannte Argumente: %s",
    "ambiguous option: %(option)s could match %(matches)s": "mehrdeutige Option: %(option)s passt zu %(matches)s",
    "expected one argument": "ein Argument erwartet",
    "expected at most one argument": "höchstens ein Argument erwartet",
    "expected at least one argument": "mindestens ein Argument erwartet",
    "expected %s argument": "%s Argument erwartet",
    "expected %s arguments": "%s Argumente erwartet",
    "not allowed with argument %s": "nicht zusammen mit Argument %s erlaubt",
}

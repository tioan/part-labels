# PT-P900W-Statusantwort

[English version](brother-pt-p900w-status.md)

Nachschlagetabellen für die 32 Byte lange Antwort auf die Statusabfrage `ESC i S` (`1B 69 53`). Sie gelten
für PT-P900, PT-P900W und PT-P950NW.

Die Werte stammen aus Brothers
[Raster Command Reference v1.02](https://download.brother.com/welcome/docp100407/cv_ptp900_jpn_raster_102.pdf),
japanische Ausgabe, Seiten 24 bis 33. Die Texte sind unsere eigene Übersetzung, maßgeblich ist das Original.
Beim PT-P910BT weichen die Werte teilweise ab, er ist hier nicht aufgeführt.

## Aufbau der Antwort

| Offset | Feld | Wert |
|---|---|---|
| 0 | Kopfmarke | `0x80` |
| 1 | Größe | `0x20` |
| 2 | Brother-Kennung | `0x42` (`B`) |
| 3 | Serienkennung | `0x30` (`0`) |
| 4 | Modellkennung | siehe [Modellkennung](#modellkennung) |
| 5 | Länderkennung | `0x30` (`0`) |
| 6 | Akkustand | siehe [Akkustand](#akkustand) |
| 7 | Erweiterter Fehler | siehe [Erweiterter Fehler](#erweiterter-fehler) |
| 8 | Fehlerinformation 1 | siehe [Fehlerinformation 1](#fehlerinformation-1) |
| 9 | Fehlerinformation 2 | siehe [Fehlerinformation 2](#fehlerinformation-2) |
| 10 | Medienbreite | siehe [Medienbreite und Medienlänge](#medienbreite-und-medienlänge) |
| 11 | Medienart | siehe [Medienart](#medienart) |
| 12 | Anzahl der Farben | `0x00` |
| 13 | Schriftart | `0x00` |
| 14 | Japanische Schriftart | `0x00` |
| 15 | Modus | mit `ESC i M` gesetzter Wert, sonst `0x00` |
| 16 | Dichte | `0x00` |
| 17 | Medienlänge | siehe [Medienbreite und Medienlänge](#medienbreite-und-medienlänge) |
| 18 | Statusart | siehe [Statusart](#statusart) |
| 19 | Phasenart | siehe [Phase](#phase) |
| 20 | Phasennummer, oberes Byte | siehe [Phase](#phase) |
| 21 | Phasennummer, unteres Byte | siehe [Phase](#phase) |
| 22 | Benachrichtigungsnummer | siehe [Benachrichtigungsnummer](#benachrichtigungsnummer) |
| 23 | Größe der Erweiterung | `0x00` |
| 24 | Bandfarbe | siehe [Bandfarbe](#bandfarbe) |
| 25 | Schriftfarbe | siehe [Schriftfarbe](#schriftfarbe) |
| 26 bis 31 | Unbenutzt | `0x00` |

## Modellkennung

| Wert | Modell |
|---|---|
| `0x6F` (`o`) | PT-P900W |
| `0x70` (`p`) | PT-P950NW |
| `0x71` (`q`) | PT-P900 |

## Akkustand

| Wert | Bedeutung |
|---|---|
| `0x00` | Voll |
| `0x01` | Halb |
| `0x02` | Niedrig |
| `0x03` | Muss geladen werden |
| `0x04` | Netzteil in Betrieb |
| `0xFF` | Unbekannt |

## Erweiterter Fehler

| Wert | Bedeutung |
|---|---|
| `0x10` | Ende des FLe-Bands |
| `0x1D` | Fehler beim Druck in hoher Auflösung oder im Entwurfsmodus |
| `0x1E` | Netzteil ein- oder ausgesteckt |
| `0x21` | Nicht unterstütztes Medium |

## Fehlerinformation 1

Jedes Bit ist ein eigener Merker, mehrere Fehler addieren sich also. `0x05` bedeutet: kein Medium und Messerstau.

| Maske | Bedeutung |
|---|---|
| `0x01` | Kein Medium |
| `0x02` | Medienende |
| `0x04` | Messerstau |
| `0x08` | Akku schwach |
| `0x10` | Bei dieser Modellreihe nicht verwendet |
| `0x20` | Unbenutzt |
| `0x40` | Hochspannungs-Netzteil |
| `0x80` | Unbenutzt |

## Fehlerinformation 2

| Maske | Bedeutung |
|---|---|
| `0x01` | Falsches Medium, bitte tauschen |
| `0x02` | Puffer voll |
| `0x04` | Übertragungsfehler |
| `0x08` | Übertragungspuffer voll |
| `0x10` | Deckel offen |
| `0x20` | Überhitzung |
| `0x40` | Fehler bei der Erkennung des Bandanfangs |
| `0x80` | Systemfehler |

## Medienbreite und Medienlänge

Breite und Länge sind in mm angegeben. Die Länge ist außer bei FLe-Etiketten `0x00`.

| Medium | Breite | Länge |
|---|---|---|
| Kein Band | `0x00` | `0x00` |
| TZe 3,5 mm | `0x04` | `0x00` |
| TZe 6 mm | `0x06` | `0x00` |
| TZe 9 mm | `0x09` | `0x00` |
| TZe 12 mm | `0x0C` | `0x00` |
| TZe 18 mm | `0x12` | `0x00` |
| TZe 24 mm | `0x18` | `0x00` |
| TZe 36 mm | `0x24` | `0x00` |
| Schrumpfschlauch 5,8 mm | `0x06` | `0x00` |
| Schrumpfschlauch 8,8 mm | `0x09` | `0x00` |
| Schrumpfschlauch 11,7 mm | `0x0C` | `0x00` |
| Schrumpfschlauch 17,7 mm | `0x12` | `0x00` |
| Schrumpfschlauch 23,6 mm | `0x18` | `0x00` |
| FLe-Etikett 21 x 45 mm | `0x15` | `0x2D` |

## Medienart

| Wert | Bedeutung |
|---|---|
| `0x00` | Kein Band |
| `0x01` | Laminiertes Band |
| `0x03` | Nicht laminiertes Band |
| `0x04` | Stoffband |
| `0x11` | Schrumpfschlauch, 2:1 |
| `0x13` | FLe-Band |
| `0x14` | Flexible-ID-Band |
| `0x15` | Satinband |
| `0x17` | Schrumpfschlauch, 3:1 |
| `0xFF` | Nicht unterstütztes Band |

## Statusart

| Wert | Bedeutung |
|---|---|
| `0x00` | Antwort auf eine Statusabfrage |
| `0x01` | Druck beendet |
| `0x02` | Fehler aufgetreten |
| `0x03` | Schnittstellenmodus beendet (unbenutzt) |
| `0x04` | Ausschalten |
| `0x05` | Benachrichtigung |
| `0x06` | Phasenwechsel |
| `0x07` bis `0x20` | Unbenutzt |
| `0x21` bis `0xFF` | Darf nicht verwendet werden |

Tritt beim Drucken ein Fehler auf, sendet der Drucker von sich aus einen Fehlerstatus.

## Phase

Ohne Phasennummer bleiben beide Bytes der Phasennummer `0x00`.

| Phasenart | Bedeutung |
|---|---|
| `0x00` | Bearbeiten, empfangsbereit |
| `0x01` | Normaler Druck |

| Phasenart | Phasennummer | Bedeutung |
|---|---|---|
| Bearbeiten | 0 (`0x00 0x00`) | Empfangsbereit |
| Bearbeiten | 1 (`0x00 0x01`) | Bandvorschub |
| Normaler Druck | 0 (`0x00 0x00`) | Druck läuft |
| Normaler Druck | 10 (`0x00 0x0A`) | Unbenutzt |
| Normaler Druck | 20 (`0x00 0x14`) | Deckel beim Empfang offen |
| Normaler Druck | 25 (`0x00 0x19`) | Unbenutzt |

## Benachrichtigungsnummer

| Wert | Bedeutung |
|---|---|
| `0x00` | Ungültig |
| `0x01` | Deckel geöffnet |
| `0x02` | Deckel geschlossen |
| `0x03` | Abkühlen begonnen |
| `0x04` | Abkühlen beendet |

## Bandfarbe

| Wert | Farbe | Hinweis |
|---|---|---|
| `0x01` | Weiß | |
| `0x02` | Sonstige | |
| `0x03` | Transparent | |
| `0x04` | Rot | |
| `0x05` | Blau | |
| `0x06` | Gelb | |
| `0x07` | Grün | |
| `0x08` | Schwarz | |
| `0x09` | Transparent | weiße Schrift |
| `0x20` | Weiß, matt | |
| `0x21` | Transparent, matt | |
| `0x22` | Silber, matt | |
| `0x23` | Gold, satiniert | der japanische Name in der Quelle sagt „Gold, matt“ |
| `0x24` | Silber, satiniert | |
| `0x30` | Blau (D) | TZe-535 (12 mm), TZe-545 (18 mm), TZe-555 (24 mm) |
| `0x31` | Rot (D) | TZe-435 (12 mm) |
| `0x40` | Neonorange | |
| `0x41` | Neongelb | |
| `0x50` | Beerenrosa (S) | TZe-MQP35 |
| `0x51` | Hellgrau (S) | TZe-MQL35 |
| `0x52` | Limettengrün (S) | TZe-MQG35 |
| `0x60` | Gelb (F) | |
| `0x61` | Rosa (F) | |
| `0x62` | Blau (F) | |
| `0x70` | Weiß, Schrumpfschlauch | |
| `0x90` | Weiß, Flexible-ID | |
| `0x91` | Gelb, Flexible-ID | |
| `0xF0` | Reinigung | |
| `0xF1` | Schablone | |
| `0xFF` | Nicht unterstützt | |

## Schriftfarbe

| Wert | Farbe |
|---|---|
| `0x01` | Weiß |
| `0x02` | Sonstige |
| `0x04` | Rot |
| `0x05` | Blau |
| `0x08` | Schwarz |
| `0x0A` | Gold |
| `0x62` | Blau (F) |
| `0xF0` | Reinigung |
| `0xF1` | Schablone |
| `0xFF` | Nicht unterstützt |

## Beispiel

Antwort eines PT-P900W mit gelbem 36-mm-Band, am Netzteil und ohne Fehler:

```text
80 20 42 30 6f 30 04 00 00 00 24 01 00 00 00 00 00 00 00 00 00 00 00 00 06 08 00 00 00 00 00 00
```

| Offset | Wert | Bedeutung |
|---|---|---|
| 4 | `0x6F` | PT-P900W |
| 6 | `0x04` | Netzteil in Betrieb |
| 8, 9 | `0x00 0x00` | Keine Fehler |
| 10 | `0x24` | 36 mm |
| 11 | `0x01` | Laminiertes Band |
| 18 | `0x00` | Antwort auf eine Statusabfrage |
| 19 | `0x00` | Empfangsbereit |
| 24 | `0x06` | Gelbes Band |
| 25 | `0x08` | Schwarze Schrift |

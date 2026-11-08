# PT-P900W status reply

[Deutsche Fassung](brother-pt-p900w-status.de.md)

Lookup tables for the 32-byte reply to the status request `ESC i S` (`1B 69 53`). They apply to the
PT-P900, PT-P900W and PT-P950NW.

The values come from Brother's
[Raster Command Reference v1.02](https://download.brother.com/welcome/docp100407/cv_ptp900_jpn_raster_102.pdf),
Japanese edition, pages 24 to 33. The wording is our own translation, so the original is authoritative.
Values for the PT-P910BT differ in places and are not listed here.

## Reply layout

| Offset | Field | Value |
|---|---|---|
| 0 | Head mark | `0x80` |
| 1 | Size | `0x20` |
| 2 | Brother code | `0x42` (`B`) |
| 3 | Series code | `0x30` (`0`) |
| 4 | Model code | see [Model code](#model-code) |
| 5 | Country code | `0x30` (`0`) |
| 6 | Battery level | see [Battery level](#battery-level) |
| 7 | Extended error | see [Extended error](#extended-error) |
| 8 | Error information 1 | see [Error information 1](#error-information-1) |
| 9 | Error information 2 | see [Error information 2](#error-information-2) |
| 10 | Media width | see [Media width and length](#media-width-and-length) |
| 11 | Media type | see [Media type](#media-type) |
| 12 | Number of colors | `0x00` |
| 13 | Font | `0x00` |
| 14 | Japanese font | `0x00` |
| 15 | Mode | value set with `ESC i M`, otherwise `0x00` |
| 16 | Density | `0x00` |
| 17 | Media length | see [Media width and length](#media-width-and-length) |
| 18 | Status type | see [Status type](#status-type) |
| 19 | Phase type | see [Phase](#phase) |
| 20 | Phase number, high byte | see [Phase](#phase) |
| 21 | Phase number, low byte | see [Phase](#phase) |
| 22 | Notification number | see [Notification number](#notification-number) |
| 23 | Extension size | `0x00` |
| 24 | Tape color | see [Tape color](#tape-color) |
| 25 | Text color | see [Text color](#text-color) |
| 26 to 31 | Unused | `0x00` |

## Model code

| Value | Model |
|---|---|
| `0x6F` (`o`) | PT-P900W |
| `0x70` (`p`) | PT-P950NW |
| `0x71` (`q`) | PT-P900 |

## Battery level

| Value | Meaning |
|---|---|
| `0x00` | Full |
| `0x01` | Half |
| `0x02` | Low |
| `0x03` | Needs charging |
| `0x04` | AC adapter in use |
| `0xFF` | Unknown |

## Extended error

| Value | Meaning |
|---|---|
| `0x10` | End of FLe tape |
| `0x1D` | High resolution or draft printing error |
| `0x1E` | AC adapter plugged or unplugged |
| `0x21` | Unsupported media |

## Error information 1

Each bit is a flag, so several errors add up. `0x05` means no media and a cutter jam.

| Mask | Meaning |
|---|---|
| `0x01` | No media |
| `0x02` | End of media |
| `0x04` | Cutter jam |
| `0x08` | Low battery |
| `0x10` | Not used on this model family |
| `0x20` | Unused |
| `0x40` | High-voltage adapter |
| `0x80` | Unused |

## Error information 2

| Mask | Meaning |
|---|---|
| `0x01` | Wrong media, replace it |
| `0x02` | Buffer full |
| `0x04` | Communication error |
| `0x08` | Communication buffer full |
| `0x10` | Cover open |
| `0x20` | Overheating |
| `0x40` | Leading edge detection error |
| `0x80` | System error |

## Media width and length

Width and length are given in mm. The length is `0x00` except for FLe labels.

| Media | Width | Length |
|---|---|---|
| No tape | `0x00` | `0x00` |
| TZe 3.5 mm | `0x04` | `0x00` |
| TZe 6 mm | `0x06` | `0x00` |
| TZe 9 mm | `0x09` | `0x00` |
| TZe 12 mm | `0x0C` | `0x00` |
| TZe 18 mm | `0x12` | `0x00` |
| TZe 24 mm | `0x18` | `0x00` |
| TZe 36 mm | `0x24` | `0x00` |
| Heat-shrink tube 5.8 mm | `0x06` | `0x00` |
| Heat-shrink tube 8.8 mm | `0x09` | `0x00` |
| Heat-shrink tube 11.7 mm | `0x0C` | `0x00` |
| Heat-shrink tube 17.7 mm | `0x12` | `0x00` |
| Heat-shrink tube 23.6 mm | `0x18` | `0x00` |
| FLe label 21 x 45 mm | `0x15` | `0x2D` |

## Media type

| Value | Meaning |
|---|---|
| `0x00` | No tape |
| `0x01` | Laminated tape |
| `0x03` | Non-laminated tape |
| `0x04` | Fabric tape |
| `0x11` | Heat-shrink tube, 2:1 |
| `0x13` | FLe tape |
| `0x14` | Flexible ID tape |
| `0x15` | Satin tape |
| `0x17` | Heat-shrink tube, 3:1 |
| `0xFF` | Unsupported tape |

## Status type

| Value | Meaning |
|---|---|
| `0x00` | Reply to a status request |
| `0x01` | Printing finished |
| `0x02` | Error occurred |
| `0x03` | Interface mode finished (unused) |
| `0x04` | Power off |
| `0x05` | Notification |
| `0x06` | Phase change |
| `0x07` to `0x20` | Unused |
| `0x21` to `0xFF` | Must not be used |

The printer sends an error status by itself when an error occurs during printing.

## Phase

Without a phase number, both phase number bytes stay `0x00`.

| Phase type | Meaning |
|---|---|
| `0x00` | Editing, ready to receive |
| `0x01` | Normal printing |

| Phase type | Phase number | Meaning |
|---|---|---|
| Editing | 0 (`0x00 0x00`) | Ready to receive |
| Editing | 1 (`0x00 0x01`) | Feeding |
| Normal printing | 0 (`0x00 0x00`) | Printing |
| Normal printing | 10 (`0x00 0x0A`) | Unused |
| Normal printing | 20 (`0x00 0x14`) | Cover open while receiving |
| Normal printing | 25 (`0x00 0x19`) | Unused |

## Notification number

| Value | Meaning |
|---|---|
| `0x00` | Invalid |
| `0x01` | Cover opened |
| `0x02` | Cover closed |
| `0x03` | Cooling started |
| `0x04` | Cooling finished |

## Tape color

| Value | Color | Note |
|---|---|---|
| `0x01` | White | |
| `0x02` | Other | |
| `0x03` | Clear | |
| `0x04` | Red | |
| `0x05` | Blue | |
| `0x06` | Yellow | |
| `0x07` | Green | |
| `0x08` | Black | |
| `0x09` | Clear | white text |
| `0x20` | Matte white | |
| `0x21` | Matte clear | |
| `0x22` | Matte silver | |
| `0x23` | Satin gold | the Japanese name in the source says matte gold |
| `0x24` | Satin silver | |
| `0x30` | Blue (D) | TZe-535 (12 mm), TZe-545 (18 mm), TZe-555 (24 mm) |
| `0x31` | Red (D) | TZe-435 (12 mm) |
| `0x40` | Fluorescent orange | |
| `0x41` | Fluorescent yellow | |
| `0x50` | Berry pink (S) | TZe-MQP35 |
| `0x51` | Light gray (S) | TZe-MQL35 |
| `0x52` | Lime green (S) | TZe-MQG35 |
| `0x60` | Yellow (F) | |
| `0x61` | Pink (F) | |
| `0x62` | Blue (F) | |
| `0x70` | White, heat-shrink tube | |
| `0x90` | White, flexible ID | |
| `0x91` | Yellow, flexible ID | |
| `0xF0` | Cleaning | |
| `0xF1` | Stencil | |
| `0xFF` | Unsupported | |

## Text color

| Value | Color |
|---|---|
| `0x01` | White |
| `0x02` | Other |
| `0x04` | Red |
| `0x05` | Blue |
| `0x08` | Black |
| `0x0A` | Gold |
| `0x62` | Blue (F) |
| `0xF0` | Cleaning |
| `0xF1` | Stencil |
| `0xFF` | Unsupported |

## Example

A reply read from a PT-P900W with yellow 36 mm tape, on AC power and without errors:

```text
80 20 42 30 6f 30 04 00 00 00 24 01 00 00 00 00 00 00 00 00 00 00 00 00 06 08 00 00 00 00 00 00
```

| Offset | Value | Meaning |
|---|---|---|
| 4 | `0x6F` | PT-P900W |
| 6 | `0x04` | AC adapter in use |
| 8, 9 | `0x00 0x00` | No errors |
| 10 | `0x24` | 36 mm |
| 11 | `0x01` | Laminated tape |
| 18 | `0x00` | Reply to a status request |
| 19 | `0x00` | Ready to receive |
| 24 | `0x06` | Yellow tape |
| 25 | `0x08` | Black text |

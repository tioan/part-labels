# part-labels

Small ID labels for identifying parts in photos, printed on a Brother PT-P900W over USB.

## Label standard

| Use | Tape | Code | Module | Code size |
|---|---|---|---|---|
| Default | 12 mm | Data Matrix 14x14 | 0.71 mm (10 dots) | 9.9 mm |
| Small parts | 9 mm | Data Matrix 14x14 | 0.49 mm (7 dots) | 6.9 mm |
| Last resort, good light only | 6 mm | Data Matrix 14x14 | 0.28 mm (4 dots) | 4.0 mm |

- IDs are 10 random Crockford Base32 characters. There is no registry; `strips/issued.jsonl`
  only logs what was sent to the printer, including aborted jobs.
- A series gets half cuts between labels and one full cut at the end. Each full cut wastes
  about 20 mm of tape, because the printer ejects at least 27 mm per cut.
- Avoid direct flash on glossy tape where possible.

18 mm is defined in `labels.py` (1.06 mm modules), but standard labels on it are untested.

## Test results

All photos were decoded with zxing-cpp. Full results were only collected for one device
and yellow tape, so other surfaces may behave differently.

- 12 mm, 0.71 mm: 4 of 4 read directly, with and without flash, at about 11 px per module.
- 6 mm, 0.28 mm: 5 of 5 direct in good light. In the dark with flash, 1 direct and 3 of 4 with
  preprocessing.
- QR codes were tested too. Same-size modules can read as well as Data Matrix, but Data Matrix
  needs fewer modules and so gets about twice the module size on the same tape.

## Usage

```bash
nix-shell --run 'python3 -I labels.py status'
```

```bash
nix-shell --run 'python3 -I labels.py labels 20'
```

```bash
nix-shell --run 'python3 -I labels.py labels 20 --tape 9'
```

```bash
nix-shell --run 'python3 -I read_photo.py photo1.jpg photo2.jpg'
```

Printing stops if the loaded tape width does not match. `labels.py generate`, `verify` and
`print` handle the comparison test strips in `strips/`.

## Sources

- Brother Raster Command Reference for PT-P900/P900W/P950NW/P910BT, v1.02:
  https://download.brother.com/welcome/docp100407/cv_ptp900_jpn_raster_102.pdf
- ptouch-print by Dominic Radermacher (GPL-3.0), raster line bit layout, commit 3e026ef:
  https://git.familie-radermacher.ch/linux/ptouch-print.git

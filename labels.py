#!/usr/bin/env python3
"""Generate and print dot-exact part label test strips on a Brother PT-P900W.

Raster commands and the pin table come from Brother's "Raster Command Reference"
for PT-P900/P900W/P950NW/P910BT, v1.02:
https://download.brother.com/welcome/docp100407/cv_ptp900_jpn_raster_102.pdf

The raster line bit layout follows ptouch-print by Dominic Radermacher (GPL-3.0),
src/ptouch-print.c, rasterline_setpixel(), commit 3e026ef:
https://git.familie-radermacher.ch/linux/ptouch-print.git
ptouch-print itself does not list the PT-P900W and documents that printers above
180 dpi are not supported correctly, so it is not used here.
"""
import argparse
import json
import secrets
import time
from pathlib import Path

DPI = 360
HEAD_PINS = 560
RASTER_BYTES = HEAD_PINS // 8
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford Base32
ID_LENGTH = 10
USB_VENDOR, USB_PRODUCT = 0x04F9, 0x2085

# TZe tape: mm -> left margin pins, printable pins, physical width in dots.
TAPES = {
    6: (240, 64, 84),
    9: (219, 106, 128),
    12: (197, 150, 170),
    18: (155, 234, 256),
    24: (112, 320, 340),
    36: (45, 454, 512),
}

# kind -> zint symbol settings, modules per side, required quiet zone in modules.
# QR: version 1 with error correction H. Data Matrix: square 14x14.
KINDS = {
    "QR": (("QRCODE", 4, 1), 21, 4),
    "DM": (("DATAMATRIX", -1, 3), 14, 1),
}

# Test grid: tape mm -> (kind, dots per module). Every entry keeps the full quiet
# zone on the physical tape, except QR with 3 dots on 6 mm (3.5 of 4 modules) and
# QR with 6 dots on 12 mm (3.7 of 4 modules).
GRID = {
    6: [("QR", 3), ("DM", 3), ("DM", 4)],
    9: [("QR", 3), ("QR", 4), ("DM", 4), ("DM", 5), ("DM", 7)],
    12: [("QR", 4), ("QR", 5), ("QR", 6), ("DM", 5), ("DM", 7), ("DM", 10)],
    18: [("QR", 6), ("QR", 8), ("DM", 8), ("DM", 15)],
}

# Label standard per tape: the largest Data Matrix module with a full quiet zone.
STANDARD = {
    6: ("DM", 4),
    9: ("DM", 7),
    12: ("DM", 10),
    18: ("DM", 15),
    24: ("DM", 21),
    36: ("DM", 32),
}
MIN_RASTER_LINES = 57  # 4 mm, the minimum label length for TZe tape
MIN_MARGIN_DOTS = 14  # 1 mm, the minimum feed margin

STRIPS = Path(__file__).parent / "strips"


def module_mm(dots: int) -> float:
    return dots * 25.4 / DPI


def new_id() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(ID_LENGTH))


def code_matrix(kind: str, value: str):
    """Return the code as a modules x modules 8-bit image, 0 = black."""
    import zint
    from PIL import Image

    (symbology, option_1, option_2), modules, _ = KINDS[kind]
    symbol = zint.Symbol()
    symbol.symbology = getattr(zint.Symbology, symbology)
    symbol.option_1 = option_1
    symbol.option_2 = option_2
    symbol.encode(value)
    symbol.buffer()
    if (symbol.rows, symbol.width) != (modules, modules):
        raise ValueError(f"{value} does not fit a {modules}x{modules} {kind} code")
    bitmap = symbol.bitmap
    size = bitmap.shape[1], bitmap.shape[0]
    return Image.frombytes("RGB", size, bitmap.tobytes()).convert("L").resize((modules, modules), Image.NEAREST)


def build_strip(tape: int):
    """Return (1-bit strip image with height = printable pins, manifest entries)."""
    from PIL import Image, ImageDraw, ImageFont

    _, pins, tape_dots = TAPES[tape]
    font = ImageFont.load_default(size=26)
    cells, manifest = [], []
    for kind, dots in GRID[tape]:
        _, modules, quiet = KINDS[kind]
        value = new_id()
        code_dots = modules * dots
        if code_dots > pins:
            raise ValueError(f"{kind} with {dots} dots does not fit {pins} pins")
        margin = (tape_dots - code_dots) / 2 / dots
        size_mm = module_mm(dots)
        label = [kind, f"{size_mm:.2f}"]
        text_width = max(int(font.getlength(line)) for line in label) + 2
        quiet_dots = quiet * dots
        # Keep the caption clear of the code so it cannot disturb detection.
        text_gap = max(quiet_dots, 24)
        width = quiet_dots + code_dots + text_gap + text_width + 16
        cell = Image.new("L", (width, pins), 255)
        code = code_matrix(kind, value).resize((code_dots, code_dots), Image.NEAREST)
        cell.paste(code, (quiet_dots, (pins - code_dots) // 2))
        draw = ImageDraw.Draw(cell)
        x = quiet_dots + code_dots + text_gap
        draw.text((x, pins // 2 - 30), label[0], fill=0, font=font)
        draw.text((x, pins // 2 + 2), label[1], fill=0, font=font)
        # Cut marks on the tape edges, outside every quiet zone.
        draw.rectangle((width - 3, 0, width - 1, 7), fill=0)
        draw.rectangle((width - 3, pins - 8, width - 1, pins - 1), fill=0)
        cells.append(cell)
        manifest.append(
            {
                "id": value,
                "kind": kind,
                "tape_mm": tape,
                "dots_per_module": dots,
                "module_mm": round(size_mm, 3),
                "code_mm": round(code_dots * 25.4 / DPI, 2),
                "quiet_modules_across_tape": round(margin, 1),
            }
        )
    strip = Image.new("L", (sum(c.width for c in cells), pins), 255)
    x = 0
    for cell in cells:
        strip.paste(cell, (x, 0))
        x += cell.width
    return strip.point(lambda p: 255 if p >= 128 else 0).convert("1"), manifest


def raster_lines(strip, tape: int) -> bytes:
    """Convert the strip to G commands; row 0 is the highest pin of the print area."""
    left, pins, _ = TAPES[tape]
    if strip.height != pins:
        raise ValueError(f"strip height {strip.height} does not match {pins} pins on {tape} mm tape")
    pixels = strip.load()
    out = bytearray()
    for x in range(strip.width):
        line = bytearray(RASTER_BYTES)
        for y in range(pins):
            if pixels[x, pins - 1 - y] == 0:
                pin = left + y
                line[RASTER_BYTES - 1 - pin // 8] |= 1 << (pin % 8)
        out += b"G" + RASTER_BYTES.to_bytes(2, "little") + line
    return bytes(out)


def print_job(strip, tape: int) -> bytes:
    lines = strip.width
    return b"".join(
        [
            b"\x00" * 200,  # invalidate
            b"\x1b@",  # initialize
            b"\x1bia\x01",  # raster mode
            # Print info: media type, width and recovery are validated by the printer.
            b"\x1biz\x86\x00" + bytes([tape, 0]) + lines.to_bytes(4, "little") + b"\x02\x00",
            b"\x1biM\x40",  # auto cut on, no mirroring
            b"\x1biA\x01",  # cut after each label
            b"\x1biK\x08",  # no chain printing, no half cut, normal resolution
            b"\x1bid\x0e\x00",  # 14 dot (1 mm) margin, the documented minimum
            b"M\x00",  # uncompressed
            raster_lines(strip, tape),
            b"\x1a",  # print and feed
        ]
    )


def label_image(tape: int, value: str, dots: int):
    """Return a code-only Data Matrix label; the 1 mm cut margin counts toward the quiet zone."""
    from PIL import Image

    kind = "DM"
    _, pins, tape_dots = TAPES[tape]
    _, modules, quiet = KINDS[kind]
    code_dots = modules * dots
    if code_dots > pins or code_dots + 2 * quiet * dots > tape_dots:
        raise SystemExit(f"{dots} dots per module do not fit {tape} mm tape with a full quiet zone")
    # Above 14 dots per module the 1 mm cut margin alone is narrower than the quiet zone.
    quiet_padding = max(quiet * dots - MIN_MARGIN_DOTS, 0)
    width = max(code_dots + 2 * quiet_padding, MIN_RASTER_LINES)
    label = Image.new("L", (width, pins), 255)
    code = code_matrix(kind, value).resize((code_dots, code_dots), Image.NEAREST)
    label.paste(code, ((width - code_dots) // 2, (pins - code_dots) // 2))
    return label.point(lambda p: 255 if p >= 128 else 0).convert("1")


def label_page(label, tape: int, index: int, total: int, half_cut: bool) -> bytes:
    """Build the control codes and raster data of one page, as the reference requires per page."""
    page_type = 2 if index == total - 1 else (0 if index == 0 else 1)
    return b"".join(
        [
            b"\x1bia\x01",  # raster mode
            b"\x1biz\x86\x00" + bytes([tape, 0]) + label.width.to_bytes(4, "little") + bytes([page_type, 0]),
            # Half cut mode: auto cut only on the last page, so only the series end gets a full cut.
            # An auto cut count on every page cut before the last label in testing.
            b"\x1biM" + bytes([0x40 if not half_cut or index == total - 1 else 0x00]),
            b"\x1biA\x01",
            b"\x1biK" + bytes([0x0C if half_cut else 0x08]),  # no chain printing, optional half cut
            b"\x1bid" + MIN_MARGIN_DOTS.to_bytes(2, "little"),
            b"M\x00",  # uncompressed
            raster_lines(label, tape),
            b"\x1a" if index == total - 1 else b"\x0c",  # print, the last page also feeds
        ]
    )


class Printer:
    def __enter__(self):
        import libusb_package
        import usb.core
        import usb.util

        self.usb_core, self.usb_util = usb.core, usb.util
        # libusb-package bundles libusb, so no system library is needed.
        backend = libusb_package.get_libusb1_backend()
        self.dev = usb.core.find(idVendor=USB_VENDOR, idProduct=USB_PRODUCT, backend=backend)
        if self.dev is None:
            raise SystemExit("PT-P900W not found on USB")
        self.intf = self.dev.get_active_configuration()[(0, 0)]
        usb.util.claim_interface(self.dev, self.intf)
        direction = usb.util.endpoint_direction
        self.ep_out = usb.util.find_descriptor(
            self.intf, custom_match=lambda e: direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )
        self.ep_in = usb.util.find_descriptor(
            self.intf, custom_match=lambda e: direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        )
        return self

    def __exit__(self, *_):
        self.usb_util.release_interface(self.dev, self.intf)
        self.usb_util.dispose_resources(self.dev)

    def read_status(self, timeout: float = 5.0) -> bytes | None:
        data = b""
        deadline = time.time() + timeout
        while len(data) < 32 and time.time() < deadline:
            try:
                data += bytes(self.ep_in.read(32, timeout=500))
            except self.usb_core.USBTimeoutError:
                pass
        return data[:32] if len(data) >= 32 else None

    def status(self) -> bytes:
        # A finished job can leave notifications queued, e.g. with the previous tape width.
        while self.read_status(timeout=0.6) is not None:
            pass
        self.ep_out.write(b"\x00" * 200 + b"\x1b@" + b"\x1biS")
        deadline = time.time() + 5
        while time.time() < deadline:
            status = self.read_status(timeout=1)
            # Status type 0x00 marks the reply to a status request.
            if status is not None and status[18] == 0x00:
                return status
        raise SystemExit("no status reply from printer")

    def send(self, data: bytes) -> None:
        for start in range(0, len(data), 16384):
            self.ep_out.write(data[start : start + 16384], timeout=30000)


def describe(status: bytes) -> str:
    return (
        f"width={status[10]} mm, media=0x{status[11]:02x}, tape color=0x{status[24]:02x}, "
        f"text color=0x{status[25]:02x}, errors=0x{status[8]:02x}/0x{status[9]:02x}, "
        f"status type=0x{status[18]:02x}, phase=0x{status[19]:02x}"
    )


def cmd_generate(_args) -> None:
    STRIPS.mkdir(exist_ok=True)
    manifest_path = STRIPS / "manifest.json"
    # Existing strips keep their IDs, because they may already be printed and photographed.
    all_entries = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    existing = {e["tape_mm"] for e in all_entries}
    for tape in GRID:
        if tape in existing:
            print(f"{tape} mm: kept")
            continue
        strip, manifest = build_strip(tape)
        strip.save(STRIPS / f"strip-{tape}mm.png", dpi=(DPI, DPI))
        all_entries += manifest
        print(f"{tape} mm: {len(manifest)} codes, length {strip.width * 25.4 / DPI:.0f} mm")
    manifest_path.write_text(json.dumps(all_entries, indent=2) + "\n")


def cmd_verify(_args) -> None:
    import zxingcpp
    from PIL import Image, ImageFilter

    entries = json.loads((STRIPS / "manifest.json").read_text())
    failed = 0
    for tape in GRID:
        expected = {e["id"] for e in entries if e["tape_mm"] == tape}
        # Add the white tape edges, since the strip only covers the printable pins.
        strip = Image.open(STRIPS / f"strip-{tape}mm.png").convert("L")
        canvas = Image.new("L", (strip.width + 80, TAPES[tape][2] + 80), 255)
        canvas.paste(strip, (40, 40 + (TAPES[tape][2] - strip.height) // 2))
        variants = {
            "1:1": canvas,
            "rotated+blur": canvas.rotate(5, resample=Image.BICUBIC, fillcolor=255, expand=True).filter(
                ImageFilter.GaussianBlur(1.0)
            ),
        }
        for name, img in variants.items():
            found = {r.text for r in zxingcpp.read_barcodes(img)}
            missing = expected - found
            failed += len(missing)
            print(f"{tape} mm {name}: {len(expected & found)}/{len(expected)} found", sorted(missing) or "")
    raise SystemExit(1 if failed else 0)


def cmd_status(_args) -> None:
    with Printer() as printer:
        print(describe(printer.status()))


def cmd_print(args) -> None:
    from PIL import Image

    tape = args.tape
    strip = Image.open(STRIPS / f"strip-{tape}mm.png").convert("1")
    with Printer() as printer:
        status = printer.status()
        print("before:", describe(status))
        if status[8] or status[9]:
            raise SystemExit("printer reports an error, nothing printed")
        if status[10] != tape:
            raise SystemExit(f"{status[10]} mm tape loaded, {tape} mm needed, nothing printed")
        printer.send(print_job(strip, tape))
        deadline = time.time() + 120
        while time.time() < deadline:
            reply = printer.read_status(timeout=2)
            if reply is None:
                continue
            print("printer:", describe(reply))
            if reply[18] == 0x02:
                raise SystemExit("printer reported an error during printing")
            if reply[18] == 0x01:
                print("print complete")
                return
        raise SystemExit("no completion status within 120 s, check the printer")


def confirm_tape(tape: int, kind: str, dots: int, count: int) -> None:
    """Ask before printing, since an auto-detected tape may be a leftover cassette."""
    _, modules, _ = KINDS[kind]
    code_mm = modules * dots * 25.4 / DPI
    print(f"Detected {tape} mm tape: {count} x {kind}, module {module_mm(dots):.2f} mm, code {code_mm:.1f} mm")
    try:
        answer = input("Is this the tape you want? [Y/n] ").strip().lower()
    except EOFError:
        raise SystemExit("no answer available, nothing printed") from None
    if answer not in ("", "y", "yes"):
        raise SystemExit("cancelled, nothing printed")


def cmd_labels(args) -> None:
    """Print a series of cut labels; IDs are logged before anything is sent."""
    with Printer() as printer:
        status = printer.status()
        print("before:", describe(status))
        if status[8] or status[9]:
            raise SystemExit("printer reports an error, nothing printed")
        tape = status[10]
        if tape not in STANDARD:
            raise SystemExit(f"no standard label defined for {tape} mm tape")
        kind, dots = STANDARD[tape]
        if args.tape is None:
            confirm_tape(tape, kind, dots, args.count)
        elif args.tape != tape:
            raise SystemExit(f"{tape} mm tape loaded, {args.tape} mm requested, nothing printed")
        # Half cuts save tape, since every full cut costs about 20 mm of blank tape.
        half_cut = args.count > 1 and not args.full_cut
        print_series(printer, tape, [dots] * args.count, half_cut)


def print_series(printer, tape: int, dots_per_label: list[int], half_cut: bool) -> None:
    """Log the IDs, then print one label per entry with the given dots per module."""
    kind = "DM"
    ids = [new_id() for _ in dots_per_label]
    STRIPS.mkdir(exist_ok=True)
    with (STRIPS / "issued.jsonl").open("a") as log:
        for value, dots in zip(ids, dots_per_label):
            log.write(json.dumps({"id": value, "kind": kind, "tape_mm": tape, "dots_per_module": dots}) + "\n")
    # The printer reports no completion for a page ended by FF, so the job goes out in one piece.
    pages = [
        label_page(label_image(tape, value, dots), tape, i, len(ids), half_cut)
        for i, (value, dots) in enumerate(zip(ids, dots_per_label))
    ]
    printer.send(b"\x00" * 200 + b"\x1b@" + b"".join(pages))
    deadline = time.time() + 60 + 15 * len(ids)
    completed = 0
    while time.time() < deadline:
        reply = printer.read_status(timeout=8 if completed else 2)
        if reply is None:
            if completed:
                break
            continue
        if reply[18] == 0x02:
            raise SystemExit(f"printer error: {describe(reply)}")
        if reply[18] == 0x01:
            completed += 1
    print(f"{completed} completion reports for {len(ids)} labels")
    if not completed:
        raise SystemExit("no completion status, check the printer")
    for value, dots in zip(ids, dots_per_label):
        print(f"issued: {value} ({module_mm(dots):.2f} mm module)")


def cmd_probe(args) -> None:
    """Print one half-cut Data Matrix label per given module size on the required tape."""
    with Printer() as printer:
        status = printer.status()
        print("before:", describe(status))
        if status[8] or status[9]:
            raise SystemExit("printer reports an error, nothing printed")
        if status[10] != args.tape:
            raise SystemExit(f"{status[10]} mm tape loaded, {args.tape} mm requested, nothing printed")
        print_series(printer, args.tape, args.dots, len(args.dots) > 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("generate").set_defaults(func=cmd_generate)
    commands.add_parser("verify").set_defaults(func=cmd_verify)
    commands.add_parser("status").set_defaults(func=cmd_status)
    print_parser = commands.add_parser("print")
    print_parser.add_argument("tape", type=int, choices=sorted(GRID))
    print_parser.set_defaults(func=cmd_print)
    labels_parser = commands.add_parser("labels")
    labels_parser.add_argument("count", type=int)
    labels_parser.add_argument(
        "--tape", type=int, choices=sorted(STANDARD), help="required tape width; without it, confirm the detected tape"
    )
    labels_parser.add_argument("--full-cut", action="store_true", help="full cut after every label instead of half cuts")
    labels_parser.set_defaults(func=cmd_labels)
    probe_parser = commands.add_parser("probe", help="print one label per module size")
    probe_parser.add_argument("tape", type=int, choices=sorted(STANDARD))
    probe_parser.add_argument("dots", type=int, nargs="+", help="dots per module, one value per label")
    probe_parser.set_defaults(func=cmd_probe)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

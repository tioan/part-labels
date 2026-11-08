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
import re
import secrets
import time
from pathlib import Path

import i18n
from cli import HelpParser, add_language_option, positive_int
from i18n import number, tr
from printer_status import StatusLookup

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
    24: [("QR", 9), ("QR", 11), ("DM", 15), ("DM", 21)],
    36: [("QR", 14), ("QR", 17), ("DM", 24), ("DM", 32)],
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
MIN_EJECT_MM = 27  # The shortest piece of tape the printer can cut, from the raster reference
LEADER_MM = 22  # Blank tape before the first label of a job, measured on a photo of 6 mm tape
PRINT_WRITE_TIMEOUT_MS = 30000
STATUS_WRITE_TIMEOUT_MS = 5000
START_TIMEOUT_S = 15

# Both languages accept both answers, so a habit from the other language cannot cancel a job.
YES = ("", "y", "yes", "j", "ja")

STRIPS = Path(__file__).parent / "strips"
LOOKUP = StatusLookup()


def label_count(text: str) -> tuple[int, int]:
    """Parse 100 as one strip of 100 labels and 5x100 as five strips of 100 labels."""
    match = re.fullmatch(r"(?:(\d+)[xX])?(\d+)", text)
    strips, per_strip = (int(match[1] or 1), int(match[2])) if match else (0, 0)
    if strips < 1 or per_strip < 1:
        raise argparse.ArgumentTypeError(tr("must be a number like 100 or strips x labels like 5x100"))
    return strips, per_strip


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


def label_raster_lines(dots: int) -> int:
    """Return the printed length of a Data Matrix label in dots, without the cut margins."""
    _, modules, quiet = KINDS["DM"]
    # Above 14 dots per module the 1 mm cut margin alone is narrower than the quiet zone.
    quiet_padding = max(quiet * dots - MIN_MARGIN_DOTS, 0)
    return max(modules * dots + 2 * quiet_padding, MIN_RASTER_LINES)


def strip_length_mm(dots: int, count: int, full_cut: bool) -> float:
    """Estimate the tape of one strip, including blank tape from the printer's cutter position."""
    label_mm = (label_raster_lines(dots) + 2 * MIN_MARGIN_DOTS) * 25.4 / DPI
    if full_cut:
        return count * max(label_mm, MIN_EJECT_MM)
    return max(count * label_mm + LEADER_MM, MIN_EJECT_MM)


def format_length(mm: float) -> str:
    return f"{number(mm / 1000, 1)} m" if mm >= 1000 else f"{mm / 10:.0f} cm"


def label_image(tape: int, value: str, dots: int):
    """Return a code-only Data Matrix label; the 1 mm cut margin counts toward the quiet zone."""
    from PIL import Image

    kind = "DM"
    _, pins, tape_dots = TAPES[tape]
    _, modules, quiet = KINDS[kind]
    code_dots = modules * dots
    if code_dots > pins or code_dots + 2 * quiet * dots > tape_dots:
        raise SystemExit(tr("{dots} dots per module do not fit {tape} mm tape with a full quiet zone", dots=dots, tape=tape))
    width = label_raster_lines(dots)
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


class PrinterStopped(Exception):
    """A printer stop during a series, with how many labels at most reached the printer."""

    def __init__(self, reason: str, reached: int, count: int):
        super().__init__(reason)
        self.reason, self.reached, self.count = reason, reached, count


class Printer:
    def __enter__(self):
        import libusb_package
        import usb.core
        import usb.util

        self.usb_core, self.usb_util = usb.core, usb.util
        self.pending: list[bytes] = []
        self.sent_bytes = 0
        # libusb-package bundles libusb, so no system library is needed.
        self.backend = libusb_package.get_libusb1_backend()
        self._connect()
        return self

    def _connect(self) -> None:
        self.dev = self.usb_core.find(idVendor=USB_VENDOR, idProduct=USB_PRODUCT, backend=self.backend)
        if self.dev is None:
            raise SystemExit(tr("PT-P900W not found on USB"))
        try:
            self.intf = self.dev.get_active_configuration()[(0, 0)]
            self.usb_util.claim_interface(self.dev, self.intf)
        except self.usb_core.USBError as error:
            raise SystemExit(tr("USB connection to the printer failed: {error}", error=error)) from None
        util = self.usb_util
        direction = util.endpoint_direction
        self.ep_out = util.find_descriptor(
            self.intf, custom_match=lambda e: direction(e.bEndpointAddress) == util.ENDPOINT_OUT
        )
        self.ep_in = util.find_descriptor(
            self.intf, custom_match=lambda e: direction(e.bEndpointAddress) == util.ENDPOINT_IN
        )

    def _disconnect(self) -> None:
        try:
            self.usb_util.release_interface(self.dev, self.intf)
            self.usb_util.dispose_resources(self.dev)
        except self.usb_core.USBError:
            pass  # The connection may already be gone; the original problem matters more.

    def try_reset(self) -> bytes | None:
        """Clear a stopped printer and return its status, or None if it does not answer.

        Brother documents the reset command that status() sends. The USB reset and the new
        connection cover a blocked transfer and a printer that was switched off and on.
        """

        def plain() -> bytes:
            self.pending.clear()
            self.dev.clear_halt(self.ep_out)
            return self.status()

        def after_usb_reset() -> bytes:
            self.dev.reset()
            return reconnected()

        def reconnected() -> bytes:
            self._disconnect()
            self._connect()
            self.pending.clear()
            return self.status()

        for attempt in (plain, after_usb_reset, reconnected):
            try:
                return attempt()
            except (SystemExit, self.usb_core.USBError):
                continue
        return None

    def __exit__(self, _type, error, _traceback):
        self._disconnect()
        if isinstance(error, self.usb_core.USBError):
            raise SystemExit(tr("USB connection to the printer failed: {error}", error=error)) from None

    def read_status(self, timeout: float = 5.0) -> bytes | None:
        if self.pending:
            return self.pending.pop(0)
        data = b""
        deadline = time.time() + timeout
        while len(data) < 32 and time.time() < deadline:
            try:
                data += bytes(self.ep_in.read(32, timeout=500))
            except self.usb_core.USBTimeoutError:
                pass
            except self.usb_core.USBError as error:
                raise SystemExit(tr("USB connection to the printer failed: {error}", error=error)) from None
        return data[:32] if len(data) >= 32 else None

    def status(self) -> bytes:
        # A finished job can leave notifications queued, e.g. with the previous tape width.
        while self.read_status(timeout=0.6) is not None:
            pass
        self._write(b"\x00" * 200 + b"\x1b@" + b"\x1biS", STATUS_WRITE_TIMEOUT_MS)
        deadline = time.time() + 5
        while time.time() < deadline:
            status = self.read_status(timeout=1)
            # Status type 0x00 marks the reply to a status request.
            if status is not None and status[18] == 0x00:
                return status
        raise SystemExit(tr("no status reply from printer"))

    def send(self, data: bytes) -> None:
        for start in range(0, len(data), 16384):
            chunk = data[start : start + 16384]
            self._write(chunk, PRINT_WRITE_TIMEOUT_MS)
            self.sent_bytes += len(chunk)

    def _write(self, data: bytes, timeout_ms: int) -> None:
        try:
            self.ep_out.write(data, timeout=timeout_ms)
        except self.usb_core.USBTimeoutError:
            # A printer in an error state stops taking data, but may still say why.
            self._check_for_error(wait_ms=2000)
            raise SystemExit(tr("printer stopped accepting data, check the tape and press its power button briefly")) from None
        except self.usb_core.USBError as error:
            raise SystemExit(tr("USB connection to the printer failed: {error}", error=error)) from None

    def _check_for_error(self, wait_ms: int) -> None:
        """Stop on an error the printer reported by itself, and keep other replies for later.

        Only for a blocked write: polling with short reads while sending stopped the printer from
        printing in testing, although all data was accepted.
        """
        deadline = time.time() + wait_ms / 1000
        while True:
            try:
                reply = bytes(self.ep_in.read(32, timeout=wait_ms))
            except self.usb_core.USBTimeoutError:
                reply = b""
            except self.usb_core.USBError as error:
                raise SystemExit(tr("USB connection to the printer failed: {error}", error=error)) from None
            if len(reply) >= 32:
                if reply[18] == 0x02:
                    raise SystemExit(tr("printer error during printing: {errors}", errors=LOOKUP.error_text(reply)))
                self.pending.append(reply[:32])
            elif time.time() >= deadline:
                return


def describe(status: bytes) -> str:
    return LOOKUP.line(status)


def require_no_error(status: bytes) -> None:
    if status[8] or status[9]:
        raise SystemExit(tr("printer error, nothing printed: {errors}", errors=LOOKUP.error_text(status)))


def cmd_generate(_args) -> None:
    STRIPS.mkdir(exist_ok=True)
    manifest_path = STRIPS / "manifest.json"
    # Existing strips keep their IDs, because they may already be printed and photographed.
    all_entries = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    existing = {e["tape_mm"] for e in all_entries}
    for tape in GRID:
        if tape in existing:
            print(tr("{tape} mm: kept", tape=tape))
            continue
        strip, manifest = build_strip(tape)
        strip.save(STRIPS / f"strip-{tape}mm.png", dpi=(DPI, DPI))
        all_entries += manifest
        length = number(strip.width * 25.4 / DPI, 0)
        print(tr("{tape} mm: {codes} codes, length {length} mm", tape=tape, codes=len(manifest), length=length))
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
            tr("rotated+blur"): canvas.rotate(5, resample=Image.BICUBIC, fillcolor=255, expand=True).filter(
                ImageFilter.GaussianBlur(1.0)
            ),
        }
        for name, img in variants.items():
            found = {r.text for r in zxingcpp.read_barcodes(img)}
            missing = expected - found
            failed += len(missing)
            summary = tr(
                "{tape} mm {variant}: {found}/{expected} found",
                tape=tape,
                variant=name,
                found=len(expected & found),
                expected=len(expected),
            )
            print(summary, sorted(missing) or "")
    raise SystemExit(1 if failed else 0)


def cmd_status(args) -> None:
    with Printer() as printer:
        status = printer.status()
    if args.raw:
        print(status.hex(" "))
    print(LOOKUP.report(status))


def cmd_print(args) -> None:
    from PIL import Image

    tape = args.tape
    strip = Image.open(STRIPS / f"strip-{tape}mm.png").convert("1")
    with Printer() as printer:
        status = printer.status()
        print(tr("before:"), describe(status))
        require_no_error(status)
        if status[10] != tape:
            raise SystemExit(tr("{loaded} mm tape loaded, {needed} mm needed, nothing printed", loaded=status[10], needed=tape))
        printer.send(print_job(strip, tape))
        deadline = time.time() + 120
        while time.time() < deadline:
            reply = printer.read_status(timeout=2)
            if reply is None:
                continue
            print(tr("printer:"), describe(reply))
            if reply[18] == 0x02:
                raise SystemExit(tr("printer error during printing: {errors}", errors=LOOKUP.error_text(reply)))
            if reply[18] == 0x01:
                print(tr("print complete"))
                return
        raise SystemExit(tr("no completion status within 120 s, check the printer"))


def confirm_tape(tape: int, kind: str, dots: int, count: int) -> None:
    """Ask before printing, since an auto-detected tape may be a leftover cassette."""
    _, modules, _ = KINDS[kind]
    code_mm = modules * dots * 25.4 / DPI
    print(
        tr(
            "Detected {tape} mm tape: {count} x {kind}, module {module} mm, code {code} mm",
            tape=tape,
            count=count,
            kind=kind,
            module=number(module_mm(dots), 2),
            code=number(code_mm, 1),
        )
    )
    try:
        answer = input(tr("Is this the tape you want? [Y/n] ")).strip().lower()
    except EOFError:
        raise SystemExit(tr("no answer available, nothing printed")) from None
    if answer not in YES:
        raise SystemExit(tr("cancelled, nothing printed"))


def cmd_labels(args) -> None:
    """Print a series of cut labels; IDs are logged before anything is sent."""
    with Printer() as printer:
        status = printer.status()
        print(tr("before:"), describe(status))
        require_no_error(status)
        tape = status[10]
        if tape not in STANDARD:
            raise SystemExit(tr("no standard label defined for {tape} mm tape", tape=tape))
        kind, dots = STANDARD[tape]
        strips, per_strip = args.count
        if strips > 1:
            print(tr("{strips} strips with {count} labels each", strips=strips, count=per_strip))
        strip_mm = strip_length_mm(dots, per_strip, args.full_cut or per_strip == 1)
        if strips > 1:
            print(
                tr(
                    "Tape needed: about {strip} per strip, {total} in total",
                    strip=format_length(strip_mm),
                    total=format_length(strips * strip_mm),
                )
            )
        else:
            print(tr("Tape needed: about {total}", total=format_length(strip_mm)))
        if args.tape is None:
            confirm_tape(tape, kind, dots, strips * per_strip)
        elif args.tape != tape:
            raise SystemExit(tr("{loaded} mm tape loaded, {requested} mm requested, nothing printed", loaded=tape, requested=args.tape))
        # Half cuts save tape, since every full cut costs about 20 mm of blank tape.
        queue = [per_strip] * strips
        total = strips
        done = 0
        while queue:
            size = queue.pop(0)
            if done:
                # The tape may have run out or been changed since the previous strip.
                require_ready_for_next_strip(printer.status(), tape, done + 1, total)
            try:
                print_series(printer, tape, [dots] * size, size > 1 and not args.full_cut)
            except PrinterStopped as stop:
                missing, tape = recover(printer, tape, stop)
                # The rest of the series follows on whichever tape is loaded now.
                kind, dots = STANDARD[tape]
                if missing:
                    # The replacement strip takes the place of the stopped one.
                    queue.insert(0, missing)
                continue
            done += 1
            if total > 1:
                print(tr("strip {strip}/{strips} printed", strip=done, strips=total))


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip().lower()
    except EOFError:
        raise SystemExit(tr("no answer available, stopped")) from None


def accept_other_tape(loaded: int, needed: int) -> bool:
    """Offer a different tape after a stop, for when no cassette of the same width is left."""
    if loaded not in STANDARD:
        print(tr("no standard label defined for {tape} mm tape", tape=loaded))
        return False
    _, dots = STANDARD[loaded]
    _, modules, _ = KINDS["DM"]
    answer = ask(
        tr(
            "{loaded} mm tape is loaded instead of {needed} mm: module {module} mm, code {code} mm. Continue with it? [Y/n] ",
            loaded=loaded,
            needed=needed,
            module=number(module_mm(dots), 2),
            code=number(modules * module_mm(dots), 1),
        )
    )
    return answer in YES


def recover(printer, tape: int, stop: PrinterStopped) -> tuple[int, int]:
    """Report a stop, reset the printer on request and return the labels to print and the tape."""
    print(stop.reason)
    print(tr("at most {reached} of {count} labels reached the printer before it stopped", reached=stop.reached, count=stop.count))
    while True:
        if ask(tr("Replace the tape if needed and press the printer's power button briefly to clear the error. Continue? Nothing is printed yet. [Y/n] ")) not in YES:
            raise SystemExit(tr("stopped, no further labels printed"))
        status = printer.try_reset()
        if status is None:
            print(tr("printer does not answer, press its power button briefly, or turn it off and on again"))
        elif status[8] or status[9]:
            print(tr("printer still reports: {errors}", errors=LOOKUP.error_text(status)))
        elif status[10] == tape or accept_other_tape(status[10], tape):
            tape = status[10]
            break
    print(tr("printer is ready"))
    missing = stop.count - stop.reached
    while True:
        answer = ask(tr("At least {count} labels are missing. Print them as a new job? [Y/n or a number] ", count=missing))
        if answer in YES:
            return missing, tape
        if answer in ("n", "no", "nein"):
            raise SystemExit(tr("stopped, no further labels printed"))
        if answer.isdecimal():
            return int(answer), tape
        print(tr("please answer y, n or a number"))


def require_ready_for_next_strip(status: bytes, tape: int, strip: int, strips: int) -> None:
    done = strip - 1
    if status[8] or status[9]:
        raise SystemExit(
            tr(
                "printer error, stopped after {done} of {strips} strips: {errors}",
                done=done,
                strips=strips,
                errors=LOOKUP.error_text(status),
            )
        )
    if status[10] != tape:
        raise SystemExit(
            tr(
                "{loaded} mm tape loaded, {needed} mm needed, stopped after {done} of {strips} strips",
                loaded=status[10],
                needed=tape,
                done=done,
                strips=strips,
            )
        )


def log_job(event: str, **details) -> None:
    """Keep the printer's replies locally, because they are the only evidence after a failed job."""
    STRIPS.mkdir(exist_ok=True)
    entry = {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **details}
    with (STRIPS / "print-log.jsonl").open("a") as log:
        log.write(json.dumps(entry) + "\n")


def labels_handed_over(sent_bytes: int, pages: list[bytes]) -> int:
    """Count the pages that were sent completely."""
    count = 0
    for page in pages:
        sent_bytes -= len(page)
        if sent_bytes < 0:
            break
        count += 1
    return count


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
    header = b"\x00" * 200 + b"\x1b@"
    printer.sent_bytes = 0
    print(tr("printing {count} labels ...", count=len(ids)), flush=True)
    log_job("send", tape=tape, labels=len(ids))
    completed = 0
    sent = started = False
    try:
        printer.send(header + b"".join(pages))
        sent = True
        log_job("sent", bytes=printer.sent_bytes)
        sent_at = time.time()
        deadline = sent_at + 60 + 15 * len(ids)
        while time.time() < deadline:
            reply = printer.read_status(timeout=8 if completed else 2)
            if reply is None:
                if completed:
                    break
                if not started and time.time() - sent_at > START_TIMEOUT_S:
                    raise SystemExit(tr("printer did not start printing"))
                continue
            log_job("reply", raw=reply.hex(" "))
            if reply[18] == 0x02:
                raise SystemExit(tr("printer error during printing: {errors}", errors=LOOKUP.error_text(reply)))
            # A phase change to printing or a completion report shows that the job arrived.
            if reply[19] == 0x01 or reply[18] == 0x01:
                started = True
            if reply[18] == 0x01:
                completed += 1
    except SystemExit as stop:
        # The printer does not report single labels, so only an upper limit is known.
        reached = labels_handed_over(printer.sent_bytes - len(header), pages) if started or not sent else 0
        log_job("stopped", reason=str(stop), reached=reached)
        raise PrinterStopped(str(stop), reached, len(ids)) from None
    log_job("done", completed=completed)
    print(tr("{completed} completion reports for {count} labels", completed=completed, count=len(ids)))
    if not completed:
        raise SystemExit(tr("no completion status, check the printer"))
    for value, dots in zip(ids, dots_per_label):
        print(tr("issued: {value} ({module} mm module)", value=value, module=number(module_mm(dots), 2)))


def cmd_probe(args) -> None:
    """Print one half-cut Data Matrix label per given module size on the required tape."""
    with Printer() as printer:
        status = printer.status()
        print(tr("before:"), describe(status))
        require_no_error(status)
        if status[10] != args.tape:
            raise SystemExit(tr("{loaded} mm tape loaded, {requested} mm requested, nothing printed", loaded=status[10], requested=args.tape))
        try:
            print_series(printer, args.tape, args.dots, len(args.dots) > 1)
        except PrinterStopped as stop:
            raise SystemExit(stop.reason) from None


def main() -> None:
    global LOOKUP
    arguments = i18n.init()
    LOOKUP = StatusLookup()
    parser = HelpParser(
        description=tr("Print small Data Matrix ID labels on a Brother PT-P900W connected over USB."),
        epilog=tr("""typical use:
  uv run labels.py status             show the loaded tape, prints nothing
  uv run labels.py labels 20          print 20 new labels for the loaded tape
  uv run labels.py labels 20 --tape 9 same, but stop unless 9 mm tape is loaded

run "uv run labels.py <command> --help" for details on a command."""),
    )
    add_language_option(parser)
    commands = parser.add_subparsers(dest="command", required=True, metavar=tr("<command>"), title=tr("commands"))

    def add_command(name: str, summary: str, details: str = "", epilog: str = ""):
        return commands.add_parser(name, help=summary, description=details or summary, epilog=epilog)

    add_command(
        "labels",
        tr("print new labels with random IDs (main command)"),
        tr("""Print new labels with random IDs, in the standard size for the tape.

standard sizes (Data Matrix, module / code size):
   6 mm  0.28 mm /  4.0 mm   only if nothing larger fits, needs good light
   9 mm  0.49 mm /  6.9 mm   small parts
  12 mm  0.71 mm /  9.9 mm   default for most parts
  18 mm  1.06 mm / 14.8 mm   larger devices, boxes
  24 mm  1.48 mm / 20.7 mm   cases, crates
  36 mm  2.26 mm / 31.6 mm   shelves, racks

Several labels get half cuts between them and one full cut at the end, which saves tape.
With 5x100 each strip is its own job with new IDs, and a printer problem stops the remaining strips.
Without --tape, the detected tape is shown and you confirm it with [Y/n]."""),
        tr("""examples:
  uv run labels.py labels 20
  uv run labels.py labels 5x100
  uv run labels.py labels 20 --tape 12
  uv run labels.py labels 5 --full-cut"""),
    )
    labels_parser = commands.choices["labels"]
    labels_parser.add_argument(
        "count",
        type=label_count,
        help=tr("number of labels, or strips x labels: 5x100 prints 5 separate strips with 100 labels each"),
    )
    labels_parser.add_argument(
        "--tape",
        type=int,
        choices=sorted(STANDARD),
        help=tr("required tape width in mm; prints without asking, but stops if another tape is loaded"),
    )
    labels_parser.add_argument(
        "--full-cut", action="store_true", help=tr("full cut after every label; each cut wastes about 20 mm of tape")
    )
    labels_parser.set_defaults(func=cmd_labels)

    status_parser = add_command(
        "status",
        tr("show the loaded tape and printer errors, prints nothing"),
        tr("""Show the printer status in plain text, prints nothing.

The explanations come from the tables in docs/brother-pt-p900w-status*.md."""),
        tr("""examples:
  uv run labels.py status
  uv run labels.py --lang de status
  uv run labels.py status --raw"""),
    )
    status_parser.add_argument("--raw", action="store_true", help=tr("also show the 32 raw reply bytes"))
    status_parser.set_defaults(func=cmd_status)

    probe_parser = add_command(
        "probe",
        tr("print one label per module size, to compare sizes"),
        tr("""Print one label per given module size, to compare sizes on one tape.

A dot is 0.07 mm, so 10 dots per module mean 0.71 mm. Sizes without a full quiet zone are refused."""),
        tr("""example:
  uv run labels.py probe 36 32 24    two labels on 36 mm tape: 2.26 and 1.69 mm"""),
    )
    probe_parser.add_argument("tape", type=int, choices=sorted(STANDARD), help=tr("tape width in mm, must be loaded"))
    probe_parser.add_argument("dots", type=positive_int, nargs="+", help=tr("dots per module, one value per label"))
    probe_parser.set_defaults(func=cmd_probe)

    print_parser = add_command(
        "print-test-strip",
        tr("print a test strip to compare QR and Data Matrix sizes, not for real labels"),
        tr("""Print the test strip for a tape: several QR and Data Matrix sizes with captions.

The strip always holds the same test IDs from strips/manifest.json, and there is no confirmation.
Only a full cut at the end; marks on the tape edges show where to cut by hand."""),
        tr("""example:
  uv run labels.py print-test-strip 24"""),
    )
    print_parser.add_argument("tape", type=int, choices=sorted(GRID), help=tr("tape width in mm, must be loaded"))
    print_parser.set_defaults(func=cmd_print)

    add_command(
        "generate-test-strips",
        tr("create missing test strips in strips/, prints nothing"),
        tr("Create missing test strips in strips/. Existing strips keep their IDs. Prints nothing."),
    ).set_defaults(func=cmd_generate)
    add_command(
        "verify-test-strips",
        tr("check the test strip images with the decoder, prints nothing"),
        tr("Decode the test strip images, also rotated and blurred, and report missing codes. Prints nothing."),
    ).set_defaults(func=cmd_verify)

    args = parser.parse_args(arguments)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print()
        raise SystemExit(tr("cancelled; labels already sent may still print, restart the printer if it does not recover")) from None


if __name__ == "__main__":
    main()

"""Explain PT-P900W status replies, using the tables in docs/ as the only source of values."""
import re
from pathlib import Path

import i18n

DOCS = {
    "en": Path(__file__).parent / "docs" / "brother-pt-p900w-status.md",
    "de": Path(__file__).parent / "docs" / "brother-pt-p900w-status.de.md",
}

# Section headings per language; the tables hold the values and meanings.
SECTIONS = {
    "model": ("Model code", "Modellkennung"),
    "battery": ("Battery level", "Akkustand"),
    "extended_error": ("Extended error", "Erweiterter Fehler"),
    "error_1": ("Error information 1", "Fehlerinformation 1"),
    "error_2": ("Error information 2", "Fehlerinformation 2"),
    "media_type": ("Media type", "Medienart"),
    "status_type": ("Status type", "Statusart"),
    "phase": ("Phase", "Phase"),
    "notification": ("Notification number", "Benachrichtigungsnummer"),
    "tape_color": ("Tape color", "Bandfarbe"),
    "text_color": ("Text color", "Schriftfarbe"),
}

TEXT = {
    "en": {
        "model": "Model",
        "tape": "Tape",
        "text_color": "Text color",
        "power": "Power",
        "errors": "Errors",
        "state": "State",
        "notification": "Notification",
        "none": "none",
        "unknown": "unknown value",
    },
    "de": {
        "model": "Modell",
        "tape": "Band",
        "text_color": "Schriftfarbe",
        "power": "Stromversorgung",
        "errors": "Fehler",
        "state": "Zustand",
        "notification": "Benachrichtigung",
        "none": "keine",
        "unknown": "unbekannter Wert",
    },
}

HEX = r"`0x([0-9A-Fa-f]{2})`"
SINGLE = re.compile(rf"^{HEX}(?: \(`.`\))?$")
RANGE = re.compile(rf"^{HEX} (?:to|bis) {HEX}$")
PHASE_NUMBER = re.compile(r"^(\d+) \(`0x[0-9A-Fa-f]{2} 0x[0-9A-Fa-f]{2}`\)$")


def _rows_by_heading(text: str) -> dict[str, list[list[str]]]:
    rows: dict[str, list[list[str]]] = {}
    heading = None
    for line in text.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            rows[heading] = []
        elif heading and line.startswith("|") and not line.startswith("|---"):
            rows[heading].append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


class StatusLookup:
    """Lookup tables for one language."""

    def __init__(self, language: str | None = None):
        self.language = language or i18n.current()
        index = list(DOCS).index(self.language)
        by_heading = _rows_by_heading(DOCS[self.language].read_text())
        self.values: dict[str, dict[int, str]] = {}
        self.phase_numbers: dict[tuple[int, int], str] = {}
        for key, headings in SECTIONS.items():
            rows = by_heading[headings[index]]
            values: dict[int, str] = {}
            for cells in rows:
                single = SINGLE.match(cells[0])
                span = RANGE.match(cells[0])
                if single:
                    meaning = cells[1]
                    if len(cells) > 2 and cells[2]:
                        meaning = f"{meaning} ({cells[2]})"
                    values[int(single[1], 16)] = meaning
                elif span:
                    for value in range(int(span[1], 16), int(span[2], 16) + 1):
                        values[value] = cells[1]
            self.values[key] = values
            if key == "phase":
                for cells in rows:
                    number = PHASE_NUMBER.match(cells[1]) if len(cells) > 2 else None
                    if number:
                        for phase_type, meaning in values.items():
                            if meaning.startswith(cells[0]):
                                self.phase_numbers[(phase_type, int(number[1]))] = cells[2]

    def _text(self, key: str) -> str:
        return TEXT[self.language][key]

    def name(self, section: str, value: int) -> str:
        known = self.values[section].get(value)
        return known if known is not None else f"{self._text('unknown')} 0x{value:02x}"

    def _flags(self, section: str, value: int) -> list[str]:
        return [self.name(section, 1 << bit) for bit in range(8) if value & (1 << bit)]

    def errors(self, status: bytes) -> list[str]:
        """Return every error the reply reports, including extended errors."""
        found = self._flags("error_1", status[8]) + self._flags("error_2", status[9])
        if status[7]:
            found.append(self.name("extended_error", status[7]))
        return found

    def error_text(self, status: bytes) -> str:
        return ", ".join(self.errors(status)) or self._text("none")

    def tape(self, status: bytes) -> str:
        if status[10] == 0:
            return self.name("media_type", status[11])
        return ", ".join([f"{status[10]} mm", self.name("media_type", status[11]), self.name("tape_color", status[24])])

    def phase(self, status: bytes) -> str:
        number = status[20] << 8 | status[21]
        known = self.phase_numbers.get((status[19], number))
        return known if known is not None else self.name("phase", status[19])

    def line(self, status: bytes) -> str:
        """Return the reply as one line, for progress output."""
        return (
            f"{self._text('tape')}: {self.tape(status)}; {self._text('errors')}: {self.error_text(status)}; "
            f"{self.name('status_type', status[18])}; {self._text('state')}: {self.phase(status)}"
        )

    def report(self, status: bytes) -> str:
        """Return the reply as a readable block."""
        entries = [
            (self._text("model"), self.name("model", status[4])),
            (self._text("tape"), self.tape(status)),
            (self._text("power"), self.name("battery", status[6])),
            (self._text("errors"), self.error_text(status)),
            (self._text("state"), f"{self.phase(status)} ({self.name('status_type', status[18])})"),
        ]
        if status[10]:
            entries.insert(2, (self._text("text_color"), self.name("text_color", status[25])))
        if status[22]:
            entries.append((self._text("notification"), self.name("notification", status[22])))
        width = max(len(label) for label, _ in entries) + 1
        return "\n".join(f"{label + ':':<{width}} {value}" for label, value in entries)

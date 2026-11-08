"""Check the status lookup against the tables in docs/, without a printer."""
import re
import unittest

from printer_status import DOCS, SECTIONS, StatusLookup

EXAMPLE = bytes.fromhex(
    "80 20 42 30 6f 30 04 00 00 00 24 01 00 00 00 00 00 00 00 00 00 00 00 00 06 08 00 00 00 00 00 00"
)


def reply(**fields: int) -> bytes:
    data = bytearray(EXAMPLE)
    for name, value in fields.items():
        data[int(name[1:])] = value
    return bytes(data)


class StatusLookupTest(unittest.TestCase):
    def test_languages_share_all_values(self):
        english, german = StatusLookup("en"), StatusLookup("de")
        for section in SECTIONS:
            self.assertTrue(english.values[section], section)
            self.assertEqual(english.values[section].keys(), german.values[section].keys(), section)
        self.assertEqual(english.phase_numbers.keys(), german.phase_numbers.keys())

    def test_every_table_value_is_loaded(self):
        for language, path in DOCS.items():
            lookup = StatusLookup(language)
            text = path.read_text()
            heading = SECTIONS["tape_color"][list(DOCS).index(language)]
            section = text.split(f"## {heading}\n")[1].split("\n## ")[0]
            self.assertEqual(len(lookup.values["tape_color"]), len(re.findall(r"^\| `0x", section, re.M)))

    def test_example_reply(self):
        report = StatusLookup("en").report(EXAMPLE)
        for expected in ("PT-P900W", "36 mm", "Laminated tape", "Yellow", "Black", "AC adapter in use", "none"):
            self.assertIn(expected, report)
        self.assertIn("Netzteil in Betrieb", StatusLookup("de").report(EXAMPLE))

    def test_flexible_id_tape(self):
        tape = StatusLookup("de").tape(reply(b10=12, b11=0x14, b24=0x91))
        self.assertEqual(tape, "12 mm, Flexible-ID-Band, Gelb, Flexible-ID")

    def test_no_tape(self):
        lookup = StatusLookup("en")
        status = reply(b8=0x01, b10=0, b11=0)
        self.assertEqual(lookup.tape(status), "No tape")
        self.assertEqual(lookup.errors(status), ["No media"])

    def test_combined_and_extended_errors(self):
        status = reply(b7=0x21, b8=0x05, b9=0x10)
        self.assertEqual(
            StatusLookup("en").errors(status), ["No media", "Cutter jam", "Cover open", "Unsupported media"]
        )
        self.assertEqual(StatusLookup("de").errors(reply(b9=0x10)), ["Deckel offen"])

    def test_status_type_range_and_unknown_value(self):
        lookup = StatusLookup("en")
        self.assertEqual(lookup.name("status_type", 0x10), "Unused")
        self.assertEqual(lookup.name("media_type", 0x99), "unknown value 0x99")

    def test_phase_numbers(self):
        lookup = StatusLookup("en")
        self.assertEqual(lookup.phase(reply(b19=0, b21=1)), "Feeding")
        self.assertEqual(lookup.phase(reply(b19=1, b21=20)), "Cover open while receiving")
        self.assertEqual(StatusLookup("de").phase(reply(b19=1, b21=0)), "Druck läuft")


if __name__ == "__main__":
    unittest.main()

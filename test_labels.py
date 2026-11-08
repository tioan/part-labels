"""Check strip parsing and the multi-strip flow with a fake printer."""
import argparse
import unittest
from types import SimpleNamespace
from unittest import mock

import labels

READY = bytes.fromhex(
    "80 20 42 30 6f 30 04 00 00 00 0c 01 00 00 00 00 00 00 00 00 00 00 00 00 06 08 00 00 00 00 00 00"
)


def status(**fields: int) -> bytes:
    data = bytearray(READY)
    for name, value in fields.items():
        data[int(name[1:])] = value
    return bytes(data)


class LabelCountTest(unittest.TestCase):
    def test_valid_counts(self):
        self.assertEqual(labels.label_count("100"), (1, 100))
        self.assertEqual(labels.label_count("5x100"), (5, 100))
        self.assertEqual(labels.label_count("5X100"), (5, 100))

    def test_invalid_counts(self):
        for text in ("0", "0x5", "5x0", "x5", "5x", "-1", "abc", "2x3x4", "1.5"):
            with self.assertRaises(argparse.ArgumentTypeError, msg=text):
                labels.label_count(text)


class StripsTest(unittest.TestCase):
    def run_labels(self, statuses, count="3x2", **options):
        printer = mock.MagicMock()
        printer.status.side_effect = statuses
        fake = mock.MagicMock()
        fake.return_value.__enter__.return_value = printer
        args = SimpleNamespace(count=labels.label_count(count), tape=12, full_cut=False, **options)
        with mock.patch.object(labels, "Printer", fake), mock.patch.object(
            labels, "print_series"
        ) as series, mock.patch("builtins.print"):
            try:
                labels.cmd_labels(args)
            except SystemExit as stop:
                return series, str(stop)
        return series, None

    def test_every_strip_is_a_job_with_half_cuts(self):
        series, error = self.run_labels([READY] * 3)
        self.assertIsNone(error)
        self.assertEqual(series.call_count, 3)
        for call in series.call_args_list:
            self.assertEqual(call.args[2], [10, 10])
            self.assertIs(call.args[3], True)

    def test_one_label_per_strip_gets_a_full_cut(self):
        series, _ = self.run_labels([READY] * 2, count="2x1")
        self.assertIs(series.call_args_list[0].args[3], False)

    def test_error_stops_the_remaining_strips(self):
        series, error = self.run_labels([READY, READY, status(b8=0x02)])
        self.assertEqual(series.call_count, 2)
        self.assertIn("2", error)

    def test_changed_tape_stops_the_remaining_strips(self):
        series, error = self.run_labels([READY, status(b10=9)])
        self.assertEqual(series.call_count, 1)
        self.assertIn("9", error)

    def test_wrong_tape_prints_nothing(self):
        series, error = self.run_labels([status(b10=9)])
        self.assertEqual(series.call_count, 0)
        self.assertIn("nothing printed", error)


if __name__ == "__main__":
    unittest.main()

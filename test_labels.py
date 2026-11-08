"""Check strip parsing and the multi-strip flow with a fake printer."""
import argparse
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import usb.core

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


class FakeEndpoint:
    def __init__(self, write_error=None, replies=()):
        self.write_error, self.replies, self.written = write_error, list(replies), []

    def write(self, data, timeout):
        if self.write_error:
            raise self.write_error
        self.written.append(bytes(data))

    def read(self, _size, timeout):
        if self.replies:
            return self.replies.pop(0)
        raise usb.core.USBTimeoutError("timeout", 60, 60)


def fake_printer(endpoint):
    printer = object.__new__(labels.Printer)
    printer.usb_core, printer.pending, printer.sent_bytes = usb.core, [], 0
    printer.ep_out = printer.ep_in = endpoint
    return printer


class LabelsHandedOverTest(unittest.TestCase):
    PAGES = [b"a" * 10, b"b" * 10, b"c" * 10]

    def test_counts_only_complete_pages(self):
        for sent, expected in ((-5, 0), (0, 0), (9, 0), (10, 1), (19, 1), (20, 2), (30, 3)):
            self.assertEqual(labels.labels_handed_over(sent, self.PAGES), expected, sent)

    def test_series_reports_the_count_when_the_printer_stops(self):
        printer = mock.MagicMock()
        printer.sent_bytes = 0

        def send(data):
            printer.sent_bytes = 202 + 2 * len(page)
            raise SystemExit("stopped")

        page = labels.label_page(labels.label_image(12, "0123456789", 10), 12, 0, 3, True)
        printer.send.side_effect = send
        with mock.patch.object(labels, "label_page", return_value=page), mock.patch.object(
            labels, "label_image"
        ), mock.patch.object(labels, "STRIPS", labels.Path(self.tmp.name)), self.assertRaises(
            labels.PrinterStopped
        ) as stopped:
            labels.print_series(printer, 12, [10, 10, 10], True)
        self.assertEqual((stopped.exception.reached, stopped.exception.count), (2, 3))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)


class RecoveryTest(unittest.TestCase):
    STOP = labels.PrinterStopped("End of media", 73, 100)

    def recover(self, answers, resets):
        printer = mock.MagicMock()
        printer.try_reset.side_effect = resets
        with mock.patch("builtins.input", side_effect=answers), mock.patch("builtins.print") as output:
            try:
                result = labels.recover(printer, 12, self.STOP)
            except SystemExit as stop:
                result = str(stop)
        return result, printer, " | ".join(str(c.args[0]) for c in output.call_args_list)

    def test_confirmed_reset_offers_the_missing_labels(self):
        result, printer, text = self.recover(["", "y"], [READY])
        self.assertEqual(result, 27)
        self.assertIn("at most 73 of 100", text)
        printer.try_reset.assert_called_once()

    def test_own_number_replaces_the_estimate(self):
        self.assertEqual(self.recover(["y", "35"], [READY])[0], 35)

    def test_declined_reset_touches_nothing(self):
        result, printer, _ = self.recover(["n"], [READY])
        self.assertIn("stopped", result)
        printer.try_reset.assert_not_called()

    def test_declined_reprint_stops(self):
        self.assertIn("stopped", self.recover(["y", "n"], [READY])[0])

    def test_retries_until_the_printer_is_ready(self):
        result, printer, text = self.recover(
            ["y", "y", "y", "y", "y"], [None, status(b8=0x01), status(b10=9), READY]
        )
        self.assertEqual(result, 27)
        self.assertEqual(printer.try_reset.call_count, 4)
        self.assertIn("turn it off and on", text)
        self.assertIn("No media", text)
        self.assertIn("9 mm tape loaded", text)

    def test_invalid_answer_asks_again(self):
        self.assertEqual(self.recover(["y", "maybe", "5"], [READY])[0], 5)

    def test_no_input_stops(self):
        printer = mock.MagicMock()
        with mock.patch("builtins.input", side_effect=EOFError), mock.patch("builtins.print"), self.assertRaises(
            SystemExit
        ):
            labels.recover(printer, 12, self.STOP)


class ContinueAfterStopTest(unittest.TestCase):
    def test_missing_labels_and_remaining_strips_follow(self):
        printer = mock.MagicMock()
        printer.status.return_value = READY
        fake = mock.MagicMock()
        fake.return_value.__enter__.return_value = printer
        args = SimpleNamespace(count=(2, 100), tape=12, full_cut=False)
        stopped = labels.PrinterStopped("End of media", 73, 100)
        with mock.patch.object(labels, "Printer", fake), mock.patch.object(
            labels, "print_series", side_effect=[stopped, None, None]
        ) as series, mock.patch.object(labels, "recover", return_value=27), mock.patch("builtins.print"):
            labels.cmd_labels(args)
        self.assertEqual([len(call.args[2]) for call in series.call_args_list], [100, 27, 100])


class ResetTest(unittest.TestCase):
    def printer(self):
        printer = fake_printer(mock.MagicMock())
        printer.dev = mock.MagicMock()
        printer._disconnect = mock.MagicMock()
        printer._connect = mock.MagicMock()
        return printer

    def test_plain_reset_is_tried_first(self):
        printer = self.printer()
        with mock.patch.object(printer, "status", return_value=READY):
            self.assertEqual(printer.try_reset(), READY)
        printer.dev.clear_halt.assert_called_once()
        printer.dev.reset.assert_not_called()

    def test_falls_back_to_usb_reset(self):
        printer = self.printer()
        with mock.patch.object(printer, "status", side_effect=[SystemExit("x"), READY]):
            self.assertEqual(printer.try_reset(), READY)
        printer.dev.reset.assert_called_once()

    def test_reports_none_when_nothing_answers(self):
        printer = self.printer()
        with mock.patch.object(printer, "status", side_effect=SystemExit("x")):
            self.assertIsNone(printer.try_reset())


class SendErrorTest(unittest.TestCase):
    TIMEOUT = usb.core.USBTimeoutError("timeout", 60, 60)

    def test_write_timeout_reports_the_printer_error(self):
        endpoint = FakeEndpoint(self.TIMEOUT, [status(b8=0x02, b18=0x02)])
        with self.assertRaises(SystemExit) as stop:
            fake_printer(endpoint).send(b"x")
        self.assertIn("End of media", str(stop.exception))

    def test_write_timeout_without_reply_gives_advice(self):
        with self.assertRaises(SystemExit) as stop:
            fake_printer(FakeEndpoint(self.TIMEOUT)).send(b"x")
        self.assertIn("check the tape", str(stop.exception))

    def test_error_during_sending_stops_the_rest(self):
        endpoint = FakeEndpoint(replies=[status(b9=0x10, b18=0x02)])
        with self.assertRaises(SystemExit) as stop:
            fake_printer(endpoint).send(b"x" * 40000)
        self.assertIn("Cover open", str(stop.exception))
        self.assertEqual(len(endpoint.written), 1)

    def test_other_replies_are_kept_for_later(self):
        finished = status(b18=0x01)
        printer = fake_printer(FakeEndpoint(replies=[finished]))
        printer.send(b"x")
        self.assertEqual(printer.read_status(timeout=0), finished)

    def test_status_uses_the_short_timeout(self):
        printer = fake_printer(FakeEndpoint(self.TIMEOUT))
        with self.assertRaises(SystemExit):
            printer.status()


if __name__ == "__main__":
    unittest.main()

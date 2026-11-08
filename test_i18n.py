"""Check language selection and that every translatable text has a matching translation."""
import ast
import os
import re
import string
import unittest
from pathlib import Path
from unittest import mock

import i18n
from translations import ARGPARSE_DE, DE

SOURCES = ["cli.py", "labels.py", "read_photo.py", "sort_photos.py"]


def source_texts() -> set[str]:
    texts = set()
    for name in SOURCES:
        tree = ast.parse((Path(__file__).parent / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "tr":
                first = node.args[0]
                if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                    raise AssertionError(f"{name}:{node.lineno}: tr() needs a literal text")
                texts.add(first.value)
    return texts


def placeholders(text: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}


class TranslationTest(unittest.TestCase):
    def test_every_text_is_translated_and_none_is_stale(self):
        texts = source_texts()
        self.assertEqual(texts - DE.keys(), set())
        self.assertEqual(DE.keys() - texts, set())

    def test_placeholders_match(self):
        for english, german in DE.items():
            self.assertEqual(placeholders(english), placeholders(german), english)

    def test_argparse_placeholders_match(self):
        pattern = re.compile(r"%(?:\(\w+\))?[sr]")
        for english, german in ARGPARSE_DE.items():
            self.assertEqual(sorted(pattern.findall(english)), sorted(pattern.findall(german)), english)

    def test_argparse_texts_exist_in_python(self):
        import argparse
        import inspect

        source = inspect.getsource(argparse)
        for text in ("usage: ", "options", "positional arguments", "show this help message and exit"):
            self.assertIn(text, source)


def env(**values: str):
    return mock.patch.dict(os.environ, values, clear=True)


class LanguageChoiceTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(i18n.platform, "system", return_value="Linux")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(i18n.init, [])

    def test_default_is_english(self):
        with env():
            self.assertEqual(i18n.choose_language(), "en")

    def test_system_language(self):
        for value, expected in (("de_DE.UTF-8", "de"), ("en_US.UTF-8", "en"), ("fr_FR.UTF-8", "en"), ("C", "en")):
            with env(LANG=value):
                self.assertEqual(i18n.choose_language(), expected, value)

    def test_lc_all_wins_over_lang(self):
        with env(LC_ALL="de_DE.UTF-8", LANG="en_US.UTF-8"):
            self.assertEqual(i18n.choose_language(), "de")

    def test_environment_variable_wins_over_system(self):
        with env(PART_LABELS_LANG="en", LANG="de_DE.UTF-8"):
            self.assertEqual(i18n.choose_language(), "en")
        with env(PART_LABELS_LANG="de_DE", LANG="en_US.UTF-8"):
            self.assertEqual(i18n.choose_language(), "de")

    def test_invalid_environment_variable_falls_back(self):
        with env(PART_LABELS_LANG="xx", LANG="de_DE.UTF-8"), mock.patch("sys.stderr"):
            self.assertEqual(i18n.choose_language(), "de")

    def test_argument_wins_at_any_position(self):
        with env(PART_LABELS_LANG="en"):
            self.assertEqual(i18n.init(["status", "--lang", "de", "--raw"]), ["status", "--raw"])
            self.assertEqual(i18n.current(), "de")
            self.assertEqual(i18n.init(["--lang=en", "status"]), ["status"])
            self.assertEqual(i18n.current(), "en")

    def test_invalid_argument_stays_for_the_parser(self):
        with env():
            self.assertEqual(i18n.init(["--lang", "xx", "status"]), ["--lang", "xx", "status"])

    def test_macos_setting_is_used_without_environment(self):
        result = mock.Mock(stdout='(\n    "de-DE",\n    "en-US"\n)\n')
        with env(), mock.patch.object(i18n.platform, "system", return_value="Darwin"), mock.patch.object(
            i18n.subprocess, "run", return_value=result
        ):
            self.assertEqual(i18n.system_language(), "de")

    def test_translation_and_numbers(self):
        with env():
            i18n.init(["--lang", "de"])
            self.assertEqual(i18n.tr("{path} is not a folder", path="x"), "x ist kein Ordner")
            self.assertEqual(i18n.number(0.706, 2), "0,71")
            i18n.init(["--lang", "en"])
            self.assertEqual(i18n.tr("{path} is not a folder", path="x"), "x is not a folder")
            self.assertEqual(i18n.number(0.706, 2), "0.71")


if __name__ == "__main__":
    unittest.main()

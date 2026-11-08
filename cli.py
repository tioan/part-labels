"""Command line helpers shared by the scripts."""
import argparse
import sys

import i18n
from i18n import tr

# argparse has its own English texts, which follow the selected language this way.
argparse._ = i18n.argparse_gettext
argparse.ngettext = i18n.argparse_ngettext


class HelpParser(argparse.ArgumentParser):
    """Show the full help on usage errors, so a missing argument explains itself."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
        super().__init__(*args, **kwargs)

    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, "\n" + tr("error: {message}", message=message) + "\n")


def add_language_option(parser: argparse.ArgumentParser) -> None:
    """Document --lang and validate it; i18n.init() has already handled valid values."""
    parser.add_argument(
        "--lang",
        choices=i18n.LANGUAGES,
        help=tr("language of all output: en or de; default from PART_LABELS_LANG, then the system language, then en"),
    )


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        value = 0
    if value < 1:
        raise argparse.ArgumentTypeError(tr("must be a whole number of at least 1"))
    return value

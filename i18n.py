"""Language selection and translation; English is the source language and the default.

Priority: --lang, then the PART_LABELS_LANG environment variable, then the system language.
"""
import os
import platform
import re
import subprocess
import sys

from translations import ARGPARSE_DE, DE

LANGUAGES = ("en", "de")
DEFAULT_LANGUAGE = "en"
ENV_VARIABLE = "PART_LABELS_LANG"

_current = DEFAULT_LANGUAGE


def _supported(value: str) -> str | None:
    """Return the supported language of a value like de_DE.UTF-8, or None."""
    code = re.split(r"[-_.@:]", value.strip().lower())[0]
    return code if code in LANGUAGES else None


def _system_languages() -> list[str]:
    values = []
    # LC_ALL overrides the others, and LANGUAGE can hold a list of preferences.
    for name in ("LC_ALL", "LC_MESSAGES", "LANGUAGE", "LANG"):
        value = os.environ.get(name, "")
        if value and value.split(".")[0].upper() not in ("C", "POSIX"):
            values.append(value)
    if not values and platform.system() == "Darwin":
        # Programs started from the desktop or an IDE often have no LANG on macOS.
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleLanguages"], capture_output=True, text=True, timeout=2
            )
            values += re.findall(r'[A-Za-z]{2}[A-Za-z_-]*', result.stdout)
        except (OSError, subprocess.SubprocessError):
            pass
    return values


def system_language() -> str:
    """Return the language of the first system preference; an unsupported one means the default."""
    values = _system_languages()
    return (_supported(values[0]) or DEFAULT_LANGUAGE) if values else DEFAULT_LANGUAGE


def choose_language(cli_value: str | None = None) -> str:
    if cli_value in LANGUAGES:
        return cli_value
    env_value = os.environ.get(ENV_VARIABLE, "")
    if env_value:
        language = _supported(env_value)
        if language:
            return language
        print(f"ignoring {ENV_VARIABLE}={env_value}, use one of: {', '.join(LANGUAGES)}", file=sys.stderr)
    return system_language()


def init(argv: list[str] | None = None) -> list[str]:
    """Set the language from the arguments and return them without a valid --lang.

    This runs before the parser exists, because the help texts need the language. It also allows
    --lang at any position. Invalid values stay in place, so the parser reports them.
    """
    global _current
    arguments = list(sys.argv[1:] if argv is None else argv)
    remaining, cli_value = [], None
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--lang" and index + 1 < len(arguments) and arguments[index + 1] in LANGUAGES:
            cli_value = arguments[index + 1]
            index += 2
            continue
        if argument.startswith("--lang=") and argument.split("=", 1)[1] in LANGUAGES:
            cli_value = argument.split("=", 1)[1]
            index += 1
            continue
        remaining.append(argument)
        index += 1
    _current = choose_language(cli_value)
    return remaining


def current() -> str:
    return _current


def tr(source: str, /, **values) -> str:
    """Translate an English text and fill in its {placeholders}; any placeholder name is allowed."""
    text = DE.get(source, source) if _current == "de" else source
    return text.format(**values) if values else text


def number(value: float, decimals: int) -> str:
    """Format a number with the decimal separator of the current language."""
    text = f"{value:.{decimals}f}"
    return text.replace(".", ",") if _current == "de" else text


def argparse_gettext(message: str) -> str:
    return ARGPARSE_DE.get(message, message) if _current == "de" else message


def argparse_ngettext(singular: str, plural: str, count: int) -> str:
    return argparse_gettext(singular if count == 1 else plural)

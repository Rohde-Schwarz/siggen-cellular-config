"""Load test parameters from INI config files."""

import argparse
import configparser
from collections.abc import Iterable
from pathlib import Path

from utils.helpers import parse_frequency

_REPO_ROOT = Path(__file__).resolve().parent.parent
_INSTRUMENT_CONFIG = _REPO_ROOT / "instrument.ini"

_BOOL_VALUES = {
    "true": True, "yes": True, "on": True,
    "false": False, "no": False, "off": False,
}


def _strip_inline_comment(raw: str) -> str:
    """Remove trailing ``#`` / ``;`` comments (configparser does not strip these inline)."""
    for sep in ("#", ";"):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    return raw.strip()


def _coerce_value(
    key: str,
    raw: str,
    freq_keys: frozenset[str],
    bool_keys: frozenset[str],
):
    """Coerce an INI string value to bool, int, frequency, or str."""
    value = _strip_inline_comment(raw)
    if not value:
        return None

    if key in freq_keys:
        return parse_frequency(value)

    try:
        return int(value)
    except ValueError:
        if key in bool_keys:
            return _BOOL_VALUES.get(value.lower(), value)
        return value


def load_ini_as_namespace(
    path: str | Path,
    extra_configs: Iterable[Path] = (),
    freq_keys: frozenset[str] = frozenset(),
    bool_keys: frozenset[str] = frozenset(),
) -> argparse.Namespace:
    """Load INI sections into a flat argparse.Namespace.

    Loads instrument.ini first, then any extra_configs, then the per-test INI.
    Later files override earlier ones. Keys are coerced to int, frequency (Hz),
    bool, or str depending on freq_keys / bool_keys membership.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    cp = configparser.ConfigParser()
    for ini_path in (_INSTRUMENT_CONFIG, *extra_configs, config_path):
        if ini_path.is_file():
            cp.read(ini_path, encoding="utf-8")

    flat: dict[str, object] = {}
    for section in cp.sections():
        for key, raw in cp.items(section):
            flat[key] = _coerce_value(key, raw, freq_keys, bool_keys)

    return argparse.Namespace(**flat)

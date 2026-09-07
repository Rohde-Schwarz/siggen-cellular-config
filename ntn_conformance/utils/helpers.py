"""General-purpose helpers for NTN test scripts."""

import argparse
import re

freq_units = {
    "hz": 1,
    "khz": 1_000,
    "k": 1_000,
    "mhz": 1_000_000,
    "m": 1_000_000,
    "ghz": 1_000_000_000,
    "g": 1_000_000_000,
}

freq_pattern = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\s*$")


def parse_frequency(value: str):
    """Parse a frequency from Hz integer or suffixed value (e.g. 1620000000, 1.62G)."""
    match = freq_pattern.match(str(value))
    if not match:
        raise argparse.ArgumentTypeError(f"Invalid frequency: {value!r}")
    number_str, unit = match.group(1), match.group(2)
    if unit is None:
        return int(number_str)
    multiplier = freq_units.get(unit.lower())
    if multiplier is None:
        raise argparse.ArgumentTypeError(
            f"Unknown frequency unit {unit!r} in {value!r}; use Hz, k/kHz, M/MHz, or G/GHz."
        )
    return round(float(number_str) * multiplier)

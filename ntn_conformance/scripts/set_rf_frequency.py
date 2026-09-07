"""Bulk-update freq in NR5G test INI files."""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

from utils.helpers import parse_frequency

# FR1 NTN uplink operating bands (Hz). Matches NR5G/ts-38181-chapter7/tables_3gpp.py OPERATING_BANDS.
OPERATING_BANDS: dict[str, tuple[int, int]] = {
    "n253": (1_668_000_000, 1_675_000_000),
    "n254": (1_610_000_000, 1_626_500_000),
    "n255": (1_626_500_000, 1_660_500_000),
    "n256": (1_980_000_000, 2_010_000_000),
}


class SetRfFrequencyResult(NamedTuple):
    freq_hz: int | None
    interferer_freq_hz: int | None
    section: str | None
    updated: list[str]
    skipped: list[str]
    band_warnings: list[str]


def resolve_operating_band(freq_hz: int, operating_bands: dict[str, tuple[int, int]]) -> str | None:
    """Return the first FR1 NTN band that contains freq_hz, or None if out of band."""
    for band, (ful_low_hz, ful_high_hz) in operating_bands.items():
        if ful_low_hz <= freq_hz <= ful_high_hz:
            return band
    return None


CHAPTER_DIRS = ("ts-38181-chapter7", "ts-38181-chapter8")


def _iter_test_ini_files(nr5g_root: Path):
    """Yield INI files under chapter 7 and 8 config trees only."""
    for chapter in CHAPTER_DIRS:
        chapter_root = nr5g_root / chapter
        if chapter_root.is_dir():
            yield from sorted(chapter_root.rglob("*.ini"))


def _matches_section(ini_path: Path, section: str | None) -> bool:
    if section is None:
        return True
    return f"configs/{section}/" in ini_path.as_posix()


def _replace_ini_assignment(line: str, key: str, new_value: str) -> str | None:
    """Replace the value on a matching INI assignment line, preserving spacing, comment, and newline."""
    pattern = re.compile(rf"^(\s*{re.escape(key)}\s*=\s*)\S+")
    if not pattern.match(line):
        return None
    return pattern.sub(rf"\g<1>{new_value}", line, count=1)


def _update_ini_file(
    path: Path,
    *,
    freq_hz: int | None,
    interferer_freq_hz: int | None,
    update_band: bool,
    operating_bands: dict[str, tuple[int, int]],
) -> tuple[str, str | None]:
    """Update freq and/or interferer_freq in one INI file.

    Returns (status, band_warning) where status is 'updated', 'unchanged', or 'skipped'.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_lines: list[str] = []
    target_keys_found = False
    changed = False
    band_warning: str | None = None
    target_band: str | None = None

    if update_band and freq_hz is not None:
        target_band = resolve_operating_band(freq_hz, operating_bands)
        if target_band is None:
            band_warning = (
                f"{path}: freq {freq_hz} Hz is outside FR1 NTN bands; band left unchanged"
            )

    for line in lines:
        if freq_hz is not None:
            updated_line = _replace_ini_assignment(line, "freq", str(freq_hz))
            if updated_line is not None:
                target_keys_found = True
                if updated_line != line:
                    changed = True
                new_lines.append(updated_line)
                continue

        if interferer_freq_hz is not None:
            updated_line = _replace_ini_assignment(line, "interferer_freq", str(interferer_freq_hz))
            if updated_line is not None:
                target_keys_found = True
                if updated_line != line:
                    changed = True
                new_lines.append(updated_line)
                continue

        if update_band and target_band is not None:
            updated_line = _replace_ini_assignment(line, "band", target_band)
            if updated_line is not None:
                target_keys_found = True
                if updated_line != line:
                    changed = True
                new_lines.append(updated_line)
                continue

        new_lines.append(line)

    if not target_keys_found:
        return "skipped", None

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")
        return "updated", band_warning

    return "unchanged", band_warning


def set_rf_frequency(
    *,
    freq: int | str | None = None,
    interferer_freq: int | str | None = None,
    section: str | None = None,
    nr5g_dir: Path | str | None = None,
    operating_bands: dict[str, tuple[int, int]] | None = None,
) -> SetRfFrequencyResult:
    """Update freq and/or interferer_freq in NR5G test INIs, optionally limited to one section."""
    if freq is None and interferer_freq is None:
        raise ValueError("At least one of freq or interferer_freq must be provided.")
    if interferer_freq is not None and section != "7_5":
        raise ValueError("--interferer-freq is only supported with --section 7_5.")

    freq_hz = None if freq is None else (freq if isinstance(freq, int) else parse_frequency(str(freq)))
    interferer_freq_hz = (
        None
        if interferer_freq is None
        else (
            interferer_freq
            if isinstance(interferer_freq, int)
            else parse_frequency(str(interferer_freq))
        )
    )
    bands = OPERATING_BANDS if operating_bands is None else operating_bands

    if nr5g_dir is None:
        nr5g_root = Path(__file__).resolve().parent.parent / "NR5G"
    else:
        nr5g_root = Path(nr5g_dir)

    updated: list[str] = []
    skipped: list[str] = []
    band_warnings: list[str] = []

    for ini_path in _iter_test_ini_files(nr5g_root):
        if not _matches_section(ini_path, section):
            continue

        rel_path = str(ini_path.relative_to(nr5g_root.parent))
        update_band = section == "7_5" or (section is None and "configs/7_5/" in ini_path.as_posix())
        status, band_warning = _update_ini_file(
            ini_path,
            freq_hz=freq_hz,
            interferer_freq_hz=interferer_freq_hz,
            update_band=update_band and freq_hz is not None,
            operating_bands=bands,
        )
        if band_warning is not None:
            band_warnings.append(band_warning)
        if status == "updated":
            updated.append(rel_path)
        elif status == "skipped":
            skipped.append(rel_path)

    return SetRfFrequencyResult(
        freq_hz=freq_hz,
        interferer_freq_hz=interferer_freq_hz,
        section=section,
        updated=updated,
        skipped=skipped,
        band_warnings=band_warnings,
    )


def print_summary(result: SetRfFrequencyResult) -> None:
    """Print a human-readable summary of set_rf_frequency() results."""
    scope = f"section {result.section}" if result.section else "all sections"
    print(f"Scope: {scope}")
    if result.freq_hz is not None:
        print(f"RF frequency: {result.freq_hz} Hz")
    if result.interferer_freq_hz is not None:
        print(f"Interferer frequency: {result.interferer_freq_hz} Hz")
    print(f"Updated {len(result.updated)} file(s)")
    for path in result.updated:
        print(f"  {path}")
    if result.skipped:
        print(f"Skipped {len(result.skipped)} file(s) with no matching key(s)")
        for path in result.skipped:
            print(f"  {path}")
    if result.band_warnings:
        print("Band warnings:")
        for warning in result.band_warnings:
            print(f"  {warning}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update freq in NR5G test INI files. For §7.5 configs, band is updated when "
        "freq falls in an FR1 NTN operating band. Use --section to limit which configs are changed.",
    )
    parser.add_argument(
        "--section",
        help="Config section folder name (e.g. 7_2, 7_5, 8_2_1). Omit to update all NR5G INIs.",
    )
    parser.add_argument(
        "--freq",
        type=parse_frequency,
        help="RF center frequency in Hz or with unit suffix (e.g. 1620000000, 1.62G, 1620MHz).",
    )
    parser.add_argument(
        "--interferer-freq",
        type=parse_frequency,
        help="Interferer frequency for §7.5 INIs only; requires --section 7_5.",
    )
    args = parser.parse_args()

    if args.freq is None and args.interferer_freq is None:
        parser.error("At least one of --freq or --interferer-freq is required.")
    if args.interferer_freq is not None and args.section != "7_5":
        parser.error("--interferer-freq is only supported with --section 7_5.")

    try:
        result = set_rf_frequency(
            freq=args.freq,
            interferer_freq=args.interferer_freq,
            section=args.section,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print_summary(result)


if __name__ == "__main__":
    main()

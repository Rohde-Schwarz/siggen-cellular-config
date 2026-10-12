"""Bulk-update freq in NR5G and NB-IoT test INI files."""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

from utils.helpers import parse_frequency

# FR1 NTN uplink operating bands (Hz). Matches NR5G/ts-38181-chapter7/tables_3gpp.py OPERATING_BANDS.
NR_OPERATING_BANDS: dict[str, tuple[int, int]] = {
    "n253": (1_668_000_000, 1_675_000_000),
    "n254": (1_610_000_000, 1_626_500_000),
    "n255": (1_626_500_000, 1_660_500_000),
    "n256": (1_980_000_000, 2_010_000_000),
}

# NTN E-UTRA uplink operating bands (Hz). Matches NB_IoT/ts-36181-chapter7/tables_3gpp.py OPERATING_BANDS.
NB_IOT_OPERATING_BANDS: dict[str, tuple[int, int]] = {
    "n249": (1_616_000_000, 1_626_500_000),
    "n252": (2_000_000_000, 2_020_000_000),
    "n253": (1_668_000_000, 1_675_000_000),
    "n254": (1_610_000_000, 1_626_500_000),
    "n255": (1_626_500_000, 1_660_500_000),
    "n256": (1_980_000_000, 2_010_000_000),
}

# Backward-compatible alias for tests and callers that imported OPERATING_BANDS.
OPERATING_BANDS = NR_OPERATING_BANDS


class RatIniTree(NamedTuple):
    """One RAT's chapter folders and operating-band table for §7.5 band updates."""

    label: str
    root_dir_name: str
    chapter_dirs: tuple[str, ...]
    operating_bands: dict[str, tuple[int, int]]


RAT_INI_TREES: dict[str, RatIniTree] = {
    "nr": RatIniTree(
        "NR5G",
        "NR5G",
        ("ts-38181-chapter7", "ts-38181-chapter8"),
        NR_OPERATING_BANDS,
    ),
    "nb-iot": RatIniTree(
        "NB-IoT",
        "NB_IoT",
        ("ts-36181-chapter7", "ts-36181-chapter8"),
        NB_IOT_OPERATING_BANDS,
    ),
}


class SetRfFrequencyResult(NamedTuple):
    freq_hz: int | None
    interferer_freq_hz: int | None
    section: str | None
    rat: str
    updated: list[str]
    skipped: list[str]
    band_warnings: list[str]


def resolve_operating_bands(freq_hz: int, operating_bands: dict[str, tuple[int, int]]) -> list[str]:
    """Return all operating bands that contain freq_hz (may be empty or have multiple matches)."""
    return [band for band, (lo, hi) in operating_bands.items() if lo <= freq_hz <= hi]


def _iter_test_ini_files(rat_root: Path, chapter_dirs: tuple[str, ...]):
    """Yield INI files under chapter 7 and 8 config trees only."""
    for chapter in chapter_dirs:
        chapter_root = rat_root / chapter
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
    explicit_band: str | None = None,
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
        if explicit_band is not None:
            band_range = operating_bands.get(explicit_band)
            if band_range is None:
                band_warning = (
                    f"{path}: band '{explicit_band}' is not in the operating-band table; band left unchanged"
                )
            elif not (band_range[0] <= freq_hz <= band_range[1]):
                band_warning = (
                    f"{path}: freq {freq_hz} Hz is outside band {explicit_band} range "
                    f"({band_range[0]}–{band_range[1]} Hz); band left unchanged"
                )
            else:
                target_band = explicit_band
        else:
            matching = resolve_operating_bands(freq_hz, operating_bands)
            if len(matching) == 1:
                target_band = matching[0]
            elif len(matching) > 1:
                band_warning = (
                    f"{path}: freq {freq_hz} Hz matches multiple bands ({', '.join(matching)}); "
                    "supply --band to disambiguate; band left unchanged"
                )
            else:
                band_warning = (
                    f"{path}: freq {freq_hz} Hz is outside configured operating bands; band left unchanged"
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


def _resolve_rat_keys(rat: str) -> list[str]:
    if rat == "all":
        return list(RAT_INI_TREES)
    if rat not in RAT_INI_TREES:
        raise ValueError(f"Unknown rat '{rat}'. Expected one of: all, {', '.join(RAT_INI_TREES)}.")
    return [rat]


def _process_ini_tree(
    repo_root: Path,
    tree: RatIniTree,
    rat_root_override: Path | None,
    *,
    freq_hz: int | None,
    interferer_freq_hz: int | None,
    section: str | None,
    operating_bands_override: dict[str, tuple[int, int]] | None,
    explicit_band: str | None = None,
    updated: list[str],
    skipped: list[str],
    band_warnings: list[str],
) -> None:
    if rat_root_override is None:
        rat_root = repo_root / tree.root_dir_name
    else:
        rat_root = rat_root_override

    bands = tree.operating_bands if operating_bands_override is None else operating_bands_override

    for ini_path in _iter_test_ini_files(rat_root, tree.chapter_dirs):
        if not _matches_section(ini_path, section):
            continue

        rel_path = str(ini_path.relative_to(repo_root))
        update_band = section == "7_5" or (section is None and "configs/7_5/" in ini_path.as_posix())
        status, band_warning = _update_ini_file(
            ini_path,
            freq_hz=freq_hz,
            interferer_freq_hz=interferer_freq_hz,
            update_band=update_band and freq_hz is not None,
            operating_bands=bands,
            explicit_band=explicit_band,
        )
        if band_warning is not None:
            band_warnings.append(band_warning)
        if status == "updated":
            updated.append(rel_path)
        elif status == "skipped":
            skipped.append(rel_path)


def set_rf_frequency(
    *,
    freq: int | str | None = None,
    interferer_freq: int | str | None = None,
    section: str | None = None,
    rat: str = "all",
    band: str | None = None,
    nr5g_dir: Path | str | None = None,
    nb_iot_dir: Path | str | None = None,
    operating_bands: dict[str, tuple[int, int]] | None = None,
) -> SetRfFrequencyResult:
    """Update freq and/or interferer_freq in NR5G and/or NB-IoT test INIs.

    ``rat`` is ``nr``, ``nb-iot``, or ``all`` (default). Optionally limit to one config section folder.
    Supply ``band`` to pin the operating band when the frequency lies in an ambiguous overlap region.
    """
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

    repo_root = Path(__file__).resolve().parent.parent
    rat_keys = _resolve_rat_keys(rat)

    updated: list[str] = []
    skipped: list[str] = []
    band_warnings: list[str] = []

    overrides: dict[str, Path | None] = {
        "nr": Path(nr5g_dir) if nr5g_dir is not None else None,
        "nb-iot": Path(nb_iot_dir) if nb_iot_dir is not None else None,
    }

    for rat_key in rat_keys:
        tree = RAT_INI_TREES[rat_key]
        _process_ini_tree(
            repo_root,
            tree,
            overrides[rat_key],
            freq_hz=freq_hz,
            interferer_freq_hz=interferer_freq_hz,
            section=section,
            operating_bands_override=operating_bands,
            explicit_band=band,
            updated=updated,
            skipped=skipped,
            band_warnings=band_warnings,
        )

    return SetRfFrequencyResult(
        freq_hz=freq_hz,
        interferer_freq_hz=interferer_freq_hz,
        section=section,
        rat=rat,
        updated=updated,
        skipped=skipped,
        band_warnings=band_warnings,
    )


def print_summary(result: SetRfFrequencyResult) -> None:
    """Print a human-readable summary of set_rf_frequency() results."""
    scope = f"section {result.section}" if result.section else "all sections"
    rat_label = result.rat if result.rat != "all" else "NR5G and NB-IoT"
    print(f"RAT: {rat_label}")
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
        description="Update freq in NR5G and NB-IoT test INI files. For §7.5 configs, band is "
        "updated when freq falls in the RAT operating-band table. Use --section to limit which "
        "configs are changed.",
    )
    parser.add_argument(
        "--rat",
        choices=("nr", "nb-iot", "all"),
        default="all",
        help="Which test INI trees to update (default: both NR5G and NB-IoT).",
    )
    parser.add_argument(
        "--section",
        help="Config section folder name (e.g. 7_2, 7_5, 8_2_1). Omit to update all INIs in scope.",
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
    parser.add_argument(
        "--band",
        help=(
            "Pin the operating band for §7.5 band updates (e.g. n254, n255). "
            "Required when the frequency falls in an overlapping range such as "
            "NB-IoT n249/n254 or the shared NB-IoT/NR n254/n255 boundary. "
            "The frequency is validated against the supplied band's range before "
            "any INI is written; a mismatch emits a warning and leaves the band unchanged."
        ),
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
            rat=args.rat,
            band=args.band,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print_summary(result)


if __name__ == "__main__":
    main()
    
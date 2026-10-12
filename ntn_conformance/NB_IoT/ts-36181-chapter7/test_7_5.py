"""3GPP TS 36.181 §7.5 Out-of-band Blocking

The out-of-band blocking characteristics is a measure of the receiver ability to receive a wanted
signal at its assigned channel at the TAB connector for SAN type 1-H in the presence of an unwanted
interferer out of the operating band, which is a CW signal for out-of-band blocking.

The throughput shall be ≥ 95% of the maximum throughput of the reference measurement channel, with
a wanted and an interfering signal coupled to SAN type 1-H TAB connector.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RsInstrument import RsInstrument

from tables_3gpp import OPERATING_BANDS, SAN_OOB, get_power_levels, san_table_key
from utils.helpers import parse_frequency
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw, reset_smw
from NB_IoT.utils import (
    build_base_parser,
    configure_frc,
    configure_node,
    configure_pusch,
    configure_triggers,
    get_eutra_mode,
    parse_args_or_ini,
    check_argument,
    ajust_arb_sequence_length,
    switch_on_baseband
)

# TS 36.181 Table 7.5.5-1 NOTE 2: standalone NB-IoT spurious-response exception retest, 3.75 kHz only.
SPURIOUS_RESPONSE_EXCEPTION_POWER_DBM = -46.0


def resolve_ful_edges(band: str, ful_low_hz: int | None = None, ful_high_hz: int | None = None):
    """Resolve F_UL,low and F_UL,high from band preset, with optional manual overrides."""
    try:
        band_ful_low_hz, band_ful_high_hz = OPERATING_BANDS[band]
    except KeyError as exc:
        raise ValueError(f"Unknown operating band: {band}") from exc
    return (
        band_ful_low_hz if ful_low_hz is None else ful_low_hz,
        band_ful_high_hz if ful_high_hz is None else ful_high_hz,
    )


def print_ful_edges(band: str, ful_low_hz: int, ful_high_hz: int, overridden: bool):
    """Print resolved UL operating band edges."""
    suffix = " (manual override)" if overridden else ""
    print(f"UL operating band {band}: F_UL,low={ful_low_hz} Hz, F_UL,high={ful_high_hz} Hz{suffix}")


def get_oob_range_bounds(ful_low_hz: int, ful_high_hz: int):
    """Return (range1_max_hz, range2_min_hz, range2_max_hz) for OOB blocking validation."""
    range1_max_hz = ful_low_hz - 20_000_000
    range2_min_hz = ful_high_hz + 20_000_000
    return range1_max_hz, range2_min_hz, 12_750_000_000


def validate_interferer_freq(i_freq_hz: int, ful_low_hz: int, ful_high_hz: int):
    """Return (range_label, is_valid). range_label is 'range 1', 'range 2', or None."""
    range1_max_hz, range2_min_hz, range2_max_hz = get_oob_range_bounds(ful_low_hz, ful_high_hz)
    if 1_000_000 <= i_freq_hz <= range1_max_hz:
        return "range 1", True
    if range2_min_hz <= i_freq_hz <= range2_max_hz:
        return "range 2", True
    return None, False


def print_interferer_freq_validation(i_freq_hz: int, ful_low_hz: int, ful_high_hz: int):
    """Print OOB range validation result and return whether the frequency is valid."""
    range_label, is_valid = validate_interferer_freq(i_freq_hz, ful_low_hz, ful_high_hz)
    range1_max_hz, range2_min_hz, range2_max_hz = get_oob_range_bounds(ful_low_hz, ful_high_hz)
    if is_valid and range_label == "range 1":
        print(f"Interferer frequency {i_freq_hz} Hz is in range 1 (1_000_000 Hz - {range1_max_hz} Hz)")
    elif is_valid and range_label == "range 2":
        print(f"Interferer frequency {i_freq_hz} Hz is in range 2 ({range2_min_hz} Hz - {range2_max_hz} Hz)")
    else:
        print(
            f"！！！WARNING: Interferer frequency {i_freq_hz} Hz is not in a valid OOB blocking range.",
            file=sys.stderr,
        )
    return is_valid


def configure_interferer(smw: RsInstrument, i_freq_hz: int, power_dbm: float):
    """Configure Source2 CW interfering signal (power and frequency only)."""
    print("Configuring interfering signal (Source2)...")
    write_scpi(smw, f":SOURce2:POWer:POWer {power_dbm}")
    write_scpi(smw, f":SOURce2:FREQuency:CW {i_freq_hz}")
    print(f"Interfering signal (Source2): CW configured, {power_dbm} dBm at {i_freq_hz} Hz")


def main():
    parser = build_base_parser(
        "Look up TS 36.181 section 7.5 SAN out-of-band blocking requirements for a BW/SCS combination and optionally "
        "configure an SMW.",
    )
    parser.add_argument(
        "--interferer-freq", type=parse_frequency, required=True,
        help="CW interferer frequency in Hz or with unit suffix (e.g. 1500000000, 1.5G); validated against OOB "
             "blocking ranges.",
    )

    parser.add_argument(
        "--tdd", action="store_true",
        help="Use Table 7.5.5-1 LEO TDD OOB blocking (BW 200 kHz, SCS 15 kHz only; "
             "1.4 MHz does not support TDD).",
    )

    parser.add_argument(
        "--band", choices=tuple(OPERATING_BANDS), default="n254",
        help="NB-IoT operating band for F_UL,low/F_UL,high preset (default: n254).",
    )
    parser.add_argument(
        "--ful-low", type=parse_frequency, default=None,
        help="Override lowest frequency of UL operating band in Hz or with unit suffix.",
    )
    parser.add_argument(
        "--ful-high", type=parse_frequency, default=None,
        help="Override highest frequency of UL operating band in Hz or with unit suffix.",
    )
    parser.add_argument(
        "--spurious-response-exception", action="store_true", default=False,
        help="Table 7.5.5-1 NOTE 2: retest a spurious-response exception frequency at -46 dBm "
             "(standalone NB-IoT, SCS 3.75 kHz only).",
    )
    args = parse_args_or_ini(parser)

    ful_low = getattr(args, "ful_low", None)
    ful_high = getattr(args, "ful_high", None)
    ful_edges_overridden = ful_low is not None or ful_high is not None
    ful_low_hz, ful_high_hz = resolve_ful_edges(args.band, ful_low, ful_high)
    print_ful_edges(args.band, ful_low_hz, ful_high_hz, ful_edges_overridden)

    if ful_low_hz >= ful_high_hz:
        print("Error: F_UL,low must be less than F_UL,high.", file=sys.stderr)
        sys.exit(1)

    print_interferer_freq_validation(args.interferer_freq, ful_low_hz, ful_high_hz)

    spurious_response_exception = getattr(args, "spurious_response_exception", False)
    if spurious_response_exception and args.scs != 3.75:
        print(
            "Error: --spurious-response-exception is only defined for SCS 3.75 kHz "
            "(TS 36.181 Table 7.5.5-1 NOTE 2).",
            file=sys.stderr,
        )
        sys.exit(1)
    if spurious_response_exception:
        print(
            "Spurious-response exception retest: interferer "
            f"{SPURIOUS_RESPONSE_EXCEPTION_POWER_DBM} dBm (Table 7.5.5-1 NOTE 2)"
        )

    if not args.ip:
        return

    if args.san_class is None:
        print("Error: --class is required when --ip is set.", file=sys.stderr)
        sys.exit(1)

    check_argument(args)

    try:
        table_key = san_table_key(args.san_class, args.tdd, args.bw, args.scs)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    test_config = get_power_levels(SAN_OOB[table_key], args.bw, args.scs)
    interferer_power_dbm = (
        SPURIOUS_RESPONSE_EXCEPTION_POWER_DBM
        if spurious_response_exception
        else test_config.interfering_power_dbm
    )

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        reset_smw(smw)
        configure_triggers(smw)
        mode = get_eutra_mode(args.bw)
        configure_node(smw, args.bw, args.scs, mode, args.tdd, args.ue_id, cell_id=args.cell_id)
        configure_pusch(smw, args.bw, args.scs, mode, args.tdd)
        configure_frc(smw, test_config.ref_meas_channel, mode)

        if mode == "IOT":
            ajust_arb_sequence_length(smw)

        configure_rf(smw, test_config.power_dbm, args.freq, source=1)
        switch_on_baseband(smw)
        configure_interferer(smw, args.interferer_freq, interferer_power_dbm)

        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

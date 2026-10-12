"""3GPP TS 38.181 §7.5 Out-of-band Blocking

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

from tables_3gpp import (
    OPERATING_BANDS, SAT_GEO_OOB, SAT_LEO_OOB, apply_nb_iot_inband_channel, get_power_levels,
)
from utils.helpers import parse_frequency
from NR5G.utils import build_base_parser, configure_frc, configure_node, configure_triggers
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw


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
            f"WARNING: Interferer frequency {i_freq_hz} Hz is not in a valid OOB blocking range.",
            file=sys.stderr,
        )
    return is_valid


def configure_interferer(smw: RsInstrument, i_freq_hz: int):
    """Configure Source2 CW interfering signal (power and frequency only)."""
    print("Configuring interfering signal (Source2)...")
    write_scpi(smw, ":SOURce2:POWer:POWer -44.0")
    write_scpi(smw, f":SOURce2:FREQuency:CW {i_freq_hz}")
    print(f"Interfering signal (Source2): CW configured, -44.0 dBm at {i_freq_hz} Hz")


def main():
    parser = build_base_parser(
        "Look up TS 38.181 section 7.5 SAN out-of-band blocking requirements for a BW/SCS combination and optionally "
        "configure an SMW.",
    )
    parser.add_argument(
        "--interferer-freq", type=parse_frequency, required=True,
        help="CW interferer frequency in Hz or with unit suffix (e.g. 1500000000, 1.5G); validated against OOB "
             "blocking ranges.",
    )
    parser.add_argument(
        "--band", choices=tuple(OPERATING_BANDS), default="n254",
        help="NR operating band for F_UL,low/F_UL,high preset (default: n254).",
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
        "--nb-iot-inband", action="store_true",
        help="Use G-FR1-NTN-A1-10 / A1-11 reference channels where applicable (SAN supports NB-IoT in-band operation).",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    ful_low = getattr(args, "ful_low", None)
    ful_high = getattr(args, "ful_high", None)
    ful_edges_overridden = ful_low is not None or ful_high is not None
    ful_low_hz, ful_high_hz = resolve_ful_edges(args.band, ful_low, ful_high)
    print_ful_edges(args.band, ful_low_hz, ful_high_hz, ful_edges_overridden)

    if ful_low_hz >= ful_high_hz:
        print("Error: F_UL,low must be less than F_UL,high.", file=sys.stderr)
        sys.exit(1)

    print_interferer_freq_validation(args.interferer_freq, ful_low_hz, ful_high_hz)

    if not args.ip:
        return

    if args.san_class is None:
        print("Error: --class is required when --ip is set.", file=sys.stderr)
        sys.exit(1)

    test_config = get_power_levels(
        SAT_LEO_OOB if args.san_class == "leo" else SAT_GEO_OOB,
        args.bw,
        args.scs,
    )
    test_config = apply_nb_iot_inband_channel(test_config, args.bw, args.scs, args.nb_iot_inband)

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_triggers(smw)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id, source=1)
        configure_frc(smw, test_config.ref_meas_channel, source=1, ue_id=args.ue_id)
        configure_rf(smw, test_config.power_dbm, args.freq, source=1)
        configure_interferer(smw, args.interferer_freq)
        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

"""3GPP TS 38.181 §8.4.1 PRACH false alarm probability and missed detection

Look up required SNR from tables 8.4.1.5-1 (1.25 kHz SCS), 8.4.1.5-2 (15 kHz SCS),
and 8.4.1.5-3 (30 kHz SCS) for the given test parameters.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import FADING_PROFILES, PRACH_PERF_REQ_8_4_1, get_prach_test_config
from NR5G.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_fading, configure_node,
    configure_output, configure_prach, configure_triggers, configure_ueid,
)
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw


def main():
    parser = build_base_parser(
        "Look up TS 38.181 §8.4.1 PRACH missed detection / false alarm requirements.",
        include_class=False,
        require_num_rx=True,
    )
    parser.add_argument(
        "--propagation",
        choices=("AWGN", "NTN_TDLA100_200_SISO", "NTN_TDLA100_200_LOW"),
        required=True,
        help="Propagation condition: AWGN, NTN_TDLA100_200_SISO (1 RX), or NTN_TDLA100_200_LOW (2 RX).",
    )
    parser.add_argument(
        "--prach-scs", dest="prach_scs", type=float, choices=(1.25, 15.0, 30.0), required=True,
        help="PRACH subcarrier spacing in kHz (1.25, 15, or 30).",
    )
    parser.add_argument(
        "--burst-format", dest="burst_format", choices=("0", "2", "B4", "C2"), required=True,
        help="PRACH burst format (0 or 2 for 1.25 kHz SCS; B4 or C2 for 15/30 kHz SCS).",
    )
    parser.add_argument(
        "--test-mode", dest="test_mode", default="detection_rate",
        choices=("detection_rate", "false_detection_rate"),
        help="Test mode: detection_rate (default) or false_detection_rate (noise only).",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
        # INI loader coerces numeric strings to int; restore expected types.
        args.prach_scs = float(args.prach_scs)
        args.burst_format = str(args.burst_format)
    else:
        args = parser.parse_args()

    test_config = get_prach_test_config(
        PRACH_PERF_REQ_8_4_1,
        args.scs, args.prach_scs, args.bw, args.num_rx, args.propagation, args.burst_format,
    )

    print(f"Test mode: {args.test_mode}")
    print("--------------------------------")

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_advance_mode(smw, args.num_rx)
        configure_triggers(smw, sources=1)
        if args.test_mode != "false_detection_rate":
            configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id)
            configure_ueid(smw, args.ue_id)
            configure_prach(smw, args.burst_format, test_config.freq_offset_hz, args.prach_scs)
            if args.propagation != "AWGN":
                configure_fading(smw, args.propagation, FADING_PROFILES[args.propagation], args.num_rx)
        configure_awgn(
            smw, test_config.snr_db, test_config.awgn_bw, args.num_rx,
            noise_only_mode=(args.test_mode == "false_detection_rate"),
            awgn_power_dbm=test_config.awgn_power_dbm,
        )
        rf_power_dbm = (
            test_config.awgn_power_dbm
            if args.test_mode == "false_detection_rate"
            else round(test_config.awgn_power_dbm + test_config.snr_db, 2)
        )
        for source in range(1, args.num_rx + 1):
            configure_rf(smw, rf_power_dbm, args.freq, source=source)
        configure_output(smw, args.num_rx)
        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

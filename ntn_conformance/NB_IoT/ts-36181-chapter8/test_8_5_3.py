"""3GPP TS 36.181 §8.5.3 Performance requirements for NPRACH

The performance requirement of NPRACH for preamble detection is determined by two parameters:
The total probability of false detection of the preamble (Pfa) and the probability of detection of the preamble (Pd).
The performance is measured for the required SNR
-	at probability of Pd which shall not be smaller than 99% and
-	at probability of Pfa which shall not be larger than 0.1%.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import (FADING_PROFILES, NPRACH_PERF_REQ_FDD, NPRACH_PERF_REQ_TDD, PrachTestConfig,
                         get_prach_test_config)
from NB_IoT.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_fading, configure_node,
    configure_output, configure_prach, configure_triggers, configure_trigger_delay, switch_on_baseband
)
from NB_IoT.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw, reset_smw

# unit is MHz
AWGN_BW = 0.18
# unit is dBm
AWGN_POWER_LEVEL = -100.5


def main():
    parser = build_base_parser(
        "Look up TS 36.181 §8.5.3 Performance requirements for NPRACH.",
        include_class=False,
        include_bw=False,
        include_scs=False,
        require_num_rx=False,
    )

    parser.add_argument(
        "--tdd", action="store_true",
        help="NPRACH missed detection test requirements for TDD.",
    )

    parser.add_argument(
        "--repetition-num",
        type=int, choices=(4, 8, 16), dest="repetition_num",
        default=8,
        help="NPRACH Repetition number.",
    )

    parser.add_argument(
        "--propagation",
        choices=("NTN-TDLA100-1", "NTN-TDLC5-1"),
        default="NTN-TDLA100-1",
        help="Propagation condition: NTN-TDLA100-1, or NTN-TDLC5-1.",
    )

    parser.add_argument(
        "--preamble-format", dest="preamble_format", type=int, choices=(0, 1), default=0,
        help="Preamble format  (0 or 1).",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
        # Fill CLI defaults for keys omitted from the INI (e.g. tdd → False).
        args = parser.parse_args([], namespace=args)
        # INI loader coerces numeric strings to int; restore expected types.
        args.preamble_format = int(args.preamble_format)
    else:
        args = parser.parse_args()

    test_config = get_prach_test_config(
        NPRACH_PERF_REQ_TDD if args.tdd else NPRACH_PERF_REQ_FDD,
        args.num_rx, args.repetition_num, args.preamble_format, args.propagation
    )

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        reset_smw(smw)
        configure_advance_mode(smw, args.num_rx)
        configure_triggers(smw, sources=1)
        configure_trigger_delay(smw, sources=1, delay=test_config.time_error_tolerance_us)
        
        # Narrowband physical layer cell identity is 0.
        configure_node(smw, bw=0.2, scs=15, mode="IOT", tdd=args.tdd, ue_id=args.ue_id, cell_id=0)

        configure_prach(smw, args.tdd, args.preamble_format, args.repetition_num, freq_offset_hz=200)

        configure_fading(smw, args.propagation, FADING_PROFILES[args.propagation], args.num_rx)

        switch_on_baseband(smw, sources=1)

        cn_db = round(test_config.snr_db + test_config.delta_power, 2)
        configure_awgn(
            smw, cn_db, AWGN_BW, args.num_rx,
            noise_only_mode=False,
            awgn_power_dbm=AWGN_POWER_LEVEL,
        )

        rf_power_dbm = round(AWGN_POWER_LEVEL + cn_db, 2)
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

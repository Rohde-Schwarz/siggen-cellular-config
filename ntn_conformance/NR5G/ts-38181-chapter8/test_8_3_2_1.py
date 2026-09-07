"""3GPP TS 38.181 §8.3.2.1 PUCCH Format 1 - NACK to ACK detection

Look up required SNR from tables 8.3.2.1.5-1 and 8.3.2.1.5-2 for the given test parameters.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import FADING_PROFILES, PUCCH_PERF_REQ_8_3_2_1, get_pucch_test_config
from NR5G.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_fading, configure_node,
    configure_output, configure_pucch, configure_triggers, configure_ueid,
)
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw


def main():
    parser = build_base_parser(
        "Look up TS 38.181 §8.3.2.1 PUCCH Format 1 requirements.",
        include_class=False,
        require_num_rx=True,
    )
    parser.add_argument(
        "--propagation", choices=tuple(FADING_PROFILES), required=True,
        help="Propagation condition: NTN_TDLA100_200_LOW or NTN_TDLC5_200_LOW.",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    test_config = get_pucch_test_config(
        PUCCH_PERF_REQ_8_3_2_1,
        args.bw, args.scs, args.num_rx, args.propagation,
    )

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_advance_mode(smw, args.num_rx)
        configure_triggers(smw, sources=1)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id)
        configure_ueid(smw, args.ue_id)
        configure_pucch(
            smw, fmt=1, bw=args.bw, scs=args.scs, ack_pattern="#H0,2",
        )
        configure_fading(smw, args.propagation, FADING_PROFILES[args.propagation], args.num_rx)
        configure_awgn(
            smw, test_config.snr_db, test_config.awgn_bw, args.num_rx,
            awgn_power_dbm=test_config.awgn_power_dbm,
        )
        for source in range(1, args.num_rx + 1):
            configure_rf(smw, round(test_config.awgn_power_dbm + test_config.snr_db, 2), args.freq, source=source)
        configure_output(smw, args.num_rx)
        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

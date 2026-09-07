"""3GPP TS 38.181 §8.2.5 Performance requirements for PUSCH with DMRS bundling

Look up FRC and required SNR from tables 8.2.5.5-1 through 8.2.5.5-4 for the given test
parameters.
"""
# Similar to 8.2.4 in terms of PHY configuration

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import FADING_PROFILES, PUSCH_PERF_REQ_8_2_5, get_pusch_test_config
from NR5G.utils import (
    NUM_RBS,
    build_base_parser, configure_advance_mode, configure_awgn, configure_fading, configure_frc,
    configure_harq, configure_node, configure_output, configure_repTypeA_dmrsBundling,
    configure_triggers,
)
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw


def main():
    parser = build_base_parser(
        "Look up TS 38.181 §8.2.5 PUSCH with DMRS bundling requirements.",
        include_class=False,
        require_num_rx=True,
    )
    parser.add_argument(
        "--propagation", choices=tuple(FADING_PROFILES), required=True,
        help="Propagation condition: NTN_TDLA100_200_LOW or NTN_TDLC5_200_LOW.",
    )
    parser.add_argument(
        "--pusch-type", choices=("A", "B"), required=True,
        help="PUSCH mapping type (Type A or Type B).",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    test_config = get_pusch_test_config(
        PUSCH_PERF_REQ_8_2_5,
        args.pusch_type, args.bw, args.scs, args.num_rx, args.propagation,
    )

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_advance_mode(smw, args.num_rx)
        configure_triggers(smw)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id)

        num_rbs = NUM_RBS[(args.bw, args.scs)]
        rb_offset = (num_rbs - 6 + 1) // 2

        configure_frc(smw, test_config.frc, map_type=args.pusch_type, ue_id=args.ue_id, rb_offset=rb_offset)
        configure_harq(smw)
        configure_repTypeA_dmrsBundling(smw, args.scs)
        configure_fading(smw, args.propagation, FADING_PROFILES[args.propagation], args.num_rx)
        configure_awgn(smw, test_config.snr_db, test_config.awgn_bw, args.num_rx)
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

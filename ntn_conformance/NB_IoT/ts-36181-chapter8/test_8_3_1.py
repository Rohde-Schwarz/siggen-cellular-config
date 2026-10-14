"""3GPP TS 36.181 §8.3.1 ACK missed detection for PUCCH format 1a transmission
on single antenna port for coverage enhancement.

The performance requirement of PUCCH for ACK missed detection is determined by two parameters:
The probability of false detection of the ACK and the probability of detection of ACK.
The performance is measured for the required SNR
-	at probability of detection which shall not be smaller than 99% and
-	at probability of false detection of the ACK which shall not be larger than 1%.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import (FADING_PROFILES, PUCCH_FORMAT_1A_PERF_REQ_FDD,
                         get_pucch_test_config)
from NB_IoT.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_emtc_pucch,
    configure_fading, configure_output, configure_triggers,
    switch_on_baseband, parse_args_or_ini,
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw, reset_smw

# Table 8.3.1.4.2-1
AWGN_BW = 1.08
AWGN_POWER_LEVEL = -89.7


def main():
    parser = build_base_parser(
        "Look up TS 36.181 §8.3.1 ACK missed detection for PUCCH format 1a.",
        include_class=False,
        include_bw=False,
        include_scs=False,
        require_num_rx=True,
    )

    parser.add_argument(
        "--repetition-num",
        type=int, dest="repetition_num",
        default=8,
        help="PUCCH repetition number: 8 (Table 8.3.1.2.1-1).",
    )

    parser.add_argument(
        "--propagation",
        default="NTN-TDLA100-5",
        help="Propagation condition: NTN-TDLA100-5 (Table 8.3.1.2.1-1).",
    )

    args = parse_args_or_ini(parser)

    test_config = get_pucch_test_config(
        PUCCH_FORMAT_1A_PERF_REQ_FDD,
        args.num_rx, args.repetition_num, args.propagation,
    )

    print("--------------------------------")

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        reset_smw(smw)
        configure_advance_mode(smw, args.num_rx)
        configure_triggers(smw, sources=1)

        configure_emtc_pucch(
            smw, args.repetition_num, test_config.freq_offset_hz, test_config.timing_offset,
            ue_id=args.ue_id, cell_id=args.cell_id,
        )

        configure_fading(smw, args.propagation, FADING_PROFILES[args.propagation], args.num_rx)

        switch_on_baseband(smw, sources=1)

        configure_awgn(
            smw, test_config.snr_db, AWGN_BW, args.num_rx,
            noise_only_mode=False,
            awgn_power_dbm=AWGN_POWER_LEVEL,
        )

        rf_power_dbm = round(AWGN_POWER_LEVEL + test_config.snr_db, 2)

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

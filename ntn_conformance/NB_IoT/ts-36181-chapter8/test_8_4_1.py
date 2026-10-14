"""3GPP TS 36.181 §8.4.1 PRACH — false alarm probability and missed detection

The performance requirement of PRACH for preamble detection is determined by two parameters:
the total probability of false detection of the preamble (Pfa) and the probability of detection
of the preamble (Pd).
The performance is measured for the required SNR
- at probability of Pd which shall not be smaller than 99% and
- at probability of Pfa which shall not be larger than 0.1%.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import FADING_PROFILES, EMTC_PRACH_PERF_REQ_FDD, get_prach_test_config
from NB_IoT.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_emtc_prach,
    configure_fading, configure_output, configure_triggers, configure_trigger_delay,
    switch_on_baseband, parse_args_or_ini,
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw, reset_smw

# Table 8.4.1.4.2-1
AWGN_BW = 1.08
AWGN_POWER_LEVEL = -89.7


def main():
    parser = build_base_parser(
        "Look up TS 36.181 §8.4.1 PRACH false alarm probability and missed detection.",
        include_class=False,
        include_bw=False,
        include_scs=False,
        require_num_rx=True,
    )

    parser.add_argument(
        "--burst-format", dest="burst_format", type=int, choices=(0, 1, 2, 3),
        default=0,
        help="PRACH burst format: 0, 1, 2, or 3 (Table 8.4.1.5-1).",
    )

    parser.add_argument(
        "--repetition-num",
        type=int, choices=(8, 16), dest="repetition_num",
        default=8,
        help="PRACH repetition number: 8 (burst formats 0/1) or 16 (burst formats 2/3).",
    )

    parser.add_argument(
        "--propagation",
        choices=("NTN-TDLA100-5",),
        default="NTN-TDLA100-5",
        help="Propagation condition: NTN-TDLA100-5 (Table 8.4.1.5-1).",
    )

    args = parse_args_or_ini(parser)
    args.burst_format = int(args.burst_format)

    test_config = get_prach_test_config(
        EMTC_PRACH_PERF_REQ_FDD,
        args.num_rx, args.repetition_num, args.burst_format, args.propagation,
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
        configure_trigger_delay(smw, sources=1, delay=test_config.time_error_tolerance_us)

        configure_emtc_prach(
            smw, args.burst_format, args.repetition_num, freq_offset_hz=270,
            timing_offset=test_config.time_error_tolerance_us,
            ue_id=args.ue_id, cell_id=args.cell_id,
        )

        configure_fading(
            smw, args.propagation, FADING_PROFILES[args.propagation], args.num_rx,
        )

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

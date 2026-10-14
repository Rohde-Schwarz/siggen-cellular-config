"""3GPP TS 36.181 §8.5.2 ACK missed detection for NPUSCH format 2

The performance requirement of NPUSCH format 2 for ACK missed detection is determined by two parameters:
The probability of false detection of the ACK and the probability of detection of ACK.
The performance is measured for the required SNR
-	at probability of detection which shall not be smaller than 99% and
-	at probability of false detection of the ACK which shall not be larger than 1%.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import (FADING_PROFILES, NPUSCH_FORMAT2_PERF_REQ_FDD, NPUSCH_FORMAT2_PERF_REQ_TDD,
                         get_pusch_test_config)
from NB_IoT.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_fading, configure_node, configure_pusch,
    configure_npusch_signal_pattern, set_arb_length_signal_pattern, configure_output, configure_triggers,
    switch_on_baseband, parse_args_or_ini,
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw, reset_smw

# unit is MHz
AWGN_BW = 0.18
# unit is dBm
AWGN_POWER_LEVEL = -100.5


def main():
    parser = build_base_parser(
        "Look up TS 36.181 §8.5.2 ACK missed detection for NPUSCH format 2.",
        include_class=False,
        include_bw=False,
        require_num_rx=True,
    )

    parser.add_argument(
        "--tdd", action="store_true",
        help="NPUSCH format 2 ACK missed detection test requirements for TDD.",
    )

    parser.add_argument(
        "--repetition-num",
        type=int, choices=(4, 16), dest="repetition_num",
        default=16,
        help="NPUSCH format 2 repetition number: FDD 16, TDD 4.",
    )

    parser.add_argument(
        "--propagation",
        default="NTN-TDLA100-1",
        help="Propagation condition: NTN-TDLA100-1.",
    )

    args = parse_args_or_ini(parser)
    # INI loader coerces numeric strings to int; restore expected types.
    args.scs = float(args.scs)

    test_config = get_pusch_test_config(
        NPUSCH_FORMAT2_PERF_REQ_TDD if args.tdd else NPUSCH_FORMAT2_PERF_REQ_FDD,
        args.num_rx, args.repetition_num, args.scs, "NTN-TDLA100-1")

    print("--------------------------------")

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        reset_smw(smw)
        configure_advance_mode(smw, args.num_rx)
        configure_triggers(smw, sources=1)

        # NPUSCH Format 2 no need to do  Channel Coding / Scrambling, so pusch_coding_on is False
        configure_node(
            smw, bw=0.2, scs=args.scs, mode="IOT",
            tdd=args.tdd, ue_id=args.ue_id, cell_id=args.cell_id,
        )

        configure_pusch(smw, 0.2, args.scs, mode="IOT", pusch_coding_on=False)

        npusch_format = 2
        time_segment_ms = configure_npusch_signal_pattern(
            smw, npusch_format, test_config.freq_offset_hz, test_config.timing_offset,
            args.tdd, args.repetition_num,
        )

        set_arb_length_signal_pattern(smw, args.tdd, time_segment_ms)
        configure_fading(smw, "NTN-TDLA100-1", FADING_PROFILES["NTN-TDLA100-1"], args.num_rx)

        switch_on_baseband(smw, sources=1)

        cn_db = round(test_config.snr_db + test_config.delta_power, 2)
        configure_awgn(
        smw, cn_db, AWGN_BW, args.num_rx,
        noise_only_mode=False,
        awgn_power_dbm=AWGN_POWER_LEVEL)

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

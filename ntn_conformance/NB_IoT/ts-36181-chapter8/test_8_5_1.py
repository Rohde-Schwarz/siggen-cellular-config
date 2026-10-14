"""3GPP TS 36.181 §8.5.1 Performance requirements for NPUSCH format 1

The performance requirement of NPUSCH format 1 is determined by a minimum required throughput for a given SNR.
The required throughput is expressed as a fraction of maximum throughput for the FRCs listed in annex A.
The performance requirements assume HARQ re-transmissions.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import (FADING_PROFILES, NPUSCH_FORMAT1_PERF_REQ_FDD, NPUSCH_FORMAT1_PERF_REQ_TDD,
                         NPUSCH_FORMAT1_PERF_REQ_OCC_FDD, get_pusch_test_config)
from NB_IoT.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_fading, configure_node, configure_pusch,
    configure_npusch_signal_pattern, set_arb_length_signal_pattern, configure_output, configure_triggers,
    configure_harq, configure_frc, switch_on_baseband,
    parse_args_or_ini,
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw, reset_smw

# unit is MHz
AWGN_BW = 0.18
# unit is dBm
AWGN_POWER_LEVEL = -100.5


def main():
    parser = build_base_parser(
        "Look up TS 36.181 §8.5.1 performance requirements for NPUSCH format 1.",
        include_class=False,
        include_bw=False,
        require_num_rx=True,
    )

    parser.add_argument(
        "--tdd", action="store_true",
        help="NPUSCH format 1 performance test requirements for TDD (Table 8.5.1.5-3).",
    )

    parser.add_argument(
        "--repetition-num",
        type=int, choices=(2, 4, 8, 16), dest="repetition_num",
        default=16,
        help="NPUSCH format 1 repetition number: FDD 4 (3.75 kHz) / 16 (15 kHz), "
             "TDD 4, OCC 2 (3.75 kHz) / 8 (15 kHz).",
    )

    parser.add_argument(
        "--propagation",
        choices=("NTN-TDLA100-1", "NTN-TDLC5-1"),
        default="NTN-TDLA100-1",
        help="Propagation condition: NTN-TDLA100-1, or NTN-TDLC5-1.",
    )

    parser.add_argument(
        "--occ-sequence-index", dest="occ_sequence_index",
        type=int, choices=(0, 1), default=None,
        help="FDD length-2 OCC sequence index (0 or 1). "
             "3.75 kHz symbol-level (Table 8.5.1.5-4) or 15 kHz slot-level (Table 8.5.1.5-5).",
    )

    args = parse_args_or_ini(parser)
    if args.tdd and args.occ_sequence_index is not None:
        parser.error(
            "Length-2 OCC is only defined for FDD "
            "(Tables 8.5.1.5-4 / 8.5.1.5-5); "
            "do not combine --tdd with --occ-sequence-index"
        )

    # INI loader coerces numeric strings to int; restore expected types.
    args.scs = float(args.scs)
    if args.occ_sequence_index is not None:
        args.occ_sequence_index = int(args.occ_sequence_index)

    test_config = get_pusch_test_config(
        NPUSCH_FORMAT1_PERF_REQ_TDD if args.tdd
        else NPUSCH_FORMAT1_PERF_REQ_OCC_FDD if args.occ_sequence_index is not None
        else NPUSCH_FORMAT1_PERF_REQ_FDD,
        args.num_rx, args.repetition_num, args.scs, args.propagation,
        occ_sequence_index=args.occ_sequence_index,
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

        configure_node(
            smw, bw=0.2, scs=args.scs, mode="IOT",
            tdd=args.tdd, ue_id=args.ue_id, cell_id=args.cell_id,
        )

        configure_pusch(smw, 0.2, args.scs, mode="IOT")
        configure_frc(smw, test_config.frc, mode="IOT", repetition_num=args.repetition_num)

        npusch_format = 1
        time_segment_ms = configure_npusch_signal_pattern(
            smw, npusch_format, test_config.freq_offset_hz, test_config.timing_offset,
            args.tdd, args.repetition_num, frc_on=True, occ_sequence_index=args.occ_sequence_index)

        set_arb_length_signal_pattern(smw, args.tdd, time_segment_ms)
        if not args.tdd:
            configure_harq(smw)

        configure_fading(smw, args.propagation, FADING_PROFILES[args.propagation], args.num_rx)

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

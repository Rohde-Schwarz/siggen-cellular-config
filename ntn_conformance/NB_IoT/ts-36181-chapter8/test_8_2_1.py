"""3GPP TS 36.181 §8.2.1 Performance requirements of PUSCH in multipath fading
propagation conditions transmission on single antenna port for coverage enhancement

The performance requirement of PUSCH is determined by a minimum required throughput for a given SNR.
The required throughput is expressed as a fraction of maximum throughput for the FRCs listed in annex A.
The performance requirements assume HARQ re-transmissions.

The tests for CEModeA defined in clause 8.2.1 are applicable only to the space access nodes supporting
coverage enhancement configured with CEModeA. The tests for CEModeB defined in clause 8.2.1 are
applicable only to the space access nodes supporting coverage enhancement configured with CEModeB.

The throughput measured according to clause 8.2.1.4.2 shall not be below the limits for the SNR levels
specified in table 8.2.1.5-1 for CEMode A tests and not be below the limits for the SNR levels specified
in table 8.2.1.5-2 for CEMode B tests.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import FADING_PROFILES, PUSCH_PERF_REQ_FDD, get_pusch_test_config
from NB_IoT.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_emtc_pusch,
    configure_fading, configure_node, configure_output, configure_triggers, configure_harq,
    switch_on_baseband, parse_args_or_ini,
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw, reset_smw

# Table 8.2.1.4.2-1
AWGN_BW = 1.08
AWGN_POWER_LEVEL = -92.7

# Table 8.2.1.5-1 is CEMode A (8 repetitions); Table 8.2.1.5-2 is CEMode B (256).
CE_MODE_REPETITION = {"A": 8, "B": 256}
REPETITION_CE_MODE = {repetition: mode for mode, repetition in CE_MODE_REPETITION.items()}


def resolve_ce_mode(parser, args) -> None:
    """Link --ce-mode and --repetition-num.

    Either flag selects the test. When both are given they must agree.
    When neither is given, CEMode A (8 repetitions) is used.
    """
    if getattr(args, "ce_mode", None) is not None:
        args.ce_mode = str(args.ce_mode).strip().upper()
        if args.ce_mode not in CE_MODE_REPETITION:
            parser.error(f"--ce-mode must be A or B, got {args.ce_mode!r}")

    if args.repetition_num is not None and args.repetition_num not in REPETITION_CE_MODE:
        parser.error(
            "--repetition-num must be 8 (CEMode A) or 256 (CEMode B), "
            f"got {args.repetition_num}"
        )

    if args.ce_mode is not None and args.repetition_num is not None:
        expected = CE_MODE_REPETITION[args.ce_mode]
        if args.repetition_num != expected:
            parser.error(
                f"--ce-mode {args.ce_mode} requires --repetition-num {expected}, "
                f"got {args.repetition_num}"
            )
    elif args.ce_mode is not None:
        args.repetition_num = CE_MODE_REPETITION[args.ce_mode]
    elif args.repetition_num is not None:
        args.ce_mode = REPETITION_CE_MODE[args.repetition_num]
    else:
        args.ce_mode = "A"
        args.repetition_num = CE_MODE_REPETITION["A"]


def main():
    parser = build_base_parser(
        "Look up TS 36.181 §8.2.1 PUSCH performance requirements for coverage enhancement.",
        include_class=False,
        include_bw=False,
        require_num_rx=True,
    )

    parser.add_argument(
        "--ce-mode",
        choices=("A", "B"),
        type=str.upper,
        dest="ce_mode",
        help="Coverage enhancement mode. A selects 8 PUSCH repetitions "
             "(Table 8.2.1.5-1); B selects 256 (Table 8.2.1.5-2). "
             "Sets --repetition-num when that flag is omitted. "
             "Default is A when neither --ce-mode nor --repetition-num is given.",
    )
    parser.add_argument(
        "--repetition-num",
        type=int, choices=(8, 256), dest="repetition_num",
        help="PUSCH repetition number: 8 (CEMode A) or 256 (CEMode B). "
             "Must match --ce-mode when both are given. "
             "Sets --ce-mode when that flag is omitted.",
    )

    parser.add_argument(
        "--propagation",
        choices=("NTN-TDLA100-5", "NTN-TDLC5-5"),
        default="NTN-TDLA100-5",
        help="Propagation condition: NTN-TDLA100-5, or NTN-TDLC5-5.",
    )

    args = parse_args_or_ini(parser)
    resolve_ce_mode(parser, args)
    args.scs = float(args.scs)

    test_config = get_pusch_test_config(
        PUSCH_PERF_REQ_FDD,
        args.num_rx, args.repetition_num, args.scs, args.propagation,
        ce_mode=args.ce_mode,
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

        configure_emtc_pusch(
            smw, test_config.frc, args.repetition_num, test_config.freq_offset_hz, test_config.timing_offset,
            ue_id=args.ue_id, cell_id=args.cell_id,
        )

        configure_harq(smw)
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

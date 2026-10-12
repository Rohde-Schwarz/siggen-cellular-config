"""3GPP TS 36.181 §7.2 Reference sensitivity level

The reference sensitivity power level PREFSENS is the minimum mean power received at the TAB
connector for SAN type 1-H at which a throughput requirement shall be met for a specified
reference measurement channel.
The throughput shall be ≥ 95% of the maximum throughput of the reference measurement channel
as specified in annex A.1 with parameters specified in table 7.2.5-1 and 7.2.5-2 for SAN type
1-H in all operating band in NB-IoT NTN.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# pylint: disable=wrong-import-position
from tables_3gpp import SAN_REF_SENS_LEVELS, get_power_levels, san_table_key
from NB_IoT.utils import (
    build_base_parser,
    check_argument,
    get_eutra_mode,
    configure_frc,
    configure_node,
    configure_pusch,
    configure_triggers,
    ajust_arb_sequence_length,
    parse_args_or_ini,
    switch_on_baseband
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw, reset_smw


def main():
    """Configure the SMW for TS 36.181 §7.2 reference sensitivity."""
    parser = build_base_parser(
        "Look up TS 36.181 table 7.2.5 SAN reference sensitivity for a BW/SCS combination.",
    )
    parser.add_argument(
        "--tdd", action="store_true",
        help="Use FRC A14-3 reference channels where applicable for TDD frequency bands "
             "(0.2 MHz / 15 kHz only; 1.4 MHz does not support TDD).",
    )
    args = parse_args_or_ini(parser)

    check_argument(args)

    try:
        table_key = san_table_key(args.san_class, args.tdd, args.bw, args.scs)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not args.ip:
        return

    test_config = get_power_levels(SAN_REF_SENS_LEVELS[table_key], args.bw, args.scs)

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        reset_smw(smw)
        configure_triggers(smw)
        mode = get_eutra_mode(args.bw)
        configure_node(smw, args.bw, args.scs, mode, args.tdd, args.ue_id, cell_id=args.cell_id)
        configure_pusch(smw, args.bw, args.scs, mode, args.tdd)
        configure_frc(smw, test_config.ref_meas_channel, mode)

        if mode == "IOT":
            ajust_arb_sequence_length(smw)

        switch_on_baseband(smw)
        configure_rf(smw, test_config.power_dbm, args.freq)

        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

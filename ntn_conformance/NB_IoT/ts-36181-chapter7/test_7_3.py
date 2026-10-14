"""3GPP TS 36.181 §7.3 Dynamic range

The dynamic range is specified as a measure of the capability of the receiver to receive a wanted
signal in the presence of an interfering signal at the TAB connector for SAN type 1-H inside the
received SAN channel bandwidth. In this condition, a throughput requirement shall be met for a
specified reference measurement channel. The interfering signal for the dynamic range requirement
is an AWGN signal.
The throughput shall be ≥ 95% of the maximum throughput of the reference measurement channel
as specified in annex A.2 or annex A.15 with parameters specified in table 7.3.5-1, 7.3.5-2,
7.3.5-3 and 7.3.5-4 for SAN type 1-H in all operating bands in NB-IoT NTN.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RsInstrument import RsInstrument

# pylint: disable=wrong-import-position
from tables_3gpp import SAN_DYNAMIC_RANGE, get_power_levels, TestConfig, AWGN_BANDWIDTH, san_table_key
from NB_IoT.utils import (
    build_base_parser,
    get_eutra_mode,
    configure_frc,
    configure_node,
    configure_pusch,
    configure_triggers,

    ajust_arb_sequence_length,
    parse_args_or_ini,
    check_argument,
    switch_on_baseband,
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw, reset_smw


def cn_ratio(test_config: TestConfig):
    """Return AWGN C/N ratio from wanted and interfering signal mean powers."""
    return round(test_config.power_dbm - test_config.interfering_power_dbm, 2)


def configure_awgn(smw: RsInstrument, test_config: TestConfig, bw: float):
    """Configure AWGN interference on Source1 using C/N from the 3GPP table."""
    print("Configuring AWGN...")
    channel_bandwidth_hz = AWGN_BANDWIDTH[bw]

    write_scpi(smw, ":SOURce1:AWGN:MODE ADD")
    write_scpi(smw, f":SOURce1:AWGN:BWIDth {channel_bandwidth_hz}")
    write_scpi(smw, ":SOURce1:AWGN:BWIDth:RATio 1.5")
    write_scpi(smw, ":SOURce1:AWGN:DISP:MODE RFA")
    write_scpi(smw, ":SOURce1:AWGN:POWer:MODE CN")
    write_scpi(smw, ":SOURce1:AWGN:POWer:RMODe CARR")
    write_scpi(smw, f":SOURce1:AWGN:CNRatio {cn_ratio(test_config)}")
    write_scpi(smw, ":SOURce1:AWGN:BRATe 100000")
    write_scpi(smw, ":SOURce1:AWGN:STATe 1")

    print(
        f"AWGN configured successfully, C/N={cn_ratio(test_config)} dB, "
        f"AWGN Bandwidth={channel_bandwidth_hz} Hz"
    )


def main():
    """Configure the SMW for TS 36.181 §7.3 dynamic range."""
    parser = build_base_parser(
        "Look up TS 36.181 table 7.3.5 SAN dynamic range with AWGN interference "
        "for a BW/SCS combination.",
    )
    parser.add_argument(
        "--tdd", action="store_true",
        help="Use Table 7.3.5-4 LEO TDD dynamic range (BW 200 kHz, SCS 15 kHz only; "
             "1.4 MHz does not support TDD).",
    )
    args = parse_args_or_ini(parser)

    try:
        table_key = san_table_key(args.san_class, args.tdd, args.bw, args.scs)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not args.ip:
        return

    if args.san_class is None:
        print("Error: --class is required when --ip is set.", file=sys.stderr)
        sys.exit(1)

    check_argument(args)

    test_config = get_power_levels(SAN_DYNAMIC_RANGE[table_key], args.bw, args.scs)

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
        configure_awgn(smw, test_config, args.bw)

        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

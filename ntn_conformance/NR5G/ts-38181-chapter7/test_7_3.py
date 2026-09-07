"""3GPP TS 38.181 §7.3 Dynamic range

The dynamic range is specified as a measure of the capability of the receiver to receive a wanted
signal in the presence of an interfering signal at the TAB connector for SAN type 1-H inside the
received SAN channel bandwidth. In this condition, a throughput requirement shall be met for a
specified reference measurement channel. The interfering signal for the dynamic range requirement
is an AWGN signal.
The throughput shall be ≥ 95% of the maximum throughput of the reference measurement channel for
SAN LEO class.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RsInstrument import RsInstrument

from tables_3gpp import SAN_LEO_DYNAMIC_RANGE, TestConfig, get_power_levels
from NR5G.utils import build_base_parser, configure_frc, configure_node, configure_triggers
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, query_scpi, write_scpi
from utils.smw_utils import configure_rf, connect_smw


def cn_ratio(test_config: TestConfig):
    """Return AWGN C/N ratio from wanted and interfering signal mean powers."""
    return round(test_config.power_dbm - test_config.interfering_power_dbm, 2)


def configure_awgn(smw: RsInstrument, test_config: TestConfig, scs: int):
    """Configure AWGN interference and NR5G output power reference settings."""
    print("Configuring AWGN...")
    channel_rb_query = ":SOURce1:BB:NR5G:UBWP:USER0:CELL0:UL:BWP0:RBNumber?"
    allocated_rb_query = ":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:RBNumber?"
    channel_bandwidth_hz = int(query_scpi(smw, channel_rb_query)) * 12 * scs * 1000
    allocated_bandwidth_hz = int(query_scpi(smw, allocated_rb_query)) * 12 * scs * 1000
    write_scpi(smw, ":SOURce1:AWGN:MODE ADD")
    write_scpi(smw, ":SOURce1:AWGN:BWIDth:RATio 1")
    write_scpi(smw, ":SOURce1:AWGN:DISP:MODE RFA")
    write_scpi(smw, ":SOURce1:AWGN:POWer:MODE CN")
    write_scpi(smw, ":SOURce1:AWGN:POWer:RMODe CARR")
    write_scpi(smw, f":SOURce1:AWGN:BWIDth {channel_bandwidth_hz}")
    write_scpi(smw, f":SOURce1:AWGN:CNRatio {cn_ratio(test_config)}")
    write_scpi(smw, ":SOURce1:AWGN:STATe 1")
    write_scpi(smw, ":SOURce1:BB:NR5G:OUTPut:POWer:MODE PSDC")
    write_scpi(smw, f":SOURce1:BB:NR5G:OUTPut:POWer:RSBW {allocated_bandwidth_hz}")
    print(
        f"AWGN configured successfully, C/N={cn_ratio(test_config)} dB, "
        f"Channel Bandwidth={channel_bandwidth_hz} Hz, "
        f"Allocated Bandwidth={allocated_bandwidth_hz} Hz"
    )
    return channel_bandwidth_hz, allocated_bandwidth_hz


def main():
    parser = build_base_parser(
        "Look up TS 38.181 table 7.3.2.1-1 SAN LEO reference sensitivity with AWGN "
        "interference for a BW/SCS combination.",
        include_class=False,
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    test_config = get_power_levels(SAN_LEO_DYNAMIC_RANGE, args.bw, args.scs)

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_triggers(smw)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id)
        configure_frc(smw, test_config.ref_meas_channel, ue_id=args.ue_id)
        configure_rf(smw, test_config.power_dbm, args.freq)
        configure_awgn(smw, test_config, args.scs)
        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

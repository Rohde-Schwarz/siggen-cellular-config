"""3GPP TS 38.181 §7.2 Reference sensitivity level

The reference sensitivity power level PREFSENS is the minimum mean power received at the TAB
connector for SAN type 1-H at which a throughput requirement shall be met for a specified
reference measurement channel.
The throughput shall be ≥ 95% of the maximum throughput of the reference measurement channel
as specified in annex A.1 with parameters specified in table 7.2.5-1 and 7.2.5-2 for SAN type
1-H in all operating band in FR1-NTN.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import (
    SAN_GEO_REF_SENS_LEVELS, SAN_LEO_REF_SENS_LEVELS, apply_nb_iot_inband_channel, get_power_levels,
)
from NR5G.utils import build_base_parser, configure_frc, configure_node, configure_triggers
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log
from utils.smw_utils import configure_rf, connect_smw


def main():
    parser = build_base_parser("Look up TS 38.181 table 7.2.5 SAN reference sensitivity for a BW/SCS combination.")
    parser.add_argument(
        "--nb-iot-inband", action="store_true",
        help="Use G-FR1-NTN-A1-10 / A1-11 reference channels where applicable (SAN supports NB-IoT in-band operation).",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    if not args.ip:
        return

    test_config = get_power_levels(
        SAN_LEO_REF_SENS_LEVELS if args.san_class != "geo" else SAN_GEO_REF_SENS_LEVELS,
        args.bw,
        args.scs,
    )
    test_config = apply_nb_iot_inband_channel(test_config, args.bw, args.scs, args.nb_iot_inband)

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_triggers(smw)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id)
        configure_frc(smw, test_config.ref_meas_channel, ue_id=args.ue_id)
        configure_rf(smw, test_config.power_dbm, args.freq)
        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

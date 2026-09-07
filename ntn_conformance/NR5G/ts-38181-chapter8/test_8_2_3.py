"""3GPP TS 38.181 §8.2.3 Performance requirements for UL timing adjustment

Look up FRC and required SNR from tables 8.2.3.5-1 and 8.2.3.5-2 for the given test
parameters.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import MOV_PROP_PROFILES, PUSCH_PERF_REQ_8_2_3, get_pusch_test_config
from NR5G.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_dmrsID, configure_fading,
    configure_frc, configure_harq, configure_iqMapping, configure_node, configure_output,
    configure_triggers,
)
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import connect_smw, configure_rf
from RsInstrument import RsInstrument


def configure_multi_ue_rf_porting(smw: RsInstrument):
    """Configure RF porting for UL timing cases with 2 RX (to map 2 UEs to 2 RF ports)
       For cases with 1 RX, the RF porting is not needed and each RF port outputs one UE
    """
    print("Configuring RF porting...")
    try:
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF1:MODE Add")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF2:MODE Add")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF1:STReam3:STATe 1")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF2:STReam4:STATe 1")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:IQOutput1:STReam3:STATe 0")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:IQOutput2:STReam4:STATe 0")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:BBMM1:STReam1:STATe 0")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:BBMM2:STReam2:STATe 0")
    except Exception as exc:
        raise RuntimeError(f"RF porting configuration failed: {exc}") from exc


def main():
    parser = build_base_parser(
        "Look up TS 38.181 §8.2.3 UL timing adjustment requirements.",
        include_class=False,
        include_ue_id=False,
        require_num_rx=True,
    )
    parser.add_argument(
        "--propagation", choices=tuple(MOV_PROP_PROFILES), required=True,
        help="Moving propagation condition: MP_NTN_15 (15 kHz) or MP_NTN_30 (30 kHz).",
    )
    parser.add_argument(
        "--pusch-type", choices=("A", "B"), required=True,
        help="PUSCH mapping type (Type A or Type B).",
    )
    parser.add_argument(
        "--moving-ue-id", dest="moving_ue_id", type=int, default=0,
        help="NR5G UE ID for the moving UE on Entity1 (default: 0).",
    )
    parser.add_argument(
        "--stationary-ue-id", dest="stationary_ue_id", type=int, default=0,
        help="NR5G UE ID for the stationary UE on Entity2 (default: 0).",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    test_config = get_pusch_test_config(
        PUSCH_PERF_REQ_8_2_3,
        args.pusch_type, args.bw, args.scs, args.num_rx, args.propagation,
    )

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_advance_mode(smw, args.num_rx, multi_ue=True)
        configure_iqMapping(smw, args.num_rx, multi_ue=True)

        # Configure UE 0 - Moving UE
        configure_triggers(smw, ue=0)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id, ue=0)
        configure_frc(smw, test_config.frc, map_type=args.pusch_type, ue=0, ue_id=args.moving_ue_id)
        configure_dmrsID(smw, ue=0)
        configure_harq(smw, timing_advance=True, ue=0)
        configure_fading(smw, args.propagation, MOV_PROP_PROFILES[args.propagation], sources=1, ue=0)
        configure_awgn(smw, test_config.snr_db, test_config.awgn_bw, sources=1, ue=0)
        configure_rf(smw, round(test_config.awgn_power_dbm + test_config.snr_db, 2), args.freq, source=1)
        
        # Configure UE 1 - Stationary UE
        configure_triggers(smw, ue=1)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id, ue=1)           
        configure_frc(
            smw, test_config.frc, map_type=args.pusch_type, ue=1, rb_offset=12,
            ue_id=args.stationary_ue_id,
        )
        configure_dmrsID(smw, ue=1)

        configure_rf(smw, round(test_config.awgn_power_dbm + test_config.snr_db, 2), args.freq, source=2)
        if (args.num_rx == 2):
            configure_multi_ue_rf_porting(smw)
        configure_output(smw)
        if args.log_scpi:
            print_scpi_log()        
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

"""3GPP TS 38.181 §8.2.6 Performance requirements for PUSCH with inter-slot OCC

Look up FRC and required SNR from tables 8.2.6.5-1 through 8.2.6.5-4 for the given test
parameters. Configures two UEs (OCC index 0 and 1) in one OCC group.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tables_3gpp import FADING_PROFILES, PUSCH_PERF_REQ_8_2_6, get_pusch_test_config
from NR5G.utils import (
    build_base_parser, configure_advance_mode, configure_awgn, configure_fading, configure_frc,
    configure_harq, configure_iqMapping, configure_node, configure_OCC, configure_output,
    configure_triggers,
)
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw
from RsInstrument import RsInstrument


def configure_multi_ue_rf_porting(smw: RsInstrument):
    """Configure RF porting for dual-UE setups with 2 RX (map 2 UEs to 2 RF ports)."""
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
        "Look up TS 38.181 §8.2.6 PUSCH with inter-slot OCC requirements.",
        include_class=False,
        include_ue_id=False,
        require_num_rx=True,
    )
    parser.add_argument(
        "--propagation", choices=tuple(FADING_PROFILES), required=True,
        help="Propagation condition: NTN_TDLC5_200_SISO (1 RX) or NTN_TDLC5_200_LOW (2 RX).",
    )
    parser.add_argument(
        "--pusch-type", choices=("A", "B"), required=True,
        help="PUSCH mapping type (Type A or Type B).",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    test_config = get_pusch_test_config(
        PUSCH_PERF_REQ_8_2_6,
        args.pusch_type, args.bw, args.scs, args.num_rx, args.propagation,
    )

    if not args.ip:
        return

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    rf_power_dbm = round(test_config.awgn_power_dbm + test_config.snr_db, 2)
    try:
        configure_advance_mode(smw, args.num_rx, multi_ue=True)
        configure_iqMapping(smw, args.num_rx, multi_ue=True)

        fsim_standard = FADING_PROFILES[args.propagation]
        for ue in (0, 1):
            configure_triggers(smw, ue=ue)
            configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id, ue=ue)
            configure_frc(smw, test_config.frc, map_type=args.pusch_type, ue=ue)
            configure_harq(smw, sources=2, ue=ue)
            configure_OCC(smw, ue=ue, occ_index=ue)
            configure_fading(
                smw, args.propagation, fsim_standard, sources=1, ue=ue,
            )

        configure_awgn(smw, test_config.snr_db, test_config.awgn_bw, sources=1, ue=0)
        configure_rf(smw, rf_power_dbm, args.freq, source=1)
        configure_rf(smw, rf_power_dbm, args.freq, source=2)
        if args.num_rx == 2:
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

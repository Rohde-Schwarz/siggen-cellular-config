"""3GPP TS 38.181 §7.8 In-channel selectivity

In-channel selectivity (ICS) is a measure of the receiver ability to receive a wanted signal at its
assigned resource block locations at the TAB connector for SAN type 1-H in the presence of an
interfering signal received at a larger power spectral density. In this condition a throughput
requirement shall be met for a specified reference measurement channel. The interfering signal
shall be an NR signal which is time aligned with the wanted signal.
For SAN type 1-H, the throughput shall be ≥ 95% of the maximum throughput of the reference
measurement channel.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RsInstrument import RsInstrument

from tables_3gpp import (
    ICS_INTERFERER_RBS, ICS_RB_OFFSETS_IS_HIGH, ICS_RB_OFFSETS_IS_LOW,
    SAT_GEO_ICS, SAT_LEO_ICS, TestConfig, get_power_levels,
)
from NR5G.utils import build_base_parser, configure_frc, configure_node, configure_triggers
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw


def get_interferer_rbs(bw: int, scs: int):
    """Return interferer RB count for the given wanted signal BW/SCS."""
    try:
        return ICS_INTERFERER_RBS[(bw, scs)]
    except KeyError as exc:
        raise ValueError(f"No interferer RB count for BW={bw} MHz, SCS={scs} kHz") from exc


def configure_interferer_allocation(smw: RsInstrument, nrbs: int, rb_offset: int = 0, *, ue_id: int = 0):
    """Configure manual PUSCH allocation for Source2 (16 QAM DFT-s-OFDM, no FRC)."""
    write_scpi(smw, f":SOURce2:BB:NR5G:UBWP:USER0:UEID {ue_id}")
    write_scpi(smw, ":SOURce2:BB:NR5G:UBWP:USER0:USCH:CCODing:STATe 1")
    write_scpi(smw, ":SOURce2:BB:NR5G:UBWP:USER0:CELL0:UL:BWP0:PUSCh:TPSTate 1")
    write_scpi(smw, ":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:NALLoc 1")
    write_scpi(smw, ":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:CONTent PUSC")
    write_scpi(smw, f":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:RBNumber {nrbs}")
    write_scpi(smw, f":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:RBOFfset {rb_offset}")
    write_scpi(smw, ":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:CW0:MOD QAM16")


def configure_interferer(
    smw: RsInstrument,
    test_config: TestConfig,
    bw: int,
    scs: int,
    nrbs: int,
    rb_offset: int,
    freq: int,
    cell_id: int,
    interferer_cell_id: int | None,
    interferer_ue_id: int = 0,
):
    """Configure Source2 ICS interfering signal (16 QAM DFT-s-OFDM PUSCH, co-channel)."""
    print("Configuring interfering signal (Source2)...")
    resolved_cell_id = cell_id if interferer_cell_id is None else interferer_cell_id
    configure_node(smw, bw, scs, freq, cell_id=resolved_cell_id, source=2, link="UP")
    configure_interferer_allocation(smw, nrbs, rb_offset, ue_id=interferer_ue_id)
    print(
        f"Interfering signal (Source2): PUSCH allocation configured, "
        f"{nrbs} RBs at offset {rb_offset}, 16 QAM DFT-s-OFDM"
    )
    configure_rf(smw, test_config.interfering_power_dbm, freq, source=2)


def main():
    parser = build_base_parser(
        "Look up TS 38.181 table 7.8 SAN ICS requirements for a BW/SCS combination and optionally configure an SMW.",
    )
    parser.add_argument(
        "--interferer-cell-id", dest="interferer_cell_id", type=int, default=None,
        help="NR5G cell ID for the interfering signal on Source2 (default: same as --cell-id).",
    )
    parser.add_argument(
        "--interferer-ue-id", dest="interferer_ue_id", type=int, default=0,
        help="NR5G UE ID for the interfering signal on Source2 (default: 0).",
    )
    parser.add_argument(
        "--interference-pos", dest="interference_pos", choices=("lower", "higher"), required=True,
        help="Whether the interfering signal is placed at lower or higher resource blocks.",
    )
    if len(sys.argv) == 2 and sys.argv[1].endswith(".ini"):
        args = load_ini_as_namespace(sys.argv[1])
    else:
        args = parser.parse_args()

    if not args.ip:
        return

    if args.san_class is None:
        print("Error: --class is required when --ip is set.", file=sys.stderr)
        sys.exit(1)

    test_config = get_power_levels(
        SAT_LEO_ICS if args.san_class == "leo" else SAT_GEO_ICS,
        args.bw,
        args.scs,
    )
    nrbs = get_interferer_rbs(args.bw, args.scs)
    offset_table = ICS_RB_OFFSETS_IS_HIGH if args.interference_pos == "higher" else ICS_RB_OFFSETS_IS_LOW
    ws_rb_offset, is_rb_offset = offset_table[(args.bw, args.scs)]

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_triggers(smw, sources=2)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id, source=1)
        configure_frc(smw, test_config.ref_meas_channel, source=1, rb_offset=ws_rb_offset, ue_id=args.ue_id)
        configure_rf(smw, test_config.power_dbm, args.freq, source=1)
        configure_interferer(
            smw, test_config, args.bw, args.scs, nrbs, is_rb_offset, args.freq,
            args.cell_id, args.interferer_cell_id, args.interferer_ue_id,
        )
        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

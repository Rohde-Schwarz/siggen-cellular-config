"""3GPP TS 38.181 §7.4.1 Adjacent Level Selectivity (ACS)

Adjacent channel selectivity (ACS) is a measure of the receiver's ability to receive a wanted signal
at its assigned channel frequency at TAB connector for SAN type 1-H in the presence of an adjacent
channel signal with a specified centre frequency offset of the interfering signal to the band edge
of a victim system.
The throughput shall be ≥ 95% of the maximum throughput of the reference measurement channel.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RsInstrument import RsInstrument

from tables_3gpp import (
    ACS_INTERFERER_OFFSET_MHZ, ACS_INTERFERER_PARAMS, SAT_GEO_ACS, SAT_LEO_ACS, TestConfig,
    get_power_levels,
)
from NR5G.utils import build_base_parser, configure_frc, configure_node, configure_triggers
from NR5G.utils import load_ini_as_namespace
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw


def get_interferer_params(bw: int):
    """Return interferer (bw, scs, nrbs) for the given wanted signal BW."""
    try:
        return ACS_INTERFERER_PARAMS[bw]
    except KeyError as exc:
        raise ValueError(f"No interferer parameters for wanted BW={bw} MHz") from exc


def compute_interferer_freq(freq: int, bw: int, edge: str):
    """Compute interferer center frequency from wanted signal center and RF bandwidth edge."""
    try:
        offset_hz = int(ACS_INTERFERER_OFFSET_MHZ[bw] * 1_000_000)
    except KeyError as exc:
        raise ValueError(f"No interferer offset for wanted BW={bw} MHz") from exc
    half_bw_hz = int(bw / 2 * 1_000_000)
    if edge == "upper":
        return freq + half_bw_hz + offset_hz
    return freq - half_bw_hz - offset_hz


def configure_interferer_allocation(smw: RsInstrument, nrbs: int, scs: int, *, ue_id: int = 0, bw: int = 0):
    """Configure manual PDSCH allocation for Source2 (no FRC)."""
    if (bw == 3):
        write_scpi(smw, ":SOURce2:BB:NR5G:NODE:CELL0:SSPBch0:STATe 0")
    write_scpi(smw, f":SOURce2:BB:NR5G:UBWP:USER0:CELL0:DL:BWP0:SCSPacing N{scs}")
    write_scpi(smw, f":SOURce2:BB:NR5G:UBWP:USER0:CELL0:DL:BWP0:RBNumber {nrbs}")
    write_scpi(smw, ":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:NALLoc 1")
    write_scpi(smw, ":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:CONTent PDSC")
    write_scpi(smw, ":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:SYMNumber 14")
    write_scpi(smw, f":SOURce2:BB:NR5G:UBWP:USER0:UEID {ue_id}")
    write_scpi(smw, ":SOURce2:BB:NR5G:UBWP:USER0:DSCH:CCODing:STATe 1")
    write_scpi(smw, f":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:RBNumber {nrbs}")
    write_scpi(smw, ":SOURce2:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:RBOFfset 0")


def configure_interferer(
    smw: RsInstrument,
    test_config: TestConfig,
    bw: int,
    edge: str,
    freq: int,
    cell_id: int,
    interferer_cell_id: int | None,
    interferer_ue_id: int = 0,
):
    """Configure Source2 ACS interfering signal (CP-OFDM QPSK PDSCH, no FRC)."""
    print("Configuring interfering signal (Source2)...")
    resolved_cell_id = cell_id if interferer_cell_id is None else interferer_cell_id
    i_bw, i_scs, i_nrbs = get_interferer_params(bw)
    i_freq = compute_interferer_freq(freq, bw, edge)
    configure_node(smw, i_bw, i_scs, i_freq, cell_id=resolved_cell_id, source=2, link="DOWN")
    configure_interferer_allocation(smw, i_nrbs, i_scs, ue_id=interferer_ue_id, bw=i_bw)
    print(f"Interfering signal (Source2): PDSCH allocation configured, {i_nrbs} RBs")
    configure_rf(smw, test_config.interfering_power_dbm, i_freq, source=2)
    return i_bw, i_scs, i_nrbs, i_freq


def main():
    parser = build_base_parser(
        "Look up TS 38.181 table 7.4.1 SAN ACS requirements for a BW/SCS combination and optionally configure an SMW.",
    )
    parser.add_argument(
        "--edge", choices=("lower", "upper"),
        help="SAN RF bandwidth edge for the interfering signal (required when --ip is set).",
    )
    parser.add_argument(
        "--interferer-cell-id", dest="interferer_cell_id", type=int, default=None,
        help="NR5G cell ID for the interfering signal on Source2 (default: same as --cell-id).",
    )
    parser.add_argument(
        "--interferer-ue-id", dest="interferer_ue_id", type=int, default=0,
        help="NR5G UE ID for the interfering signal on Source2 (default: 0).",
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
    if args.edge is None:
        print("Error: --edge is required when --ip is set.", file=sys.stderr)
        sys.exit(1)

    test_config = get_power_levels(
        SAT_LEO_ACS if args.san_class == "leo" else SAT_GEO_ACS,
        args.bw,
        args.scs,
    )

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        configure_triggers(smw, sources=2)
        configure_node(smw, args.bw, args.scs, args.freq, cell_id=args.cell_id, source=1)
        configure_frc(smw, test_config.ref_meas_channel, source=1, ue_id=args.ue_id)
        configure_rf(smw, test_config.power_dbm, args.freq, source=1)
        configure_interferer(
            smw, test_config, args.bw, args.edge, args.freq, args.cell_id, args.interferer_cell_id,
            args.interferer_ue_id,
        )
        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

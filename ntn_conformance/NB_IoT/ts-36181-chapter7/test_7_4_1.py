"""3GPP TS 36.181 §7.4.1 Adjacent Channel Selectivity (ACS)

Adjacent channel selectivity (ACS) is a measure of the receiver's ability to receive a wanted signal at its assigned
channel frequency at TAB connector for SAN type 1-H in the presence of an adjacent channel signal with a specified
centre frequency offset of the interfering signal to the band edge of a victim system.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RsInstrument import RsInstrument

# pylint: disable=wrong-import-position
from tables_3gpp import get_power_levels, TestConfig, SAN_ACS, ACS_INTERFERER_OFFSET_MHZ, san_table_key
from NB_IoT.utils import (
    NPUSCH_NUM_TRANSMISSION,
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
    configure_interferer_pusch
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw, reset_smw


def compute_interferer_freq(freq: int, bw: float, edge: str):
    """Compute interferer center frequency from wanted signal center and RF bandwidth edge."""
    try:
        offset_hz = int(ACS_INTERFERER_OFFSET_MHZ[bw] * 1_000_000)
    except KeyError as exc:
        raise ValueError(f"No interferer offset for wanted BW={bw} MHz") from exc
    half_bw_hz = int(bw / 2 * 1_000_000)
    if edge == "upper":
        return freq + half_bw_hz + offset_hz
    return freq - half_bw_hz - offset_hz


def configure_interferer_pi4_qpsk(
    smw: RsInstrument,
    source: int = 2,
    tdd: bool = False,
):
    """Configure interferer modulation."""
    try:
        num_trans = NPUSCH_NUM_TRANSMISSION["TDD" if tdd else "FDD"]

        for i in range(1, (num_trans + 1)):
            write_scpi(smw, f":SOURce{source}:BB:EUTRa:UL:UE1:NIOT:TRANs{i}:MODulation PI4Q")
    except Exception as exc:
        raise RuntimeError(f"iot PI/4 QPSK configuration failed: {exc}") from exc


def configure_interferer(
    smw: RsInstrument,
    test_config: TestConfig,
    bw: float,
    mode: str,
    edge: str,
    freq: int,
    cell_id: int,
    interferer_cell_id: int | None,
    interferer_ue_id: int = 0,
):
    """Configure Source2 ACS interfering signal (uplink PUSCH, no FRC)."""
    print("Configuring interfering signal (Source2)...")
    resolved_cell_id = cell_id if interferer_cell_id is None else interferer_cell_id
    i_freq = compute_interferer_freq(freq, bw, edge)

    scs = 15
    configure_node(smw, bw, scs, mode, cell_id=resolved_cell_id, source=2)
    configure_pusch(smw, bw, scs, mode, source=2)
    configure_interferer_pusch(smw, interferer_ue_id, source=2)

    if mode == "IOT":
        configure_frc(smw, test_config.ref_meas_channel, mode, source=2)
        write_scpi(smw, ":SOURce2:BB:EUTRa:UL:UE1:NIOT:FRC:STATe 0")
        write_scpi(smw, ":SOURce2:BB:EUTRa:UL:UE1:CELL0:PUSCh:SCRambling:STATe 1")
        write_scpi(smw, ":SOURce2:BB:EUTRa:UL:UE1:CELL0:PUSCh:CCODing:STATe 0")

        configure_interferer_pi4_qpsk(smw, source=2)

    configure_rf(smw, test_config.interfering_power_dbm, i_freq, source=2)
    return i_freq


def main():
    """Configure the SMW for TS 36.181 §7.4.1 adjacent channel selectivity."""
    parser = build_base_parser(
        "Look up TS 36.181 table 7.4.1.5 SAN ACS requirements "
        "for a BW/SCS combination and optionally configure an SMW.",
    )

    parser.add_argument(
        "--tdd", action="store_true",
        help="Use Table 7.4.1.5-3 LEO TDD ACS (BW 200 kHz, SCS 15 kHz only; "
             "1.4 MHz does not support TDD).",
    )

    parser.add_argument(
        "--edge", choices=("lower", "upper"),
        help="SAN RF bandwidth edge for the interfering signal (required when --ip is set).",
    )

    """
    In ACS, the wanted and interfering UE IDs / RNTIs may be the same or different;
    TS 36.181 §7.4.1 measures the receiver’s ability to suppress adjacent-channel interference.
    The DUT decodes only the wanted channel.
    """
    parser.add_argument(
        "--interferer-cell-id", dest="interferer_cell_id", type=int, default=1,
        help="NB-IoT cell ID for the interfering signal on Source2 (default: differ from --cell-id).",
    )
    parser.add_argument(
        "--interferer-ue-id", dest="interferer_ue_id", type=int, default=1,
        help="NB-IoT UE ID for the interfering signal on Source2 (default: 1).",
    )

    args = parse_args_or_ini(parser)

    if not args.ip:
        return

    if args.san_class is None:
        print("Error: --class is required when --ip is set.", file=sys.stderr)
        sys.exit(1)
    if args.edge is None:
        print("Error: --edge is required when --ip is set.", file=sys.stderr)
        sys.exit(1)

    check_argument(args)
    try:
        table_key = san_table_key(args.san_class, args.tdd, args.bw, args.scs)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    test_config = get_power_levels(SAN_ACS[table_key], args.bw, args.scs)

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        reset_smw(smw)
        configure_triggers(smw, sources=2)
        mode = get_eutra_mode(args.bw)
        configure_node(smw, args.bw, args.scs, mode, args.tdd, args.ue_id, cell_id=args.cell_id)

        configure_pusch(smw, args.bw, args.scs, mode, args.tdd)
        configure_frc(smw, test_config.ref_meas_channel, mode)

        configure_interferer(smw, test_config, args.bw, mode, args.edge, args.freq,
                             args.cell_id, args.interferer_cell_id, args.interferer_ue_id)

        if mode == "IOT":
            ajust_arb_sequence_length(smw, sources=2)

        switch_on_baseband(smw, sources=2)
        configure_rf(smw, test_config.power_dbm, args.freq)

        if args.log_scpi:
            print_scpi_log()
    except Exception as exc:
        print(f"Error configuring SMW: {exc}")
    finally:
        smw.close()


if __name__ == "__main__":
    main()

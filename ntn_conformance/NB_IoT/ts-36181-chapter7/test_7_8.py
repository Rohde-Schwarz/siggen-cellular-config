"""3GPP TS 36.181 §7.8	In-channel selectivity

In-channel selectivity (ICS) is a measure of the receiver ability to receive a wanted signal at its assigned resource
block locations at TAB connector for SAN type 1-H in the presence of an interfering signal received at a larger power
spectral density. In this condition a throughput requirement shall be met for a specified reference measurement channel.
The interfering signal shall be an E-UTRA signal which is time aligned with the wanted signal.

For SAN supporting E-UTRA, the throughput shall be ≥ 95% of the maximum throughput of the reference measurement channel
as specified in annex A.1 with parameters specified in table 7.8.2-1 for GEO SAN, in table 7.8.2-2 for LEO SAN.
The characteristics of the interfering signal is further specified in annex C.
"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from RsInstrument import RsInstrument

# pylint: disable=wrong-import-position
from tables_3gpp import SAT_GEO_ICS, SAT_LEO_ICS, get_power_levels, TestConfig
from NB_IoT.utils import (
    build_base_parser,
    configure_frc,
    configure_node,
    configure_pusch,
    configure_triggers,
    parse_args_or_ini,
    switch_on_baseband,
    configure_interferer_pusch
)
from utils.scpi_utils import enable_scpi_logging, print_scpi_log, write_scpi
from utils.smw_utils import configure_rf, connect_smw, reset_smw


def configure_interferer_allocation(
    smw: RsInstrument,
    interference_pos: str,
    source: int = 2
):
    """Configure interfering signal according to ICS defined in Annex E and Table 7.8.5-1, 7.8.5-2."""
    try:
        offset_vrb = {"higher": 3, "lower": 0}[interference_pos]
    except KeyError as exc:
        raise ValueError(
            f'interference_pos must be "higher" or "lower", got {interference_pos!r}'
        ) from exc

    try:
        write_scpi(smw, f":SOURce{source}:BB:EUTRa:UL:CELL0:SUBF0:ALLoc0:CW1:PUSCh:MODulation QAM16")
        write_scpi(smw, f":SOURce{source}:BB:EUTRa:UL:CELL0:SUBF0:ALLoc0:PUSCh:SET1:RBCount 3")
        write_scpi(smw, f":SOURce{source}:BB:EUTRa:UL:CELL0:SUBF0:ALLoc0:PUSCh:SET1:VRBoffset {offset_vrb}")
    except Exception as exc:
        raise RuntimeError(f"PUSCH configuration failed: {exc}") from exc


def configure_interferer(
    smw: RsInstrument,
    test_config: TestConfig,
    bw: float,
    mode: str,
    interference_pos: str,
    freq: int,
    cell_id: int,
    interferer_cell_id: int | None,
    interferer_ue_id: int = 0,
):
    """Configure Source2 ICS interfering signal (uplink PUSCH, no FRC)."""
    print("Configuring interfering signal (Source2)...")
    resolved_cell_id = cell_id if interferer_cell_id is None else interferer_cell_id

    scs = 15
    configure_node(smw, bw, scs, mode, cell_id=resolved_cell_id, source=2)
    configure_interferer_pusch(smw, interferer_ue_id, source=2)
    configure_interferer_allocation(smw, interference_pos, source=2)

    configure_rf(smw, test_config.interfering_power_dbm, freq, source=2)


def main():
    """Configure the SMW for TS 36.181 §7.8 in-channel selectivity."""
    parser = build_base_parser(
        "Look up TS 36.181 table 7.8.5 SAN ICS wanted and interfering power "
        "for a BW/SCS combination and optionally configure an SMW.",
        include_bw=False,
        include_scs=False
    )

    parser.add_argument(
        "--interference-pos", dest="interference_pos", choices=("lower", "higher"), required=True,
        help="Whether the interfering signal is placed at lower or higher resource blocks.",
    )

    parser.add_argument(
        "--interferer-cell-id", dest="interferer_cell_id", type=int, default=1,
        help="NB-IoT cell ID for the interfering signal on Source2 (default: differ from --cell-id).",
    )
    parser.add_argument(
        "--interferer-ue-id", dest="interferer_ue_id", type=int, default=2,
        help="NB-IoT UE ID for the interfering signal on Source2 (default: 2).",
    )

    args = parse_args_or_ini(parser)

    if not args.ip:
        return

    if args.san_class is None:
        print("Error: --class is required when --ip is set.", file=sys.stderr)
        sys.exit(1)

    test_config = get_power_levels(
        SAT_LEO_ICS if args.san_class == "leo" else SAT_GEO_ICS,
        bw=1.4,
        scs=15
    )

    enable_scpi_logging(args.log_scpi)
    smw = connect_smw(args.ip)
    try:
        reset_smw(smw)
        configure_triggers(smw, sources=2)

        mode = "LTE"
        configure_node(smw, args.bw, args.scs, mode, cell_id=args.cell_id)
        configure_pusch(smw, args.bw, args.scs, mode)
        configure_frc(smw, test_config.ref_meas_channel, mode)

        configure_interferer(smw, test_config, args.bw, mode, args.interference_pos, args.freq,
                             args.cell_id, args.interferer_cell_id, args.interferer_ue_id)

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

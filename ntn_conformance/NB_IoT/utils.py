"""EUTR-specific utilities: FRC map, base parser, and SMW baseband configuration."""

import argparse
import math
import sys
from pathlib import Path

from RsInstrument import RsInstrument

from utils.config_utils import load_ini_as_namespace as _load_ini_generic
from utils.helpers import parse_frequency
from utils.scpi_utils import write_scpi, query_scpi
from utils.smw_utils import get_harq_connector, is_smw_b9


# Mapping between 3GPP FRCs and the corresponding SCPI names
FRC_TYPE: dict[str, str] = {
    **{f"FRC-A1-{n}": f"TS36181_A1{n}" for n in range(1, 10)},
    **{f"FRC-A2-{n}": f"TS36181_A2{n}" for n in range(1, 6)},
    **{f"FRC-A5-{n}": f"TS36181_A5{n}" for n in range(1, 3)},
    **{f"FRC-A14-{n}": f"TS36181_A14{n}" for n in range(1, 4)},
    **{f"FRC-A15-{n}": f"TS36181_A15{n}" for n in range(1, 3)},
    **{f"FRC-A16-{n}": f"TS36181_A16{n}" for n in range(1, 4)},
}

# TDD: one transmission. FDD: five transmissions to generate a continuous signal (chapter 7).
NPUSCH_NUM_TRANSMISSION = {
    "TDD": 1,
    "FDD": 5,
}


def load_ini_as_namespace(path: str | Path) -> argparse.Namespace:
    """Load an EUTR test INI, merging instrument.ini and EUTR/options.ini."""
    return _load_ini_generic(
        path,
        extra_configs=(Path(__file__).resolve().parent / "options.ini",),
        freq_keys=frozenset({"freq", "interferer_freq", "ful_low", "ful_high"}),
        bool_keys=frozenset({
            "log_scpi", "nb_iot_inband", "additional_dmrs", "tdd",
            "spurious_response_exception",
        }),
    )


def apply_parser_defaults(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> argparse.Namespace:
    """Fill Namespace attributes omitted from an INI with argparse defaults.

    Optional flags such as ``tdd`` become False when the INI leaves them out
    (1.4 MHz E-UTRA in-band does not support TDD). Cannot use
    ``parser.parse_args([], namespace=args)`` here: chapter 7 parsers still
    mark ``--bw`` / ``--scs`` as required, so an empty argv would fail.
    """
    for action in parser._actions:
        dest = action.dest
        if not dest or action.default is argparse.SUPPRESS:
            continue
        if not hasattr(args, dest):
            setattr(args, dest, action.default)
    return args


def parse_args_or_ini(
    parser: argparse.ArgumentParser,
    argv: list[str] | None = None,
) -> argparse.Namespace:
    """Parse CLI args, or load a single ``.ini`` path and apply parser defaults."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 1 and argv[0].endswith(".ini"):
        return apply_parser_defaults(parser, load_ini_as_namespace(argv[0]))
    return parser.parse_args(argv)


def set_entity(ue: int | None) -> str:
    """Return the :ENTity{n} prefix string, or empty string when ue is None.

    ue is 0-based; SCPI uses :ENTity1 for ue=0, :ENTity2 for ue=1, etc.
    """
    return f":ENTity{ue + 1}" if ue is not None else ""


def build_base_parser(
    description: str,
    *,
    include_class: bool = True,
    include_bw: bool = True,
    include_scs: bool = True,
    include_ue_id: bool = True,
    require_num_rx: bool = False
):
    """Build an ArgumentParser with the common BW/SCS/freq/IP options shared by all scripts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--bw", dest="bw", type=float, required=include_bw,
        help="Channel bandwidth of the test case in MHz (e.g. 1.4, 0.2).",
    )
    parser.add_argument(
        "--scs", type=float, required=include_scs,
        help="Sub-carrier spacing of the test case in kHz (e.g. 15, 3.75).",
    )
    parser.add_argument(
        "--num-rx", type=int, choices=(1, 2), required=require_num_rx, default=1,
        help="Number of RX antennas (1 or 2).",
    )
    if include_class:
        parser.add_argument(
            "--class", dest="san_class", choices=("leo", "geo"),
            help="SAN orbit class. If omitted, both LEO and GEO are printed.",
        )
    parser.add_argument(
        "--freq", type=parse_frequency, default=1_620_000_000,
        help="PCFReq / RF frequency in Hz or with unit suffix (e.g. 1620000000, 1.62G).",
    )
    parser.add_argument(
        "--cell-id", dest="cell_id", type=int, default=150,
        help="EUTR cell ID for the wanted signal on Source1 (default: 150).",
    )

    if include_ue_id:
        parser.add_argument(
            "--ue-id", dest="ue_id", type=int, default=1,
            help="NB-IoT UE ID for the wanted signal on Source1 (default: 1).",
        )

    parser.add_argument("--ip", help="SMW IP address. When set, "
                                     "the script connects over raw TCP/IP socket.")

    parser.add_argument(
        "--log-scpi", action="store_true",
        help="Write all SCPI commands sent to the SMW during this run to scpi-list.iec in the repo root.",
    )
    return parser


def check_argument(args):
    if args.tdd and args.bw == 1.4:
        raise ValueError(
            "TDD is not supported for 1.4 MHz channel bandwidth "
            "(E-UTRA in-band); use 0.2 MHz / 15 kHz."
        )


def switch_on_baseband(smw: RsInstrument, application="EUTR", sources: int = 1):
    for s in range(1, sources + 1):
        write_scpi(smw, f":SOURce{s}:BB:{application}:STATe 1")


def configure_triggers(smw: RsInstrument, sources: int = 1, *, ue: int | None = None):
    """Configure EUTR triggers before any baseband settings.

    Args:
        sources: Number of RF sources to configure (1 or 2). Source1 always uses
            external gate input USER3; Source2 shares the same trigger when enabled.
        ue: Optional 0-based UE index; when set, prefixes all SCPI commands with :ENTity{ue+1}.
    """
    if sources not in (1, 2):
        raise ValueError(f"sources must be 1 or 2, got {sources}")
    ep = set_entity(ue)
    print("Configuring triggers...")
    try:
        write_scpi(smw, f"{ep}:SOURce1:BB:EUTR:TRIGger:SEQuence AAUT")
        write_scpi(smw, f"{ep}:SOURce1:BB:EUTR:TRIGger:SOURce EGT1")
        if sources == 2:
            write_scpi(smw, f"{ep}:SOURce2:BB:EUTR:TRIGger:SEQuence AAUT")
            write_scpi(smw, f"{ep}:SOURce2:BB:EUTR:TRIGger:SOURce EGT1")
        write_scpi(smw, ":SOURce1:INPut:USER3:DIRection INP")
        write_scpi(smw, ":SOURce1:INPut:USER3:SIGNal TRIG1")
        print(f"Trigger{'s' if sources == 2 else ''} configured successfully")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Trigger configuration failed: {exc}") from exc


def configure_trigger_delay(smw: RsInstrument, sources: int = 1, delay: float = 0.0):
    """Configure EUTR trigger delay for PRACH."""
    print("Configuring triggers delay...")
    if sources not in (1, 2):
        raise ValueError(f"sources must be 1 or 2, got {sources}")

    delay_in_sec = delay * 1e-6
    try:
        write_scpi(smw, f":SOURce{sources}:BB:EUTRa:TRIGger:DELay:UNIT TIME")
        write_scpi(smw, f":SOURce{sources}:BB:EUTRa:TRIGger:EXTernal1:TDELay {delay_in_sec}")

        print("Trigger delay configured successfully")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Trigger configuration failed: {exc}") from exc


def configure_advance_mode(smw: RsInstrument, num_rx: int, *, multi_ue: bool = False):
    """Configure SMW advanced fading mode for 1 TX and multiple RX paths.

    MIMO1X2 corresponds to 1 TX and 2 RX antennas. Call only when num_rx is not 1.
    When multiUE is True, uses MIMO2X1X1 (1 RX) or MIMO2X1X2 (2 RX) for dual-UE setups.
    """
    if multi_ue is False and num_rx == 1 and not is_smw_b9(smw):
        return
    # FAAFBB stands for MIMO2X1X1
    fading_by_num_rx = {1: "FAAFBB", 2: "MIMO2X1X2"} if multi_ue else {1: "FAAFBB", 2: "MIMO1X2"}
    try:
        fading_mode = fading_by_num_rx[num_rx]
    except KeyError as exc:
        raise ValueError(f"Unsupported num_rx={num_rx} for advanced mode configuration") from exc
    print(f"Configuring advanced mode ({fading_mode})...")
    try:
        write_scpi(smw, ":SCONfiguration:MODE ADV")
        write_scpi(smw, ":SCONfiguration:BASeband:SOURce SEP")
        write_scpi(smw, f":SCONfiguration:FADing {fading_mode}")
        write_scpi(smw, ":SCONfiguration:APPLy")
        print(f"Advanced mode configured successfully ({fading_mode})")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Advanced mode configuration failed: {exc}") from exc


def configure_iqMapping(smw: RsInstrument, num_rx: int, *, multi_ue: bool = False):
    """Configure SMW IQ output mapping for multi-UE MIMO2X1X2 setups (§8.2.3)."""
    fading_by_num_rx = {1: "MIMO2X1X1", 2: "MIMO2X1X2"} if multi_ue else {2: "MIMO1X2"}
    try:
        fading_mode = fading_by_num_rx[num_rx]
    except KeyError:
        return
    if fading_mode != "MIMO2X1X2":
        # IQ mapping is only changed for MIMO2X1X2 so far.
        return
    print("Configuring IQ mapping (MIMO2X1X2)...")
    try:
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF1:MODE Single")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF2:MODE Single")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF1:STReam3:STATe 0")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:RF2:STReam4:STATe 0")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:IQOutput1:STReam3:STATe 1")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:IQOutput2:STReam4:STATe 1")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:BBMM1:STReam1:STATe 1")
        write_scpi(smw, ":SCONfiguration:OUTPut:MAPPing:BBMM2:STReam2:STATe 1")
        print("IQ mapping configured successfully (MIMO2X1X2)")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"IQ mapping configuration failed: {exc}") from exc


def configure_fading(
    smw: RsInstrument,
    propagation: str,
    fsim_standard: str,
    sources: int = 2,
    *,
    ue: int | None = None,
):
    """Configure the fading simulator (Chapter 8 only).

    Args:
        sources: Number of RF sources to configure (1 or 2). Defaults to 2 for
            single-UE setups; use 1 per UE in multi-UE configurations.
        ue: Optional 0-based UE index; when set, prefixes all SCPI commands with :ENTity{ue+1}.
    """
    if sources not in (1, 2):
        raise ValueError(f"sources must be 1 or 2, got {sources}")
    ep = set_entity(ue)
    print(f"Configuring fading ({propagation})...")

    if sources == 2:
        fading_suffix = "L"
    else:
        fading_suffix = ""

    try:

        for source in range(1, sources + 1):
            write_scpi(smw, f"{ep}:SOURce{source}:FSIMulator:STANdard {fsim_standard}{fading_suffix}")
            write_scpi(smw, f"{ep}:SOURce{source}:FSIMulator:STATe 1")
        print(f"Fading configured successfully ({propagation})")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Fading configuration failed: {exc}") from exc


def get_eutra_mode(bw: float, emtc: bool = False) -> str:
    """Return SMW EUTRA mode: LTE only for 1.4 MHz without eMTC, otherwise IOT."""
    return "LTE" if not emtc and bw == 1.4 else "IOT"


def get_bw_scs_str(bw: float, scs: float) -> tuple[str, str]:
    """Return SMW BW/SCS tokens (MHz / kHz), e.g. (1.4, 3.75) → ('1_40', '375')."""
    if bw is None or scs is None:
        raise ValueError(f"bw and scs are required, got bw={bw!r}, scs={scs!r}")
    bw_map = {1.4: "1_40", 0.2: "0_20"}
    scs_map = {3.75: "375"}
    return bw_map.get(bw, str(int(bw))), scs_map.get(scs, str(int(scs)))


def set_tdd(smw: RsInstrument, prefix):
    write_scpi(smw, f"{prefix}DUPLexing TDD")
    write_scpi(smw, f"{prefix}TDD:UDConf 1")
    write_scpi(smw, f"{prefix}TIMC:NTAoffset NTA624")


def set_niot_num_transmission(
    smw: RsInstrument,
    num_trans: int,
    prefix: str = ":SOURce1:BB:EUTRa:",
):
    write_scpi(smw, f"{prefix}UL:UE1:NIOT:NTRansmiss {num_trans}")


def configure_pusch(smw: RsInstrument, bw: float,
    scs: float, mode: str, tdd: bool = False, pusch_coding_on: bool = True, source: int = 1, ue: int | None = None):
    try:
        ep = set_entity(ue)

        bw_str, scs_str = get_bw_scs_str(bw, scs)
        prefix = f"{ep}:SOURce{source}:BB:EUTR:"

        if pusch_coding_on:
            write_scpi(smw, f"{prefix}UL:UE1:CELL0:PUSCh:SCRambling:STATe 1")
            write_scpi(smw, f"{prefix}UL:UE1:CELL0:PUSCh:CCODing:STATe 1")

        if mode == "IOT":
            write_scpi(smw, f"{prefix}UL:UE1:NIOT:SCSPacing S{scs_str}")

            num_trans = NPUSCH_NUM_TRANSMISSION["TDD" if tdd else "FDD"]
            write_scpi(smw, f"{prefix}UL:UE1:NIOT:NTRansmiss {num_trans}")

        print(f"PUSCH/NPUSCH configured successfully (BW={bw} MHz, SCS={scs} kHz)")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"PUSCH/NPUSCH configuration failed: {exc}") from exc


def configure_node(
    smw: RsInstrument,
    bw: float,
    scs: float,
    mode: str,
    tdd: bool = False,
    ue_id: int = 1,
    *,
    cell_id: int = 150,
    source: int = 1,
    link: str = "UP",
    ue: int | None = None,
):
    """Configure EUTR node settings for the given source."""
    if source == 1:
        print("Configuring wanted signal (Source1)...")

    try:
        ep = set_entity(ue)

        bw_str, scs_str = get_bw_scs_str(bw, scs)
        prefix = f"{ep}:SOURce{source}:BB:EUTR:"

        write_scpi(smw, f"{prefix}STDM {mode}")
        write_scpi(smw, f"{prefix}LINK {link}")

        if tdd:
            set_tdd(smw, prefix)

        write_scpi(smw, f"{prefix}UL:BW BW{bw_str}")
        write_scpi(smw, f"{prefix}UL:PLCI:CID {cell_id}")

        write_scpi(smw, f"{prefix}UL:UE1:STATe 1")
        write_scpi(smw, f"{prefix}UL:UE1:ID {ue_id}")

        print(f"Node configured successfully (BW={bw} MHz, SCS={scs} kHz, Cell ID={cell_id})")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Node configuration failed: {exc}") from exc


def configure_frc(
    smw: RsInstrument,
    ref_meas_channel: str,
    mode: str,
    repetition_num: int | None = None,
    source: int = 1,
    frc_type_map: dict[str, str] | None = None,
    *,
    ue: int | None = None
) -> str:
    """Select the FRC type matching the given reference measurement channel.

    For NB-IoT (``mode="IOT"``), ``num_trans`` is programmed before the FRC, and
    ``adjust_arb`` applies the SMW suggested sequence length afterwards. Leave
    both unset when a later step (e.g. NPUSCH ACK) owns those settings.
    """
    print(f"Configuring FRC ({ref_meas_channel})...")
    try:
        mapping = FRC_TYPE if frc_type_map is None else frc_type_map
        try:
            frc_type = mapping[ref_meas_channel]
        except KeyError as exc:
            raise ValueError(f"No FRC type mapping for reference measurement channel: {ref_meas_channel}") from exc

        ep = set_entity(ue)
        prefix = f"{ep}:SOURce{source}:BB:EUTR:"

        if mode == "LTE":
            write_scpi(smw, f"{prefix}UL:UE1:CELL0:FRC:STATe 1")
            write_scpi(smw, f"{prefix}UL:UE1:CELL0:FRC:TYPE {frc_type}")
        else:
            write_scpi(smw, f"{prefix}UL:UE1:NIOT:FRC:STATe 1")
            write_scpi(smw, f"{prefix}UL:UE1:NIOT:FRC:TYPE {frc_type}")
            if repetition_num is not None and "A16" in frc_type:
                write_scpi(smw, f"{prefix}UL:UE1:NIOT:FRC:NNPRep {repetition_num}")

        print(f"FRC configured successfully ({ref_meas_channel})")
        print("--------------------------------")

        return prefix

    except Exception as exc:
        raise RuntimeError(f"FRC configuration failed: {exc}") from exc


def configure_awgn(
    smw: RsInstrument,
    snr_db: float,
    awgn_bw: float,
    sources: int = 2,
    *,
    awgn_power_dbm: float | None = None,
    noise_only_mode: bool = False,
    ue: int | None = None,
):
    """Configure AWGN interference and EUTR output power reference settings.
    So far only used for Chapter 8 tests.
    Source1 AWGN is routed to RFA; Source2 AWGN is routed to RFB.
    """
    if sources not in (1, 2):
        raise ValueError(f"sources must be 1 or 2, got {sources}")
    if noise_only_mode and awgn_power_dbm is None:
        raise ValueError("awgn_power_dbm is required when noise_only_mode is True")
    ep = set_entity(ue)
    awgn_bw_hz = int(awgn_bw * 1_000_000)
    print("Configuring AWGN...")
    for source in range(1, sources + 1):
        prefix = f"{ep}:SOURce{source}:AWGN:"
        disp_mode = "RFA" if source == 1 else "RFB"
        write_scpi(smw, f"{prefix}CMODe:STATe 1")
        if noise_only_mode:
            write_scpi(smw, f"{prefix}MODE ONLY")
            write_scpi(smw, f"{prefix}BWIDth:RATio 1.5")
            write_scpi(smw, f"{prefix}DISP:MODE {disp_mode}")
            write_scpi(smw, f"{prefix}BWIDth {awgn_bw_hz}")
            write_scpi(smw, f"{prefix}POWer:NOISe {awgn_power_dbm}")
            write_scpi(smw, f"{prefix}STATe 1")
        else:
            write_scpi(smw, f"{prefix}MODE ADD")
            write_scpi(smw, f"{prefix}BWIDth:RATio 1.5")
            write_scpi(smw, f"{prefix}DISP:MODE {disp_mode}")
            write_scpi(smw, f"{prefix}POWer:MODE CN")
            write_scpi(smw, f"{prefix}POWer:RMODe CARR")
            write_scpi(smw, f"{prefix}BWIDth {awgn_bw_hz}")
            write_scpi(smw, f"{prefix}CNRatio {snr_db}")
            write_scpi(smw, f"{prefix}BRATe 100000")
            write_scpi(smw, f"{prefix}STATe 1")

    if noise_only_mode:
        print(
            f"AWGN configured successfully on {sources} source(s), noise-only mode, "
            f"power={awgn_power_dbm} dBm, AWGN bandwidth={awgn_bw_hz} Hz"
        )
    else:
        print(
            f"AWGN configured successfully on {sources} source(s), C/N={snr_db} dB, "
            f"AWGN bandwidth={awgn_bw_hz} Hz"
        )
        print("--------------------------------")


def configure_harq(smw: RsInstrument, *, ue: int | None = None):
    """Configure HARQ feedback for NB_IoT uplink testing (Chapter 8 only)."""
    print("Configuring HARQ feedback...")
    ep = set_entity(ue)
    try:
        tm_port = get_harq_connector(smw)
        write_scpi(smw, f":SOURce1:INPut:TM{tm_port}:DIRection INP")
        write_scpi(smw, f":SOURce1:INPut:TM{tm_port}:SIGNal FEED")

        write_scpi(smw, f"{ep}:SOURce1:BB:EUTRa:UL:RTFB:BBSelector 0")
        write_scpi(smw, f"{ep}:SOURce1:BB:EUTRa:UL:RTFB:MODE SER")
        write_scpi(smw, f"{ep}:SOURce1:BB:EUTRa:UL:RTFB:ADUDelay -0.3")
        write_scpi(smw, f"{ep}:SOURce1:BB:EUTRa:UL:RTFB:SERate SR115_2K")
        write_scpi(smw, f"{ep}:SOURce1:INPut:TM1:CLOCk:LEVel 1")

        print("HARQ feedback configured successfully")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"HARQ feedback configuration failed: {exc}") from exc


def configure_output(smw: RsInstrument, sources: int = 2):
    """Set the related output states enabled."""
    if sources not in (1, 2):
        raise ValueError(f"sources must be 1 or 2, got {sources}")
    print("Configuring outputs...")
    try:
        write_scpi(smw, ":SOURce1:IQ:OUTPut:ANALog:STATe 1")
        if sources == 2:
            write_scpi(smw, ":SOURce2:IQ:OUTPut:ANALog:STATe 1")
        write_scpi(smw, ":SOURce1:IQ:OUTPut:DIGital:BBMM1:STATe 1")
        print("Outputs configured successfully")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Output configuration failed: {exc}") from exc


def configure_interferer_pusch(
    smw: RsInstrument,
    ue_id: int = 0,
    source: int = 2
):
    """Configure interferer PUSCH."""
    try:
        write_scpi(smw, f":SOURce{source}:BB:EUTRa:UL:UE1:CELL0:PUSCh:DATA ZERO")
        write_scpi(smw, f":SOURce{source}:BB:EUTRa:UL:UE1:ID {ue_id}")
        write_scpi(smw, f":SOURce{source}:BB:EUTRa:UL:UE1:CELL0:PUSCh:CCODing:STATe 0")
    except Exception as exc:
        raise RuntimeError(f"PUSCH configuration failed: {exc}") from exc


def set_tdd_config(smw: RsInstrument):
    write_scpi(smw, ":SOURce1:BB:EUTRa:TDD:UDConf 1")
    write_scpi(smw, ":SOURce1:BB:EUTRa:TDD:SPSConf 7")


def set_nprach(smw: RsInstrument, preamble_format, repetition_num, tdd=False):
    """Configure NPRACH according to Table 8.5.3.5-1 FDD, Table 8.5.3.5-2 TDD NPRACH Test Parameters"""
    write_scpi(smw, ":SOURce1:BB:EUTRa:UL:UE1:MODE PRAC")

    prach_prefix = ":SOURce1:BB:EUTRa:UL:PRACh:NIOT:"
    write_scpi(smw, f"{prach_prefix}PFMT F{preamble_format}")

    if tdd:
        periodicity = 160
        starting_time = 10
    else:
        periodicity = 10
        starting_time = 8

    nprach_periodicity = repetition_num * periodicity
    write_scpi(smw, f"{prach_prefix}CFG0:REP R{repetition_num}")
    write_scpi(smw, f"{prach_prefix}CFG0:PERD {nprach_periodicity}")
    write_scpi(smw, f"{prach_prefix}CFG0:STTM {starting_time}")
    write_scpi(smw, f"{prach_prefix}CFG0:SUBC 12")

    arb_length = nprach_periodicity
    set_arb_length(smw, arb_length)


def configure_prach(
    smw: RsInstrument,
    tdd: bool = False,
    preamble_format: int = 0,
    repetition_num: int = 1,
    freq_offset_hz: int = 0,
) -> None:
    """Configure NPRACH for Chapter 8 tests."""
    print(f"Configuring NPRACH (format {preamble_format})...")
    try:
        if preamble_format not in (0, 1):
            raise ValueError(f"Unsupported PRACH burst format: {preamble_format}")

        if tdd:
            set_tdd_config(smw)

        set_nprach(smw, preamble_format, repetition_num, tdd)
        write_scpi(smw, f":SOURce1:BB:FOFFset {freq_offset_hz}")

        print("NPRACH configured successfully.")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"NPRACH configuration failed: {exc}") from exc


# NB-IoT UL slot duration in ms (TS 36.211 Table 10.1.2.3-1).
_NIOT_SLOT_DURATION_MS = {"S15": 0.5, "S375": 2.0}


def _scpi_enum_int(value: str, prefix: str) -> int:
    """Parse an SMW enum token such as 'R16' or 'RU1' into an int."""
    token = value.strip().upper()
    prefix = prefix.upper()
    if token.startswith(prefix):
        token = token[len(prefix):]
    return int(token)


def calculate_npusch_ack_periodicity(smw: RsInstrument) -> int:
    """Query SMW TRANs1 and return NPUSCH format  ACK duration in ms.

    T_ACK = N_Rep * N_RU * N_slots^RU * T_slot
    """
    niot_prefix = ":SOURce1:BB:EUTRa:UL:UE1:NIOT:"
    trans_prefix = f"{niot_prefix}TRANs1:"

    scs = query_scpi(smw, f"{niot_prefix}SCSPacing?").upper()
    try:
        slot_duration_ms = _NIOT_SLOT_DURATION_MS[scs]
    except KeyError as exc:
        raise ValueError(f"Unsupported NB-IoT subcarrier spacing: {scs}") from exc

    n_rep = _scpi_enum_int(query_scpi(smw, f"{trans_prefix}REPetitions?"), "R")
    n_ru = _scpi_enum_int(query_scpi(smw, f"{trans_prefix}NRUNits?"), "RU")
    n_slots = int(query_scpi(smw, f"{trans_prefix}NSLTs?"))
    if n_slots <= 0:
        raise ValueError(f"NPUSCH slots per RU is {n_slots}; configure format 2 first")

    ack_duration_ms = n_rep * n_ru * n_slots * slot_duration_ms
    return int(ack_duration_ms)


def ajust_arb_sequence_length(smw: RsInstrument, prach_mode='', sources: int = 1, ue: int | None = None):
    ep = set_entity(ue)

    for s in range(1, sources + 1):
        prefix = f"{ep}:SOURce{s}:BB:EUTR:"

        suggested_len = int(query_scpi(smw, f"{prefix}UL:UE1:{prach_mode}NIOT:ARB:SUGGested?"))
        write_scpi(smw, f"{prefix}SLENgth {suggested_len}")


def calculate_arb_length(time_segment: int):
    """Return the smallest common multiple of ack_duration_ms and 10 ms that is > suggested_len_ms."""
    period_ms = math.lcm(int(time_segment), 10)
    return period_ms


def set_arb_length(smw: RsInstrument, arb_length: int):
    write_scpi(smw, f":SOURce1:BB:EUTRa:SUSL {arb_length}")


def set_arb_length_signal_pattern(smw: RsInstrument, tdd: bool = False, time_segment_ms: int = 1):
    if not tdd:
        arb_length = calculate_arb_length(time_segment_ms)
    else:
        # for TDD, idle duration equal to valid signal duration
        arb_length = 2 * 10 * int(query_scpi(smw, ":SOURce1:BB:EUTR:UL:UE1:NIOT:ARB:SUGGested?"))

    set_arb_length(smw, arb_length)


def check_ntn_freq_timing_offset(smw: RsInstrument,
    san_cfg_prefix: str,
    freq_offset_hz: int,
    timing_offset: float) -> None:

    measured_freq_offset = query_scpi(
        smw, f"{san_cfg_prefix}FOFFset?"
    )
    if float(measured_freq_offset) != freq_offset_hz:
        raise ValueError(
            f"frequency offset is {measured_freq_offset} Hz, "
            f"expected {freq_offset_hz} Hz"
        )

    measured_timing_offset = query_scpi(
        smw, f"{san_cfg_prefix}TOFFset?"
    )
    if float(measured_timing_offset) != timing_offset:
        raise ValueError(
            f"timing offset is {measured_timing_offset} us/RU, "
            f"expected {timing_offset} us/RU"
        )


def configure_npusch_signal_pattern(
    smw: RsInstrument,
    npusch_format: int,
    freq_offset_hz: int,
    timing_offset: float,
    tdd: bool = False,
    repetition_num: int = 16,
    frc_on: bool = False,
    occ_sequence_index: int = None
) -> int:
    """Configure NPUSCH format  for Chapter 8 ACK missed detection tests."""
    print(f"Configuring NPUSCH format {npusch_format} (repetitions {repetition_num})...")
    try:
        if repetition_num not in (2, 4, 8, 16):
            raise ValueError(f"Unsupported NPUSCH format {npusch_format} repetition number: {repetition_num}")

        if tdd:
            set_tdd_config(smw)

        write_scpi(smw, ":SOURce1:BB:EUTRa:UL:UE1:MODE STD")
        write_scpi(smw, ":SOURce1:BB:EUTRa:UL:UE1:SAN:TEST:STATe 1")

        num_trans = NPUSCH_NUM_TRANSMISSION["TDD" if tdd else "FDD"]
        write_scpi(smw, f":SOURce1:BB:EUTRa:UL:UE1:NIOT:NTRansmiss {num_trans}")

        for i in range(1, num_trans + 1):
            prefix = f":SOURce1:BB:EUTRa:UL:UE1:NIOT:TRANs{i}:"
            write_scpi(smw, f"{prefix}FORMat F{npusch_format}")

            # for NPUSCH format 2
            if not frc_on:
                write_scpi(smw, f"{prefix}REPetitions R{repetition_num}")
                write_scpi(smw, f"{prefix}SIRF 0")
                write_scpi(smw, f"{prefix}HARQ:PATTern #H1,1")

            # for NPUSCH format 1 OCC
            if occ_sequence_index is not None:
                write_scpi(smw, f"{prefix}SAN:OCC:STATe 1")
                write_scpi(smw, f"{prefix}SAN:OCC:SINDex OSI{occ_sequence_index}")

        san_cfg_prefix = ":SOURce1:BB:EUTRa:UL:UE1:NIOT:TRANs1:SAN:"
        check_ntn_freq_timing_offset(smw, san_cfg_prefix, freq_offset_hz, timing_offset)

        # ACK + equal idle; 1 subframe = 1 ms. Query after NPUSCH allocation set after FRC on
        if not tdd:
            ack_duration_ms = calculate_npusch_ack_periodicity(smw)
            time_segment_ms = 2 * ack_duration_ms

            print(
                f"NPUSCH format {npusch_format} signal_pattern configured: "
                f"(ACK duration={ack_duration_ms} ms, start SF step={time_segment_ms})."
            )

            for i in range(1, num_trans + 1):
                write_scpi(smw, f":SOURce1:BB:EUTRa:UL:UE1:NIOT:TRANs{i}:STSFrame {(i - 1) * time_segment_ms}")
        else:
            time_segment_ms = None

        print(
            f"NPUSCH format {npusch_format} signal_pattern configured successfully ."
        )

        print("--------------------------------")

        return time_segment_ms
    except Exception as exc:
        raise RuntimeError(f"NPUSCH configuration failed: {exc}") from exc


# Annex A.5 FRC parameters for eMTC PUSCH (§8.2.1).
# CE level 0/1 = CEModeA; 2/3 = CEModeB.
_EMTC_PUSCH_FRC: dict[str, dict[str, int]] = {
    "FRC-A5-1": {"n_rb": 1, "tbs": 104, "ce_level": "CE23"},
    "FRC-A5-2": {"n_rb": 6, "tbs": 600, "ce_level": "CE01"},
}


def configure_emtc_pusch(
    smw: RsInstrument,
    frc: str,
    repetition_num: int,
    freq_offset_hz: int,
    timing_offset: float,
    ue_id: int = 1,
    cell_id: int = 150,
    source: int = 1,
    ue: int | None = None,
) -> None:
    """Configure eMTC PUSCH for TS 36.181 §8.2.1 (CEMode A/B).

    Sets UE release to eMTC, CE level, one PUSCH transmission from Table A.5-1
    (narrowband 0, lowest RBs, frequency hopping off), and baseband frequency offset.
    """
    try:
        alloc = _EMTC_PUSCH_FRC[frc]
    except KeyError as exc:
        raise ValueError(f"Unsupported eMTC PUSCH FRC: {frc}") from exc
    if repetition_num not in (8, 256):
        raise ValueError(f"Unsupported eMTC PUSCH repetition number: {repetition_num}")

    print(
        f"Configuring eMTC PUSCH ({frc}, repetitions {repetition_num}, "
        f"CE level {alloc['ce_level']})..."
    )
    try:
        ep = set_entity(ue)

        prefix = f"{ep}:SOURce{source}:BB:EUTR:"
        write_scpi(smw, f"{prefix}STDM IOT")
        write_scpi(smw, f"{prefix}LINK UP")
        write_scpi(smw, f"{prefix}UL:BW BW1_40")
        write_scpi(smw, f"{prefix}UL:PUSCh:NHOPping 0")
        write_scpi(smw, f"{prefix}UL:PLCI:CID {cell_id}")

        write_scpi(smw, f"{prefix}UL:UE1:STATe 1")
        write_scpi(smw, f"{prefix}UL:UE1:ID {ue_id}")

        ue_prefix = f"{ep}:SOURce{source}:BB:EUTRa:UL:UE1:"
        write_scpi(smw, f"{ue_prefix}RELease EMTC")
        write_scpi(smw, f"{ue_prefix}MODE STD")

        write_scpi(smw, f"{ue_prefix}CELL0:PUSCh:SCRambling:STATe 1")
        write_scpi(smw, f"{ue_prefix}CELL0:PUSCh:CCODing:STATe 1")

        write_scpi(smw, f"{ue_prefix}EMTC:CELevel {alloc['ce_level']}")
        write_scpi(smw, f"{ue_prefix}EMTC:NTRansmiss 1")

        trans = f"{ue_prefix}EMTC:TRANs1:"
        write_scpi(smw, f"{trans}CONTent PUSCh")
        write_scpi(smw, f"{trans}MODulation QPSK")
        write_scpi(smw, f"{trans}REPetitions R{repetition_num}")
        write_scpi(smw, f"{trans}STSFrame 0")
        write_scpi(smw, f"{trans}STNBand 0")
        write_scpi(smw, f"{trans}NRBLocks {alloc['n_rb']}")
        write_scpi(smw, f"{trans}RBOFfset 0")

        try:
            frc_type = FRC_TYPE[frc]
        except KeyError as exc:
            raise ValueError(f"No FRC type mapping for eMTC PUSCH FRC: {frc}") from exc
        write_scpi(smw, f"{prefix}UL:UE1:CELL0:FRC:STATe 1")
        write_scpi(smw, f"{prefix}UL:UE1:CELL0:FRC:TYPE {frc_type}")
        write_scpi(smw, f"{prefix}STDMode IOT")

        write_scpi(smw, f":SOURce1:BB:FOFFset {freq_offset_hz}")
        write_scpi(smw, f"{ue_prefix}SAN:TEST:STATe 1")

        san_cfg_prefix = f"{ep}:SOURce{source}:BB:EUTRa:UL:UE1:EMTC:TRANs1:SAN:"
        check_ntn_freq_timing_offset(smw, san_cfg_prefix, freq_offset_hz, timing_offset)

        suggested = int(query_scpi(smw, f"{ue_prefix}EMTC:ARB:SUGGested?"))
        set_arb_length(smw, max(suggested * 10, 10))

        print(
            f"eMTC PUSCH configured successfully "
            f"UE ID={ue_id}, Cell ID={cell_id}, freq offset={freq_offset_hz} Hz)"
        )
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"eMTC PUSCH configuration failed: {exc}") from exc


def configure_emtc_pucch(
    smw: RsInstrument,
    repetition_num: int,
    freq_offset_hz: int,
    timing_offset: float,
    ue_id: int = 1,
    cell_id: int = 150,
    source: int = 1,
    ue: int | None = None,
) -> None:
    """Configure eMTC PUCCH format 1a for TS 36.181 §8.3.1 (ACK missed detection).

    CEMode A (CE level 0/1), 1.4 MHz, format 1a, 1 RB. FDD uses five PUCCH
    transmissions so that ACK and an equal idle period form a continuous
    pattern (figure 8.3.1.4.2-1): start subframes 0, 16, 32, 48, 64 for
    8 repetitions. Frequency hopping is off (Table 8.3.1.2.1-1 NOTE 1);
    narrowband hopping interval is 4 subframes (FDD CEMode A).
    """
    if repetition_num != 8:
        raise ValueError(
            f"Unsupported eMTC PUCCH format 1a repetition number: {repetition_num}"
        )

    # FDD: five transmissions (ACK + equal idle) for a continuous pattern.
    num_trans = NPUSCH_NUM_TRANSMISSION["FDD"]
    period_sf = 2 * repetition_num

    print(
        f"Configuring eMTC PUCCH format 1a (repetitions {repetition_num}, "
        f"{num_trans} transmissions, period {period_sf} SF)..."
    )
    try:
        ep = set_entity(ue)
        prefix = f"{ep}:SOURce{source}:BB:EUTR:"
        ue_prefix = f"{ep}:SOURce{source}:BB:EUTRa:UL:UE1:"

        write_scpi(smw, f"{prefix}STDM IOT")
        write_scpi(smw, f"{prefix}LINK UP")
        write_scpi(smw, f"{prefix}UL:BW BW1_40")

        write_scpi(smw, f"{prefix}UL:PLCI:CID {cell_id}")

        write_scpi(smw, f"{prefix}UL:UE1:STATe 1")
        write_scpi(smw, f"{prefix}UL:UE1:ID {ue_id}")

        write_scpi(smw, f"{ue_prefix}RELease EMTC")
        write_scpi(smw, f"{ue_prefix}MODE STD")
        write_scpi(smw, f"{ue_prefix}STATe 1")

        write_scpi(smw, f"{ue_prefix}SAN:TEST:STATe 1")

        write_scpi(smw, f"{ue_prefix}EMTC:CELevel CE01")
        write_scpi(smw, f"{ue_prefix}EMTC:HOPP H4")
        write_scpi(smw, f"{ue_prefix}EMTC:NTRansmiss {num_trans}")

        for i in range(1, num_trans + 1):
            trans = f"{ue_prefix}EMTC:TRANs{i}:"
            write_scpi(smw, f"{trans}CONTent PUCCh")
            write_scpi(smw, f"{trans}FORMat F1A")
            write_scpi(smw, f"{trans}REPetitions R{repetition_num}")
            write_scpi(smw, f"{trans}STSFrame {(i - 1) * period_sf}")
            write_scpi(smw, f"{trans}POWer 0")
            write_scpi(smw, f"{trans}NPUCch 1")
            write_scpi(smw, f"{trans}PUCCh:HARQ:PATTern #H1,1")

        san_cfg_prefix = f"{ep}:SOURce{source}:BB:EUTRa:UL:UE1:EMTC:TRANs1:SAN:"
        check_ntn_freq_timing_offset(smw, san_cfg_prefix, freq_offset_hz, timing_offset)

        suggested = int(query_scpi(smw, f"{ue_prefix}EMTC:ARB:SUGGested?"))
        set_arb_length(smw, suggested * 10)

        print(
            f"eMTC PUCCH format 1a configured successfully "
            f"(start SF step={period_sf}, freq offset={freq_offset_hz} Hz)"
        )
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"eMTC PUCCH configuration failed: {exc}") from exc


# Table A.6-1 test preambles for coverage enhancement.
# Requirements use PRACH Configuration Indexes (3, 19, 35, 51)
# for Format 0, Format 1, Format 2, and Format 3.
# ncs_conf is SMW NCSConf (zeroCorrelationZoneConfig, unrestricted set).
# Table A.6-1 Ncs 13 / 167 / 167 / 0 maps to NCSConf 1 / 13 / 13 / 0.
EMTC_PRACH_PREAMBLE: dict[int, dict[str, int]] = {
    0: {"config_index": 3, "ncs_conf": 1, "logical_sequence_index": 22, "v": 32},
    1: {"config_index": 19, "ncs_conf": 13, "logical_sequence_index": 22, "v": 2},
    2: {"config_index": 35, "ncs_conf": 13, "logical_sequence_index": 22, "v": 0},
    3: {"config_index": 51, "ncs_conf": 0, "logical_sequence_index": 22, "v": 0},
}


def configure_emtc_prach(
    smw: RsInstrument,
    burst_format: int,
    repetition_num: int,
    freq_offset_hz: int,
    timing_offset: float,
    ue_id: int = 0,
    cell_id: int = 150,
    source: int = 1,
    ue: int | None = None,
) -> None:
    """Configure eMTC PRACH for TS 36.181 §8.4.1 (preamble detection).

    Preamble parameters come from ``EMTC_PRACH_PREAMBLE`` (Table A.6-1) for
    ``burst_format``. Δt equals ``timing_offset`` (µs). ``freq_offset_hz`` is
    the baseband frequency offset.
    """
    try:
        preamble = EMTC_PRACH_PREAMBLE[burst_format]
    except KeyError as exc:
        raise ValueError(f"Unsupported eMTC PRACH burst format: {burst_format}") from exc
    if repetition_num not in (8, 16):
        raise ValueError(f"Unsupported PRACH repetition number for SAN testing: {repetition_num}")

    print(
        f"Configuring eMTC PRACH (format {burst_format}, "
        f"PRACH config {preamble['config_index']}, "
        f"repetitions {repetition_num}, time offset {timing_offset} us)..."
    )
    try:
        ep = set_entity(ue)
        prefix = f"{ep}:SOURce{source}:BB:EUTR:"
        ue_prefix = f"{ep}:SOURce{source}:BB:EUTRa:UL:UE1:"
        prach = f"{ep}:SOURce{source}:BB:EUTRa:UL:PRACh:EMTC:"

        write_scpi(smw, f"{prefix}STDM IOT")
        write_scpi(smw, f"{prefix}LINK UP")
        write_scpi(smw, f"{prefix}UL:BW BW1_40")
        write_scpi(smw, f"{prefix}UL:PLCI:CID {cell_id}")

        write_scpi(smw, f"{prefix}UL:UE1:STATe 1")
        write_scpi(smw, f"{prefix}UL:UE1:ID {ue_id}")
        write_scpi(smw, f"{ue_prefix}RELease EMTC")
        write_scpi(smw, f"{ue_prefix}MODE PRAC")
        write_scpi(smw, f"{ue_prefix}STATe 1")

        write_scpi(smw, f"{prach}HOFF 0")
        write_scpi(smw, f"{prach}RSET URES")

        # CE level 0 is the attempt under test. Levels 1–3 are unused.
        write_scpi(smw, f"{prach}CELV0:CONFig {preamble['config_index']}")
        write_scpi(smw, f"{prach}CELV0:FOFFset 0")
        write_scpi(smw, f"{prach}CELV0:HOPPing 0")
        write_scpi(smw, f"{prach}CELV0:REPetit R{repetition_num}")
        write_scpi(smw, f"{prach}CELV0:SSFPeriod NONE")

        write_scpi(smw, f"{ue_prefix}PRACh:EMTC:PRATtempts 1")
        att = f"{ue_prefix}PRACh:ATT0:EMTC:"
        write_scpi(smw, f"{att}CELV 0")
        write_scpi(smw, f"{att}SFSTart 1")
        write_scpi(smw, f"{att}NCSConf {preamble['ncs_conf']}")
        write_scpi(smw, f"{att}RSEQuence {preamble['logical_sequence_index']}")
        write_scpi(smw, f"{att}SINDex {preamble['v']}")
        write_scpi(smw, f"{att}DT {timing_offset}")
        write_scpi(smw, f"{att}POWer 0")

        write_scpi(smw, f"{ep}:SOURce{source}:BB:FOFFset {freq_offset_hz}")

        suggested = int(query_scpi(smw, f"{ue_prefix}PRACh:EMTC:ARB:SUGGested?"))
        write_scpi(smw, f"{prefix}SLENgth {suggested}")

        print(
            f"eMTC PRACH configured successfully "
            f"(ARB {suggested} frames, freq offset={freq_offset_hz} Hz)"
        )
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"eMTC PRACH configuration failed: {exc}") from exc

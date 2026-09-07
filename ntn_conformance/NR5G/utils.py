"""NR5G-specific utilities: FRC map, base parser, and SMW baseband configuration."""

import argparse
from pathlib import Path

from RsInstrument import RsInstrument

from utils.config_utils import load_ini_as_namespace as _load_ini_generic
from utils.helpers import parse_frequency
from utils.scpi_utils import write_scpi

# Mapping between 3GPP FRCs and the corresponding SCPI names
NTN_FRC_TYPE: dict[str, str] = {
    **{f"G-FR1-NTN-A1-{n}": f"TS38181_FR1A1{n}" for n in range(1, 10)},
    "G-FR1-NTN-A1-10": "FR1NA110",
    "G-FR1-NTN-A1-11": "FR1NA111",
    "G-FR1-NTN-A1-12": "FR1NA112",
    **{f"G-FR1-NTN-A2-{n}": f"TS38181_FR1A2{n}" for n in range(1, 7)},
    "G-FR1-NTN-A2-7": "FR1NA27",
    **{f"G-FR1-NTN-A3-{n}": f"TS38181_FR1A3{n}" for n in range(1, 7)},
    "G-FR1-NTN-A3-7": "FR1NA37",
    "G-FR1-NTN-A3-8": "FR1NA38",
    "G-FR1-NTN-A3A-1": "TS38181_FR1A3A1",
    "G-FR1-NTN-A3A-2": "FR1NA3A2",
    "G-FR1-A3A-2": "FR1NA3A2",
    "G-FR1-NTN-A3A-4": "FR1NA3A4",
}

NUM_RBS: dict[tuple[int, int], int] = {
    (3, 15): 15,
    (5, 15): 25,
    (5, 30): 11,
    (10, 15): 52,
    (10, 30): 24,
}


def load_ini_as_namespace(path: str | Path) -> argparse.Namespace:
    """Load an NR5G test INI, merging instrument.ini and NR5G/options.ini."""
    return _load_ini_generic(
        path,
        extra_configs=(Path(__file__).resolve().parent / "options.ini",),
        freq_keys=frozenset({"freq", "interferer_freq", "ful_low", "ful_high"}),
        bool_keys=frozenset({
            "log_scpi", "nb_iot_inband", "additional_dmrs",
        }),
    )


def set_entity(ue: int | None) -> str:
    """Return the :ENTity{n} prefix string, or empty string when ue is None.

    ue is 0-based; SCPI uses :ENTity1 for ue=0, :ENTity2 for ue=1, etc.
    """
    return f":ENTity{ue + 1}" if ue is not None else ""


def build_base_parser(
    description: str,
    *,
    include_class: bool = True,
    include_ue_id: bool = True,
    require_num_rx: bool = False,
):
    """Build an ArgumentParser with the common BW/SCS/freq/IP options shared by all scripts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--bw", dest="bw", type=int, required=True,
        help="Channel bandwidth of the test case in MHz (e.g. 10).",
    )
    parser.add_argument(
        "--scs", type=int, required=True,
        help="Sub-carrier spacing of the test case in kHz (e.g. 15, 30, 60).",
    )
    parser.add_argument(
        "--num-rx", type=int, choices=(1, 2), required=require_num_rx,
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
        "--cell-id", dest="cell_id", type=int, default=0,
        help="NR5G cell ID for the wanted signal on Source1 (default: 0).",
    )
    if include_ue_id:
        parser.add_argument(
            "--ue-id", dest="ue_id", type=int, default=0,
            help="NR5G UE ID for the wanted signal on Source1 (default: 0).",
        )
    parser.add_argument("--ip", help="SMW IP address. When set, the script connects over raw TCP/IP socket.")
    parser.add_argument(
        "--log-scpi", action="store_true",
        help="Write all SCPI commands sent to the SMW during this run to scpi-list.iec in ntn_conformance/.",
    )
    return parser


def configure_triggers(smw: RsInstrument, sources: int = 1, *, ue: int | None = None):
    """Configure NR5G triggers before any baseband settings.

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
        write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:TRIGger:SEQuence AAUT")
        write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:TRIGger:SOURce EGT1")
        if sources == 2:
            write_scpi(smw, f"{ep}:SOURce2:BB:NR5G:TRIGger:SEQuence AAUT")
            write_scpi(smw, f"{ep}:SOURce2:BB:NR5G:TRIGger:SOURce EGT1")
        write_scpi(smw, ":SOURce1:INPut:USER3:DIRection INP")
        write_scpi(smw, ":SOURce1:INPut:USER3:SIGNal TRIG1")
        print(f"Trigger{'s' if sources == 2 else ''} configured successfully")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Trigger configuration failed: {exc}") from exc


def configure_advance_mode(smw: RsInstrument, num_rx: int, *, multi_ue: bool = False):
    """Configure SMW advanced fading mode for 1 TX and multiple RX paths.

    MIMO1X2 corresponds to 1 TX and 2 RX antennas. Call only when num_rx is not 1.
    When multiUE is True, uses MIMO2X1X1 (1 RX) or MIMO2X1X2 (2 RX) for dual-UE setups.
    """
    if multi_ue is False and num_rx == 1:
        return
    # FAAFBB stands for MIMO2X1X1
    fading_by_num_rx = {1: "FAAFBB", 2: "MIMO2X1X2"} if multi_ue else {2: "MIMO1X2"}
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


def configure_dmrsID(smw: RsInstrument, *, ue: int):
    """Configure DMRS identity for multi-UE setups (§8.2.3).

    UE 0 (moving UE) uses DMRS ID 0; UE 1 (stationary UE) uses DMRS ID 1.
    """
    if ue not in (0, 1):
        raise ValueError(f"ue must be 0 or 1, got {ue}")
    dmrs_id = ue
    ep = set_entity(ue)
    print(f"Configuring DMRS ID ({dmrs_id}) on UE {ue}...")
    try:
        write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:UBWP:USER0:CELL0:UL:BWP0:PUSCh:DMTA:SID0 {dmrs_id}")
        write_scpi(
            smw,
            f"{ep}:SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:PUSCh:DMRS:NSID {dmrs_id}",
        )
        print(f"DMRS ID configured successfully (UE {ue}, ID={dmrs_id})")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"DMRS ID configuration failed: {exc}") from exc


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
    try:
        for source in range(1, sources + 1):
            write_scpi(smw, f"{ep}:SOURce{source}:FSIMulator:STANdard {fsim_standard}")
            write_scpi(smw, f"{ep}:SOURce{source}:FSIMulator:STATe 1")
        print(f"Fading configured successfully ({propagation})")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Fading configuration failed: {exc}") from exc


def configure_node(
    smw: RsInstrument,
    bw: int,
    scs: int,
    freq: int = 1_620_000_000,
    *,
    cell_id: int = 0,
    source: int = 1,
    link: str = "UP",
    ue: int | None = None,
):
    """Configure NR5G node settings for the given source."""
    if source == 1:
        print("Configuring wanted signal (Source1)...")
    try:
        ep = set_entity(ue)
        prefix = f"{ep}:SOURce{source}:BB:NR5G:"
        write_scpi(smw, f"{prefix}STATe 1")
        write_scpi(smw, f"{prefix}LINK {link}")
        write_scpi(smw, f"{prefix}NODE:CELL0:CELLid {cell_id}")
        if source == 1 or link == "UP":
            write_scpi(smw, f"{prefix}NODE:CELL0:TAPos 2")
        write_scpi(smw, f"{prefix}NODE:CELL0:CARDeply FR1LT3")
        write_scpi(smw, f"{prefix}NODE:RFPHase:MODE MAN")
        write_scpi(smw, f"{prefix}NODE:CELL0:PCFReq {freq}")
        write_scpi(smw, f"{prefix}NODE:CELL0:CBW BW{bw}")
        selected_txbw = f"S{scs}K"
        write_scpi(smw, f"{prefix}NODE:CELL0:TXBW:{selected_txbw}:USE 1")
        for txbw in ("S15K", "S30K", "S60K"):
            if txbw != selected_txbw:
                write_scpi(smw, f"{prefix}NODE:CELL0:TXBW:{txbw}:USE 0")
        write_scpi(smw, f"{prefix}NODE:CELL0:TXBW:RESolve")
        print(f"Node configured successfully (BW={bw} MHz, SCS={scs} kHz, freq={freq} Hz, Cell ID={cell_id})")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Node configuration failed: {exc}") from exc


def configure_ueid(
    smw: RsInstrument,
    ue_id: int = 0,
    *,
    source: int = 1,
    ue: int | None = None,
):
    """Set NR5G UE ID for the given source and optional multi-UE entity."""
    ep = set_entity(ue)
    write_scpi(smw, f"{ep}:SOURce{source}:BB:NR5G:UBWP:USER0:UEID {ue_id}")


def configure_frc(
    smw: RsInstrument,
    ref_meas_channel: str,
    source: int = 1,
    frc_type_map: dict[str, str] | None = None,
    rb_offset: int = 0,
    *,
    map_type: str | None = None,
    ue: int | None = None,
    ue_id: int = 0,
):
    """Select the FRC type matching the given reference measurement channel."""
    print(f"Configuring FRC ({ref_meas_channel})...")
    try:
        mapping = NTN_FRC_TYPE if frc_type_map is None else frc_type_map
        try:
            frc_type = mapping[ref_meas_channel]
        except KeyError as exc:
            raise ValueError(f"No FRC type mapping for reference measurement channel: {ref_meas_channel}") from exc
        ep = set_entity(ue)
        prefix = f"{ep}:SOURce{source}:BB:NR5G:"
        write_scpi(smw, f"{prefix}UBWP:USER0:USCH:CCODing:STATe 1")
        write_scpi(smw, f"{prefix}UBWP:USER0:CELL0:UL:BWP0:FRC:STATe 1")
        write_scpi(smw, f"{prefix}UBWP:USER0:CELL0:UL:BWP0:FRC:TYPE {frc_type}")
        configure_ueid(smw, ue_id, source=source, ue=ue)
        write_scpi(smw, f"{prefix}UBWP:USER0:CELL0:UL:BWP0:FRC:RBOFfset {rb_offset}")
        if map_type is not None:
            write_scpi(smw, f"{prefix}UBWP:USER0:CELL0:UL:BWP0:FRC:MAPType {map_type}")
            write_scpi(smw, f"{prefix}UBWP:USER0:CELL0:UL:BWP0:FRC:PTRs:STATe 0")

        print(f"FRC configured successfully ({ref_meas_channel})")
        print("--------------------------------")
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
    """Configure AWGN interference and NR5G output power reference settings.
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
            write_scpi(smw, f"{prefix}BWIDth:RATio 1")
            write_scpi(smw, f"{prefix}DISP:MODE {disp_mode}")
            write_scpi(smw, f"{prefix}POWer:MODE CN")
            write_scpi(smw, f"{prefix}POWer:RMODe CARR")
            write_scpi(smw, f"{prefix}BWIDth {awgn_bw_hz}")
            write_scpi(smw, f"{prefix}CNRatio {snr_db}")
            write_scpi(smw, f"{prefix}STATe 1")
    write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:OUTPut:POWer:MODE PSDC")
    write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:OUTPut:POWer:RSBW {awgn_bw_hz}")
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


def configure_harq(smw: RsInstrument, *, timing_advance: bool = False, ue: int | None = None):
    """Configure HARQ feedback for NR5G uplink testing (Chapter 8 only)."""
    print("Configuring HARQ feedback...")
    ep = set_entity(ue)
    try:
        write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:HFB:MODE SER")
        write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:HFB:SRATe R1M9")
        write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:HFB:DELay -2")
        write_scpi(smw, ":SOURce1:INPut:TM3:DIRection INP")
        write_scpi(smw, ":SOURce1:INPut:TM3:SIGNal FEED")
        write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:HFB:BASeband 0") 
        if timing_advance:
            write_scpi(smw, f"{ep}:SOURce1:BB:NR5G:HFB:TAMode 1")
        print("HARQ feedback configured successfully")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"HARQ feedback configuration failed: {exc}") from exc


def configure_repTypeA(smw: RsInstrument):
    """Configure PUSCH repetition Type A scheduler allocation (§8.2.4)."""
    prefix = ":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:"
    print("Configuring PUSCH repetition Type A...")
    write_scpi(smw, f"{prefix}REPetitions TA")
    write_scpi(smw, f"{prefix}PERiod 1")
    write_scpi(smw, f"{prefix}DURation 1")
    write_scpi(smw, f"{prefix}AGFT F2")
    print("PUSCH repetition Type A configured successfully.")
    print("--------------------------------")


def configure_pucch(
    smw: RsInstrument,
    fmt: int,
    bw: int,
    scs: int,
    *,
    additional_dmrs: bool | None = None,
    ack_pattern: str | None = None,
    section: str | None = None,
    multi_slot: bool = False,
):
    """Configure PUCCH allocation for Chapter 8 tests."""
    try:
        num_rbs = NUM_RBS[(bw, scs)]
    except KeyError as exc:
        raise ValueError(f"No NUM_RBS entry for BW={bw} MHz, SCS={scs} kHz") from exc

    adrmrs_state = 1 if additional_dmrs else 0
    prefix = ":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:"
    print(f"Configuring PUCCH Format {fmt}...")
    try:
        write_scpi(smw, f":SOURce1:BB:NR5G:UBWP:USER0:CELL0:UL:BWP0:PUCCh:ADMRs:STATe {adrmrs_state}")
        write_scpi(smw, f"{prefix}CONTent PUCC")
        write_scpi(smw, f"{prefix}FMT F{fmt}")

        if fmt == 0:
            write_scpi(smw, f"{prefix}SYMNumber 2")
            write_scpi(smw, f"{prefix}SYMoffset 12")
            write_scpi(smw, f"{prefix}PUCCh:ISFHopping 1")
            write_scpi(smw, f"{prefix}RBNumber 1")
            write_scpi(smw, f"{prefix}PUCCh:SHOPping {num_rbs - 1}")
            write_scpi(smw, f"{prefix}PUCCh:PL:ACK:BITS 1")
            write_scpi(smw, f"{prefix}PUCCh:PL:ACK:PATTern #H1,1")
            write_scpi(smw, f"{prefix}REPetitions SLOT")
        elif fmt == 1:
            if multi_slot:
                allocations = [(0, 0), (num_rbs - 1, 1)]
                pattern = ack_pattern if ack_pattern is not None else "#H3,2"

                def multislot_alloc(p, rb_offset, slot=None):
                    write_scpi(smw, f"{p}CONTent PUCC")
                    write_scpi(smw, f"{p}FMT F1")
                    write_scpi(smw, f"{p}RBNumber 1")
                    write_scpi(smw, f"{p}RBOffset {rb_offset}")
                    if slot is not None:
                        write_scpi(smw, f"{p}SLOT {slot}")
                    write_scpi(smw, f"{p}SYMNumber 14")
                    write_scpi(smw, f"{p}SYMoffset 0")
                    write_scpi(smw, f"{p}REPetitions CUST")
                    write_scpi(smw, f"{p}PERiod 2")
                    write_scpi(smw, f"{p}DURation 1")
                    write_scpi(smw, f"{p}PUCCh:PL:ACK:BITS 2")
                    write_scpi(smw, f"{p}PUCCh:PL:ACK:PATTern {pattern}")

                if scs == 30:
                    bwp_prefix = ":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:"
                    write_scpi(smw, f"{bwp_prefix}NALLoc 2")
                    for alloc_idx, (rb_offset, slot) in enumerate(allocations):
                        multislot_alloc(f"{bwp_prefix}ALLoc{alloc_idx}:", rb_offset, slot)
                elif scs == 15:
                    for subframe_idx, (rb_offset, _slot) in enumerate(allocations):
                        bwp_prefix = f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe_idx}:USER0:BWPart0:"
                        write_scpi(smw, f"{bwp_prefix}NALLoc 1")
                        multislot_alloc(f"{bwp_prefix}ALLoc0:", rb_offset)
            else:
                pattern = ack_pattern if ack_pattern is not None else "#H3,2"
                write_scpi(smw, f"{prefix}SYMNumber 14")
                write_scpi(smw, f"{prefix}SYMoffset 0")
                write_scpi(smw, f"{prefix}PUCCh:ISFHopping 1")
                write_scpi(smw, f"{prefix}RBNumber 1")
                write_scpi(smw, f"{prefix}PUCCh:SHOPping {num_rbs - 1}")
                write_scpi(smw, f"{prefix}PUCCh:PL:ACK:BITS 2")
                write_scpi(smw, f"{prefix}PUCCh:PL:ACK:PATTern {pattern}")
                write_scpi(smw, f"{prefix}REPetitions SLOT")
                write_scpi(smw, f"{prefix}PUCCh:FS:TDOCc 0")
        elif fmt == 2:
            if section == "8_3_3_2":
                hopping_rb = 3 if bw == 3 else num_rbs - 9
                write_scpi(smw, f"{prefix}SYMNumber 2")
                write_scpi(smw, f"{prefix}SYMoffset 12")
                write_scpi(smw, f"{prefix}PUCCh:ISFHopping 1")
                write_scpi(smw, f"{prefix}RBNumber 9")
                write_scpi(smw, f"{prefix}PUCCh:SHOPping {hopping_rb}")
                write_scpi(smw, f"{prefix}PUCCh:PL:UCI:BITS 22")
                write_scpi(smw, f"{prefix}PUCCh:PL:UCI:PATTern #H000000,22")
                write_scpi(smw, f"{prefix}REPetitions SLOT")
            elif section == "8_3_3_1":
                write_scpi(smw, f"{prefix}SYMNumber 1")
                write_scpi(smw, f"{prefix}SYMoffset 13")
                write_scpi(smw, f"{prefix}PUCCh:ISFHopping 0")
                write_scpi(smw, f"{prefix}RBNumber 4")
                write_scpi(smw, f"{prefix}PUCCh:SHOPping {num_rbs - 4}")
                write_scpi(smw, f"{prefix}PUCCh:PL:UCI:BITS 4")
                write_scpi(smw, f"{prefix}PUCCh:PL:UCI:PATTern #HF,4")
                write_scpi(smw, f"{prefix}REPetitions SLOT")
        elif fmt == 3:
            write_scpi(smw, f"{prefix}SYMNumber 14")
            write_scpi(smw, f"{prefix}SYMoffset 0")
            write_scpi(smw, f"{prefix}PUCCh:ISFHopping 1")
            write_scpi(smw, f"{prefix}RBNumber 1")
            write_scpi(smw, f"{prefix}PUCCh:SHOPping {num_rbs - 1}")
            write_scpi(smw, f"{prefix}PUCCh:PL:UCI:BITS 16")
            write_scpi(smw, f"{prefix}PUCCh:PL:UCI:PATTern #H0000,16")
            write_scpi(smw, f"{prefix}REPetitions SLOT")
        elif fmt == 4:
            write_scpi(smw, f"{prefix}SYMNumber 14")
            write_scpi(smw, f"{prefix}SYMoffset 0")
            write_scpi(smw, f"{prefix}PUCCh:ISFHopping 1")
            write_scpi(smw, f"{prefix}RBNumber 1")
            write_scpi(smw, f"{prefix}PUCCh:SHOPping {num_rbs - 1}")
            write_scpi(smw, f"{prefix}PUCCh:PL:UCI:BITS 22")
            write_scpi(smw, f"{prefix}PUCCh:PL:UCI:PATTern #H000000,22")
            write_scpi(smw, f"{prefix}REPetitions SLOT")
            write_scpi(smw, f"{prefix}PUCCh:FS:OCCindex 0")
            write_scpi(smw, f"{prefix}PUCCh:FS:OCCLength L2")
        else:
            raise ValueError(f"Unsupported PUCCH format: {fmt}")

        print(f"PUCCH Format {fmt} configured successfully")
        print("--------------------------------")
    except (ValueError, RuntimeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"PUCCH configuration failed: {exc}") from exc


def configure_repTypeA_dmrsBundling(smw: RsInstrument, scs: int):
    """Configure PUSCH repetition Type A with DMRS bundling (§8.2.5)."""
    prefix = ":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:ALLoc0:"
    print("Configuring PUSCH repetition Type A with DMRS bundling...")
    try:
        write_scpi(smw, f"{prefix}REPetitions TA")
        write_scpi(smw, f"{prefix}PERiod 1")
        write_scpi(smw, f"{prefix}DURation 1")
        write_scpi(smw, f"{prefix}AGFT {'F4' if scs == 15 else 'F8'}")
        print("PUSCH repetition Type A with DMRS bundling configured successfully.")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"PUSCH repetition Type A with DMRS bundling configuration failed: {exc}") from exc


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


def configure_prach(
    smw: RsInstrument,
    burst_format: str,
    freq_offset_hz: int,
    prach_scs: float,
) -> None:
    """Configure PRACH for Chapter 8 tests."""
    print(f"Configuring PRACH (format {burst_format})...")
    try:
        scs_pacing_map = {1.25: "N1_25", 15.0: "N15", 30.0: "N30"}
        scs_pacing = scs_pacing_map[prach_scs]

        if burst_format in ("0", "2"):
            n_cs = 13
            scs_hz = 1250  # 1.25 kHz PRACH SCS
            l_ra = 839
            logical_sequence_index = 22
            v = 32
            zc_zone = 1

            tau_cs = n_cs / (scs_hz * l_ra)
            t_offset_base = tau_cs / 2

            write_scpi(smw, ":SOURce1:BB:NR5G:OUTPut:SUSLen 20")
            for loop_idx in range(10):
                subframe = 2 * loop_idx + 1
                t_offset = t_offset_base + loop_idx * 1e-7
                bwp_prefix = f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:"
                alloc_prefix = f"{bwp_prefix}ALLoc0:"
                write_scpi(smw, f"{bwp_prefix}NALLoc 1")
                write_scpi(smw, f"{alloc_prefix}CONTent PRAC")
                write_scpi(smw, f"{alloc_prefix}PRACh:SCSPacing {scs_pacing}")
                write_scpi(smw, f"{alloc_prefix}SLOT 0")
                write_scpi(smw, f"{alloc_prefix}STATe 1")
                write_scpi(smw, f"{alloc_prefix}SYMoffset 0")
                write_scpi(smw, f"{alloc_prefix}REPetitions OFF")
                write_scpi(smw, f"{alloc_prefix}PERiod 9")
                write_scpi(smw, f"{alloc_prefix}DURation 1")
                write_scpi(smw, f"{alloc_prefix}PRACh:FORMat F{burst_format}")
                write_scpi(smw, f"{alloc_prefix}PRACh:RSET URES")
                write_scpi(smw, f"{alloc_prefix}PRACh:RSEQuence {logical_sequence_index}")
                write_scpi(smw, f"{alloc_prefix}PRACh:ZCZone {zc_zone}")
                write_scpi(smw, f"{alloc_prefix}PRACh:PRINdex {v}")
                write_scpi(smw, f"{alloc_prefix}TOFFset {t_offset:.7f}")
                print(f"Configuring PRACH (format {burst_format} - subframe {subframe})...")

            write_scpi(smw, ":SOURce1:BB:NR5G:SCHed:CELL0:SUBF0:USER0:BWPart0:NALLoc 0")
            write_scpi(smw, f":SOURce1:BB:FOFFset {freq_offset_hz}")
        elif burst_format in ("B4", "C2"):

            write_scpi(smw, ":SOURce1:BB:NR5G:OUTPut:SUSLen 90")
            for loop_idx in range(9):
                subframe = loop_idx
                t_offset = loop_idx * 1e-7
                bwp_prefix = f":SOURce1:BB:NR5G:SCHed:CELL0:SUBF{subframe}:USER0:BWPart0:"
                alloc_prefix = f"{bwp_prefix}ALLoc0:"
                write_scpi(smw, f"{bwp_prefix}NALLoc 1")
                write_scpi(smw, f"{alloc_prefix}CONTent PRAC")
                write_scpi(smw, f"{alloc_prefix}PRACh:SCSPacing {scs_pacing}")
                write_scpi(smw, f"{alloc_prefix}SLOT 0")
                write_scpi(smw, f"{alloc_prefix}STATe 1")
                write_scpi(smw, f"{alloc_prefix}SYMoffset 0")
                write_scpi(smw, f"{alloc_prefix}REPetitions CUST")
                write_scpi(smw, f"{alloc_prefix}PERiod 9")
                write_scpi(smw, f"{alloc_prefix}DURation 1")
                write_scpi(smw, f"{alloc_prefix}PRACh:FORMat F{burst_format}")
                write_scpi(smw, f"{alloc_prefix}PRACh:RSET URES")
                write_scpi(smw, f"{alloc_prefix}PRACh:RSEQuence 0")
                write_scpi(smw, f"{alloc_prefix}PRACh:ZCZone 11")
                write_scpi(smw, f"{alloc_prefix}PRACh:PRINdex 0")
                write_scpi(smw, f"{alloc_prefix}TOFFset {t_offset:.7f}")
                print(f"Configuring PRACH (format {burst_format} - subframe {subframe})...")

            write_scpi(smw, f":SOURce1:BB:FOFFset {freq_offset_hz}")
        else:
            raise ValueError(f"Unsupported PRACH burst format: {burst_format}")

        print("PRACH configured successfully.")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"PRACH configuration failed: {exc}") from exc
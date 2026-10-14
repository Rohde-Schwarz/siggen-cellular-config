"""3GPP TS 38.181 chapter 8 lookup tables.

Values are derived from 3GPP TS 38.181 for SMW configuration. They are not a
substitute for the official ETSI/3GPP publication. See NOTICE at the GitHub repository root.
"""

from typing import NamedTuple


FADING_PROFILES: dict[str, str] = {
    "NTN_TDLA100_200_LOW": "NTNTDLA100D200L",
    "NTN_TDLC5_200_LOW": "NTNTDLC5D200L",
    "NTN_TDLA100_200_SISO": "NTNTDLA100D200",
    "NTN_TDLC5_200_SISO": "NTNTDLC5D200",
}

MOV_PROP_PROFILES: dict[str, str] = {
    "MP_NTN_15": "MPNTNX15",
    "MP_NTN_30": "MPNTNX30",
}


class PuschTestConfig(NamedTuple):
    frc: str
    snr_db: float
    awgn_power_dbm: float
    awgn_bw: float


class PucchTestConfig(NamedTuple):
    snr_db: float
    awgn_power_dbm: float
    awgn_bw: float


class PrachTestConfig(NamedTuple):
    snr_db: float
    time_error_tolerance_us: float
    freq_offset_hz: int
    awgn_power_dbm: float
    awgn_bw: float


def get_pusch_test_config(
    table: dict[tuple[str, int, int, int, str], PuschTestConfig],
    pusch_type: str,
    bw: int,
    scs: int,
    num_rx: int,
    propagation: str,
) -> PuschTestConfig:
    """Return FRC, SNR, and AWGN settings from the given PUSCH performance table."""
    try:
        config = table[(pusch_type, bw, scs, num_rx, propagation)]
    except KeyError as exc:
        raise ValueError(
            f"Invalid test config: pusch_type={pusch_type}, BW={bw} MHz, "
            f"SCS={scs} kHz, num_rx={num_rx}, propagation={propagation!r}",
        ) from exc

    print("Test Configuration")
    print("--------------------------------")
    print(f"Channel Bandwidth: {bw} MHz")
    print(f"Subcarrier Spacing: {scs} kHz")
    print(f"Number of RX Antennas: {num_rx}")
    print(f"Propagation Condition: {propagation}")
    print(f"PUSCH Type: {pusch_type}")
    print(f"FRC: {config.frc}")
    print(f"SNR: {config.snr_db} dB")
    print(f"AWGN Power: {config.awgn_power_dbm} dBm")
    print(f"AWGN Bandwidth: {config.awgn_bw} MHz")
    print(f"Wanted Signal Power: {round(config.awgn_power_dbm + config.snr_db, 2)} dBm")
    print("--------------------------------")
    return config


def get_pucch_test_config(
    table: dict,
    bw: int,
    scs: int,
    num_rx: int,
    propagation: str,
    additional_dmrs: bool | None = None,
) -> PucchTestConfig:
    """Return SNR and AWGN settings from a PUCCH performance table.

    Leave additional_dmrs as None for all sections except §8.3.4 / §8.3.5
    (PUCCH Formats 3 & 4), where True/False selects the DM-RS configuration.
    """
    key = (
        (bw, scs, num_rx, propagation)
        if additional_dmrs is None
        else (bw, scs, num_rx, propagation, additional_dmrs)
    )
    try:
        config = table[key]
    except KeyError as exc:
        dmrs = f", additional_dmrs={additional_dmrs}" if additional_dmrs is not None else ""
        raise ValueError(
            f"Invalid test config: BW={bw} MHz, SCS={scs} kHz, "
            f"num_rx={num_rx}, propagation={propagation!r}{dmrs}",
        ) from exc

    print("Test Configuration")
    print("--------------------------------")
    print(f"Channel Bandwidth: {bw} MHz")
    print(f"Subcarrier Spacing: {scs} kHz")
    print(f"Number of RX Antennas: {num_rx}")
    print(f"Propagation Condition: {propagation}")
    if additional_dmrs is not None:
        print(f"additional_dmrs: {additional_dmrs}")
    print(f"SNR: {config.snr_db} dB")
    print(f"AWGN Power: {config.awgn_power_dbm} dBm")
    print(f"AWGN Bandwidth: {config.awgn_bw} MHz")
    print(f"Wanted Signal Power: {round(config.awgn_power_dbm + config.snr_db, 2)} dBm")
    print("--------------------------------")
    return config


def get_prach_test_config(
    table: dict[tuple[float, int, int, str, str], PrachTestConfig],
    scs: int,
    prach_scs: float,
    bw: int,
    num_rx: int,
    propagation: str,
    burst_format: str,
) -> PrachTestConfig:
    """Return SNR, time error tolerance, frequency offset and AWGN settings from a PRACH table.

    AWGN depends on carrier BW (not PRACH SCS); bw selects the correct AWGN power/bandwidth.
    """
    try:
        config = table[(prach_scs, bw, num_rx, propagation, burst_format)]
    except KeyError as exc:
        raise ValueError(
            f"Invalid test config: PRACH SCS={prach_scs} kHz, BW={bw} MHz, "
            f"num_rx={num_rx}, propagation={propagation!r}, burst_format={burst_format!r}",
        ) from exc

    print("Test Configuration")
    print("--------------------------------")
    print(f"Subcarrier Spacing (BWP): {scs} kHz")
    print(f"Subcarrier Spacing (PRACH): {prach_scs} kHz")
    print(f"Channel Bandwidth: {bw} MHz")
    print(f"Number of RX Antennas: {num_rx}")
    print(f"Propagation Condition: {propagation}")
    print(f"Burst Format: {burst_format}")
    print(f"SNR: {config.snr_db} dB")
    print(f"Time Error Tolerance: {config.time_error_tolerance_us} us")
    print(f"Frequency Offset: {config.freq_offset_hz} Hz")
    print(f"AWGN Power: {config.awgn_power_dbm} dBm")
    print(f"AWGN Bandwidth: {config.awgn_bw} MHz")
    print(f"Wanted Signal Power: {round(config.awgn_power_dbm + config.snr_db, 2)} dBm")
    print("--------------------------------")
    return config


"""
§8.2.1 Performance requirements for PUSCH with transform precoding disabled
"""

# Tables 8.2.1.5-1 through 8.2.1.5-4
# Key: (pusch_type, bw, scs, num_rx, propagation)
# Columns: frc, snr_db (dB), awgn_power_dbm (dBm), awgn_bw (MHz)
PUSCH_PERF_REQ_8_2_1: dict[tuple[str, int, int, int, str], PuschTestConfig] = {
    ("A", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-1", 3.8, -86.5, 4.5),
    ("A", 5, 15, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-1", 2.2, -86.5, 4.5),
    ("A", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-1", -0.1, -86.5, 4.5),
    ("A", 5, 15, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-1", -0.6, -86.5, 4.5),
    ("A", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-2", 3.5, -83.6, 8.64),
    ("A", 10, 30, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-2", 2.0, -83.6, 8.64),
    ("A", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-2", -0.4, -83.6, 8.64),
    ("A", 10, 30, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-2", -0.8, -83.6, 8.64),
    ("B", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-1", 3.9, -86.5, 4.5),
    ("B", 5, 15, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-1", 2.2, -86.5, 4.5),
    ("B", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-1", 0.0, -86.5, 4.5),
    ("B", 5, 15, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-1", -0.6, -86.5, 4.5),
    ("B", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-2", 3.5, -83.6, 8.64),
    ("B", 10, 30, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-2", 1.9, -83.6, 8.64),
    ("B", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-2", -0.4, -83.6, 8.64),
    ("B", 10, 30, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-2", -0.8, -83.6, 8.64),
}


"""
§8.2.2 Performance requirements for PUSCH with transform precoding enabled
"""

# Tables 8.2.2.5-1 through 8.2.2.5-4
# Key: (pusch_type, bw, scs, num_rx, propagation)
# Columns: frc, snr_db (dB), awgn_power_dbm (dBm), awgn_bw (MHz)
PUSCH_PERF_REQ_8_2_2: dict[tuple[str, int, int, int, str], PuschTestConfig] = {
    ("A", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-3", 4.3, -86.5, 4.5),
    ("A", 5, 15, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-3", 2.2, -86.5, 4.5),
    ("A", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-3", 0.1, -86.5, 4.5),
    ("A", 5, 15, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-3", -0.6, -86.5, 4.5),
    ("A", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-4", 4.1, -83.6, 8.64),
    ("A", 10, 30, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-4", 1.9, -83.6, 8.64),
    ("A", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-4", -0.1, -83.6, 8.64),
    ("A", 10, 30, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-4", -0.8, -83.6, 8.64),
    ("B", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-3", 4.3, -86.5, 4.5),
    ("B", 5, 15, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-3", 2.2, -86.5, 4.5),
    ("B", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-3", 0.1, -86.5, 4.5),
    ("B", 5, 15, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-3", -0.6, -86.5, 4.5),
    ("B", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-4", 4.1, -83.6, 8.64),
    ("B", 10, 30, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-4", 1.9, -83.6, 8.64),
    ("B", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-4", -0.1, -83.6, 8.64),
    ("B", 10, 30, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-4", -0.8, -83.6, 8.64),
}


"""
§8.2.3 Performance requirements for UL timing adjustment
"""

# Tables 8.2.3.5-1 and 8.2.3.5-2
# Key: (pusch_type, bw, scs, num_rx, propagation)
# Columns: frc, snr_db (dB), awgn_power_dbm (dBm), awgn_bw (MHz)
# Propagation: MP_NTN_15 (15 kHz SCS), MP_NTN_30 (30 kHz SCS)
PUSCH_PERF_REQ_8_2_3: dict[tuple[str, int, int, int, str], PuschTestConfig] = {
    ("A", 5, 15, 1, "MP_NTN_15"): PuschTestConfig("G-FR1-NTN-A3-5", 4.7, -86.5, 4.5),
    ("A", 10, 30, 1, "MP_NTN_30"): PuschTestConfig("G-FR1-NTN-A3-6", 4.2, -83.6, 8.64),
    ("A", 5, 15, 2, "MP_NTN_15"): PuschTestConfig("G-FR1-NTN-A3-5", 0.3, -86.5, 4.5),
    ("A", 10, 30, 2, "MP_NTN_30"): PuschTestConfig("G-FR1-NTN-A3-6", 0.1, -83.6, 8.64),
    ("B", 5, 15, 1, "MP_NTN_15"): PuschTestConfig("G-FR1-NTN-A3-5", 4.8, -86.5, 4.5),
    ("B", 10, 30, 1, "MP_NTN_30"): PuschTestConfig("G-FR1-NTN-A3-6", 4.2, -83.6, 8.64),
    ("B", 5, 15, 2, "MP_NTN_15"): PuschTestConfig("G-FR1-NTN-A3-5", 0.3, -86.5, 4.5),
    ("B", 10, 30, 2, "MP_NTN_30"): PuschTestConfig("G-FR1-NTN-A3-6", 0.2, -83.6, 8.64),
}


"""
§8.2.4 Performance requirements for PUSCH repetition Type A
"""

# Tables 8.2.4.5-1 through 8.2.4.5-4
# Key: (pusch_type, bw, scs, num_rx, propagation)
# Columns: frc, snr_db (dB), awgn_power_dbm (dBm), awgn_bw (MHz)
# Propagation: NTN-TDLA100-200 Low only
PUSCH_PERF_REQ_8_2_4: dict[tuple[str, int, int, int, str], PuschTestConfig] = {
    ("A", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3A-1", -4.5, -86.5, 4.5),
    ("A", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3A-1", -7.9, -86.5, 4.5),
    ("A", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-A3A-2", -4.5, -83.6, 8.64),
    ("A", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-A3A-2", -7.9, -83.6, 8.64),
    ("B", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3A-1", -4.5, -86.5, 4.5),
    ("B", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3A-1", -7.9, -86.5, 4.5),
    ("B", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-A3A-2", -4.5, -83.6, 8.64),
    ("B", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-A3A-2", -7.9, -83.6, 8.64),
}


"""
§8.2.5 Performance requirements for PUSCH with DMRS bundling
"""

# Tables 8.2.5.5-1 through 8.2.5.5-4
# Key: (pusch_type, bw, scs, num_rx, propagation)
# Columns: frc, snr_db (dB), awgn_power_dbm (dBm), awgn_bw (MHz)
# Propagation: NTN-TDLA100-200 Low only
PUSCH_PERF_REQ_8_2_5: dict[tuple[str, int, int, int, str], PuschTestConfig] = {
    ("A", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-7", -0.1, -86.5, 4.5),
    ("A", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-7", -3.6, -86.5, 4.5),
    ("A", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-8", -2.9, -83.6, 8.64),
    ("A", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-8", -6.1, -83.6, 8.64),
    ("B", 5, 15, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-7", 0.0, -86.5, 4.5),
    ("B", 5, 15, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-7", -3.5, -86.5, 4.5),
    ("B", 10, 30, 1, "NTN_TDLA100_200_SISO"): PuschTestConfig("G-FR1-NTN-A3-8", -2.8, -83.6, 8.64),
    ("B", 10, 30, 2, "NTN_TDLA100_200_LOW"): PuschTestConfig("G-FR1-NTN-A3-8", -6.1, -83.6, 8.64),
}


"""
§8.2.6 Performance requirements for PUSCH with inter-slot OCC
"""

# Tables 8.2.6.5-1 through 8.2.6.5-4
# Key: (pusch_type, bw, scs, num_rx, propagation)
# Columns: frc, snr_db (dB), awgn_power_dbm (dBm), awgn_bw (MHz)
# Propagation: NTN-TDLC5-200 Low (SISO for 1 RX, Low for 2 RX)
PUSCH_PERF_REQ_8_2_6: dict[tuple[str, int, int, int, str], PuschTestConfig] = {
    ("A", 5, 15, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3A-3", -4.5, -86.5, 4.5),
    ("A", 5, 15, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3A-3", -7.5, -86.5, 4.5),
    ("A", 10, 30, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3A-4", -4.3, -83.6, 8.64),
    ("A", 10, 30, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3A-4", -7.3, -83.6, 8.64),
    ("B", 5, 15, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3A-3", -4.6, -86.5, 4.5),
    ("B", 5, 15, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3A-3", -7.5, -86.5, 4.5),
    ("B", 10, 30, 1, "NTN_TDLC5_200_SISO"): PuschTestConfig("G-FR1-NTN-A3A-4", -4.3, -83.6, 8.64),
    ("B", 10, 30, 2, "NTN_TDLC5_200_LOW"): PuschTestConfig("G-FR1-NTN-A3A-4", -7.4, -83.6, 8.64),
}


"""
§8.3.1 PUCCH Format 0
"""

# Tables 8.3.1.5-1 and 8.3.1.5-2
# AWGN from Table 8.3.1.4.2-1
# Key: (bw, scs, num_rx, propagation)
# Columns: snr_db (dB), awgn_power_dbm (dBm), awgn_bw (MHz)
PUCCH_PERF_REQ_8_3_1: dict[tuple[int, int, int, str], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(9.5, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(3.9, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(11.7, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(5.4, -80.6, 8.64),
}


"""
§8.3.2.1 PUCCH Format 1 — NACK to ACK detection
"""

# Tables 8.3.2.1.5-1 and 8.3.2.1.5-2
# Key: (bw, scs, num_rx, propagation)
PUCCH_PERF_REQ_8_3_2_1: dict[tuple[int, int, int, str], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(2.8, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-3.5, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(3.6, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-2.9, -80.6, 8.64),
}


"""
§8.3.2.2 PUCCH Format 1 — ACK Missed Detection
"""

# Tables 8.3.2.2.5-1 and 8.3.2.2.5-2
# Key: (bw, scs, num_rx, propagation)
PUCCH_PERF_REQ_8_3_2_2: dict[tuple[int, int, int, str], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(2.1, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-4.0, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(3.7, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-2.8, -80.6, 8.64),
}


"""
§8.3.3.1 PUCCH Format 2 — ACK Missed Detection
"""

# Tables 8.3.3.1.5-1 and 8.3.3.1.5-2
# Key: (bw, scs, num_rx, propagation)
PUCCH_PERF_REQ_8_3_3_1: dict[tuple[int, int, int, str], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(15.2, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(5.3, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(12.6, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(5.0, -80.6, 8.64),
}


"""
§8.3.3.2 PUCCH Format 2 — UCI BLER
"""

# Tables 8.3.3.2.5-1 and 8.3.3.2.5-2
# AWGN from Table 8.3.3.2.4.2-1 (includes 3 MHz BW)
# Key: (bw, scs, num_rx, propagation)
PUCCH_PERF_REQ_8_3_3_2: dict[tuple[int, int, int, str], PucchTestConfig] = {
    (3, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(10.2, -85.7, 2.7),
    (3, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(3.0, -85.7, 2.7),
    (5, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(6.9, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(1.4, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(7.0, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(1.1, -80.6, 8.64),
}


"""
§8.3.4 PUCCH Format 3 — Performance requirements
"""

# Tables 8.3.4.5-1 and 8.3.4.5-2
# AWGN from Table 8.3.4.4.2-1
# Key: (bw, scs, num_rx, propagation, additional_dmrs)
PUCCH_PERF_REQ_8_3_4: dict[tuple[int, int, int, str, bool], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO", False): PucchTestConfig(7.2, -83.5, 4.5),
    (5, 15, 1, "NTN_TDLA100_200_SISO", True): PucchTestConfig(7.0, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW", False): PucchTestConfig(0.9, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW", True): PucchTestConfig(0.6, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO", False): PucchTestConfig(9.8, -80.6, 8.64),
    (10, 30, 1, "NTN_TDLA100_200_SISO", True): PucchTestConfig(9.2, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW", False): PucchTestConfig(2.2, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW", True): PucchTestConfig(1.9, -80.6, 8.64),
}


"""
§8.3.5 PUCCH Format 4 — Performance requirements
"""

# Tables 8.3.5.5-1 and 8.3.5.5-2
# AWGN from Table 8.3.5.4.2-1
# Key: (bw, scs, num_rx, propagation, additional_dmrs)
PUCCH_PERF_REQ_8_3_5: dict[tuple[int, int, int, str, bool], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO", False): PucchTestConfig(9.5, -83.5, 4.5),
    (5, 15, 1, "NTN_TDLA100_200_SISO", True): PucchTestConfig(9.2, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW", False): PucchTestConfig(3.1, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW", True): PucchTestConfig(2.8, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO", False): PucchTestConfig(11.1, -80.6, 8.64),
    (10, 30, 1, "NTN_TDLA100_200_SISO", True): PucchTestConfig(11.1, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW", False): PucchTestConfig(4.1, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW", True): PucchTestConfig(3.9, -80.6, 8.64),
}


"""
§8.3.6.1.1 Multi-slot PUCCH Format 1 — NACK to ACK detection
"""

# Tables 8.3.6.1.1.5-1 and 8.3.6.1.1.5-2
# AWGN from Table 8.3.6.1.1.4.2-1
# Key: (bw, scs, num_rx, propagation)
PUCCH_PERF_REQ_8_3_6_1_1: dict[tuple[int, int, int, str], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(1.2, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-6.0, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(1.8, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-5.0, -80.6, 8.64),
}


"""
§8.3.6.1.2 Multi-slot PUCCH Format 1 — ACK Missed Detection
"""

# Tables 8.3.6.1.2.5-1 and 8.3.6.1.2.5-2
# AWGN from Table 8.3.6.1.2.4.2-1
# Key: (bw, scs, num_rx, propagation)
PUCCH_PERF_REQ_8_3_6_1_2: dict[tuple[int, int, int, str], PucchTestConfig] = {
    (5, 15, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(-1.3, -83.5, 4.5),
    (5, 15, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-7.4, -83.5, 4.5),
    (10, 30, 1, "NTN_TDLA100_200_SISO"): PucchTestConfig(-0.6, -80.6, 8.64),
    (10, 30, 2, "NTN_TDLA100_200_LOW"): PucchTestConfig(-7.0, -80.6, 8.64),
}


"""
§8.4.1 PRACH false alarm probability and missed detection
"""

# Tables 8.4.1.5-1 (1.25 kHz SCS), 8.4.1.5-2 (15 kHz SCS), 8.4.1.5-3 (30 kHz SCS)

PRACH_PERF_REQ_8_4_1: dict[tuple[float, int, int, str, str], PrachTestConfig] = {
    # --- PRACH SCS 1.25 kHz, BW=5 MHz (AWGN from Table 8.4.1.4.2-1: -83.5 dBm / 4.5 MHz) ---
    (1.25, 5, 1, "AWGN", "0"): PrachTestConfig(-11.7, 1.04, 0, -83.5, 4.5),
    (1.25, 5, 1, "AWGN", "2"): PrachTestConfig(-17.1, 1.04, 0, -83.5, 4.5),
    (1.25, 5, 1, "NTN_TDLA100_200_SISO", "0"): PrachTestConfig(1.3, 1.33, 200, -83.5, 4.5),
    (1.25, 5, 1, "NTN_TDLA100_200_SISO", "2"): PrachTestConfig(-9.1, 1.33, 200, -83.5, 4.5),
    (1.25, 5, 2, "AWGN", "0"): PrachTestConfig(-14.2, 1.04, 0, -83.5, 4.5),
    (1.25, 5, 2, "AWGN", "2"): PrachTestConfig(-19.5, 1.04, 0, -83.5, 4.5),
    (1.25, 5, 2, "NTN_TDLA100_200_LOW", "0"): PrachTestConfig(-6.2, 1.33, 200, -83.5, 4.5),
    (1.25, 5, 2, "NTN_TDLA100_200_LOW", "2"): PrachTestConfig(-14.3, 1.33, 200, -83.5, 4.5),
    # --- PRACH SCS 1.25 kHz, BW=10 MHz (AWGN from Table 8.4.1.4.2-1: -80.6 dBm / 8.64 MHz) ---
    (1.25, 10, 1, "AWGN", "0"): PrachTestConfig(-11.7, 1.04, 0, -80.6, 8.64),
    (1.25, 10, 1, "AWGN", "2"): PrachTestConfig(-17.1, 1.04, 0, -80.6, 8.64),
    (1.25, 10, 1, "NTN_TDLA100_200_SISO", "0"): PrachTestConfig(1.3, 1.33, 200, -80.6, 8.64),
    (1.25, 10, 1, "NTN_TDLA100_200_SISO", "2"): PrachTestConfig(-9.1, 1.33, 200, -80.6, 8.64),
    (1.25, 10, 2, "AWGN", "0"): PrachTestConfig(-14.2, 1.04, 0, -80.6, 8.64),
    (1.25, 10, 2, "AWGN", "2"): PrachTestConfig(-19.5, 1.04, 0, -80.6, 8.64),
    (1.25, 10, 2, "NTN_TDLA100_200_LOW", "0"): PrachTestConfig(-6.2, 1.33, 200, -80.6, 8.64),
    (1.25, 10, 2, "NTN_TDLA100_200_LOW", "2"): PrachTestConfig(-14.3, 1.33, 200, -80.6, 8.64),
    # --- PRACH SCS 15 kHz, BW=5 MHz (AWGN from Table 8.4.1.4.2-1: -83.5 dBm / 4.5 MHz) ---
    (15.0, 5, 1, "AWGN", "B4"): PrachTestConfig(-14.3, 0.52, 0, -83.5, 4.5),
    (15.0, 5, 1, "AWGN", "C2"): PrachTestConfig(-8.9, 0.52, 0, -83.5, 4.5),
    (15.0, 5, 1, "NTN_TDLA100_200_SISO", "B4"): PrachTestConfig(-2.1, 0.81, 200, -83.5, 4.5),
    (15.0, 5, 1, "NTN_TDLA100_200_SISO", "C2"): PrachTestConfig(2.5, 0.81, 200, -83.5, 4.5),
    (15.0, 5, 2, "AWGN", "B4"): PrachTestConfig(-16.5, 0.52, 0, -83.5, 4.5),
    (15.0, 5, 2, "AWGN", "C2"): PrachTestConfig(-12.2, 0.52, 0, -83.5, 4.5),
    (15.0, 5, 2, "NTN_TDLA100_200_LOW", "B4"): PrachTestConfig(-8.4, 0.81, 200, -83.5, 4.5),
    (15.0, 5, 2, "NTN_TDLA100_200_LOW", "C2"): PrachTestConfig(-4.2, 0.81, 200, -83.5, 4.5),
    # --- PRACH SCS 15 kHz, BW=10 MHz (AWGN from Table 8.4.1.4.2-1: -80.6 dBm / 8.64 MHz) ---
    (15.0, 10, 1, "AWGN", "B4"): PrachTestConfig(-14.3, 0.52, 0, -80.6, 8.64),
    (15.0, 10, 1, "AWGN", "C2"): PrachTestConfig(-8.9, 0.52, 0, -80.6, 8.64),
    (15.0, 10, 1, "NTN_TDLA100_200_SISO", "B4"): PrachTestConfig(-2.1, 0.81, 200, -80.6, 8.64),
    (15.0, 10, 1, "NTN_TDLA100_200_SISO", "C2"): PrachTestConfig(2.5, 0.81, 200, -80.6, 8.64),
    (15.0, 10, 2, "AWGN", "B4"): PrachTestConfig(-16.5, 0.52, 0, -80.6, 8.64),
    (15.0, 10, 2, "AWGN", "C2"): PrachTestConfig(-12.2, 0.52, 0, -80.6, 8.64),
    (15.0, 10, 2, "NTN_TDLA100_200_LOW", "B4"): PrachTestConfig(-8.4, 0.81, 200, -80.6, 8.64),
    (15.0, 10, 2, "NTN_TDLA100_200_LOW", "C2"): PrachTestConfig(-4.2, 0.81, 200, -80.6, 8.64),
    # --- PRACH SCS 30 kHz, BW=5 MHz (AWGN from Table 8.4.1.4.2-1: -83.5 dBm / 4.5 MHz) ---
    # Time error tolerance from Table 8.4.1.1-1 (corrected): AWGN=0.26 us, NTN=0.55 us
    (30.0, 5, 1, "AWGN", "B4"): PrachTestConfig(-14.1, 0.26, 0, -83.5, 4.5),
    (30.0, 5, 1, "AWGN", "C2"): PrachTestConfig(-8.9, 0.26, 0, -83.5, 4.5),
    (30.0, 5, 1, "NTN_TDLA100_200_SISO", "B4"): PrachTestConfig(-3.7, 0.55, 200, -83.5, 4.5),
    (30.0, 5, 1, "NTN_TDLA100_200_SISO", "C2"): PrachTestConfig(0.7, 0.55, 200, -83.5, 4.5),
    (30.0, 5, 2, "AWGN", "B4"): PrachTestConfig(-16.2, 0.26, 0, -83.5, 4.5),
    (30.0, 5, 2, "AWGN", "C2"): PrachTestConfig(-11.6, 0.26, 0, -83.5, 4.5),
    (30.0, 5, 2, "NTN_TDLA100_200_LOW", "B4"): PrachTestConfig(-9.4, 0.55, 200, -83.5, 4.5),
    (30.0, 5, 2, "NTN_TDLA100_200_LOW", "C2"): PrachTestConfig(-5.2, 0.55, 200, -83.5, 4.5),
    # --- PRACH SCS 30 kHz, BW=10 MHz (AWGN from Table 8.4.1.4.2-1: -80.6 dBm / 8.64 MHz) ---
    (30.0, 10, 1, "AWGN", "B4"): PrachTestConfig(-14.1, 0.26, 0, -80.6, 8.64),
    (30.0, 10, 1, "AWGN", "C2"): PrachTestConfig(-8.9, 0.26, 0, -80.6, 8.64),
    (30.0, 10, 1, "NTN_TDLA100_200_SISO", "B4"): PrachTestConfig(-3.7, 0.55, 200, -80.6, 8.64),
    (30.0, 10, 1, "NTN_TDLA100_200_SISO", "C2"): PrachTestConfig(0.7, 0.55, 200, -80.6, 8.64),
    (30.0, 10, 2, "AWGN", "B4"): PrachTestConfig(-16.2, 0.26, 0, -80.6, 8.64),
    (30.0, 10, 2, "AWGN", "C2"): PrachTestConfig(-11.6, 0.26, 0, -80.6, 8.64),
    (30.0, 10, 2, "NTN_TDLA100_200_LOW", "B4"): PrachTestConfig(-9.4, 0.55, 200, -80.6, 8.64),
    (30.0, 10, 2, "NTN_TDLA100_200_LOW", "C2"): PrachTestConfig(-5.2, 0.55, 200, -80.6, 8.64),
}

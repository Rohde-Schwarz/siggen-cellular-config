"""3GPP TS 38.181 chapter 7 lookup tables.

Values are derived from 3GPP TS 38.181 for SMW configuration. They are not a
substitute for the official ETSI/3GPP publication. See NOTICE at the GitHub repository root.
"""

from typing import NamedTuple


class TestConfig(NamedTuple):
    ref_meas_channel: str
    power_dbm: float
    interfering_power_dbm: float | None = None


def get_power_levels(table: dict, bw: int, scs: int):
    """Return test configuration from the given table for the given BW/SCS."""
    try:
        return table[(bw, scs)]
    except KeyError as exc:
        raise ValueError(f"Invalid test config: BW={bw} MHz, SCS={scs} kHz") from exc


# NTN NR operating bands: uplink F_UL,low and F_UL,high in Hz
# Columns: band, F_UL_low (Hz), F_UL_high (Hz)
OPERATING_BANDS: dict[str, tuple[int, int]] = {
    "n253": (1_668_000_000, 1_675_000_000),
    "n254": (1_610_000_000, 1_626_500_000),
    "n255": (1_626_500_000, 1_660_500_000),
    "n256": (1_980_000_000, 2_010_000_000),
}


"""
§7.2 Reference sensitivity level
"""

# Table 7.2.5-1: SAN GEO class reference sensitivity levels
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm)
SAN_GEO_REF_SENS_LEVELS: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-7", -100.5),
    (5, 15): TestConfig("G-FR1-NTN-A1-1", -98.6),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -98.6),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -98.6),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -98.7),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -98.7),
    (10, 60): TestConfig("G-FR1-NTN-A1-3", -95.8),
    (15, 60): TestConfig("G-FR1-NTN-A1-3", -95.8),
    (20, 15): TestConfig("G-FR1-NTN-A1-4", -92.2),
    (20, 30): TestConfig("G-FR1-NTN-A1-5", -92.5),
    (20, 60): TestConfig("G-FR1-NTN-A1-6", -92.6),
}

# Table 7.2.5-2: SAN LEO class reference sensitivity levels
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm)
SAN_LEO_REF_SENS_LEVELS: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-7", -103.6),
    (5, 15): TestConfig("G-FR1-NTN-A1-1", -101.7),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -101.7),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -101.7),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -101.8),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -101.8),
    (10, 60): TestConfig("G-FR1-NTN-A1-3", -98.9),
    (15, 60): TestConfig("G-FR1-NTN-A1-3", -98.9),
    (20, 15): TestConfig("G-FR1-NTN-A1-4", -95.3),
    (20, 30): TestConfig("G-FR1-NTN-A1-5", -95.6),
    (20, 60): TestConfig("G-FR1-NTN-A1-6", -95.7),
}

# Applicable when the SAN supports NB-IoT in-band operation (same PREFSENS as A1-1 / A1-4).
# Columns: BW (MHz), SCS (kHz), ref_meas_channel
NB_IOT_INBAND_REF_MEAS_CHANNELS: dict[tuple[int, int], str] = {
    (5, 15): "G-FR1-NTN-A1-10",
    (10, 15): "G-FR1-NTN-A1-10",
    (15, 15): "G-FR1-NTN-A1-10",
    (20, 15): "G-FR1-NTN-A1-11",
}


"""
§7.3 Dynamic range
"""

# Table 7.3.2.1-1: SAN LEO reference sensitivity with AWGN interference
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAN_LEO_DYNAMIC_RANGE: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A2-7", -79.0, -90.4),
    (5, 15): TestConfig("G-FR1-NTN-A2-1", -76.1, -88.2),
    (5, 30): TestConfig("G-FR1-NTN-A2-2", -76.8, -88.2),
    (10, 15): TestConfig("G-FR1-NTN-A2-1", -76.1, -85.0),
    (10, 30): TestConfig("G-FR1-NTN-A2-2", -76.8, -85.0),
    (10, 60): TestConfig("G-FR1-NTN-A2-3", -73.8, -85.0),
    (15, 15): TestConfig("G-FR1-NTN-A2-1", -76.1, -83.2),
    (15, 30): TestConfig("G-FR1-NTN-A2-2", -76.8, -83.2),
    (15, 60): TestConfig("G-FR1-NTN-A2-3", -73.8, -83.2),
    (20, 15): TestConfig("G-FR1-NTN-A2-4", -69.9, -81.9),
    (20, 30): TestConfig("G-FR1-NTN-A2-5", -69.9, -81.9),
    (20, 60): TestConfig("G-FR1-NTN-A2-6", -70.2, -81.9),
}


"""
§7.4.1 Adjacent Level Selectivity (ACS)
"""

# Table 7.4.1.5-2: interferer center frequency offset from SAN RF bandwidth edge
# Columns: BW (MHz), offset (MHz)
ACS_INTERFERER_OFFSET_MHZ: dict[int, float] = {
    3: 1.5075,
    5: 2.5025,
    10: 2.5075,
    15: 2.5125,
    20: 2.5025,
}

# Table 7.4.1.5-2: interferer signal type
# Columns: wanted BW (MHz), interferer BW (MHz), interferer SCS (kHz), RB count
ACS_INTERFERER_PARAMS: dict[int, tuple[int, int, int]] = {
    3: (3, 15, 15),
    5: (5, 15, 25),
    10: (5, 15, 25),
    15: (5, 15, 25),
    20: (5, 15, 25),
}

# Table 7.2.2-1 × Table 7.4.1.5-1: GEO ACS wanted + interfering power
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_GEO_ACS: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-7", -93.2, -57.0),
    (5, 15): TestConfig("G-FR1-NTN-A1-1", -93.3, -57.0),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -93.3, -57.0),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -93.3, -57.0),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -93.4, -57.0),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -93.4, -57.0),
    (10, 60): TestConfig("G-FR1-NTN-A1-3", -90.5, -57.0),
    (15, 60): TestConfig("G-FR1-NTN-A1-3", -90.5, -57.0),
    (20, 15): TestConfig("G-FR1-NTN-A1-4", -86.9, -57.0),
    (20, 30): TestConfig("G-FR1-NTN-A1-5", -87.2, -57.0),
    (20, 60): TestConfig("G-FR1-NTN-A1-6", -87.3, -57.0),
}

# Table 7.2.2-2 × Table 7.4.1.5-1: LEO ACS wanted + interfering power
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_LEO_ACS: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-7", -96.3, -60.0),
    (5, 15): TestConfig("G-FR1-NTN-A1-1", -96.4, -60.0),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -96.4, -60.0),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -96.4, -60.0),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -96.5, -60.0),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -96.5, -60.0),
    (10, 60): TestConfig("G-FR1-NTN-A1-3", -93.6, -60.0),
    (15, 60): TestConfig("G-FR1-NTN-A1-3", -93.6, -60.0),
    (20, 15): TestConfig("G-FR1-NTN-A1-4", -90.0, -60.0),
    (20, 30): TestConfig("G-FR1-NTN-A1-5", -90.3, -60.0),
    (20, 60): TestConfig("G-FR1-NTN-A1-6", -90.4, -60.0),
}


"""
§7.5 Out-of-band Blocking
"""

# Table 7.2.2-1 + Table 7.5.5-1: GEO OOB blocking wanted power (P_REFSENS + 6 dB)
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm)
SAT_GEO_OOB: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-7", -95.2),
    (5, 15): TestConfig("G-FR1-NTN-A1-1", -93.3),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -93.3),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -93.3),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -93.4),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -93.4),
    (10, 60): TestConfig("G-FR1-NTN-A1-3", -90.5),
    (15, 60): TestConfig("G-FR1-NTN-A1-3", -90.5),
    (20, 15): TestConfig("G-FR1-NTN-A1-4", -86.9),
    (20, 30): TestConfig("G-FR1-NTN-A1-5", -87.2),
    (20, 60): TestConfig("G-FR1-NTN-A1-6", -87.3),
}

# Table 7.2.2-2 + Table 7.5.5-1: LEO OOB blocking wanted power (P_REFSENS + 6 dB)
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm)
SAT_LEO_OOB: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-7", -98.3),
    (5, 15): TestConfig("G-FR1-NTN-A1-1", -96.4),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -96.4),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -96.4),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -96.5),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -96.5),
    (10, 60): TestConfig("G-FR1-NTN-A1-3", -93.6),
    (15, 60): TestConfig("G-FR1-NTN-A1-3", -93.6),
    (20, 15): TestConfig("G-FR1-NTN-A1-4", -90.0),
    (20, 30): TestConfig("G-FR1-NTN-A1-5", -90.3),
    (20, 60): TestConfig("G-FR1-NTN-A1-6", -90.4),
}


"""
§7.8 In-channel selectivity
"""

# Table 7.8.5-1: GEO ICS wanted + interfering power
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_GEO_ICS: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-12", -99.0, -94.2),
    (5, 15): TestConfig("G-FR1-NTN-A1-7", -96.8, -92.0),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -94.9, -88.1),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -94.9, -88.1),
    (20, 15): TestConfig("G-FR1-NTN-A1-1", -94.9, -88.1),
    (5, 30): TestConfig("G-FR1-NTN-A1-8", -97.5, -92.0),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -95.0, -89.0),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -95.0, -89.0),
    (20, 30): TestConfig("G-FR1-NTN-A1-2", -95.0, -89.0),
    (10, 60): TestConfig("G-FR1-NTN-A1-9", -94.4, -89.0),
    (15, 60): TestConfig("G-FR1-NTN-A1-9", -94.4, -89.0),
    (20, 60): TestConfig("G-FR1-NTN-A1-9", -94.4, -89.0),
}

# Table 7.8.5-2: LEO ICS wanted + interfering power
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_LEO_ICS: dict[tuple[int, int], TestConfig] = {
    (3, 15): TestConfig("G-FR1-NTN-A1-12", -102.1, -85.3),
    (5, 15): TestConfig("G-FR1-NTN-A1-7", -99.9, -83.1),
    (10, 15): TestConfig("G-FR1-NTN-A1-1", -98.0, -79.2),
    (15, 15): TestConfig("G-FR1-NTN-A1-1", -98.0, -79.2),
    (20, 15): TestConfig("G-FR1-NTN-A1-1", -98.0, -79.2),
    (5, 30): TestConfig("G-FR1-NTN-A1-8", -100.6, -83.1),
    (10, 30): TestConfig("G-FR1-NTN-A1-2", -98.1, -80.1),
    (15, 30): TestConfig("G-FR1-NTN-A1-2", -98.1, -80.1),
    (20, 30): TestConfig("G-FR1-NTN-A1-2", -98.1, -80.1),
    (10, 60): TestConfig("G-FR1-NTN-A1-9", -97.5, -80.1),
    (15, 60): TestConfig("G-FR1-NTN-A1-9", -97.5, -80.1),
    (20, 60): TestConfig("G-FR1-NTN-A1-9", -97.5, -80.1),
}

# Table 7.8.5-1/2: interferer RB count (SCS matches wanted signal / CLI --scs)
# Columns: BW (MHz), SCS (kHz), interferer RB count
ICS_INTERFERER_RBS: dict[tuple[int, int], int] = {
    (3, 15): 6,
    (5, 15): 10,
    (10, 15): 25,
    (15, 15): 25,
    (20, 15): 25,
    (5, 30): 5,
    (10, 30): 10,
    (15, 30): 10,
    (20, 30): 10,
    (10, 60): 5,
    (15, 60): 5,
    (20, 60): 5,
}

# Table 7.8: RB offsets as LUT for wanted and interfering signal positioning - higher
# Columns: BW (MHz), SCS (kHz), ws_rb_offset, is_rb_offset
ICS_RB_OFFSETS_IS_HIGH: dict[tuple[int, int], tuple[int, int]] = {
    (3, 15): (0, 9),
    (5, 15): (0, 15),
    (10, 15): (1, 26),
    (15, 15): (14, 40),
    (20, 15): (28, 53),
    (5, 30): (0, 6),
    (10, 30): (1, 13),
    (15, 30): (8, 20),
    (20, 30): (15, 26),
    (10, 60): (0, 6),
    (15, 60): (3, 10),
    (20, 60): (6, 13),
}

# Table 7.8: RB offsets as LUT for wanted and interfering signal positioning - lower
# Columns: BW (MHz), SCS (kHz), ws_rb_offset, is_rb_offset
ICS_RB_OFFSETS_IS_LOW: dict[tuple[int, int], tuple[int, int]] = {
    (3, 15): (6, 0),
    (5, 15): (10, 0),
    (10, 15): (26, 1),
    (15, 15): (40, 14),
    (20, 15): (53, 28),
    (5, 30): (5, 0),
    (10, 30): (12, 1),
    (15, 30): (19, 8),
    (20, 30): (25, 15),
    (10, 60): (5, 0),
    (15, 60): (9, 3),
    (20, 60): (12, 6),
}

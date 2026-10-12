"""3GPP TS 38.181 chapter 7 lookup tables."""

from typing import NamedTuple


class TestConfig(NamedTuple):
    """Lookup-table row for a 3GPP test configuration.

    ref_meas_channel: reference measurement channel, e.g. "FRC-A1-1"
    power_dbm: wanted power level
    interfering_power_dbm: interfering power level
    """
    ref_meas_channel: str
    power_dbm: float
    interfering_power_dbm: float | None = None


def get_power_levels(table: dict, bw: float, scs: float):
    """Return test configuration from the given table for the given BW/SCS."""
    try:
        return table[(bw, scs)]
    except KeyError as exc:
        raise ValueError(f"Invalid test config: BW={bw} MHz, SCS={scs} kHz") from exc


def san_table_key(san_class: str | None, tdd: bool, bw: float, scs: float) -> str:
    """Return ``geo`` / ``leo`` / ``leo_tdd`` for chapter 7 lookup tables.

    NB-IoT TDD rows exist only for standalone 200 kHz / 15 kHz. 1.4 MHz is
    E-UTRA in-band and has no TDD requirements in these tables.
    """
    if tdd:
        if (float(bw), float(scs)) != (0.2, 15.0):
            raise ValueError(
                "NB-IoT TDD is only specified for 0.2 MHz / 15 kHz "
                f"(got BW={bw} MHz, SCS={scs} kHz)."
            )
        return "leo_tdd"
    return san_class or "leo"


# NTN EUTRA operating bands: uplink F_UL,low and F_UL,high in Hz
# Columns: band, F_UL_low (Hz), F_UL_high (Hz)
# n249 is defined only for TDD NB-IoT operation
OPERATING_BANDS: dict[str, tuple[int, int]] = {
    "n249": (1_616_000_000, 1_626_500_000),
    "n252": (2_000_000_000, 2_020_000_000),
    "n253": (1_668_000_000, 1_675_000_000),
    "n254": (1_610_000_000, 1_626_500_000),
    "n255": (1_626_500_000, 1_660_500_000),
    "n256": (1_980_000_000, 2_010_000_000),
}

# Columns: channel BW (MHz), AWGN BW (Hz)
AWGN_BANDWIDTH: dict[float, int] = {
    1.4: 1_080_000,
    0.2: 180_000,
}


"""
§7.2 Reference sensitivity level
"""

# Table 7.2.5-1, Table 7.2.5-3: SAN GEO class reference sensitivity levels
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm)
SAN_GEO_REF_SENS_LEVELS: dict[tuple[float, float], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-1", -103.7),
    (0.2, 15): TestConfig("FRC-A14-1", -123.9),
    (0.2, 3.75): TestConfig("FRC-A14-2", -129.9)
}

# Table 7.2.5-2, Table 7.2.5-4: SAN LEO class FDD reference sensitivity levels
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm)
SAN_LEO_REF_SENS_LEVELS: dict[tuple[float, float], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-1", -106.8),
    (0.2, 15): TestConfig("FRC-A14-1", -127.0),
    (0.2, 3.75): TestConfig("FRC-A14-2", -133.0)
}

# Table 7.2.5-5: SAN LEO class TDD reference sensitivity levels
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm)


SAN_LEO_TDD_REF_SENS_LEVELS: dict[tuple[float, float], TestConfig] = {
    (0.2, 15): TestConfig("FRC-A14-3", -126.1),
}

SAN_REF_SENS_LEVELS: dict[str, dict[tuple[float, float], TestConfig]] = {
    "geo": SAN_GEO_REF_SENS_LEVELS,
    "leo": SAN_LEO_REF_SENS_LEVELS,
    "leo_tdd": SAN_LEO_TDD_REF_SENS_LEVELS,
}


"""
§7.3 Dynamic range
"""

# Table 7.3.5-2: SAN GEO class standalone NB-IoT FDD dynamic range
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAN_GEO_DYNAMIC_RANGE: dict[tuple[float, float], TestConfig] = {
    (0.2, 15): TestConfig("FRC-A15-1", -97.0, -93.6),
    (0.2, 3.75): TestConfig("FRC-A15-2", -102.9, -93.6),
}

# Table 7.3.5-1 (E-UTRA LEO 1.4 MHz) and Table 7.3.5-3 (standalone NB-IoT LEO FDD)
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAN_LEO_DYNAMIC_RANGE: dict[tuple[float, float], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A2-1", -81.7, -94.4),
    (0.2, 15): TestConfig("FRC-A15-1", -89.1, -85.7),
    (0.2, 3.75): TestConfig("FRC-A15-2", -95.0, -85.7),
}

# Table 7.3.5-4: SAN LEO class standalone NB-IoT TDD dynamic range
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAN_LEO_TDD_DYNAMIC_RANGE: dict[tuple[float, float], TestConfig] = {
    (0.2, 15): TestConfig("FRC-A15-1", -105.1, -101.7),
}

SAN_DYNAMIC_RANGE: dict[str, dict[tuple[float, float], TestConfig]] = {
    "geo": SAN_GEO_DYNAMIC_RANGE,
    "leo": SAN_LEO_DYNAMIC_RANGE,
    "leo_tdd": SAN_LEO_TDD_DYNAMIC_RANGE,
}

"""
§7.4.1 Adjacent Level Selectivity (ACS)
"""

# Table 7.4.1.5-1 (E-UTRA ±0.7025 MHz), Table 7.4.1.5-2/7.4.1.5-3 (standalone NB-IoT ±100 kHz)
# Columns: wanted BW (MHz), offset from SAN RF bandwidth edge (MHz)
ACS_INTERFERER_OFFSET_MHZ: dict[float, float] = {
    1.4: 0.7025,
    0.2: 0.1,
}

# Please note TS 36.181 Annex C Table C.2-1: Derivation of test requirements for conducted receiver tests
# Test Tolerance varies from chapters

# TS 36.181 Table 7.2.5-1 (PREFSENS+11 dB) × Table 7.4.1.5-1 (E-UTRA)
# TS 36.181 Table 7.2.5-3 (PREFSENS+19.5 dB) × Table 7.4.1.5-2 (standalone NB-IoT FDD): GEO
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_GEO_ACS: dict[tuple[float, float], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-1", -92.7, -57.6),
    (0.2, 15): TestConfig("FRC-A14-1", -104.4, -56.6),
    (0.2, 3.75): TestConfig("FRC-A14-2", -110.4, -56.6),
}

# TS 36.181 Table 7.2.5-2 (PREFSENS+11 dB) × Table 7.4.1.5-1 (E-UTRA)
# and Table 7.2.5-4 (PREFSENS+19.5 dB) × Table 7.4.1.5-2 (standalone NB-IoT FDD): LEO
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_LEO_ACS: dict[tuple[float, float], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-1", -95.8, -60.7),
    (0.2, 15): TestConfig("FRC-A14-1", -107.5, -59.7),
    (0.2, 3.75): TestConfig("FRC-A14-2", -113.5, -59.7),
}

# TS 36.181 Table 7.2.5-5 (PREFSENS+19.5 dB) × Table 7.4.1.5-3 (standalone NB-IoT TDD)
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_LEO_TDD_ACS: dict[tuple[float, float], TestConfig] = {
    (0.2, 15): TestConfig("FRC-A14-3", -106.6, -85.5),
}

SAN_ACS: dict[str, dict[tuple[float, float], TestConfig]] = {
    "geo": SAT_GEO_ACS,
    "leo": SAT_LEO_ACS,
    "leo_tdd": SAT_LEO_TDD_ACS,
}


"""
§7.5 Out-of-band Blocking
"""

# TS 36.181 Table 7.2.5-1 (PREFSENS+6 dB) × Table 7.5.5-1 (E-UTRA)
# and Table 7.2.5-3 (PREFSENS+6 dB) × Table 7.5.5-1 (standalone NB-IoT FDD): GEO
# Interferer is CW at -44 dBm (Table 7.5.5-1). Δf_OOB = 20 MHz (Table 7.5.5-2).
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_GEO_OOB: dict[tuple[float, float], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-1", -97.7, -44.0),
    (0.2, 15): TestConfig("FRC-A14-1", -117.9, -44.0),
    (0.2, 3.75): TestConfig("FRC-A14-2", -123.9, -44.0),
}

# TS 36.181 Table 7.2.5-2 (PREFSENS+6 dB) × Table 7.5.5-1 (E-UTRA)
# and Table 7.2.5-4 (PREFSENS+6 dB) × Table 7.5.5-1 (standalone NB-IoT FDD): LEO
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_LEO_OOB: dict[tuple[float, float], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-1", -100.8, -44.0),
    (0.2, 15): TestConfig("FRC-A14-1", -121.0, -44.0),
    (0.2, 3.75): TestConfig("FRC-A14-2", -127.0, -44.0),
}

# TS 36.181 Table 7.2.5-5 (PREFSENS+6 dB) × Table 7.5.5-1 (standalone NB-IoT TDD)
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_LEO_TDD_OOB: dict[tuple[float, float], TestConfig] = {
    (0.2, 15): TestConfig("FRC-A14-3", -120.1, -44.0),
}

SAN_OOB: dict[str, dict[tuple[float, float], TestConfig]] = {
    "geo": SAT_GEO_OOB,
    "leo": SAT_LEO_OOB,
    "leo_tdd": SAT_LEO_TDD_OOB,
}


"""
§7.8 In-channel selectivity
"""

# Table 7.8.5-1: GEO ICS wanted + interfering power
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_GEO_ICS: dict[tuple[float, int], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-4", -103.1, -97.6)
}

# Table 7.8.5-2: LEO ICS wanted + interfering power
# Columns: BW (MHz), SCS (kHz), ref_meas_channel, power_dbm (dBm), interfering_power_dbm (dBm)
SAT_LEO_ICS: dict[tuple[float, int], TestConfig] = {
    (1.4, 15): TestConfig("FRC-A1-4", -106.2, -88.7)
}

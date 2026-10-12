"""3GPP TS 36.181 chapter 8 lookup tables."""

from typing import NamedTuple


FADING_PROFILES: dict[str, str] = {
    "NTN-TDLA100-5": "NTNNBIOTTDLA100D5",
    "NTN-TDLA100-1": "NTNNBIOTTDLA100D1",
    "NTN-TDLC5-5": "NTNNBIOTTDLC5D5",
    "NTN-TDLC5-1": "NTNNBIOTTDLC5D1"
}


class PuschTestConfig(NamedTuple):
    """SNR and impairments for a PUSCH / NPUSCH performance point.

    delta_power is 10*log10(occupied BW / AWGN BW), in dB. It is 0 when the
    signal fills the AWGN bandwidth. The instrument C/N is referenced to the
    full AWGN bandwidth, so the actual carrier settings are:
        cn_db = snr_db + delta_power
        rf_power_dbm = awgn_power_dbm + cn_db
    """
    snr_db: float
    freq_offset_hz: int
    timing_offset: float
    frc: str = ""
    delta_power: float = 0.0


# Bandwidth correction for signals that do not fill the AWGN bandwidth.
DELTA_POWER_1RB = -7.78      # 1 RB / 1.08 MHz (FRC A5-1)
DELTA_POWER_SC375 = -16.81   # 3.75 kHz / 180 kHz (FRC A16-1, NPUSCH format 2, NPRACH)
DELTA_POWER_SC15 = -10.79    # 15 kHz / 180 kHz (FRC A16-3, NPUSCH format 2)


class PucchTestConfig(NamedTuple):
    snr_db: float
    freq_offset_hz: int
    timing_offset: float


class PrachTestConfig(NamedTuple):
    """SNR and time-error tolerance for a PRACH / NPRACH performance point.

    delta_power is 10*log10(occupied BW / AWGN BW), in dB. It is 0 when the
    signal fills the AWGN bandwidth. Instrument C/N and RF power use
    SNR + delta_power, the same way as PuschTestConfig.
    """
    snr_db: float
    time_error_tolerance_us: float
    delta_power: float = 0.0


def get_prach_test_config(
    table: dict[tuple[int, int, int, str], PrachTestConfig],
    num_rx: int,
    repetition_num: int,
    preamble_format: int,
    propagation: str,
) -> PrachTestConfig:
    """Return SNR, time error tolerance, frequency offset and AWGN settings from a PRACH table.

    AWGN depends on carrier BW (not PRACH SCS); bw selects the correct AWGN power/bandwidth.
    """
    try:
        config = table[(num_rx, repetition_num, preamble_format, propagation)]
    except KeyError as exc:
        raise ValueError(
            f"Invalid test config:  num_rx={num_rx}, repetition_num={repetition_num}, "
            f"preamble_format={preamble_format}, propagation={propagation!r}",
        ) from exc

    print("Test Configuration")
    print("--------------------------------")
    print(f"Number of RX Antennas: {num_rx}")
    print(f"Repetition Number: {repetition_num}")
    print(f"Propagation Condition: {propagation}")
    print(f"preamble_format: {preamble_format}")
    print(f"SNR: {config.snr_db} dB")
    print(f"Delta Power: {config.delta_power} dB")
    print(f"Time Error Tolerance: {config.time_error_tolerance_us} us")
    print("--------------------------------")
    return config


def get_pusch_test_config(
    table: dict[tuple, PuschTestConfig],
    num_rx: int,
    repetition_num: int,
    scs: float,
    propagation: str,
    occ_sequence_index: int | None = None,
    *,
    ce_mode: str | None = None,
) -> PuschTestConfig:
    """Return SNR, frequency offset, timing offset, FRC and delta power from a PUSCH table.

    OCC tables (8.5.1.5-4 / 8.5.1.5-5) are keyed with occ_sequence_index as a 5th tuple
    element (0 or 1). Non-OCC tables keep the 4-tuple key.
    """
    scs = float(scs)
    if occ_sequence_index is None:
        key: tuple = (num_rx, repetition_num, scs, propagation)
    else:
        key = (num_rx, repetition_num, scs, propagation, occ_sequence_index)
    try:
        config = table[key]
    except KeyError as exc:
        extra = (
            f", occ_sequence_index={occ_sequence_index}"
            if occ_sequence_index is not None else ""
        )
        raise ValueError(
            f"Invalid test config:  num_rx={num_rx}, repetition_num={repetition_num}, "
            f"scs={scs}, propagation={propagation!r}{extra}",
        ) from exc

    print("Test Configuration")
    print("--------------------------------")
    print(f"Number of RX Antennas: {num_rx}")
    if ce_mode is not None:
        print(f"CE Mode: {ce_mode}")
    print(f"Repetition Number: {repetition_num}")
    print(f"Subcarrier Spacing: {scs} kHz")
    print(f"Propagation Condition: {propagation}")
    if occ_sequence_index is not None:
        print(f"OCC Sequence Index: {occ_sequence_index}")
    if config.frc:
        print(f"FRC: {config.frc}")
    print(f"SNR: {config.snr_db} dB")
    print(f"Delta Power: {config.delta_power} dB")
    print(f"Frequency Offset: {config.freq_offset_hz} Hz")
    print(f"Timing Offset: {config.timing_offset} us/RU")
    print("--------------------------------")
    return config


def get_pucch_test_config(
    table: dict,
    num_rx: int,
    repetition_num: int,
    propagation: str
) -> PucchTestConfig:
    """Return SNR and AWGN settings from a PUCCH performance table.
    """
    key = (num_rx, repetition_num, propagation)

    try:
        config = table[key]
    except KeyError as exc:
        raise ValueError(
            f"Invalid test config:"
            f"num_rx={num_rx}, repetition_num={repetition_num}, propagation={propagation!r}",
        ) from exc

    print("Test Configuration")
    print("--------------------------------")

    print(f"Number of RX Antennas: {num_rx}")
    print(f"Repetition Number: {repetition_num}")
    print(f"Propagation Condition: {propagation}")

    print(f"SNR: {config.snr_db} dB")
    print(f"Frequency Offset: {config.freq_offset_hz} Hz")
    print(f"Timing Offset: {config.timing_offset} us/RU")

    print("--------------------------------")
    return config


"""
§8.2.1 PUSCH in multipath fading propagation conditions transmission
"""

# Tables 8.2.1.5-1 / 8.2.1.5-2 FDD
# (AWGN from Table 8.2.1.4.2-1: -92.7 dBm / 1.08MHz; throughput 70%)

PUSCH_PERF_REQ_FDD: dict[tuple[int, int, float, str], PuschTestConfig] = {
    # --- PUSCH Rx num, Repetition num, SCS (kHz), Propagation condition
    # Table 8.2.1.5-1: Mode A, 1.4 MHz, 1 Tx, FRC A5-2, 8 repetitions,
    # frequency offset 4 Hz (Table 8.2.1.4.2-3), timing 0.01 us/subframe (Table 8.2.1.4.2-4)
    (1, 8, 15.0, "NTN-TDLA100-5"): PuschTestConfig(-2.5, 4, 0.01, "FRC-A5-2"),
    (1, 8, 15.0, "NTN-TDLC5-5"): PuschTestConfig(-2.8, 4, 0.01, "FRC-A5-2"),
    (2, 8, 15.0, "NTN-TDLA100-5"): PuschTestConfig(-6.7, 4, 0.01, "FRC-A5-2"),
    (2, 8, 15.0, "NTN-TDLC5-5"): PuschTestConfig(-6.7, 4, 0.01, "FRC-A5-2"),

    # Table 8.2.1.5-2: Mode B, 1.4 MHz, 1 Tx, FRC A5-1, 256 repetitions,
    # frequency offset 128 Hz (Table 8.2.1.4.2-3), timing 0.01 us/subframe (Table 8.2.1.4.2-4)
    # 1 RB of the 1.08 MHz AWGN bandwidth
    (1, 256, 15.0, "NTN-TDLA100-5"): PuschTestConfig(-11.0, 128, 0.01, "FRC-A5-1", DELTA_POWER_1RB),
    (1, 256, 15.0, "NTN-TDLC5-5"): PuschTestConfig(-12.7, 128, 0.01, "FRC-A5-1", DELTA_POWER_1RB),
    (2, 256, 15.0, "NTN-TDLA100-5"): PuschTestConfig(-13.9, 128, 0.01, "FRC-A5-1", DELTA_POWER_1RB),
    (2, 256, 15.0, "NTN-TDLC5-5"): PuschTestConfig(-14.9, 128, 0.01, "FRC-A5-1", DELTA_POWER_1RB),
}


"""
§8.3.1 ACK missed detection for PUCCH format 1a transmission
"""

# Table 8.3.1.2.1-1 FDD
# (AWGN from Table 8.3.1.4.2-1: -89.7 dBm / 1.08MHz; Pd ≥ 99%, Pfa ≤ 1%)

PUCCH_FORMAT_1A_PERF_REQ_FDD: dict[tuple[int, int, str], PucchTestConfig] = {
    # --- PUCCH Rx num, Repetition num, Propagation condition
    # Table 8.3.1.2.1-1: 1.4 MHz, 1 Tx, Normal CP, 8 repetitions,
    # frequency offset 4 Hz (Table 8.3.1.4.2-2), timing 0.01 us/subframe (Table 8.3.1.4.2-3)
    (1, 8, "NTN-TDLA100-5"): PucchTestConfig(-2.0, 4, 0.01),
    (2, 8, "NTN-TDLA100-5"): PucchTestConfig(-7.6, 4, 0.01),
}

"""
§8.4.1 PRACH — false alarm probability and missed detection
"""

# Table 8.4.1.5-1 FDD
# (AWGN from Table 8.4.1.4.2-1: -89.7 dBm / 1.08MHz; Pd ≥ 99%, Pfa ≤ 0.1%)

EMTC_PRACH_PERF_REQ_FDD: dict[tuple[int, int, int, str], PrachTestConfig] = {
    # --- PRACH Rx num, Repetition num, Burst format, Propagation condition
    # Table 8.4.1.5-1: 1 Tx, PRACH frequency hopping OFF,
    # frequency offset 270 Hz, time error tolerance 2.08 us (clause 8.4.1.4.2)
    # Burst formats 0/1: 8 repetitions; burst formats 2/3: 16 repetitions
    # PRACH occupies 6 RB, equal to the 1.08 MHz AWGN bandwidth (delta_power = 0)
    (1, 8, 0, "NTN-TDLA100-5"): PrachTestConfig(-10.4, 2.08),
    (1, 8, 1, "NTN-TDLA100-5"): PrachTestConfig(-10.0, 2.08),
    (1, 16, 2, "NTN-TDLA100-5"): PrachTestConfig(-15.5, 2.08),
    (1, 16, 3, "NTN-TDLA100-5"): PrachTestConfig(-15.5, 2.08),

    (2, 8, 0, "NTN-TDLA100-5"): PrachTestConfig(-15.7, 2.08),
    (2, 8, 1, "NTN-TDLA100-5"): PrachTestConfig(-15.5, 2.08),
    (2, 16, 2, "NTN-TDLA100-5"): PrachTestConfig(-19.5, 2.08),
    (2, 16, 3, "NTN-TDLA100-5"): PrachTestConfig(-19.5, 2.08),
}


"""
§8.5.1 Performance requirements for NPUSCH format 1
"""

# Tables 8.5.1.5-1 / 8.5.1.5-2 FDD
# (AWGN from Table 8.5.1.4.2-1: -100.5 dBm / 180k; throughput 70%)

NPUSCH_FORMAT1_PERF_REQ_FDD: dict[tuple[int, int, float, str], PuschTestConfig] = {
    # --- NPUSCH Rx num, Repetition num, SCS (kHz), Propagation condition
    # Table 8.5.1.5-1: 3.75 kHz, 1 allocated SC, FRC A16-1,
    # accumulated frequency offset 128 Hz, timing 0.32 us/RU
    # 3.75 kHz of the 180 kHz AWGN bandwidth
    (1, 4, 3.75, "NTN-TDLA100-1"): PuschTestConfig(-1.4, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),
    (1, 4, 3.75, "NTN-TDLC5-1"): PuschTestConfig(-3.0, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),
    (2, 4, 3.75, "NTN-TDLA100-1"): PuschTestConfig(-4.8, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),
    (2, 4, 3.75, "NTN-TDLC5-1"): PuschTestConfig(-5.9, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),

    # Table 8.5.1.5-2: 15 kHz, 12 allocated SCs, FRC A16-2,
    # accumulated frequency offset 8 Hz, timing 0.01 us/RU
    (1, 16, 15.0, "NTN-TDLA100-1"): PuschTestConfig(-2.6, 8, 0.01, "FRC-A16-2"),
    (1, 16, 15.0, "NTN-TDLC5-1"): PuschTestConfig(-3.4, 8, 0.01, "FRC-A16-2"),
    (2, 16, 15.0, "NTN-TDLA100-1"): PuschTestConfig(-6.5, 8, 0.01, "FRC-A16-2"),
    (2, 16, 15.0, "NTN-TDLC5-1"): PuschTestConfig(-7.2, 8, 0.01, "FRC-A16-2"),
}

# Table 8.5.1.5-3 TDD
# (AWGN from Table 8.5.1.4.2-1: -100.5 dBm / 180k; throughput 70%)

NPUSCH_FORMAT1_PERF_REQ_TDD: dict[tuple[int, int, float, str], PuschTestConfig] = {
    # --- NPUSCH Rx num, Repetition num, SCS (kHz), Propagation condition
    # Table 8.5.1.5-3: 15 kHz, 12 allocated SCs, FRC A16-2,
    # accumulated frequency offset 2 Hz, timing 0.01 us/RU
    (1, 4, 15.0, "NTN-TDLA100-1"): PuschTestConfig(2.5, 2, 0.01, "FRC-A16-2"),
    (1, 4, 15.0, "NTN-TDLC5-1"): PuschTestConfig(0.3, 2, 0.01, "FRC-A16-2"),
}

# Tables 8.5.1.5-4 / 8.5.1.5-5 FDD with length-2 OCC
# (AWGN from Table 8.5.1.4.2-1: -100.5 dBm / 180k; throughput 70%)
# Key includes OCC sequence index (0 or 1); SNR is specified per UE/OCC.

NPUSCH_FORMAT1_PERF_REQ_OCC_FDD: dict[
    tuple[int, int, float, str, int], PuschTestConfig
] = {
    # --- NPUSCH Rx num, Repetition num, SCS (kHz), Propagation condition, OCC sequence index
    # Table 8.5.1.5-4: 3.75 kHz, 1 allocated SC, symbol-level length-2 OCC, FRC A16-1,
    # accumulated frequency offset 128 Hz, timing 0.32 us/RU
    # 3.75 kHz of the 180 kHz AWGN bandwidth
    (1, 2, 3.75, "NTN-TDLA100-1", 0): PuschTestConfig(-1.6, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),
    (1, 2, 3.75, "NTN-TDLA100-1", 1): PuschTestConfig(-1.6, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),
    (2, 2, 3.75, "NTN-TDLA100-1", 0): PuschTestConfig(-4.7, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),
    (2, 2, 3.75, "NTN-TDLA100-1", 1): PuschTestConfig(-4.7, 128, 0.32, "FRC-A16-1", DELTA_POWER_SC375),

    # Table 8.5.1.5-5: 15 kHz, 1 allocated SC, slot-level length-2 OCC, FRC A16-3,
    # accumulated frequency offset 128 Hz, timing 0.08 us/RU
    # 15 kHz of the 180 kHz AWGN bandwidth
    (1, 8, 15.0, "NTN-TDLA100-1", 0): PuschTestConfig(-8.4, 128, 0.08, "FRC-A16-3", DELTA_POWER_SC15),
    (1, 8, 15.0, "NTN-TDLA100-1", 1): PuschTestConfig(-8.4, 128, 0.08, "FRC-A16-3", DELTA_POWER_SC15),
    (2, 8, 15.0, "NTN-TDLA100-1", 0): PuschTestConfig(-11.1, 128, 0.08, "FRC-A16-3", DELTA_POWER_SC15),
    (2, 8, 15.0, "NTN-TDLA100-1", 1): PuschTestConfig(-11.1, 128, 0.08, "FRC-A16-3", DELTA_POWER_SC15),
}


"""
§8.5.2 ACK missed detection for NPUSCH format 2
"""

# Tables 8.5.2.5-1 / 8.5.2.5-2 FDD

NPUSCH_FORMAT2_PERF_REQ_FDD: dict[tuple[int, int, float, str], PuschTestConfig] = {
    # --- NPUSCH Rx num, Repetition num, SCS (kHz), Propagation condition
    # (AWGN from Table 8.5.2.4.2-1: -100.5 dBm / 180k) ---
    # Table 8.5.2.5-1: 3.75 kHz, accumulated frequency offset 64 Hz, timing 0.08 us/RU
    # single tone, 3.75 kHz of the 180 kHz AWGN bandwidth
    (1, 16, 3.75, "NTN-TDLA100-1"): PuschTestConfig(2.4, 64, 0.08, delta_power=DELTA_POWER_SC375),
    (2, 16, 3.75, "NTN-TDLA100-1"): PuschTestConfig(-3.3, 64, 0.08, delta_power=DELTA_POWER_SC375),

    # Table 8.5.2.5-2: 15 kHz, accumulated frequency offset 16 Hz, timing 0.02 us/RU
    # single tone, 15 kHz of the 180 kHz AWGN bandwidth
    (1, 16, 15.0, "NTN-TDLA100-1"): PuschTestConfig(5.7, 16, 0.02, delta_power=DELTA_POWER_SC15),
    (2, 16, 15.0, "NTN-TDLA100-1"): PuschTestConfig(-2.7, 16, 0.02, delta_power=DELTA_POWER_SC15),
}

# Tables 8.5.2.5-3 TDD

NPUSCH_FORMAT2_PERF_REQ_TDD: dict[tuple[int, int, float, str], PuschTestConfig] = {
    # --- NPUSCH Rx num, Repetition num, SCS (kHz), Propagation condition
    # (AWGN from Table 8.5.2.4.2-1: -100.5 dBm / 180k) ---
    # Table 8.5.2.5-3: 15 kHz, accumulated frequency offset 4 Hz, timing 0.02 us/RU
    # single tone, 15 kHz of the 180 kHz AWGN bandwidth
    (1, 4, 15.0, "NTN-TDLA100-1"): PuschTestConfig(8.2, 4, 0.02, delta_power=DELTA_POWER_SC15),
}


"""
§8.5.3 Performance requirements for NPRACH
"""

# Tables 8.5.3.5-1 FDD

NPRACH_PERF_REQ_FDD: dict[tuple[int, int, int, str], PrachTestConfig] = {
    # --- PRACH Rx num , Repetition num, Preamble format, Propagation condition
    # (AWGN from Table 8.5.3.4.2-1: -100.5 dBm / 180k) ---
    # NPRACH is a 3.75 kHz tone inside the 180 kHz AWGN bandwidth
    (1, 8, 0, "NTN-TDLA100-1"): PrachTestConfig(13.9, 33.3333, DELTA_POWER_SC375),
    (1, 8, 1, "NTN-TDLA100-1"): PrachTestConfig(14.3, 133.3333, DELTA_POWER_SC375),

    (2, 8, 0, "NTN-TDLA100-1"): PrachTestConfig(6.6, 33.3333, DELTA_POWER_SC375),
    (2, 8, 1, "NTN-TDLA100-1"): PrachTestConfig(6.7, 133.3333, DELTA_POWER_SC375),

    (1, 16, 0, "NTN-TDLA100-1"): PrachTestConfig(10.4, 33.3333, DELTA_POWER_SC375),
    (1, 16, 1, "NTN-TDLA100-1"): PrachTestConfig(10.2, 133.3333, DELTA_POWER_SC375),

    (2, 16, 0, "NTN-TDLA100-1"): PrachTestConfig(2.2, 33.3333, DELTA_POWER_SC375),
    (2, 16, 1, "NTN-TDLA100-1"): PrachTestConfig(2.3, 133.3333, DELTA_POWER_SC375)
}

# Tables 8.5.3.5-2 TDD

NPRACH_PERF_REQ_TDD: dict[tuple[int, int, int, str], PrachTestConfig] = {
    # --- PRACH Rx num , Repetition num, Preamble format, Propagation condition
    # (AWGN from Table 8.5.3.4.2-1: -100.5 dBm / 180k) ---
    # NPRACH is a 3.75 kHz tone inside the 180 kHz AWGN bandwidth
    (1, 4, 0, "NTN-TDLA100-1"): PrachTestConfig(16.1, 33.3333, DELTA_POWER_SC375),
    (1, 4, 0, "NTN-TDLC5-1"): PrachTestConfig(11.2, 33.3333, DELTA_POWER_SC375),

    (1, 4, 1, "NTN-TDLA100-1"): PrachTestConfig(15.9, 133.3333, DELTA_POWER_SC375),
    (1, 4, 1, "NTN-TDLC5-1"): PrachTestConfig(11.3, 133.3333, DELTA_POWER_SC375),

    (1, 8, 0, "NTN-TDLA100-1"): PrachTestConfig(9.7, 33.3333, DELTA_POWER_SC375),
    (1, 8, 0, "NTN-TDLC5-1"): PrachTestConfig(6.2, 33.3333, DELTA_POWER_SC375),

    (1, 8, 1, "NTN-TDLA100-1"): PrachTestConfig(9.8, 133.3333, DELTA_POWER_SC375),
    (1, 8, 1, "NTN-TDLC5-1"): PrachTestConfig(6.3, 133.3333, DELTA_POWER_SC375),
}

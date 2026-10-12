# 3GPP TS 36.181 Chapter 8 — Conducted Performance Characteristics

Python scripts for SAN type 1-H performance tests defined in TS 36.181 Chapter 8.

See the [repository README](../../README.md) for environment setup and shared utilities.

Run all commands below from the **repository root** with the virtual environment activated.

---

## Applicability

### §8.2.1 PUSCH in multipath fading (coverage enhancement)

Unless otherwise stated, §8.2.1 tests follow these rules (TS 36.181 clause 8.2.1.1):

- **CEMode A:** Applicable only if the SAN supports coverage enhancement configured with CEModeA (Table 8.2.1.5-1, 8 repetitions, FRC A5-2).
- **CEMode B:** Applicable only if the SAN supports coverage enhancement configured with CEModeB (Table 8.2.1.5-2, 256 repetitions, FRC A5-1).
- **Channel BW:** A test for a specific channel bandwidth is only applicable if the SAN supports it. For a SAN supporting FDD multiple channel bandwidths, only the tests for the lowest and the highest FDD channel bandwidths supported by the SAN are applicable. The requirement tables specify **1.4 MHz**.
- **RF channel:** Clause 8.2.1.4.1 tests channel **M** (clause 4.7).

### §8.3.1 ACK missed detection for PUCCH format 1a (coverage enhancement)

Unless otherwise stated, §8.3.1 tests follow these rules (TS 36.181 clause 8.3.1.1):

- **Coverage enhancement:** Applicable only to SANs supporting coverage enhancement (Table 8.3.1.2.1-1, PUCCH format 1a, 8 repetitions).
- **Channel BW:** A test for a specific channel bandwidth is only applicable if the SAN supports it. The requirement table specifies **1.4 MHz**.
- **RF channel:** Clause 8.3.1.4.1 tests channel **M** (clause 4.7).

### §8.4.1 PRACH false alarm probability and missed detection

Unless otherwise stated, §8.4.1 tests follow these rules (TS 36.181 clause 8.4.1.1):

- **Preamble:** Test preambles for normal mode are those in Annex A Table A.6-1 (coverage enhancement). Table 8.4.1.5-1 uses burst formats 0–3.
- **Timing error:** For NTN-TDLA100-5, a timing estimation error occurs when the error on the strongest path is larger than **2.08 µs**.
- **RF channel:** Clause 8.4.1.4.1 tests channel **M** (clause 4.7).

### §8.5.1 NPUSCH format 1

Unless otherwise stated, §8.5.1 tests follow these rules (TS 36.181 clause 8.5.1.1). The specification text applies each case to base stations that declare the corresponding feature:

- **3.75 kHz:** Applicable when 3.75 kHz subcarrier spacing is supported (Table 8.5.1.5-1, FDD).
- **15 kHz:** Single-subcarrier and multi-subcarrier tests are applicable for the number of 15 kHz subcarriers that is supported (Table 8.5.1.5-2 FDD, Table 8.5.1.5-3 TDD).
- **Length-2 OCC:** The 15 kHz slot-level length-2 OCC test applies when that feature is supported (Table 8.5.1.5-5). The 3.75 kHz symbol-level length-2 OCC test applies when that feature is supported (Table 8.5.1.5-4).
- **RF channel:** Clause 8.5.1.4.1 tests channel **M** (clause 4.9.1).
- **HARQ:** The SMW does not support HARQ feedback for NB-IoT 200 kHz TDD. `test_8_5_1.py` configures HARQ only for FDD (when `--tdd` is omitted).

### §8.5.2 ACK missed detection for NPUSCH format 2

Unless otherwise stated, §8.5.2 tests follow these rules (TS 36.181 clause 8.5.2.1):

- **3.75 kHz:** Applicable to base stations supporting 3.75 kHz subcarrier spacing (Table 8.5.2.5-1, FDD).
- **15 kHz:** Applicable to base stations supporting 15 kHz subcarrier spacing (Table 8.5.2.5-2 FDD, Table 8.5.2.5-3 TDD).
- **RF channel:** Clause 8.5.2.4.1 tests channel **M** (clause 4.9.1).

### §8.5.3 NPRACH

Unless otherwise stated, §8.5.3 tests follow these rules (TS 36.181 clause 8.5.3.1):

- **FDD:** Preamble parameters are in Table 8.5.3.1-1; missed-detection requirements are in Table 8.5.3.5-1.
- **TDD:** TDD performance requirements are optional and only valid for base stations supporting TDD. Preamble parameters are in Table 8.5.3.1-2; missed-detection requirements are in Table 8.5.3.5-2.
- **Timing error:** A timing estimation error occurs when the error on the strongest path is larger than **3.646 µs**.
- **RF channel:** Clause 8.5.3.4.1 tests channel **M** (clause 4.9.1).

## RF channels to test

Clauses 8.2.1.4.1, 8.3.1.4.1, 8.4.1.4.1, 8.5.1.4.1, 8.5.2.4.1, and 8.5.3.4.1 each set the RF channel
to test to **M** (middle of the operating band). Clauses 8.2.1, 8.3.1, and 8.4.1 point to clause 4.7;
clauses 8.5.1, 8.5.2, and 8.5.3 point to clause 4.9.1. Set `freq` / `--freq` in the INI file or on the
CLI to that channel. The scripts do not select it for you.

## Config files

Pass a per-test INI under `configs/` as the only argument, or use CLI flags instead. Global
settings (`ip`, `log_scpi`) are loaded from [`instrument.ini`](../../instrument.ini) and
[`NB_IoT/options.ini`](../options.ini). Each per-test file contains only a `[test]` section.

---

## Scripts

| Script          | Test                                                                              |
|-----------------|-----------------------------------------------------------------------------------|
| `test_8_2_1.py` | §8.2.1 PUSCH in multipath fading propagation conditions transmission              |
| `test_8_3_1.py` | §8.3.1 ACK missed detection for PUCCH format 1a transmission                      |
| `test_8_4_1.py` | §8.4.1 PRACH — false alarm probability and missed detection                       |
| `test_8_5_1.py` | §8.5.1 Performance requirements for NPUSCH format 1                               |
| `test_8_5_2.py` | §8.5.2 ACK missed detection for NPUSCH format 2                                   |
| `test_8_5_3.py` | §8.5.3 Performance requirements for NPRACH                                        |
| `configs/`      | Per-section INI folders for §8.2.1, §8.3.1, §8.4.1, §8.5.1, §8.5.2 and §8.5.3 test cases |


### §8.2.1 parameters
| Parameter | CLI flag | Values |
|-----------|----------|--------|
| RX antennas | `--num-rx` | `1`, `2` |
| Sub-carrier spacing | `--scs` | `15` (kHz) |
| CE mode | `--ce-mode` | `A` (8 repetitions, Table 8.2.1.5-1, FRC A5-2, 6 RBs), `B` (256 repetitions, Table 8.2.1.5-2, FRC A5-1, 1 RB). Sets `--repetition-num` when that flag is omitted. Default `A` |
| Repetition number | `--repetition-num` | `8` (CEMode A), `256` (CEMode B). Must match `--ce-mode` when both are given; sets `--ce-mode` when that flag is omitted |
| Propagation | `--propagation` | `NTN-TDLA100-5`, `NTN-TDLC5-5` |


### Config-files (§8.2.1)

```powershell
python NB_IoT/ts-36181-chapter8/test_8_2_1.py NB_IoT/ts-36181-chapter8/configs/8_2_1/pusch_1rx_rep8_15khz.ini
python NB_IoT/ts-36181-chapter8/test_8_2_1.py NB_IoT/ts-36181-chapter8/configs/8_2_1/pusch_1rx_rep256_15khz.ini
```

FDD only (1.4 MHz). `--ce-mode A` is 8 repetitions (Table 8.2.1.5-1, FRC A5-2, 6 RBs); `--ce-mode B` is 256 repetitions (Table 8.2.1.5-2, FRC A5-1, 1 RB). `--repetition-num 8` and `--repetition-num 256` select the same tests. If both flags are set they must agree. `--scs` is 15 kHz. Propagation is `NTN-TDLA100-5` or `NTN-TDLC5-5`. AWGN is −92.7 dBm / 1.08 MHz (Table 8.2.1.4.2-1).

See [`configs/8_2_1/`](configs/8_2_1/) for all §8.2.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `num_rx`, `ce_mode`, `repetition_num`, `scs`, `propagation`, `freq`, `cell_id`, `ue_id` |

```powershell
# FDD Table 8.2.1.5-1 — CEMode A (repetition 8), 15 kHz, FRC A5-2
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 1 --scs 15 --ce-mode A --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 1 --scs 15 --ce-mode A --propagation NTN-TDLC5-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 2 --scs 15 --ce-mode A --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 2 --scs 15 --ce-mode A --propagation NTN-TDLC5-5 --ip <ip_address> --log-scpi

# FDD Table 8.2.1.5-2 — CEMode B (repetition 256), 15 kHz, FRC A5-1
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 1 --scs 15 --ce-mode B --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 1 --scs 15 --ce-mode B --propagation NTN-TDLC5-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 2 --scs 15 --ce-mode B --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_2_1.py --num-rx 2 --scs 15 --ce-mode B --propagation NTN-TDLC5-5 --ip <ip_address> --log-scpi
```

### §8.3.1 parameters
| Parameter | CLI flag | Values |
|-----------|----------|--------|
| RX antennas | `--num-rx` | `1`, `2` |
| Repetition number | `--repetition-num` | `8` (Table 8.3.1.2.1-1, PUCCH format 1a) |
| Propagation | `--propagation` | `NTN-TDLA100-5` |

### Config-files (§8.3.1)

```powershell
python NB_IoT/ts-36181-chapter8/test_8_3_1.py NB_IoT/ts-36181-chapter8/configs/8_3_1/pucch_format1a_1rx_rep8.ini
python NB_IoT/ts-36181-chapter8/test_8_3_1.py NB_IoT/ts-36181-chapter8/configs/8_3_1/pucch_format1a_2rx_rep8.ini
```

FDD only (1.4 MHz, 15 kHz, PUCCH format 1a). Table 8.3.1.2.1-1 specifies 8 repetitions and propagation `NTN-TDLA100-5`. AWGN is −89.7 dBm / 1.08 MHz (Table 8.3.1.4.2-1); Pd ≥ 99%, Pfa ≤ 1%.

See [`configs/8_3_1/`](configs/8_3_1/) for all §8.3.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `num_rx`, `repetition_num`, `propagation`, `freq`, `cell_id`, `ue_id` |

```powershell
# FDD Table 8.3.1.2.1-1 — PUCCH format 1a, 8 repetitions, NTN-TDLA100-5
python NB_IoT/ts-36181-chapter8/test_8_3_1.py --num-rx 1 --repetition-num 8 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_3_1.py --num-rx 2 --repetition-num 8 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
```

### §8.4.1 parameters
| Parameter | CLI flag | Values |
|-----------|----------|--------|
| RX antennas | `--num-rx` | `1`, `2` |
| Repetition number | `--repetition-num` | `8` (burst formats 0/1, Table 8.4.1.5-1), `16` (burst formats 2/3, Table 8.4.1.5-1) |
| Burst format | `--burst-format` | `0`, `1`, `2`, `3` |
| Propagation | `--propagation` | `NTN-TDLA100-5` |

### Config-files (§8.4.1)

```powershell
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format0_1rx_rep8.ini
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format1_1rx_rep8.ini
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format2_1rx_rep16.ini
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format3_1rx_rep16.ini
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format0_2rx_rep8.ini
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format1_2rx_rep8.ini
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format2_2rx_rep16.ini
python NB_IoT/ts-36181-chapter8/test_8_4_1.py NB_IoT/ts-36181-chapter8/configs/8_4_1/prach_burst_format3_2rx_rep16.ini
```

FDD only (1.4 MHz). Burst formats 0 and 1 use `--repetition-num 8`; burst formats 2 and 3 use `--repetition-num 16` (Table 8.4.1.5-1). Propagation is `NTN-TDLA100-5`. AWGN is −89.7 dBm / 1.08 MHz (Table 8.4.1.4.2-1); Pd ≥ 99%, Pfa ≤ 0.1%. Frequency offset is 270 Hz; time error tolerance is 2.08 µs.

See [`configs/8_4_1/`](configs/8_4_1/) for all §8.4.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `num_rx`, `repetition_num`, `burst_format`, `propagation`, `freq`, `cell_id`, `ue_id` |

```powershell
# FDD Table 8.4.1.5-1 — burst format 0/1, repetition 8, NTN-TDLA100-5
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 1 --repetition-num 8 --burst-format 0 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 1 --repetition-num 8 --burst-format 1 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 2 --repetition-num 8 --burst-format 0 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 2 --repetition-num 8 --burst-format 1 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi

# FDD Table 8.4.1.5-1 — burst format 2/3, repetition 16, NTN-TDLA100-5
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 1 --repetition-num 16 --burst-format 2 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 1 --repetition-num 16 --burst-format 3 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 2 --repetition-num 16 --burst-format 2 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_4_1.py --num-rx 2 --repetition-num 16 --burst-format 3 --propagation NTN-TDLA100-5 --ip <ip_address> --log-scpi
```

### §8.5.1 parameters
| Parameter | CLI flag | Values |
|-----------|----------|--------|
| RX antennas | `--num-rx` | `1`, `2` (TDD Table 8.5.1.5-3 is 1 RX only) |
| Sub-carrier spacing | `--scs` | `3.75` (kHz, Tables 8.5.1.5-1 / 8.5.1.5-4), `15` (kHz, Tables 8.5.1.5-2 / 8.5.1.5-3 / 8.5.1.5-5) |
| Repetition number | `--repetition-num` | `4` (FDD 3.75 kHz, Table 8.5.1.5-1; TDD 15 kHz, Table 8.5.1.5-3), `16` (FDD 15 kHz, Table 8.5.1.5-2), `2` (OCC 3.75 kHz, Table 8.5.1.5-4), `8` (OCC 15 kHz, Table 8.5.1.5-5) |
| Propagation | `--propagation` | `NTN-TDLA100-1`, `NTN-TDLC5-1` (OCC tables are `NTN-TDLA100-1` only) |
| OCC sequence index | `--occ-sequence-index` | `0`, `1` (FDD length-2 OCC, Tables 8.5.1.5-4 / 8.5.1.5-5) |
| Duplex | `--tdd` | omit (FDD), flag (TDD, Table 8.5.1.5-3) |

### Config-files (§8.5.1)

```powershell
python NB_IoT/ts-36181-chapter8/test_8_5_1.py NB_IoT/ts-36181-chapter8/configs/8_5_1/npusch_format1_1rx_rep16_15khz.ini
python NB_IoT/ts-36181-chapter8/test_8_5_1.py NB_IoT/ts-36181-chapter8/configs/8_5_1/npusch_format1_1rx_rep4_3_75khz.ini
python NB_IoT/ts-36181-chapter8/test_8_5_1.py NB_IoT/ts-36181-chapter8/configs/8_5_1/npusch_format1_1rx_rep4_15khz_tdd.ini
python NB_IoT/ts-36181-chapter8/test_8_5_1.py NB_IoT/ts-36181-chapter8/configs/8_5_1/npusch_format1_1rx_rep2_3_75khz_occ0.ini

```

For TDD, pass `--tdd` or set `tdd = true`. FDD uses `--repetition-num 4` (Table 8.5.1.5-1, 3.75 kHz) or `16` (Table 8.5.1.5-2, 15 kHz); TDD uses `--repetition-num 4` (Table 8.5.1.5-3). Length-2 OCC cases set `occ_sequence_index` to 0 or 1: repetition 2 at 3.75 kHz (Table 8.5.1.5-4, symbol-level) or 8 at 15 kHz (Table 8.5.1.5-5, slot-level).

See [`configs/8_5_1/`](configs/8_5_1/) for all §8.5.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `num_rx`, `repetition_num`, `scs`, `propagation`, `tdd`, `occ_sequence_index` (OCC only), `freq`, `cell_id`, `ue_id` |

```powershell
# FDD Table 8.5.1.5-1 — repetition 4, 3.75 kHz
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 3.75 --repetition-num 4 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 3.75 --repetition-num 4 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 3.75 --repetition-num 4 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 3.75 --repetition-num 4 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi

# FDD Table 8.5.1.5-2 — repetition 16, 15 kHz
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 15 --repetition-num 16 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 15 --repetition-num 16 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 15 --repetition-num 16 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 15 --repetition-num 16 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi

# TDD Table 8.5.1.5-3 — repetition 4, 15 kHz, 1 RX
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --tdd --num-rx 1 --scs 15 --repetition-num 4 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --tdd --num-rx 1 --scs 15 --repetition-num 4 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi

# FDD Table 8.5.1.5-4 — OCC, repetition 2, 3.75 kHz, NTN-TDLA100-1
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 3.75 --repetition-num 2 --propagation NTN-TDLA100-1 --occ-sequence-index 0 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 3.75 --repetition-num 2 --propagation NTN-TDLA100-1 --occ-sequence-index 1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 3.75 --repetition-num 2 --propagation NTN-TDLA100-1 --occ-sequence-index 0 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 3.75 --repetition-num 2 --propagation NTN-TDLA100-1 --occ-sequence-index 1 --ip <ip_address> --log-scpi

# FDD Table 8.5.1.5-5 — OCC, repetition 8, 15 kHz, NTN-TDLA100-1
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 15 --repetition-num 8 --propagation NTN-TDLA100-1 --occ-sequence-index 0 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 1 --scs 15 --repetition-num 8 --propagation NTN-TDLA100-1 --occ-sequence-index 1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 15 --repetition-num 8 --propagation NTN-TDLA100-1 --occ-sequence-index 0 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_1.py --num-rx 2 --scs 15 --repetition-num 8 --propagation NTN-TDLA100-1 --occ-sequence-index 1 --ip <ip_address> --log-scpi
```

### §8.5.2 parameters
| Parameter | CLI flag | Values |
|-----------|----------|--------|
| RX antennas | `--num-rx` | `1`, `2` (TDD Table 8.5.2.5-3 is 1 RX only) |
| Sub-carrier spacing | `--scs` | `3.75` (kHz, Table 8.5.2.5-1), `15` (kHz, Tables 8.5.2.5-2 / 8.5.2.5-3) |
| Repetition number | `--repetition-num` | `16` (FDD, Tables 8.5.2.5-1 / 8.5.2.5-2), `4` (TDD, Table 8.5.2.5-3) |
| Propagation | `--propagation` | `NTN-TDLA100-1` |
| Duplex | `--tdd` | omit (FDD), flag (TDD, Table 8.5.2.5-3) |

### Config-files (§8.5.2)

```powershell
python NB_IoT/ts-36181-chapter8/test_8_5_2.py NB_IoT/ts-36181-chapter8/configs/8_5_2/npusch_format2_1rx_rep16_3_75khz.ini
python NB_IoT/ts-36181-chapter8/test_8_5_2.py NB_IoT/ts-36181-chapter8/configs/8_5_2/npusch_format2_2rx_rep16_3_75khz.ini
python NB_IoT/ts-36181-chapter8/test_8_5_2.py NB_IoT/ts-36181-chapter8/configs/8_5_2/npusch_format2_1rx_rep16_15khz.ini
python NB_IoT/ts-36181-chapter8/test_8_5_2.py NB_IoT/ts-36181-chapter8/configs/8_5_2/npusch_format2_2rx_rep16_15khz.ini
python NB_IoT/ts-36181-chapter8/test_8_5_2.py NB_IoT/ts-36181-chapter8/configs/8_5_2/npusch_format2_1rx_rep4_15khz_tdd.ini
```

For TDD, pass `--tdd` or set `tdd = true`. FDD uses `--repetition-num 16` (Tables 8.5.2.5-1 / 8.5.2.5-2); TDD uses `--repetition-num 4` (Table 8.5.2.5-3). `--scs` selects 3.75 kHz (Table 8.5.2.5-1) or 15 kHz (Tables 8.5.2.5-2 / 8.5.2.5-3). Propagation is fixed to `NTN-TDLA100-1`.

See [`configs/8_5_2/`](configs/8_5_2/) for all §8.5.2 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `num_rx`, `repetition_num`, `scs`, `propagation`, `tdd`, `freq`, `cell_id`, `ue_id` |

```powershell
# FDD Table 8.5.2.5-1 — repetition 16, 3.75 kHz, NTN-TDLA100-1
python NB_IoT/ts-36181-chapter8/test_8_5_2.py --num-rx 1 --scs 3.75 --repetition-num 16 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_2.py --num-rx 2 --scs 3.75 --repetition-num 16 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi

# FDD Table 8.5.2.5-2 — repetition 16, 15 kHz, NTN-TDLA100-1
python NB_IoT/ts-36181-chapter8/test_8_5_2.py --num-rx 1 --scs 15 --repetition-num 16 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_2.py --num-rx 2 --scs 15 --repetition-num 16 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi

# TDD Table 8.5.2.5-3 — repetition 4, 15 kHz, 1 RX, NTN-TDLA100-1
python NB_IoT/ts-36181-chapter8/test_8_5_2.py --tdd --num-rx 1 --scs 15 --repetition-num 4 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
```

### §8.5.3 parameters
| Parameter | CLI flag | Values |
|-----------|----------|--------|
| RX antennas | `--num-rx` | `1`, `2` (TDD Table 8.5.3.5-2 is 1 RX only) |
| Repetition number | `--repetition-num` | `8`, `16` (FDD, Table 8.5.3.5-1), `4`, `8` (TDD, Table 8.5.3.5-2) |
| Preamble format | `--preamble-format` | `0`, `1` |
| Propagation | `--propagation` | `NTN-TDLA100-1` (FDD, Table 8.5.3.5-1), `NTN-TDLA100-1`, `NTN-TDLC5-1` (TDD, Table 8.5.3.5-2) |
| Duplex | `--tdd` | omit (FDD), flag (TDD, Table 8.5.3.5-2) |

### Config-files (§8.5.3)

```powershell
python NB_IoT/ts-36181-chapter8/test_8_5_3.py NB_IoT/ts-36181-chapter8/configs/8_5_3/prach_format0_1rx_rep8_tdla100.ini
python NB_IoT/ts-36181-chapter8/test_8_5_3.py NB_IoT/ts-36181-chapter8/configs/8_5_3/prach_format1_2rx_tdla100.ini
python NB_IoT/ts-36181-chapter8/test_8_5_3.py NB_IoT/ts-36181-chapter8/configs/8_5_3/prach_format0_2rx_rep16_tdla100.ini
python NB_IoT/ts-36181-chapter8/test_8_5_3.py NB_IoT/ts-36181-chapter8/configs/8_5_3/prach_format1_1rx_rep4_tdlc5_tdd.ini
```

For TDD, pass `--tdd` or set `tdd = true`. FDD uses `--repetition-num 8` or `16` (Table 8.5.3.5-1, NTN-TDLA100-1 only, 1 or 2 RX); TDD uses `--repetition-num 4` or `8` (Table 8.5.3.5-2, 1 RX, NTN-TDLA100-1 or NTN-TDLC5-1).

See [`configs/8_5_3/`](configs/8_5_3/) for all §8.5.3 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `num_rx`, `repetition_num`, `preamble_format`, `propagation`, `tdd`, `freq`, `cell_id`, `ue_id` |

```powershell
# FDD Table 8.5.3.5-1 — repetition 8, NTN-TDLA100-1
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 1 --repetition-num 8 --preamble-format 0 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 1 --repetition-num 8 --preamble-format 1 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 2 --repetition-num 8 --preamble-format 0 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 2 --repetition-num 8 --preamble-format 1 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi

# FDD Table 8.5.3.5-1 — repetition 16, NTN-TDLA100-1
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 1 --repetition-num 16 --preamble-format 0 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 1 --repetition-num 16 --preamble-format 1 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 2 --repetition-num 16 --preamble-format 0 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --num-rx 2 --repetition-num 16 --preamble-format 1 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi

# TDD Table 8.5.3.5-2 — repetition 4, 1 RX
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 4 --preamble-format 0 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 4 --preamble-format 0 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 4 --preamble-format 1 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 4 --preamble-format 1 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi

# TDD Table 8.5.3.5-2 — repetition 8, 1 RX
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 8 --preamble-format 0 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 8 --preamble-format 0 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 8 --preamble-format 1 --propagation NTN-TDLA100-1 --ip <ip_address> --log-scpi
python NB_IoT/ts-36181-chapter8/test_8_5_3.py --tdd --num-rx 1 --repetition-num 8 --preamble-format 1 --propagation NTN-TDLC5-1 --ip <ip_address> --log-scpi
```

---

## Lookup Tables

3GPP lookup tables for Chapter 8 are defined in [`tables_3gpp.py`](tables_3gpp.py).

| Constant | Section | Description |
|----------|---------|-------------|
| `FADING_PROFILES` | all | Maps a propagation condition to the SMW FSIMulator standard name: `NTN-TDLA100-5` → `NTNNBIOTTDLA100D5`, `NTN-TDLA100-1` → `NTNNBIOTTDLA100D1`, `NTN-TDLC5-5` → `NTNNBIOTTDLC5D5`, `NTN-TDLC5-1` → `NTNNBIOTTDLC5D1` |
| `PuschTestConfig` | §8.2.1 / §8.5.1 / §8.5.2 | Lookup result: SNR (dB), frequency offset (Hz), timing offset, optional FRC, `delta_power` (dB). `delta_power` is \(10\log_{10}(\text{occupied BW}/\text{AWGN BW})\) and is 0 when the signal fills the AWGN bandwidth. Instrument C/N and RF power use SNR + `delta_power` |
| `get_pusch_test_config()` | §8.2.1 / §8.5.1 / §8.5.2 | Lookup helper. Non-OCC tables are keyed by `(num_rx, repetition_num, scs, propagation)`. The OCC table adds `occ_sequence_index` (0 or 1) as a 5th key. Pass the section table as the first argument |
| `PUSCH_PERF_REQ_FDD` | §8.2.1 | Tables 8.2.1.5-1 / 8.2.1.5-2; 1.4 MHz; SCS 15 kHz; CEMode A rep 8 (FRC A5-2) / CEMode B rep 256 (FRC A5-1); NTN-TDLA100-5 / NTN-TDLC5-5; 1 or 2 RX |
| `PucchTestConfig` | §8.3.1 | Lookup result: SNR (dB), frequency offset (Hz), timing offset |
| `get_pucch_test_config()` | §8.3.1 | Lookup helper; keyed by `(num_rx, repetition_num, propagation)`; pass `PUCCH_FORMAT_1A_PERF_REQ_FDD` as the first argument |
| `PUCCH_FORMAT_1A_PERF_REQ_FDD` | §8.3.1 | Table 8.3.1.2.1-1; 1.4 MHz; PUCCH format 1a; repetition 8; NTN-TDLA100-5; 1 or 2 RX |
| `PrachTestConfig` | §8.4.1 / §8.5.3 | Lookup result: SNR (dB), time error tolerance (µs), `delta_power` (dB). §8.4.1 PRACH fills 1.08 MHz (`delta_power` = 0). §8.5.3 NPRACH is a 3.75 kHz tone (`delta_power` = −16.81 dB). Instrument C/N and RF power use SNR + `delta_power` |
| `get_prach_test_config()` | §8.4.1 / §8.5.3 | Lookup helper; keyed by `(num_rx, repetition_num, preamble_format, propagation)`; pass `EMTC_PRACH_PERF_REQ_FDD`, `NPRACH_PERF_REQ_FDD`, or `NPRACH_PERF_REQ_TDD` as the first argument |
| `EMTC_PRACH_PERF_REQ_FDD` | §8.4.1 | Table 8.4.1.5-1; NTN-TDLA100-5; burst formats 0/1 repetition 8, formats 2/3 repetition 16; 1 or 2 RX |
| `NPUSCH_FORMAT1_PERF_REQ_FDD` | §8.5.1 | Tables 8.5.1.5-1 / 8.5.1.5-2; NTN-TDLA100-1 / NTN-TDLC5-1; SCS 3.75 kHz rep 4 (FRC A16-1) / SCS 15 kHz rep 16 (FRC A16-2); 1 or 2 RX |
| `NPUSCH_FORMAT1_PERF_REQ_TDD` | §8.5.1 | Table 8.5.1.5-3; NTN-TDLA100-1 / NTN-TDLC5-1; SCS 15 kHz; repetition 4; FRC A16-2; 1 RX |
| `NPUSCH_FORMAT1_PERF_REQ_OCC_FDD` | §8.5.1 | Tables 8.5.1.5-4 / 8.5.1.5-5; NTN-TDLA100-1 only; 5-tuple key with OCC sequence index 0 or 1; 3.75 kHz symbol-level length-2 OCC rep 2 (FRC A16-1) / 15 kHz slot-level length-2 OCC rep 8 (FRC A16-3); 1 or 2 RX |
| `NPUSCH_FORMAT2_PERF_REQ_FDD` | §8.5.2 | Tables 8.5.2.5-1 / 8.5.2.5-2; NTN-TDLA100-1 only; SCS 3.75/15 kHz; repetition 16; 1 or 2 RX |
| `NPUSCH_FORMAT2_PERF_REQ_TDD` | §8.5.2 | Table 8.5.2.5-3; NTN-TDLA100-1; SCS 15 kHz; repetition 4; 1 RX |
| `NPRACH_PERF_REQ_FDD` | §8.5.3 | Table 8.5.3.5-1; NTN-TDLA100-1 only; preamble formats 0/1; repetitions 8/16; 1 or 2 RX |
| `NPRACH_PERF_REQ_TDD` | §8.5.3 | Table 8.5.3.5-2; NTN-TDLA100-1 / NTN-TDLC5-1; preamble formats 0/1; repetitions 4/8; 1 RX |

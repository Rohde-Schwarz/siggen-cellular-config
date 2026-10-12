# 3GPP TS 38.181 Chapter 8 — Conducted Performance Characteristics

Python scripts for SAN type 1-H performance tests defined in TS 38.181 Chapter 8.

See the [NTN README](../../README.md) for environment setup and shared utilities.

Run all commands below from **`ntn_conformance/`** with the virtual environment activated.

---

## Applicability

### §8.2 PUSCH performance requirements

Unless otherwise stated, §8.2 tests follow these rules:

- **Different SCS:** PUSCH requirements apply only for each SCS declared to be supported.
- **Different Channel BW:** For each SCS declared to be supported, tests shall only be done for the widest supported channel BW. If a performance requirement is not specified for that widest BW, use the closest lower BW that has a requirement. Tested PRBs shall be centered in this widest channel BW.
- **Different configs:** Use only the supported PUSCH mapping type. If both type A and B are supported, tests shall be done for either A or B.
- **Rep-Type A:** PUSCH repetition type A requirements apply only for a SAN declaring support of low spectral efficiency MCS index table 3 and PUSCH repetition type A.

### §8.3 PUCCH performance requirements

Unless otherwise stated, §8.3 tests follow these rules:

- **Different formats:** PUCCH requirements apply only for each PUCCH format declared to be supported.
- **Different SCS:** PUCCH requirements apply only for each SCS declared to be supported.
- **Different Channel BW:** For each SCS declared to be supported, tests shall only be done for the widest supported channel BW. If a performance requirement is not specified for that widest BW, use the closest lower widest channel BW. Tested PRBs shall be centered in this widest channel BW.
- **Different configs:** PUCCH format 3/4 requirements apply only for the additional DMRS config declared to be supported. If both configurations are supported, tests shall be done with and without additional DMRS.
- **Multi-slot:** Multi-slot PUCCH requirements apply only if the SAN supports multi-slot PUCCH.

## RF channels to test

Per TS 38.181, each test section defines which **RF channels to test** apply — typically **B**
(bottom), **M** (middle), and **T** (top) of the operating band. Set `freq` / `--freq` in the INI
file or on the CLI to match the channel(s) required for that section. The scripts do not select
B/M/T for you.

## Config files

Pass a per-test INI under `configs/` as the only argument, or use CLI flags instead. Global
settings (`ip`, `timeout`, `log_scpi`) are loaded from [`instrument.ini`](../../instrument.ini) and
[`NR5G/options.ini`](../options.ini). Each per-test file contains only a `[test]` section.

---

## Scripts

| Script | Test |
|--------|------|
| `test_8_2_1.py` | §8.2.1 PUSCH performance with transform precoding disabled |
| `test_8_2_2.py` | §8.2.2 PUSCH performance with transform precoding enabled |
| `test_8_2_3.py` | §8.2.3 UL timing adjustment accuracy, dual-UE |
| `test_8_2_4.py` | §8.2.4 PUSCH performance with repetition Type A |
| `test_8_2_5.py` | §8.2.5 PUSCH performance with DMRS bundling |
| `test_8_2_6.py` | §8.2.6 PUSCH performance with inter-slot OCC  |
| `test_8_3_1.py` | §8.3.1 PUCCH Format 0 |
| `test_8_3_2_1.py` | §8.3.2.1 PUCCH Format 1 — SR false alarm |
| `test_8_3_2_2.py` | §8.3.2.2 PUCCH Format 1 — ACK missed detection |
| `test_8_3_3_1.py` | §8.3.3.1 PUCCH Format 2 — ACK missed detection |
| `test_8_3_3_2.py` | §8.3.3.2 PUCCH Format 2 — UCI BLER |
| `test_8_3_4.py` | §8.3.4 PUCCH Format 3 |
| `test_8_3_5.py` | §8.3.5 PUCCH Format 4 |
| `test_8_3_6_1_1.py` | §8.3.6.1.1 Multi-slot PUCCH Format 1 — NACK to ACK false detection |
| `test_8_3_6_1_2.py` | §8.3.6.1.2 Multi-slot PUCCH Format 1 — ACK missed detection |
| `test_8_4_1.py` | §8.4.1 PRACH — false alarm probability and missed detection |
| `configs/` | Per-section INI folders for §8.2.1–§8.2.6, §8.3.1–§8.3.6.1, and §8.4.1 test cases |

### §8.2.1 / §8.2.2 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| PUSCH mapping type | `--pusch-type` | `A`, `B` |
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX), `NTN_TDLC5_200_SISO` (1 RX), `NTN_TDLC5_200_LOW` (2 RX) |

Example (CLI):

```powershell
python NR5G/ts-38181-chapter8/test_8_2_1.py --pusch-type A --bw 5 --scs 15 --num-rx 2 --propagation NTN_TDLC5_200_LOW
python NR5G/ts-38181-chapter8/test_8_2_2.py --pusch-type B --bw 10 --scs 30 --num-rx 1 --propagation NTN_TDLA100_200_SISO
python NR5G/ts-38181-chapter8/test_8_2_3.py --pusch-type A --bw 5 --scs 15 --num-rx 2 --propagation MP_NTN_15
python NR5G/ts-38181-chapter8/test_8_2_4.py --pusch-type A --bw 5 --scs 15 --num-rx 2 --propagation NTN_TDLA100_200_LOW
python NR5G/ts-38181-chapter8/test_8_2_5.py --pusch-type B --bw 10 --scs 30 --num-rx 1 --propagation NTN_TDLA100_200_SISO
python NR5G/ts-38181-chapter8/test_8_2_6.py --pusch-type A --bw 5 --scs 15 --num-rx 2 --propagation NTN_TDLC5_200_LOW
```

### Config-files (§8.2.1)

Parameters can be stored in an INI file instead of passing them on the command line.
Pass the config file as the only argument:

```powershell
python NR5G/ts-38181-chapter8/test_8_2_1.py NR5G/ts-38181-chapter8/configs/8_2_1/5mhz_15khz_1rx_tdla100_puschtypeA.ini
```

See [`configs/8_2_1/`](configs/8_2_1/) for all §8.2.1 test-case INI files. Each per-test file contains only a `[test]` section. Global settings are loaded automatically from [`instrument.ini`](../../instrument.ini) (`ip`, `timeout`) and [`NR5G/options.ini`](../options.ini) (`log_scpi`). Each file uses these keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `pusch_type`, `num_rx`, `propagation`, `freq`, `cell_id`, `ue_id` |

CLI flags remain supported and take precedence when used instead of a config file:

```powershell
python NR5G/ts-38181-chapter8/test_8_2_1.py --bw 5 --scs 15 --pusch-type A --num-rx 2 --propagation NTN_TDLA100_200_LOW --ip <ip_address> --log-scpi
```

### Config-files (§8.2.2)

```powershell
python NR5G/ts-38181-chapter8/test_8_2_2.py NR5G/ts-38181-chapter8/configs/8_2_2/5mhz_15khz_1rx_tdla100_puschtypeA.ini
```

See [`configs/8_2_2/`](configs/8_2_2/) for all §8.2.2 test-case INI files. Each file uses the same sections and keys as §8.2.1.

```powershell
python NR5G/ts-38181-chapter8/test_8_2_2.py --bw 10 --scs 30 --pusch-type B --num-rx 1 --propagation NTN_TDLA100_200_SISO --ip <ip_address> --log-scpi
```

### §8.2.3 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| PUSCH mapping type | `--pusch-type` | `A`, `B` |
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `MP_NTN_15`, `MP_NTN_30` |
| Moving UE ID | `--moving-ue-id` | `int` (default `0`; Entity1 `:SOURce1:BB:NR5G:UBWP:USER0:UEID`) |
| Stationary UE ID | `--stationary-ue-id` | `int` (default `0`; Entity2 `:SOURce1:BB:NR5G:UBWP:USER0:UEID`) |

Example (CLI):

```powershell
python NR5G/ts-38181-chapter8/test_8_2_3.py --pusch-type A --bw 5 --scs 15 --num-rx 2 --propagation MP_NTN_15 --ip <ip_address>
```

### Config-files (§8.2.3)

```powershell
python NR5G/ts-38181-chapter8/test_8_2_3.py NR5G/ts-38181-chapter8/configs/8_2_3/5mhz_15khz_2rx_mp_ntn15_puschtypeA.ini
```

See [`configs/8_2_3/`](configs/8_2_3/) for §8.2.3 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `pusch_type`, `num_rx`, `propagation`, `freq`, `cell_id`, `moving_ue_id`, `stationary_ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_2_3.py --bw 5 --scs 15 --pusch-type A --num-rx 2 --propagation MP_NTN_15 --ip <ip_address> --log-scpi
```

### Config-files (§8.2.4)

```powershell
python NR5G/ts-38181-chapter8/test_8_2_4.py NR5G/ts-38181-chapter8/configs/8_2_4/5mhz_15khz_1rx_tdla100_puschtypeA.ini
```

See [`configs/8_2_4/`](configs/8_2_4/) for all §8.2.4 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `pusch_type`, `num_rx`, `propagation`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_2_4.py --bw 5 --scs 15 --pusch-type A --num-rx 2 --propagation NTN_TDLA100_200_LOW --ip <ip_address> --log-scpi
```

### Config-files (§8.2.5)

```powershell
python NR5G/ts-38181-chapter8/test_8_2_5.py NR5G/ts-38181-chapter8/configs/8_2_5/5mhz_15khz_1rx_tdla100_puschtypeA.ini
```

See [`configs/8_2_5/`](configs/8_2_5/) for all §8.2.5 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `pusch_type`, `num_rx`, `propagation`, `freq`, `cell_id`, `ue_id` |

Type A cases configure PUSCH repetition Type A with DMRS bundling (`AGFT N4` at 15 kHz, `AGFT N8` at 30 kHz).

**RB assignment.** TS 38.181 §8.2.5 requires the PUSCH allocation to use 6 RBs placed in the middle of the channel bandwidth. `test_8_2_5.py` derives the FRC RB offset from `NUM_RBS` in `NR5G/utils.py` using `(num_rbs - 6 + 1) // 2`, which centres the 6-RB FRC within the available RBs. For the supported test cases this yields:

| Channel BW | SCS | Total RBs | RB offset |
|------------|-----|-----------|-----------|
| 10 MHz | 30 kHz | 24 | 9 |
| 5 MHz | 15 kHz | 25 | 10 |

**Note:** For the 5 MHz / 15 kHz case the ideal offset is 9.5 RBs, so an exact centre is not possible with integer RB granularity; the script rounds up to the nearest integer offset (10).

```powershell
python NR5G/ts-38181-chapter8/test_8_2_5.py --bw 5 --scs 15 --pusch-type A --num-rx 2 --propagation NTN_TDLA100_200_LOW --ip <ip_address> --log-scpi
```

### Config-files (§8.2.6)

```powershell
python NR5G/ts-38181-chapter8/test_8_2_6.py NR5G/ts-38181-chapter8/configs/8_2_6/5mhz_15khz_1rx_tdlc5_puschtypeA.ini
```

See [`configs/8_2_6/`](configs/8_2_6/) for all §8.2.6 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `pusch_type`, `num_rx`, `propagation`, `freq`, `cell_id` |

Dual-UE OCC: Entity1 (UE0) uses OCC index 0 and DMRS port AP0; Entity2 (UE1) uses OCC index 1 and DMRS port AP1. Multiplex offset: 200 Hz `FOFFset` on Entity2 only (UE1). Fading is enabled on both entities (same TDL profile as `--propagation`); AWGN is configured on Entity1 only (`sources=1`, `ue=0`).

```powershell
python NR5G/ts-38181-chapter8/test_8_2_6.py --bw 10 --scs 30 --pusch-type B --num-rx 2 --propagation NTN_TDLC5_200_LOW --ip <ip_address> --log-scpi
```

### §8.2.4 / §8.2.5 / §8.2.6 parameters

Same as §8.2.1 / §8.2.2. Test tables for §8.2.4 and §8.2.5 define TDLA100 only: `NTN_TDLA100_200_SISO` (1 RX) or `NTN_TDLA100_200_LOW` (2 RX). §8.2.6 uses TDLC5 only: `NTN_TDLC5_200_SISO` (1 RX) or `NTN_TDLC5_200_LOW` (2 RX).

### §8.3.1 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |
| Test mode | `--test-mode` | `detection_rate` (default) |

Example (CLI):

```powershell
python NR5G/ts-38181-chapter8/test_8_3_1.py --bw 10 --scs 30 --num-rx 2 --propagation NTN_TDLA100_200_LOW
```

PUCCH is configured via `configure_pucch()` in [`NR5G/utils.py`](../utils.py). Triggers use Source1 only; fading and AWGN use both sources.

### Config-files (§8.3.1)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_1.py NR5G/ts-38181-chapter8/configs/8_3_1/10mhz_30khz_2rx_tdla100.ini
```

See [`configs/8_3_1/`](configs/8_3_1/) for all §8.3.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `test_mode`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_3_1.py --bw 5 --scs 15 --num-rx 1 --propagation NTN_TDLA100_200_SISO --test-mode detection_rate --ip <ip_address> --log-scpi
```

### §8.3.2.1 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |

PUCCH Format 1 is configured via `configure_pucch(fmt=1, ack_pattern="#H0,2")` — both ACK bits are sent as NACK.

### Config-files (§8.3.2.1)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_2_1.py NR5G/ts-38181-chapter8/configs/8_3_2_1/5mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_2_1.py NR5G/ts-38181-chapter8/configs/8_3_2_1/5mhz_15khz_2rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_2_1.py NR5G/ts-38181-chapter8/configs/8_3_2_1/10mhz_30khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_2_1.py NR5G/ts-38181-chapter8/configs/8_3_2_1/10mhz_30khz_2rx_tdla100.ini
```

See [`configs/8_3_2_1/`](configs/8_3_2_1/) for all §8.3.2.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `freq`, `cell_id`, `ue_id` |

### §8.3.2.2 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |
| Test mode | `--test-mode` | `detection_rate` (default), `false_detection_rate` |

PUCCH Format 1 is configured via `configure_pucch(fmt=1)` (ACK pattern `#H3,2` hardcoded).

### Config-files (§8.3.2.2)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_2_2.py NR5G/ts-38181-chapter8/configs/8_3_2_2/5mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_2_2.py NR5G/ts-38181-chapter8/configs/8_3_2_2/5mhz_15khz_2rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_2_2.py NR5G/ts-38181-chapter8/configs/8_3_2_2/10mhz_30khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_2_2.py NR5G/ts-38181-chapter8/configs/8_3_2_2/10mhz_30khz_2rx_tdla100.ini
```

For `false_detection_rate`, pass `--test-mode false_detection_rate` on the CLI or set `test_mode` in the INI file.

See [`configs/8_3_2_2/`](configs/8_3_2_2/) for all §8.3.2.2 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `test_mode`, `freq`, `cell_id`, `ue_id` |

### §8.3.3.1 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |
| Test mode | `--test-mode` | `detection_rate` (default), `false_detection_rate` |

PUCCH Format 2 is configured via `configure_pucch(fmt=2)` (1 symbol, offset 13, 4 RBs, 4 UCI bits `#HF,4`).

### Config-files (§8.3.3.1)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_3_1.py NR5G/ts-38181-chapter8/configs/8_3_3_1/5mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_1.py NR5G/ts-38181-chapter8/configs/8_3_3_1/5mhz_15khz_2rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_1.py NR5G/ts-38181-chapter8/configs/8_3_3_1/10mhz_30khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_1.py NR5G/ts-38181-chapter8/configs/8_3_3_1/10mhz_30khz_2rx_tdla100.ini
```

For `false_detection_rate`, pass `--test-mode false_detection_rate` on the CLI or set `test_mode` in the INI file.

See [`configs/8_3_3_1/`](configs/8_3_3_1/) for all §8.3.3.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `test_mode`, `freq`, `cell_id`, `ue_id` |

### §8.3.3.2 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `3`, `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |

PUCCH Format 2 is configured via `configure_pucch(fmt=2, section="8_3_3_2")` (2 symbols, offset 12, 9 RBs, intra-slot hopping, 22 UCI bits all set to 0 — `#H000000,22`).

### Config-files (§8.3.3.2)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_3_2.py NR5G/ts-38181-chapter8/configs/8_3_3_2/3mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_2.py NR5G/ts-38181-chapter8/configs/8_3_3_2/3mhz_15khz_2rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_2.py NR5G/ts-38181-chapter8/configs/8_3_3_2/5mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_2.py NR5G/ts-38181-chapter8/configs/8_3_3_2/5mhz_15khz_2rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_2.py NR5G/ts-38181-chapter8/configs/8_3_3_2/10mhz_30khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_3_2.py NR5G/ts-38181-chapter8/configs/8_3_3_2/10mhz_30khz_2rx_tdla100.ini
```

See [`configs/8_3_3_2/`](configs/8_3_3_2/) for all §8.3.3.2 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_3_3_2.py --bw 3 --scs 15 --num-rx 1 --propagation NTN_TDLA100_200_SISO --ip <ip_address> --log-scpi
```

### §8.3.4 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |
| Additional DMRS | `--additional-dmrs` | flag (default: off) |

PUCCH Format 3 is configured via `configure_pucch(fmt=3, additional_dmrs=...)` (14 symbols, 1 PRB, intra-slot hopping, 16 UCI bits all set to 0 — `#H0000,16`).

### Config-files (§8.3.4)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/5mhz_15khz_1rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/5mhz_15khz_1rx_tdla100_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/5mhz_15khz_2rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/5mhz_15khz_2rx_tdla100_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/10mhz_30khz_1rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/10mhz_30khz_1rx_tdla100_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/10mhz_30khz_2rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_4.py NR5G/ts-38181-chapter8/configs/8_3_4/10mhz_30khz_2rx_tdla100_add_dmrs.ini
```

See [`configs/8_3_4/`](configs/8_3_4/) for all §8.3.4 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `additional_dmrs`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_3_4.py --bw 10 --scs 30 --num-rx 2 --propagation NTN_TDLA100_200_LOW --additional-dmrs --ip <ip_address> --log-scpi
```

### §8.3.5 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |
| Additional DMRS | `--additional-dmrs` | flag (default: off) |

PUCCH Format 4 is configured via `configure_pucch(fmt=4, additional_dmrs=...)` (14 symbols, 1 PRB, intra-slot hopping, 22 UCI bits all set to 0 — `#H000000,22`, OCC index 0, OCC length L2).

### Config-files (§8.3.5)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/5mhz_15khz_1rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/5mhz_15khz_1rx_tdla100_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/5mhz_15khz_2rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/5mhz_15khz_2rx_tdla100_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/10mhz_30khz_1rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/10mhz_30khz_1rx_tdla100_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/10mhz_30khz_2rx_tdla100_no_add_dmrs.ini
python NR5G/ts-38181-chapter8/test_8_3_5.py NR5G/ts-38181-chapter8/configs/8_3_5/10mhz_30khz_2rx_tdla100_add_dmrs.ini
```

See [`configs/8_3_5/`](configs/8_3_5/) for all §8.3.5 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `additional_dmrs`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_3_5.py --bw 10 --scs 30 --num-rx 2 --propagation NTN_TDLA100_200_LOW --additional-dmrs --ip <ip_address> --log-scpi
```

### §8.3.6.1.1 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |

Multi-slot PUCCH Format 1 is configured via `configure_pucch(fmt=1, multi_slot=True, ack_pattern="#H0,2")` — both ACK bits are sent as NACK (two allocations: slot 0 at RB offset 0, slot 1 at RB offset `num_rbs - 1`, 14 symbols each, custom repetitions with period 2).

### Config-files (§8.3.6.1.1)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_6_1_1.py NR5G/ts-38181-chapter8/configs/8_3_6_1_1/5mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_6_1_1.py NR5G/ts-38181-chapter8/configs/8_3_6_1_1/5mhz_15khz_2rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_6_1_1.py NR5G/ts-38181-chapter8/configs/8_3_6_1_1/10mhz_30khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_6_1_1.py NR5G/ts-38181-chapter8/configs/8_3_6_1_1/10mhz_30khz_2rx_tdla100.ini
```

See [`configs/8_3_6_1_1/`](configs/8_3_6_1_1/) for all §8.3.6.1.1 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_3_6_1_1.py --bw 10 --scs 30 --num-rx 2 --propagation NTN_TDLA100_200_LOW --ip <ip_address> --log-scpi
```

### §8.3.6.1.2 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| Sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |
| Test mode | `--test-mode` | `detection_rate` (default), `false_detection_rate` |

Multi-slot PUCCH Format 1 is configured via `configure_pucch(fmt=1, multi_slot=True)` (two allocations: slot 0 at RB offset 0, slot 1 at RB offset `num_rbs - 1`, 14 symbols each, 2 ACK bits `#H3,2`, custom repetitions with period 2).

- `detection_rate` (§8.3.6.1.2): configures multi-slot PUCCH and uses `PUCCH_PERF_REQ_8_3_6_1_2`
- `false_detection_rate`: skips PUCCH/node config, uses `noise_only_mode=True`, and uses `PUCCH_PERF_REQ_8_3_6_1_1`

### Config-files (§8.3.6.1.2)

```powershell
python NR5G/ts-38181-chapter8/test_8_3_6_1_2.py NR5G/ts-38181-chapter8/configs/8_3_6_1_2/5mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_6_1_2.py NR5G/ts-38181-chapter8/configs/8_3_6_1_2/5mhz_15khz_2rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_6_1_2.py NR5G/ts-38181-chapter8/configs/8_3_6_1_2/10mhz_30khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_3_6_1_2.py NR5G/ts-38181-chapter8/configs/8_3_6_1_2/10mhz_30khz_2rx_tdla100.ini
```

For `false_detection_rate`, pass `--test-mode false_detection_rate` on the CLI or set `test_mode` in the INI file.

See [`configs/8_3_6_1_2/`](configs/8_3_6_1_2/) for all §8.3.6.1.2 test-case INI files. Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `num_rx`, `propagation`, `test_mode`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_3_6_1_2.py --bw 10 --scs 30 --num-rx 2 --propagation NTN_TDLA100_200_LOW --test-mode detection_rate --ip <ip_address> --log-scpi
```

### §8.4.1 parameters

| Parameter | CLI flag | Values |
|-----------|----------|--------|
| Channel bandwidth | `--bw` | `5`, `10` (MHz) |
| BWP sub-carrier spacing | `--scs` | `15`, `30` (kHz) |
| PRACH sub-carrier spacing | `--prach-scs` | `1.25`, `15`, `30` (kHz) |
| Burst format | `--burst-format` | `0`, `2` (for PRACH SCS 1.25 kHz); `B4`, `C2` (for 15/30 kHz) |
| RX antennas | `--num-rx` | `1`, `2` |
| Propagation | `--propagation` | `AWGN`, `NTN_TDLA100_200_SISO` (1 RX), `NTN_TDLA100_200_LOW` (2 RX) |
| Test mode | `--test-mode` | `detection_rate` (default), `false_detection_rate` |

Valid BWP/PRACH SCS combinations (from TS 38.181 Table):

| BW | BWP SCS (`--scs`) | PRACH SCS (`--prach-scs`) | Burst formats |
|----|-------------------|--------------------------|---------------|
| 5 MHz | 15 kHz | 1.25 kHz | 0, 2 |
| 5 MHz | 15 kHz | 15 kHz | B4, C2 |
| 5 MHz | 15 kHz | 30 kHz | B4, C2 |
| 10 MHz | 30 kHz | 1.25 kHz | 0, 2 |
| 10 MHz | 30 kHz | 15 kHz | B4, C2 |
| 10 MHz | 30 kHz | 30 kHz | B4, C2 |

AWGN power (Table 8.4.1.4.2-1) is determined by carrier BW, not PRACH SCS: 5 MHz → -83.5 dBm / 4.5 MHz, 10 MHz → -80.6 dBm / 8.64 MHz.

- `detection_rate`: full flow — `configure_node` → `configure_prach` → fading (NTN-TDLA only) → `configure_awgn`
- `false_detection_rate`: skips node/PRACH/fading, uses `noise_only_mode=True` in `configure_awgn`, RF set to AWGN power only
- Fading, AWGN, RF, and analog output follow `--num-rx` (Source1 only for 1 RX; Source1+Source2 for 2 RX)

Example (CLI):

```powershell
# Missed detection — PRACH SCS 15 kHz, BWP 15 kHz, 5 MHz BW
python NR5G/ts-38181-chapter8/test_8_4_1.py --bw 5 --scs 15 --prach-scs 15 --num-rx 1 --propagation NTN_TDLA100_200_SISO --burst-format B4

# Missed detection — PRACH SCS 1.25 kHz, BWP 30 kHz, 10 MHz BW
python NR5G/ts-38181-chapter8/test_8_4_1.py --bw 10 --scs 30 --prach-scs 1.25 --num-rx 2 --propagation AWGN --burst-format 0

# False detection rate (noise only)
python NR5G/ts-38181-chapter8/test_8_4_1.py --bw 5 --scs 15 --prach-scs 15 --num-rx 1 --propagation AWGN --burst-format B4 --test-mode false_detection_rate --ip <ip_address> --log-scpi
```

### Config-files (§8.4.1)

```powershell
python NR5G/ts-38181-chapter8/test_8_4_1.py NR5G/ts-38181-chapter8/configs/8_4_1/prach_15kHz/formatB4_5mhz_15khz_1rx_tdla100.ini
python NR5G/ts-38181-chapter8/test_8_4_1.py NR5G/ts-38181-chapter8/configs/8_4_1/prach_1_25kHz/format0_10mhz_30khz_2rx_awgn.ini
```

For `false_detection_rate`, pass `--test-mode false_detection_rate` on the CLI or set `test_mode = false_detection_rate` in the INI file.

See [`configs/8_4_1/`](configs/8_4_1/) for all 48 §8.4.1 test-case INI files (`prach_1_25kHz/`, `prach_15kHz/`, `prach_30kHz/`). Keys:

| Section | Keys |
|---------|------|
| `[test]` | `bw`, `scs`, `prach_scs`, `num_rx`, `propagation`, `burst_format`, `test_mode`, `freq`, `cell_id`, `ue_id` |

```powershell
python NR5G/ts-38181-chapter8/test_8_4_1.py --bw 5 --scs 15 --prach-scs 15 --num-rx 2 --propagation NTN_TDLA100_200_LOW --burst-format C2 --ip <ip_address> --log-scpi
```

---

## Lookup Tables

3GPP lookup tables for Chapter 8 are defined in [`tables_3gpp.py`](tables_3gpp.py).

| Constant | Section | Description |
|----------|---------|-------------|
| `PUSCH_PERF_REQ_8_2_1` | §8.2.1 | Keyed by `(pusch_type, bw, scs, num_rx, propagation)` |
| `PUSCH_PERF_REQ_8_2_2` | §8.2.2 | Keyed by `(pusch_type, bw, scs, num_rx, propagation)` |
| `PUSCH_PERF_REQ_8_2_3` | §8.2.3 | Keyed by `(pusch_type, bw, scs, num_rx, propagation)`; `MP_NTN_15` / `MP_NTN_30` |
| `PUSCH_PERF_REQ_8_2_4` | §8.2.4 | Keyed by `(pusch_type, bw, scs, num_rx, propagation)`; TDLA100 only |
| `PUSCH_PERF_REQ_8_2_5` | §8.2.5 | Keyed by `(pusch_type, bw, scs, num_rx, propagation)`; TDLA100 only |
| `PUSCH_PERF_REQ_8_2_6` | §8.2.6 | Keyed by `(pusch_type, bw, scs, num_rx, propagation)`; TDLC5 only |
| `PUCCH_PERF_REQ_8_3_1` | §8.3.1.5 | Keyed by `(bw, scs, num_rx, propagation)` |
| `PUCCH_PERF_REQ_8_3_2_1` | §8.3.2.1 | Keyed by `(bw, scs, num_rx, propagation)` |
| `PUCCH_PERF_REQ_8_3_2_2` | §8.3.2.2 | Keyed by `(bw, scs, num_rx, propagation)` |
| `PUCCH_PERF_REQ_8_3_3_1` | §8.3.3.1 | Keyed by `(bw, scs, num_rx, propagation)` |
| `PUCCH_PERF_REQ_8_3_3_2` | §8.3.3.2 | Keyed by `(bw, scs, num_rx, propagation)`; includes 3 MHz BW |
| `PUCCH_PERF_REQ_8_3_4` | §8.3.4 | Keyed by `(bw, scs, num_rx, propagation, additional_dmrs)` |
| `PUCCH_PERF_REQ_8_3_5` | §8.3.5 | Keyed by `(bw, scs, num_rx, propagation, additional_dmrs)` |
| `PUCCH_PERF_REQ_8_3_6_1_1` | §8.3.6.1.1 | Keyed by `(bw, scs, num_rx, propagation)` |
| `PUCCH_PERF_REQ_8_3_6_1_2` | §8.3.6.1.2 | Keyed by `(bw, scs, num_rx, propagation)` |
| `FADING_PROFILES` | §8.2.1+ | Maps propagation condition to SMW FSIMulator standard name |
| `MOV_PROP_PROFILES` | §8.2.3 | Maps moving propagation condition to SMW FSIMulator standard name |
| `PuschTestConfig` | §8.2.1–§8.2.6 | Lookup result: FRC, SNR (dB), AWGN power (dBm), AWGN BW (MHz) |
| `get_pusch_test_config()` | §8.2.1–§8.2.6 | Lookup helper; prints `#Test Config#` block with lookup keys and table values; pass the section table as first argument |
| `PucchTestConfig` | §8.3.1–§8.3.6 | Lookup result: SNR (dB), AWGN power (dBm), AWGN BW (MHz) |
| `get_pucch_test_config()` | §8.3.1 | Lookup helper; prints `#Test Config#` block with lookup keys and table values; pass the section table as first argument |
| `PrachTestConfig` | §8.4.1 | Lookup result: SNR (dB), time error tolerance (us), freq offset (Hz), AWGN power (dBm), AWGN BW (MHz) |
| `get_prach_test_config()` | §8.4.1 | Lookup helper; pass the section table as first argument |
| `PRACH_PERF_REQ_8_4_1` | §8.4.1 | Keyed by `(prach_scs, bw, num_rx, propagation, burst_format)`; AWGN from Table 8.4.1.4.2-1 |
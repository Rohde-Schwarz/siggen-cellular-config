# NR5G Shared Utilities

[`NR5G/utils.py`](utils.py) provides the SMW configuration functions and helpers used by all
Chapter 7 and Chapter 8 test scripts. This is the single source of SMW baseband, fading, AWGN,
HARQ, PUCCH, and PRACH configuration logic for NR5G NTN tests.

See:
- [`ts-38181-chapter7/README.md`](ts-38181-chapter7/README.md) — Chapter 7 test documentation
- [`ts-38181-chapter8/README.md`](ts-38181-chapter8/README.md) — Chapter 8 test documentation

---

## Constants

### `NTN_FRC_TYPE`

Dictionary mapping 3GPP FRC names to their corresponding SMW SCPI type strings. Covers:

- A1 channels: `G-FR1-NTN-A1-1` … `G-FR1-NTN-A1-12`
- A2 channels: `G-FR1-NTN-A2-1` … `G-FR1-NTN-A2-7`
- A3 channels: `G-FR1-NTN-A3-1` … `G-FR1-NTN-A3-8`
- A3A channels: `G-FR1-NTN-A3A-1`, `G-FR1-NTN-A3A-2`, `G-FR1-NTN-A3A-4`

Used internally by `configure_frc()`.

---

## Config Loading

### `load_ini_as_namespace(path)`

Loads an NR5G test INI file, merging three sources in order:

| File | Section | Keys |
|------|---------|------|
| `instrument.ini` (`ntn_conformance/`) | `[instrument]` | `ip`, `timeout` |
| `NR5G/options.ini` | `[options]` | `log_scpi` |
| Per-test INI file | `[test]` | test-specific keys |

Returns a flat `argparse.Namespace` with automatic type coercion:
- Frequency keys (`freq`, `interferer_freq`, `ful_low`, `ful_high`) are parsed with unit suffix
  support (e.g. `1.62G`, `1620MHz`, `1620000000`).
- Boolean keys (`log_scpi`, `nb_iot_inband`, `additional_dmrs`) are coerced from string to `bool`.
- Integer-like values are coerced automatically.

---

## CLI

### `build_base_parser(description, *, include_class=True, include_ue_id=True, require_num_rx=False)`

Builds an `argparse.ArgumentParser` with the common options shared by all chapter scripts:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--bw` | `int` | required | Channel bandwidth in MHz (e.g. `5`, `10`) |
| `--scs` | `int` | required | Sub-carrier spacing in kHz (e.g. `15`, `30`, `60`) |
| `--num-rx` | `1` \| `2` | optional | Number of RX antennas. Required when `require_num_rx=True` (not used by Chapter 7 scripts) |
| `--class` | `leo` \| `geo` | optional | SAN orbit class. Included only when `include_class=True` |
| `--freq` | frequency | `1620000000` | PCFReq / RF center frequency in Hz or with suffix (e.g. `1.62G`). Set per TS 38.181 RF channels to test (B/M/T) for each section |
| `--cell-id` | `int` | `0` | NR5G cell ID for the wanted signal on Source1 |
| `--ue-id` | `int` | `0` | NR5G UE ID for the wanted signal on Source1 (`UBWP:USER0:UEID`). Included only when `include_ue_id=True` |
| `--ip` | `str` | none | SMW IP address. When set, the script connects and configures the instrument |
| `--timeout` | `int` | `80` | SMW OPC/VISA timeout in seconds |
| `--log-scpi` | flag | off | Write all SCPI commands to `scpi-list.iec` after the run |

---

## Baseband Configuration

### `configure_triggers(smw, sources=1, *, ue=None)`

Configures armed-auto NR5G triggers using external gate input USER3.

- `sources=1` (default): only Source1 carries an NR5G signal.
- `sources=2`: Source2 also carries an NR5G signal and shares the USER3 trigger.
- `ue`: optional 0-based UE index for multi-UE setups (§8.2.3); prefixes all commands with
  `:ENTity{ue+1}`.

### `configure_node(smw, bw, scs, freq, *, cell_id=0, source=1, link="UP", ue=None)`

Configures NR5G node parameters for the given source:

- Carrier deployment: `FR1LT3`
- PCFReq frequency, channel bandwidth, TX bandwidth SCS
- Cell ID (`cell_id`) and DMRS Type A position

### `configure_ueid(smw, ue_id=0, *, source=1, ue=None)`

Sets NR5G UE ID on `:SOURce{source}:BB:NR5G:UBWP:USER0:UEID`. Used by PUCCH and PRACH tests
that do not call `configure_frc()`. In dual-UE setups (§8.2.3), pass `ue` to prefix with
`:ENTity{ue+1}`.

### `configure_frc(smw, ref_meas_channel, source=1, frc_type_map=None, rb_offset=0, *, map_type=None, ue=None, ue_id=0)`

Applies the Fixed Reference Channel (FRC) matching the given channel name. Enables channel coding,
activates the FRC, sets UE ID (`ue_id`) after FRC type selection, and sets the RB offset. Looks up
the SCPI FRC type from `NTN_FRC_TYPE` (or a custom map if provided via `frc_type_map`).

---

## Multi-RX / Dual-UE Configuration

### `configure_advance_mode(smw, num_rx, *, multi_ue=False)`

Configures the SMW advanced fading mode for multi-RX or multi-UE setups:

| `multi_ue` | `num_rx` | Mode |
|------------|---------|------|
| `False` | `1` | No-op (single-UE SISO — no advanced mode needed) |
| `False` | `2` | `MIMO1X2` |
| `True` | `1` | `MIMO2X1X1` (FAAFBB) |
| `True` | `2` | `MIMO2X1X2` |

### `configure_iqMapping(smw, num_rx, *, multi_ue=False)`

Configures the SMW IQ output mapping for dual-UE MIMO2X1X2 setups (§8.2.3). Routes streams 3 and 4
to IQ outputs 1 and 2, and streams 1 and 2 to BBMM outputs. No-op for non-MIMO2X1X2 configurations.

### `configure_dmrsID(smw, *, ue)`

Sets the DMRS identity for a specific UE in dual-UE setups (§8.2.3):

- UE 0 (moving UE): DMRS ID 0
- UE 1 (stationary UE): DMRS ID 1

---

## Fading and Noise

### `configure_fading(smw, propagation, fsim_standard, sources=2, *, ue=None)`

Configures the fading simulator for Chapter 8 tests. Sets the FSIMulator standard and enables
fading on the specified number of sources.

- `sources=2` (default): used for single-UE setups (both Source1 and Source2).
- `sources=1`: used in dual-UE setups (called once per UE).
- `ue`: optional 0-based UE index; prefixes commands with `:ENTity{ue+1}`.

### `configure_awgn(smw, snr_db, awgn_bw, sources=2, *, awgn_power_dbm=None, noise_only_mode=False, ue=None)`

Configures AWGN interference. Source1 AWGN is routed to RFA; Source2 to RFB.

**Normal mode** (`noise_only_mode=False`): AWGN is added on top of the NR5G signal at a given C/N
ratio (`snr_db`). The NR5G output power reference is set to PSDC mode with the AWGN bandwidth.

**Noise-only mode** (`noise_only_mode=True`): AWGN only (no NR5G signal), at a fixed noise power
(`awgn_power_dbm`). Used for false-detection-rate test modes in §8.3.x and §8.4.1.

---

## HARQ and Repetitions

### `configure_harq(smw, *, timing_advance=False, ue=None)`

Configures HARQ feedback for NR5G uplink testing. Sets serial feedback mode at 1.9 Mbps via USER
input TM3. When `timing_advance=True`, enables timing advance mode (required for §8.2.3).

### `configure_repTypeA(smw)`

Configures PUSCH repetition Type A scheduler allocation (§8.2.4). Sets repetition type `TA`,
period 1, duration 1, and aggregation factor `F2`.

### `configure_repTypeA_dmrsBundling(smw, scs)`

Configures PUSCH repetition Type A with DMRS bundling (§8.2.5). Aggregation factor is `F4` at
15 kHz SCS or `F8` at 30 kHz SCS.

---

## PUCCH

### `configure_pucch(smw, fmt, bw, scs, *, additional_dmrs=None, ack_pattern=None, section=None, multi_slot=False)`

Configures a PUCCH allocation for Chapter 8 tests. Supported formats:

| Format | Section | Symbols | RBs | UCI / ACK |
|--------|---------|---------|-----|-----------|
| 0 | §8.3.1 | 2, offset 12 | 1 | 1 ACK bit (`#H1,1`), intra-slot hopping |
| 1 | §8.3.2.1 | 14, offset 0 | 1 | 2 ACK bits, both NACK (`#H0,2`), intra-slot hopping |
| 1 | §8.3.2.2 | 14, offset 0 | 1 | 2 ACK bits (`#H3,2`), intra-slot hopping |
| 1 (multi-slot) | §8.3.6.1.1 | 14, offset 0 per slot | 1 | 2 ACK bits, both NACK (`#H0,2`), period 2 |
| 1 (multi-slot) | §8.3.6.1.2 | 14, offset 0 per slot | 1 | 2 ACK bits (`#H3,2`), period 2 |
| 2 | §8.3.3.1 | 1, offset 13 | 4 | 4 UCI bits (`#HF,4`) |
| 2 | §8.3.3.2 | 2, offset 12 | 9 | 22 UCI bits, all 0 (`#H000000,22`), intra-slot hopping |
| 3 | §8.3.4 | 14, offset 0 | 1 | 16 UCI bits, all 0 (`#H0000,16`), intra-slot hopping |
| 4 | §8.3.5 | 14, offset 0 | 1 | 22 UCI bits, all 0 (`#H000000,22`), OCC index 0, OCC length L2 |

Key arguments:
- `section="8_3_3_1"` or `"8_3_3_2"`: selects the correct Format 2 variant.
- `multi_slot=True`: enables the two-allocation multi-slot layout for §8.3.6.1.x.
- `additional_dmrs`: enables additional DMRS positions for Formats 3 and 4 (§8.3.4, §8.3.5).
- `ack_pattern`: overrides the default ACK bit pattern for Format 1.

See [`ts-38181-chapter8/README.md`](ts-38181-chapter8/README.md) for §8.2/§8.3 applicability rules and the §8.3 PUCCH payload bit-pattern table.

---

## PRACH

### `configure_prach(smw, burst_format, freq_offset_hz, prach_scs)`

Configures PRACH for Chapter 8 tests (§8.4.1). Supported burst formats:

| Format | PRACH SCS | Subframes configured | Notes |
|--------|-----------|----------------------|-------|
| `0`, `2` | 1.25 kHz | 10 (odd subframes 1–19), period 9 | Per-subframe time offset; baseband frequency offset applied |
| `B4`, `C2` | 15 or 30 kHz | 9 (subframes 0–8), period 9 | Custom repetitions; baseband frequency offset applied |

---

## Output

### `configure_output(smw)`

Enables the required output states for Chapter 8 tests:

- Source2 fading simulator output
- Source1 and Source2 analog IQ outputs
- Source1 digital BBMM1 output

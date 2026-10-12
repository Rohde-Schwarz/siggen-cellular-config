# NBIoT Shared Utilities

[`NB_IoT/utils.py`](utils.py) provides the SMW configuration functions and helpers used by all
Chapter 7 and Chapter 8 test scripts. This is the single source of SMW baseband, fading, AWGN,
HARQ, PUCCH, and PRACH configuration logic for NB_IoT NTN tests.

See:
- [`ts-36181-chapter7/README.md`](ts-36181-chapter7/README.md) — Chapter 7 test documentation
- [`ts-36181-chapter8/README.md`](ts-36181-chapter8/README.md) — Chapter 8 test documentation


## Constants

### `FRC_TYPE`

Dictionary mapping 3GPP FRC names to their corresponding SMW SCPI type strings. The Chapter 7 and Chapter 8 tests use:

- A1 channels: `FRC-A1-1`, `FRC-A1-4`
- A2 channels: `FRC-A2-1`
- A5 channels: `FRC-A5-1`, `FRC-A5-2`
- A14 channels: `FRC-A14-1` … `FRC-A14-3`
- A15 channels: `FRC-A15-1`, `FRC-A15-2`
- A16 channels: `FRC-A16-1` … `FRC-A16-3`

Used internally by `configure_frc()`.

---

## Config Loading

### `load_ini_as_namespace(path)`

Loads an NB_IoT test INI file, merging three sources in order:

| File | Section | Keys |
|------|---------|------|
| `instrument.ini` (repo root) | `[instrument]` | `ip` |
| `NB_IoT/options.ini` | `[options]` | `log_scpi` |
| Per-test INI file | `[test]` | test-specific keys |

Returns a flat `argparse.Namespace` with automatic type coercion:
- Frequency keys (`freq`, `interferer_freq`, `ful_low`, `ful_high`) are parsed with unit suffix
  support (e.g. `1.62G`, `1620MHz`, `1620000000`).
- Boolean keys (`log_scpi`, `nb_iot_inband`, `additional_dmrs`, `tdd`) are coerced from string to `bool`.
- Integer-like values (`15`, `1620000000`) and float-like values (`0.2`, `1.4`, `3.75`) are coerced automatically.

---

## CLI

### `build_base_parser(description, *, include_class=True, require_num_rx=False)`

Builds an `argparse.ArgumentParser` with the common options shared by all chapter scripts:

| Flag         | Type | Default | Description                                                                                      |
|--------------|------|---------|--------------------------------------------------------------------------------------------------|
| `--bw`       | `float` | required | Channel bandwidth in MHz (e.g. `0.2`, `1.4`)                                                     |
| `--scs`      | `float` | required | Sub-carrier spacing in kHz (e.g. `15`, `3.75`)                                                   |
| `--num-rx`   | `1` \| `2` | optional | Number of RX antennas. Required when `require_num_rx=True` - not relevant for Chapter 7 Tests    |
| `--class`    | `leo` \| `geo` | optional | SAN orbit class. Included only when `include_class=True`                                         |
| `--freq`     | frequency | `1620000000` | PCFReq / RF center frequency in Hz or with suffix (e.g. `1.62G`)                                 |
| `--cell-id`  | `int` | `150` | NB_IoT cell ID for the wanted signal on Source1                                                  |
| `--tdd`      | flag | off | NB_IoT duplexing TDD mode for the wanted signal on Source1. Only UL/DL configuration 1 is supported. TDD Special subframe configuration defaults to 0; Chapter 8.5.1, 8.5.2, and 8.5.3 use 7 |
| `--ip`       | `str` | none | SMW IP address. When set, the script connects and configures the instrument                      |
| `--log-scpi` | flag | off | Write all SCPI commands to `scpi-list.iec` after the run                                         |

---

## Baseband Configuration

### `configure_triggers(smw, sources=1, *, ue=None)`

Configures armed-auto NB-IoT triggers using external gate input USER3.

- `sources=1` (default): only Source1 carries an NB-IoT signal.
- `sources=2`: Source2 also carries an NB-IoT signal and shares the USER3 trigger.
- `ue`: optional 0-based UE index for multi-UE setups (§8.2.3); prefixes all commands with
  `:ENTity{ue+1}`.

### `configure_node(smw, bw, scs, freq, *, cell_id=150, source=1, link="UP", ue=None)`

Configures NBIoT node parameters for the given source:

- Carrier deployment:
- channel bandwidth, SCS
- Cell ID (`cell_id`)

### `configure_frc(smw, ref_meas_channel, mode, repetition_num=None, source=1, frc_type_map=None, *, ue=None)`

Selects the Fixed Reference Channel (FRC) matching `ref_meas_channel`. Looks up the SCPI FRC type from `FRC_TYPE` (or a custom map if provided via `frc_type_map`) and activates it. Returns the `:SOURce{source}:BB:EUTR:` command prefix.

- `mode="LTE"`: enables the E-UTRA FRC on `UL:UE1:CELL0:FRC` (1.4 MHz in-band).
- Any other `mode` (NB-IoT, `"IOT"`): enables the NB-IoT FRC on `UL:UE1:NIOT:FRC`. When `repetition_num` is set and the channel is an A16 FRC, also sets `NNPRep`.
- `ue`: optional 0-based UE index; prefixes commands with `:ENTity{ue+1}`.

---

## Multi-RX / Dual-UE Configuration

### `configure_advance_mode(smw, num_rx, *, multi_ue=False)`

Configures the SMW advanced fading mode for multi-RX，not support multi_ue:

| `multi_ue` | `num_rx` | Mode |
|------------|---------|------|
| `False` | `1` | No-op (single-UE SISO — no advanced mode needed) |
| `False` | `2` | `MIMO1X2` |


### `configure_iqMapping(smw, num_rx, *, multi_ue=False)`

Configures the SMW IQ output mapping for dual-UE MIMO2X1X2 setups (§8.2.3). Routes streams 3 and 4
to IQ outputs 1 and 2, and streams 1 and 2 to BBMM outputs. No-op for non-MIMO2X1X2 configurations.



## Fading and Noise

### `configure_fading(smw, propagation, fsim_standard, sources=2, *, ue=None)`

Configures the fading simulator for Chapter 8 tests. Enables fading on Source1, and on Source2 when `sources=2`.

- `propagation`: 3GPP profile name, used only in the log (for example `NTN-TDLA100-5`). The SCPI standard is `fsim_standard`.
- `sources`: `1` or `2`. Chapter 8 scripts pass `num_rx`. When `sources=2`, the standard is `{fsim_standard}L` (2 RX profile) and both sources are configured. When `sources=1`, the standard is used unchanged and only Source1 is configured.
- `ue`: optional 0-based UE index; prefixes commands with `:ENTity{ue+1}`.

### `configure_awgn(smw, snr_db, awgn_bw, sources=2, *, awgn_power_dbm=None, noise_only_mode=False, ue=None)`

Configures AWGN interference. Source1 AWGN is routed to RFA; Source2 to RFB.

**Normal mode** (`noise_only_mode=False`): AWGN is added on top of the NB-IoT signal at a given C/N
ratio (`snr_db`). The NB-IoT output power reference is set to PSDC mode with the AWGN bandwidth.

**Noise-only mode** (`noise_only_mode=True`): AWGN only (no NB-IoT signal), at a fixed noise power
(`awgn_power_dbm`).

---

## HARQ and Repetitions

### `configure_harq(smw, *, timing_advance=False, ue=None)`

Configures HARQ feedback for NB-IoT uplink testing. Sets serial feedback mode at 115.2 kbit/s.
B10 instruments use USER input TM3; B9 instruments use USER input TM2.


## Output

### `configure_output(smw)`

Enables the required output states for Chapter 8 tests:

- Source2 fading simulator output
- Source1 and Source2 analog IQ outputs
- Source1 digital BBMM1 output

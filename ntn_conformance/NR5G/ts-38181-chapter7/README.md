# 3GPP TS 38.181 Chapter 7 — Conducted Receiver Characteristics

Python scripts for SAN type 1-H receiver tests defined in TS 38.181 Chapter 7. Each script
configures an SMW200A to produce the wanted signal (and interferer where applicable) for a
specific test case.

See the [NTN README](../../README.md) for environment setup and shared utilities.

Run all commands below from **`ntn_conformance/`** with the virtual environment activated.

---

## Scripts

| Script | Test |
|--------|------|
| `test_7_2.py` | §7.2 Reference sensitivity |
| `test_7_3.py` | §7.3 Dynamic range (AWGN) |
| `test_7_4_1.py` | §7.4.1 Adjacent channel selectivity (ACS) |
| `test_7_5.py` | §7.5 Out-of-band blocking |
| `test_7_8.py` | §7.8 In-channel selectivity (ICS) |
| `configs/` | Per-section INI folders for §7.2, §7.3, §7.4.1, §7.5, and §7.8 test cases |

---

## Config-files

Parameters can be stored in an INI file instead of passing them on the command line.
Pass the config file as the only argument:

```powershell
python NR5G/ts-38181-chapter7/test_7_2.py NR5G/ts-38181-chapter7/configs/7_2/10mhz_15khz_leo.ini
```

See [`configs/`](configs/) for per-section INI folders (`7_2/`, `7_3/`, `7_4_1/`, `7_5/`, `7_8/`). Each per-test file contains only a `[test]` section. Global settings are loaded automatically from:

| File | Section | Keys |
|------|---------|------|
| [`instrument.ini`](../../instrument.ini) (`ntn_conformance/`) | `[instrument]` | `ip`, `timeout` |
| [`NR5G/options.ini`](../options.ini) | `[options]` | `log_scpi` |

Per-test `[test]` keys:

| Key | Description |
|-----|-------------|
| `bw`, `scs`, `san_class`, `cell_id`, `ue_id`, `freq` | Common test and RF parameters |

| Script | Additional keys |
|--------|-----------------|
| `test_7_2.py` | `nb_iot_inband` |
| `test_7_4_1.py` | `edge`, `interferer_cell_id`, `interferer_ue_id`, `nb_iot_inband` |
| `test_7_5.py` | `band`, `interferer_freq`, `nb_iot_inband` (optional: `ful_low`, `ful_high`) |
| `test_7_8.py` | `interference_pos`, `interferer_cell_id`, `interferer_ue_id` |

CLI flags remain supported when used instead of a config file.


## Common Parameters

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--bw` | `int` | Yes | — | SAN channel bandwidth in MHz (e.g. `10`). Must match an entry in the lookup table for the chosen SCS. |
| `--scs` | `int` | Yes | — | Sub-carrier spacing in kHz (e.g. `15`, `30`, or `60`). Must match an entry in the lookup table for the chosen BW. |
| `--class` | `leo` \| `geo` | Conditional | — | SAN orbit class. Determines which power-level table is used. Required when `--ip` is set (except §7.3 which is LEO-only). |
| `--freq` | `int` | No | `1620000000` | PCFReq / RF center frequency in Hz. Applied to both the NR5G baseband node and the RF output. |
| `--cell-id` | `int` | No | `0` | NR5G cell ID for the wanted signal on Source1. |
| `--ue-id` | `int` | No | `0` | NR5G UE ID for the wanted signal on Source1 (`UBWP:USER0:UEID`). |
| `--interferer-cell-id` | `int` | No | same as `--cell-id` | NR5G cell ID for the interfering signal on Source2. Only used by §7.4.1 and §7.8. |
| `--interferer-ue-id` | `int` | No | `0` | NR5G UE ID for the interfering signal on Source2. Only used by §7.4.1 and §7.8. |
| `--ip` | `str` | No | — | SMW IP address. When omitted the script looks up and validates the test configuration without connecting to any instrument. When provided the script connects and applies the full SCPI configuration. |
| `--timeout` | `int` | No | `80` | SMW OPC/VISA timeout in seconds. Overrides `instrument.ini`. |
| `--log-scpi` | flag | No | off | Writes every SCPI write command sent during the run to `scpi-list.iec` in `ntn_conformance/` after all configuration steps complete. Useful for verification and debugging. |

Per TS 38.181, each test section defines which **RF channels to test** apply — typically **B**
(bottom), **M** (middle), and **T** (top) of the operating band. Set `--freq` (and
`--interferer-freq` where used) to match the channel(s) required for that section. The scripts do
not select B/M/T for you.

### How `--ip` changes behaviour

Without `--ip` the script is **lookup-only**: it resolves BW/SCS to the correct reference
measurement channel and power levels from the 3GPP table and exits. No instrument connection
is made. This is useful to verify a test configuration before lab work.

With `--ip` the script additionally:
1. Connects to the SMW over `TCPIP::<ip>::5025::SOCKET`
2. Configures trigger(s), NR5G node, FRC, and RF output
3. Applies any test-specific signal
4. Prints a confirmation for each configuration step
5. When `--log-scpi` is set, writes the full SCPI command list to `scpi-list.iec` in `ntn_conformance/`
6. Closes the connection (even on error)

---

## §7.2 — Reference Sensitivity (`test_7_2.py`)

### Background

> The reference sensitivity power level PREFSENS is the minimum mean power received at the TAB
> connector for SAN type 1-H at which a throughput requirement shall be met for a specified
> reference measurement channel. The throughput shall be ≥ 95% of the maximum throughput of the
> reference measurement channel as specified in annex A.1 with parameters from table 7.2.5-1
> and 7.2.5-2 for SAN type 1-H in all operating bands in FR1-NTN.

### Signal setup

Single source. **Source1** transmits the wanted uplink NR5G signal at PREFSENS power.

### Parameters

All common parameters apply, plus:

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--nb-iot-inband` | flag | No | off | When set, replaces the standard A1-1 / A1-4 reference channels with A1-10 / A1-11 where applicable (BW 5–20 MHz, SCS 15 kHz). Use when the SAN supports NB-IoT in-band operation. |

### Valid BW / SCS combinations

| BW (MHz) | SCS (kHz) | GEO FRC | GEO PREFSENS (dBm) | LEO FRC | LEO PREFSENS (dBm) |
|----------|-----------|---------|-------------------|---------|-------------------|
| 3 | 15 | G-FR1-NTN-A1-7 | −100.5 | G-FR1-NTN-A1-7 | −103.6 |
| 5 | 15 | G-FR1-NTN-A1-1 | −98.6 | G-FR1-NTN-A1-1 | −101.7 |
| 10 | 15 | G-FR1-NTN-A1-1 | −98.6 | G-FR1-NTN-A1-1 | −101.7 |
| 15 | 15 | G-FR1-NTN-A1-1 | −98.6 | G-FR1-NTN-A1-1 | −101.7 |
| 10 | 30 | G-FR1-NTN-A1-2 | −98.7 | G-FR1-NTN-A1-2 | −101.8 |
| 15 | 30 | G-FR1-NTN-A1-2 | −98.7 | G-FR1-NTN-A1-2 | −101.8 |
| 10 | 60 | G-FR1-NTN-A1-3 | −95.8 | G-FR1-NTN-A1-3 | −98.9 |
| 15 | 60 | G-FR1-NTN-A1-3 | −95.8 | G-FR1-NTN-A1-3 | −98.9 |
| 20 | 15 | G-FR1-NTN-A1-4 | −92.2 | G-FR1-NTN-A1-4 | −95.3 |
| 20 | 30 | G-FR1-NTN-A1-5 | −92.5 | G-FR1-NTN-A1-5 | −95.6 |
| 20 | 60 | G-FR1-NTN-A1-6 | −92.6 | G-FR1-NTN-A1-6 | −95.7 |

### NB-IoT in-band channel substitutions (when `--nb-iot-inband` is set)

| BW (MHz) | SCS (kHz) | Substituted FRC |
|----------|-----------|----------------|
| 5 | 15 | G-FR1-NTN-A1-10 |
| 10 | 15 | G-FR1-NTN-A1-10 |
| 15 | 15 | G-FR1-NTN-A1-10 |
| 20 | 15 | G-FR1-NTN-A1-11 |

Power level (PREFSENS) is unchanged; only the reference channel is substituted.

### Example commands

```powershell
# Lookup only — LEO, 10 MHz, 30 kHz SCS
python NR5G/ts-38181-chapter7/test_7_2.py --bw 10 --scs 30 --class leo

# Configure SMW — GEO, 10 MHz, 30 kHz SCS, default frequency
python NR5G/ts-38181-chapter7/test_7_2.py --bw 10 --scs 30 --class geo --ip <ip_address>

# Configure SMW — LEO, 10 MHz, 15 kHz SCS, NB-IoT in-band, custom frequency, with SCPI log
python NR5G/ts-38181-chapter7/test_7_2.py --bw 10 --scs 15 --class leo --nb-iot-inband --freq 1970000000 --ip <ip_address> --log-scpi

# Config file — GEO, 10 MHz, 15 kHz SCS
python NR5G/ts-38181-chapter7/test_7_2.py NR5G/ts-38181-chapter7/configs/7_2/10mhz_15khz_geo.ini
```

---

## §7.3 — Dynamic Range (`test_7_3.py`)

### Background

> The dynamic range is specified as a measure of the capability of the receiver to receive a
> wanted signal in the presence of an interfering signal at the TAB connector for SAN type 1-H
> inside the received SAN channel bandwidth. In this condition, a throughput requirement shall
> be met for a specified reference measurement channel. The interfering signal for the dynamic
> range requirement is an AWGN signal. The throughput shall be ≥ 95% of the maximum throughput
> of the reference measurement channel for SAN LEO class.

### Signal setup

Single source. **Source1** transmits the wanted NR5G uplink signal; the SMW's built-in AWGN
generator is added on the same output path. The AWGN bandwidth is set to the channel bandwidth
(queried from the instrument after FRC is applied) and the C/N ratio is derived from the
wanted and interfering power levels in the table. This test applies to **LEO class only**.

### Parameters

Common parameters apply, **except `--class`** (not accepted; LEO only).

### Valid BW / SCS combinations

| BW (MHz) | SCS (kHz) | FRC | Wanted power (dBm) | Interfering power (dBm) | C/N (dB) |
|----------|-----------|-----|--------------------|------------------------|----------|
| 3 | 15 | G-FR1-NTN-A2-7 | −79.0 | −90.4 | 11.4 |
| 5 | 15 | G-FR1-NTN-A2-1 | −76.1 | −88.2 | 12.1 |
| 5 | 30 | G-FR1-NTN-A2-2 | −76.8 | −88.2 | 11.4 |
| 10 | 15 | G-FR1-NTN-A2-1 | −76.1 | −85.0 | 8.9 |
| 10 | 30 | G-FR1-NTN-A2-2 | −76.8 | −85.0 | 8.2 |
| 10 | 60 | G-FR1-NTN-A2-3 | −73.8 | −85.0 | 11.2 |
| 15 | 15 | G-FR1-NTN-A2-1 | −76.1 | −83.2 | 7.1 |
| 15 | 30 | G-FR1-NTN-A2-2 | −76.8 | −83.2 | 6.4 |
| 15 | 60 | G-FR1-NTN-A2-3 | −73.8 | −83.2 | 9.4 |
| 20 | 15 | G-FR1-NTN-A2-4 | −69.9 | −81.9 | 12.0 |
| 20 | 30 | G-FR1-NTN-A2-5 | −69.9 | −81.9 | 12.0 |
| 20 | 60 | G-FR1-NTN-A2-6 | −70.2 | −81.9 | 11.7 |

### Example commands

```powershell
# Lookup only — 10 MHz, 30 kHz SCS
python NR5G/ts-38181-chapter7/test_7_3.py --bw 10 --scs 30

# Configure SMW — 10 MHz, 30 kHz SCS
python NR5G/ts-38181-chapter7/test_7_3.py --bw 10 --scs 30 --ip <ip_address>

# Configure SMW with SCPI log
python NR5G/ts-38181-chapter7/test_7_3.py --bw 10 --scs 30 --ip <ip_address> --log-scpi

# Config file — 10 MHz, 30 kHz SCS
python NR5G/ts-38181-chapter7/test_7_3.py NR5G/ts-38181-chapter7/configs/7_3/10mhz_30khz_leo.ini
```

---

## §7.4.1 — Adjacent Channel Selectivity (`test_7_4_1.py`)

### Background

> Adjacent channel selectivity (ACS) is a measure of the receiver's ability to receive a wanted
> signal at its assigned channel frequency at TAB connector for SAN type 1-H in the presence of
> an adjacent channel signal with a specified centre frequency offset of the interfering signal
> to the band edge of a victim system. The throughput shall be ≥ 95% of the maximum throughput
> of the reference measurement channel.

### Signal setup

Two sources are used simultaneously:

- **Source1** — wanted uplink NR5G signal (UL FRC, LINK UP), trigger on USER3
- **Source2** — adjacent channel interferer: **CP-OFDM QPSK PDSCH** downlink signal (LINK DOWN, no FRC), placed at the upper or lower band edge of the wanted signal

The interferer center frequency is computed automatically from the wanted frequency, channel
bandwidth, and the band-edge offset in `ACS_INTERFERER_OFFSET_MHZ` (table 7.4.1.5-2). Interferer
signal parameters come from `ACS_INTERFERER_PARAMS`:

| Wanted BW (MHz) | Edge offset from band edge (MHz) | Interferer BW (MHz) | Interferer SCS (kHz) | Interferer RBs |
|-----------------|----------------------------------|---------------------|----------------------|----------------|
| 3 | 1.5075 | 3 | 15 | 15 |
| 5 | 2.5025 | 5 | 15 | 25 |
| 10 | 2.5075 | 5 | 15 | 25 |
| 15 | 2.5125 | 5 | 15 | 25 |
| 20 | 2.5025 | 5 | 15 | 25 |

For `--edge upper`: interferer freq = wanted freq + BW/2 + offset  
For `--edge lower`: interferer freq = wanted freq − BW/2 − offset

### Parameters

All common parameters apply, plus:

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--edge` | `lower` \| `upper` | Yes (with `--ip`) | — | Specifies which SAN RF bandwidth edge the interferer is placed at. The script computes the exact interferer center frequency from the wanted frequency and this edge. |
| `--interferer-cell-id` | `int` | No | same as `--cell-id` | NR5G cell ID for the interfering signal on Source2. Use when the interferer should use a different cell ID than the wanted signal. |
| `--interferer-ue-id` | `int` | No | `0` | NR5G UE ID for the interfering signal on Source2 (`Source2:BB:NR5G:UBWP:USER0:UEID`). |
| `--nb-iot-inband` | flag | No | off | Same A1-10 / A1-11 wanted-signal FRC substitution as §7.2 (BW 5–20 MHz, SCS 15 kHz); wanted and interferer power unchanged. |

`--class` is also required when `--ip` is set.

> **Note:** The SCS for the lowest/highest carrier received is the lowest SCS supported by the
> SAN for that bandwidth. Testing the lowest SCS for the bandwidth is therefore sufficient.

### Valid BW / SCS combinations

| BW (MHz) | SCS (kHz) | GEO FRC | GEO wanted (dBm) | GEO interferer (dBm) | LEO FRC | LEO wanted (dBm) | LEO interferer (dBm) |
|----------|-----------|---------|------------------|----------------------|---------|------------------|----------------------|
| 3 | 15 | G-FR1-NTN-A1-7 | −93.2 | −57.0 | G-FR1-NTN-A1-7 | −96.3 | −60.0 |
| 5 | 15 | G-FR1-NTN-A1-1 | −93.3 | −57.0 | G-FR1-NTN-A1-1 | −96.4 | −60.0 |
| 10 | 15 | G-FR1-NTN-A1-1 | −93.3 | −57.0 | G-FR1-NTN-A1-1 | −96.4 | −60.0 |
| 15 | 15 | G-FR1-NTN-A1-1 | −93.3 | −57.0 | G-FR1-NTN-A1-1 | −96.4 | −60.0 |
| 10 | 30 | G-FR1-NTN-A1-2 | −93.4 | −57.0 | G-FR1-NTN-A1-2 | −96.5 | −60.0 |
| 15 | 30 | G-FR1-NTN-A1-2 | −93.4 | −57.0 | G-FR1-NTN-A1-2 | −96.5 | −60.0 |
| 10 | 60 | G-FR1-NTN-A1-3 | −90.5 | −57.0 | G-FR1-NTN-A1-3 | −93.6 | −60.0 |
| 15 | 60 | G-FR1-NTN-A1-3 | −90.5 | −57.0 | G-FR1-NTN-A1-3 | −93.6 | −60.0 |
| 20 | 15 | G-FR1-NTN-A1-4 | −86.9 | −57.0 | G-FR1-NTN-A1-4 | −90.0 | −60.0 |
| 20 | 30 | G-FR1-NTN-A1-5 | −87.2 | −57.0 | G-FR1-NTN-A1-5 | −90.3 | −60.0 |
| 20 | 60 | G-FR1-NTN-A1-6 | −87.3 | −57.0 | G-FR1-NTN-A1-6 | −90.4 | −60.0 |

### Example commands

```powershell
# Configure SMW — LEO, 10 MHz, 30 kHz SCS, upper band edge
python NR5G/ts-38181-chapter7/test_7_4_1.py --bw 10 --scs 30 --class leo --edge upper --ip <ip_address>

# Configure SMW — GEO, 10 MHz, 15 kHz SCS, lower band edge
python NR5G/ts-38181-chapter7/test_7_4_1.py --bw 10 --scs 15 --class geo --edge lower --ip <ip_address>

# Wanted and interferer cell/UE IDs (defaults 0)
python NR5G/ts-38181-chapter7/test_7_4_1.py --bw 10 --scs 30 --class leo --edge upper --cell-id 0 --ue-id 0 --interferer-cell-id 0 --interferer-ue-id 0 --ip <ip_address>

# Config file — LEO, 10 MHz, 15 kHz SCS, lower band edge
python NR5G/ts-38181-chapter7/test_7_4_1.py NR5G/ts-38181-chapter7/configs/7_4_1/10mhz_15khz_leo_lower.ini
```

---

## §7.5 — Out-of-Band Blocking (`test_7_5.py`)

### Background

> The out-of-band blocking characteristics is a measure of the receiver ability to receive a
> wanted signal at its assigned channel at the TAB connector for SAN type 1-H in the presence
> of an unwanted interferer out of the operating band, which is a CW signal for out-of-band
> blocking. The throughput shall be ≥ 95% of the maximum throughput of the reference
> measurement channel, with a wanted and an interfering signal coupled to SAN type 1-H TAB
> connector.

### Signal setup

Two sources are used:

- **Source1** — wanted uplink NR5G signal (UL FRC), power = PREFSENS + 6 dB
- **Source2** — CW (unmodulated) interfering signal at a fixed power of **−44 dBm**

The CW interferer frequency is provided by the user via `--interferer-freq`. OOB range
boundaries are derived from `OPERATING_BANDS` (or `--ful-low` / `--ful-high` overrides) before
connecting to the SMW.

### OOB frequency ranges and the sweep requirement

Per 3GPP TS 38.181 table 7.5.5-1, the CW interfering signal shall be swept with a **1 MHz
step size** across two ranges:

- **Range 1:** 1 MHz to (F_UL,low − Δf_OOB) where Δf_OOB = 20 MHz
- **Range 2:** (F_UL,high + Δf_OOB) to 12750 MHz

The script configures the SMW at **one interferer frequency per invocation**. To perform the
full sweep, call the script repeatedly with each frequency step. The script always prints which
OOB range the provided frequency falls in (or a warning if it is outside both ranges) before
any SMW connection.

Example sweep loop (PowerShell):

```powershell
# Sweep range 1 for band n254 (F_UL,low=1610 MHz → range1_max=1590 MHz), 1 MHz steps
for ($f = 1000000; $f -le 1590000000; $f += 1000000) {
    python NR5G/ts-38181-chapter7/test_7_5.py --bw 10 --scs 15 --class leo --interferer-freq $f --ip <ip_address>
}

# Sweep range 2 for band n254 (F_UL,high=1626.5 MHz → range2_min=1646.5 MHz), 1 MHz steps
for ($f = 1646500000; $f -le 12750000000; $f += 1000000) {
    python NR5G/ts-38181-chapter7/test_7_5.py --bw 10 --scs 15 --class leo --interferer-freq $f --ip <ip_address>
}
```

### NR operating band presets

| Band | F_UL,low (Hz) | F_UL,high (Hz) | Range 1 max (Hz) | Range 2 min (Hz) |
|------|--------------|----------------|------------------|------------------|
| n253 | 1,668,000,000 | 1,675,000,000 | 1,648,000,000 | 1,695,000,000 |
| n254 | 1,610,000,000 | 1,626,500,000 | 1,590,000,000 | 1,646,500,000 |
| n255 | 1,626,500,000 | 1,660,500,000 | 1,606,500,000 | 1,680,500,000 |
| n256 | 1,980,000,000 | 2,010,000,000 | 1,960,000,000 | 2,030,000,000 |

The default band is **n254**. Use `--ful-low` and/or `--ful-high` to override the band edge
frequencies manually (e.g. for non-standard configurations). When bulk-updating RF frequency with
`python scripts/set_rf_frequency.py --section 7_5 --freq …`, `band` in §7.5 INIs is set
automatically from the FR1 NTN table when the new frequency is in-band. Use
`--interferer-freq` with `--section 7_5` to bulk-update the interferer frequency as well.

### Parameters

All common parameters apply, plus:

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--interferer-freq` | `int` | Yes (always) | — | CW interferer frequency in Hz. Validated against OOB ranges even without `--ip`. |
| `--band` | `n253`\|`n254`\|`n255`\|`n256` | No | `n254` | NR operating band preset from `OPERATING_BANDS`. Determines OOB range boundaries. |
| `--ful-low` | `int` | No | band preset | Override F_UL,low in Hz. |
| `--ful-high` | `int` | No | band preset | Override F_UL,high in Hz. |
| `--nb-iot-inband` | flag | No | off | Same A1-10 / A1-11 wanted-signal FRC substitution as §7.2 (BW 5–20 MHz, SCS 15 kHz); wanted power unchanged. |

`--class` is required when `--ip` is set.

### Valid BW / SCS combinations

| BW (MHz) | SCS (kHz) | GEO FRC | GEO wanted (dBm) | LEO FRC | LEO wanted (dBm) |
|----------|-----------|---------|------------------|---------|------------------|
| 3 | 15 | G-FR1-NTN-A1-7 | −95.2 | G-FR1-NTN-A1-7 | −98.3 |
| 5 | 15 | G-FR1-NTN-A1-1 | −93.3 | G-FR1-NTN-A1-1 | −96.4 |
| 10 | 15 | G-FR1-NTN-A1-1 | −93.3 | G-FR1-NTN-A1-1 | −96.4 |
| 15 | 15 | G-FR1-NTN-A1-1 | −93.3 | G-FR1-NTN-A1-1 | −96.4 |
| 10 | 30 | G-FR1-NTN-A1-2 | −93.4 | G-FR1-NTN-A1-2 | −96.5 |
| 15 | 30 | G-FR1-NTN-A1-2 | −93.4 | G-FR1-NTN-A1-2 | −96.5 |
| 10 | 60 | G-FR1-NTN-A1-3 | −90.5 | G-FR1-NTN-A1-3 | −93.6 |
| 15 | 60 | G-FR1-NTN-A1-3 | −90.5 | G-FR1-NTN-A1-3 | −93.6 |
| 20 | 15 | G-FR1-NTN-A1-4 | −86.9 | G-FR1-NTN-A1-4 | −90.0 |
| 20 | 30 | G-FR1-NTN-A1-5 | −87.2 | G-FR1-NTN-A1-5 | −90.3 |
| 20 | 60 | G-FR1-NTN-A1-6 | −87.3 | G-FR1-NTN-A1-6 | −90.4 |

Wanted power = PREFSENS + 6 dB. Interferer power is fixed at −44 dBm regardless of BW/SCS/class.

### Example commands

```powershell
# Validate interferer frequency only (no SMW) — checks OOB range membership
python NR5G/ts-38181-chapter7/test_7_5.py --bw 10 --scs 15 --class leo --interferer-freq 1500000000

# Configure SMW at a specific OOB frequency — LEO, n254 band
python NR5G/ts-38181-chapter7/test_7_5.py --bw 10 --scs 15 --class leo --interferer-freq 1500000000 --ip <ip_address>

# Configure SMW with manual band-edge override
python NR5G/ts-38181-chapter7/test_7_5.py --bw 10 --scs 15 --class leo --interferer-freq 1500000000 --ful-low 1605000000 --ful-high 1630000000 --ip <ip_address>

# Config file — LEO, 10 MHz, 15 kHz SCS (edit band, freq, interferer_freq in the INI as needed)
python NR5G/ts-38181-chapter7/test_7_5.py NR5G/ts-38181-chapter7/configs/7_5/10mhz_15khz_leo.ini
```

---

## §7.8 — In-Channel Selectivity (`test_7_8.py`)

### Background

> In-channel selectivity (ICS) is a measure of the receiver ability to receive a wanted signal
> at its assigned resource block locations at the TAB connector for SAN type 1-H in the presence
> of an interfering signal received at a larger power spectral density. In this condition a
> throughput requirement shall be met for a specified reference measurement channel. The
> interfering signal shall be an NR signal which is time aligned with the wanted signal. For
> SAN type 1-H, the throughput shall be ≥ 95% of the maximum throughput of the reference
> measurement channel.

### Signal setup

Two sources are used simultaneously at the **same center frequency** (co-channel):

- **Source1** — wanted uplink NR5G signal (UL FRC, LINK UP), with RB offset from the selected LUT
- **Source2** — co-channel NR5G interferer: **16 QAM DFT-s-OFDM PUSCH** (LINK UP, no FRC), with
  RB count from `ICS_INTERFERER_RBS` and RB offset from the selected LUT (see tables below)

Both signals use the same frequency (`--freq`) and SCS. RB offsets for wanted and interfering
signals depend on `--interference-pos`. Source2 is time-aligned with Source1 via the shared
trigger on USER3.

### Parameters

All common parameters apply. `--class` is required when `--ip` is set.

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--interference-pos` | `lower` \| `higher` | Yes | — | Whether the interfering signal is placed at lower or higher resource blocks. Selects the RB offset LUT (`ICS_RB_OFFSETS_IS_LOW` or `ICS_RB_OFFSETS_IS_HIGH`). |
| `--interferer-cell-id` | `int` | No | same as `--cell-id` | NR5G cell ID for the interfering signal on Source2. Use when the interferer should use a different cell ID than the wanted signal. |
| `--interferer-ue-id` | `int` | No | `0` | NR5G UE ID for the interfering signal on Source2 (`Source2:BB:NR5G:UBWP:USER0:UEID`). |

### Valid BW / SCS combinations

| BW (MHz) | SCS (kHz) | GEO FRC | GEO wanted (dBm) | GEO interferer (dBm) | LEO FRC | LEO wanted (dBm) | LEO interferer (dBm) | Interferer RBs |
|----------|-----------|---------|------------------|----------------------|---------|------------------|----------------------|----------------|
| 3 | 15 | G-FR1-NTN-A1-12 | −99.0 | −94.2 | G-FR1-NTN-A1-12 | −102.1 | −85.3 | 6 |
| 5 | 15 | G-FR1-NTN-A1-7 | −96.8 | −92.0 | G-FR1-NTN-A1-7 | −99.9 | −83.1 | 10 |
| 5 | 30 | G-FR1-NTN-A1-8 | −97.5 | −92.0 | G-FR1-NTN-A1-8 | −100.6 | −83.1 | 5 |
| 10 | 15 | G-FR1-NTN-A1-1 | −94.9 | −88.1 | G-FR1-NTN-A1-1 | −98.0 | −79.2 | 25 |
| 10 | 30 | G-FR1-NTN-A1-2 | −95.0 | −89.0 | G-FR1-NTN-A1-2 | −98.1 | −80.1 | 10 |
| 10 | 60 | G-FR1-NTN-A1-9 | −94.4 | −89.0 | G-FR1-NTN-A1-9 | −97.5 | −80.1 | 5 |
| 15 | 15 | G-FR1-NTN-A1-1 | −94.9 | −88.1 | G-FR1-NTN-A1-1 | −98.0 | −79.2 | 25 |
| 15 | 30 | G-FR1-NTN-A1-2 | −95.0 | −89.0 | G-FR1-NTN-A1-2 | −98.1 | −80.1 | 10 |
| 15 | 60 | G-FR1-NTN-A1-9 | −94.4 | −89.0 | G-FR1-NTN-A1-9 | −97.5 | −80.1 | 5 |
| 20 | 15 | G-FR1-NTN-A1-1 | −94.9 | −88.1 | G-FR1-NTN-A1-1 | −98.0 | −79.2 | 25 |
| 20 | 30 | G-FR1-NTN-A1-2 | −95.0 | −89.0 | G-FR1-NTN-A1-2 | −98.1 | −80.1 | 10 |
| 20 | 60 | G-FR1-NTN-A1-9 | −94.4 | −89.0 | G-FR1-NTN-A1-9 | −97.5 | −80.1 | 5 |

### RB offsets (`--interference-pos`)

RB offsets are looked up per BW/SCS from one of two tables. Both tables use the tuple
`(ws_rb_offset, is_rb_offset)`.

**`--interference-pos higher`** — wanted signal at lower RBs, interferer at higher RBs
(`ICS_RB_OFFSETS_IS_HIGH`):

| BW (MHz) | SCS (kHz) | WS RB offset | IS RB offset |
|----------|-----------|--------------|--------------|
| 3 | 15 | 0 | 9 |
| 5 | 15 | 0 | 15 |
| 10 | 15 | 1 | 26 |
| 15 | 15 | 14 | 40 |
| 20 | 15 | 28 | 53 |
| 5 | 30 | 0 | 6 |
| 10 | 30 | 1 | 13 |
| 15 | 30 | 8 | 20 |
| 20 | 30 | 15 | 26 |
| 10 | 60 | 0 | 6 |
| 15 | 60 | 3 | 10 |
| 20 | 60 | 6 | 13 |

**`--interference-pos lower`** — interferer at lower RBs, wanted signal at higher RBs
(`ICS_RB_OFFSETS_IS_LOW`):

| BW (MHz) | SCS (kHz) | WS RB offset | IS RB offset |
|----------|-----------|--------------|--------------|
| 3 | 15 | 6 | 0 |
| 5 | 15 | 10 | 0 |
| 10 | 15 | 26 | 1 |
| 15 | 15 | 40 | 14 |
| 20 | 15 | 53 | 28 |
| 5 | 30 | 5 | 0 |
| 10 | 30 | 12 | 1 |
| 15 | 30 | 19 | 8 |
| 20 | 30 | 25 | 15 |
| 10 | 60 | 5 | 0 |
| 15 | 60 | 9 | 3 |
| 20 | 60 | 12 | 6 |

### Example commands

```powershell
# Configure SMW — LEO, 10 MHz, 30 kHz SCS, interferer at higher RBs
python NR5G/ts-38181-chapter7/test_7_8.py --bw 10 --scs 30 --class leo --interference-pos higher --ip <ip_address>

# Configure SMW — GEO, 10 MHz, 60 kHz SCS, interferer at lower RBs, with SCPI log
python NR5G/ts-38181-chapter7/test_7_8.py --bw 10 --scs 60 --class geo --interference-pos lower --ip <ip_address> --log-scpi

# Wanted and interferer cell/UE IDs (defaults 0), interferer at higher RBs
python NR5G/ts-38181-chapter7/test_7_8.py --bw 10 --scs 30 --class leo --interference-pos higher --cell-id 0 --ue-id 0 --interferer-cell-id 0 --interferer-ue-id 0 --ip <ip_address>

# Config file — LEO, 10 MHz, 30 kHz SCS, interferer at lower RBs
python NR5G/ts-38181-chapter7/test_7_8.py NR5G/ts-38181-chapter7/configs/7_8/10mhz_30khz_leo_lower.ini
```

---

## Shared Lookup Tables

All power levels, reference channels, operating-band presets, and interferer parameters are
defined in [`tables_3gpp.py`](tables_3gpp.py). Each script imports only the
tables it needs.

| Constant | Section | Used by |
|----------|---------|---------|
| `SAN_GEO_REF_SENS_LEVELS`, `SAN_LEO_REF_SENS_LEVELS`, `NB_IOT_INBAND_REF_MEAS_CHANNELS`, `apply_nb_iot_inband_channel` | §7.2 (FRC swap also §7.4.1, §7.5) | `test_7_2.py`, `test_7_4_1.py`, `test_7_5.py` |
| `SAN_LEO_DYNAMIC_RANGE` | §7.3 | `test_7_3.py` |
| `ACS_INTERFERER_OFFSET_MHZ`, `ACS_INTERFERER_PARAMS`, `SAT_GEO_ACS`, `SAT_LEO_ACS` | §7.4.1 | `test_7_4_1.py` |
| `OPERATING_BANDS`, `SAT_GEO_OOB`, `SAT_LEO_OOB` | §7.5 | `test_7_5.py` |
| `SAT_GEO_ICS`, `SAT_LEO_ICS`, `ICS_INTERFERER_RBS`, `ICS_RB_OFFSETS_IS_HIGH`, `ICS_RB_OFFSETS_IS_LOW` | §7.8 | `test_7_8.py` |

`TestConfig` is also defined in `tables_3gpp.py` and imported by scripts that need it
for type annotations or to construct updated configurations (e.g. NB-IoT in-band channel
substitution in §7.2, §7.4.1, and §7.5 via `apply_nb_iot_inband_channel`).

`get_power_levels(table, bw, scs)` looks up a `TestConfig` from a chapter table for
the given bandwidth and SCS (LEO or GEO table is selected by the caller before calling).

---


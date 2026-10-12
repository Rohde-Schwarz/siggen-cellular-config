# 3GPP TS 36.181 Chapter 7 — Conducted Receiver Characteristics

Python scripts for SAN type 1-H receiver tests defined in TS 36.181 Chapter 7. Each script
configures an SMW200A to produce the wanted signal (and interferer where applicable) for a
specific test case.

See the [repository README](../../README.md) for environment setup and shared utilities.

Run all commands below from the **repository root** with the virtual environment activated.

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

```bash
python NB_IoT/ts-36181-chapter7/test_7_2.py NB_IoT/ts-36181-chapter7/configs/7_2/1_4_mhz_15khz_geo.ini
```

See [`configs/`](configs/) for per-section INI folders (`7_2/`, `7_3/`, `7_4_1/`, `7_5/`, `7_8/`). Each per-test file contains only a `[test]` section. Global settings are loaded automatically from:

| File | Section | Keys |
|------|---------|------|
| [`instrument.ini`](../../instrument.ini) (repo root) | `[instrument]` | `ip` |
| [`NB_IoT/options.ini`](../options.ini) | `[options]` | `log_scpi` |

Per-test `[test]` keys:

| Key | Description |
|-----|-------------|
| `bw`, `scs`, `san_class`, `cell_id`, `ue_id`, `freq` | Common test and RF parameters |

| Script | Additional keys |
|--------|-----------------|
| `test_7_2.py` | `tdd` |
| `test_7_3.py` | `tdd` |
| `test_7_4_1.py` | `tdd`, `edge`, `interferer_cell_id`, `interferer_ue_id` |
| `test_7_5.py` | `tdd`, `band`, `interferer_freq` (optional: `ful_low`, `ful_high`, `spurious_response_exception`) |
| `test_7_8.py` | `interference_pos`, `interferer_cell_id`, `interferer_ue_id` |

CLI flags remain supported when used instead of a config file.

To run every INI in a section folder (PowerShell). Install the package first (`pip install -e .`; verify with `pip show ntn-testing`):

```powershell
foreach ($ini in Get-ChildItem NB_IoT/ts-36181-chapter7/configs/7_2/*.ini) {
    Write-Host "=== $($ini.Name) ==="
    python NB_IoT/ts-36181-chapter7/test_7_2.py "$($ini.FullName)"
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed: $($ini.Name)"; break }
}
```

---

## Common Parameters

All five scripts share a base set of CLI parameters. Scripts that use two signal sources
(§7.4.1, §7.5, §7.8) require `--class` when `--ip` is set. `--class` selects the GEO or LEO
FDD table. Use `--tdd` with `--class leo` on §7.2, §7.3, §7.4.1, and §7.5 to select the
LEO TDD table.

Trigger configuration is handled by `configure_triggers(smw, sources)` from `NB_IoT.utils`:

| Scripts | `sources` | Reason |
|---------|-----------|--------|
| §7.2, §7.3, §7.5 | `1` (default) | Only Source1 carries an NB-IoT signal (§7.3 adds AWGN on Source1; §7.5 uses CW on Source2) |
| §7.4.1, §7.8 | `2` | Source2 also carries an NB-IoT interferer that must share the USER3 trigger |

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--bw` | `float` | Yes | — | SAN channel bandwidth in MHz (e.g. `1.4`, `0.2`). Must match an entry in the lookup table for the chosen SCS. |
| `--scs` | `float` | Yes | — | Sub-carrier spacing in kHz (e.g. `15`, `3.75`). Must match an entry in the lookup table for the chosen BW. |
| `--class` | `leo` \| `geo` | Conditional | — | SAN orbit class. Determines which power-level table is used. Required when `--ip` is set. |
| `--freq` | `int` | No | `1620000000` | PCFReq / RF center frequency in Hz. Applied to both the NB-IoT baseband node and the RF output. |
| `--cell-id` | `int` | No | `150` | NB-IoT cell ID for the wanted signal on Source1. |
| `--ue-id` | `int` | No | `1` | NB-IoT UE ID for the wanted signal on Source1. |
| `--interferer-cell-id` | `int` | No | `1` | NB-IoT cell ID for the interfering signal on Source2. Only used by §7.4.1 and §7.8. |
| `--ip` | `str` | No | — | SMW IP address. When omitted the script looks up and validates the test configuration without connecting to any instrument. When provided the script connects and applies the full SCPI configuration. |
| `--log-scpi` | flag | No | off | Writes every SCPI write command sent during the run to `scpi-list.iec` in the repository root after all configuration steps complete. Useful for verification and debugging. |

### How `--ip` changes behaviour

Without `--ip` the script is **lookup-only**: it resolves BW/SCS to the correct reference
measurement channel and power levels from the 3GPP table and exits. No instrument connection
is made. This is useful to verify a test configuration before lab work.

With `--ip` the script additionally:
1. Connects to the SMW over `TCPIP::<ip>::5025::SOCKET`
2. Configures trigger(s), NB-IoT node, FRC, and RF output
3. Applies any test-specific signal (AWGN, ACS PUSCH interferer, CW interferer, ICS PUSCH interferer)
4. Prints a confirmation for each configuration step
5. When `--log-scpi` is set, writes the full SCPI command list to `scpi-list.iec` in the repository root
6. Closes the connection (even on error)

---

## §7.2 — Reference Sensitivity (`test_7_2.py`)

### Background

> The reference sensitivity power level PREFSENS is the minimum mean power received at the TAB
> connector for SAN type 1-H at which a throughput requirement shall be met for a specified
> reference measurement channel. The throughput shall be ≥ 95% of the maximum throughput of the
> reference measurement channel as specified in annex A.1 with parameters from table 7.2.5-1
> and 7.2.5-2 for SAN type 1-H in all operating bands in NB-IoT NTN.

### Signal setup

Single source. **Source1** transmits the wanted uplink NB-IoT signal at PREFSENS power.

### Parameters

All common parameters apply, plus:

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--tdd` | flag | No | off | Use Table 7.2.5-5 / FRC-A14-3 (BW 200 kHz, SCS 15 kHz only). Applies with `--class leo`. |

### Valid BW / SCS combinations

GEO PREFSENS from TS 36.181 Table 7.2.5-1 (in-band / 1.4 MHz) and Table 7.2.5-3 (standalone 200 kHz). LEO FDD PREFSENS from Table 7.2.5-2 and Table 7.2.5-4. Values match `SAN_GEO_REF_SENS_LEVELS` and `SAN_LEO_REF_SENS_LEVELS` in `tables_3gpp.py`.

| BW (MHz) | SCS (kHz) | FRC | GEO PREFSENS (dBm) | LEO FDD PREFSENS (dBm) |
|----------|-----------|-----|-------------------|------------------------|
| 1.4 | 15 | FRC-A1-1 | −103.7 | −106.8 |
| 0.2 | 15 | FRC-A14-1 | −123.9 | −127.0 |
| 0.2 | 3.75 | FRC-A14-2 | −129.9 | −133.0 |

### LEO TDD (when `--tdd` is set)

TS 36.181 Table 7.2.5-5 / `SAN_LEO_TDD_REF_SENS_LEVELS`. Applies to `--class leo` with `--tdd`. Both FRC and PREFSENS differ from the LEO FDD 200 kHz / 15 kHz row above.

| BW (MHz) | SCS (kHz) | FRC | LEO TDD PREFSENS (dBm) |
|----------|-----------|-----|------------------------|
| 0.2 | 15 | FRC-A14-3 | −126.1 |

### Example commands

```bash
# Lookup only — LEO, 1.4 MHz, 15 kHz SCS
python NB_IoT/ts-36181-chapter7/test_7_2.py --bw 1.4 --scs 15 --class leo

# Configure SMW — GEO, 1.4 MHz, 15 kHz SCS, default frequency
python NB_IoT/ts-36181-chapter7/test_7_2.py --bw 1.4 --scs 15 --class geo --ip <ip_address>

# Configure SMW — LEO TDD, 0.2 MHz, 15 kHz SCS, custom frequency, with SCPI log
python NB_IoT/ts-36181-chapter7/test_7_2.py --bw 0.2 --scs 15 --class leo --tdd --freq 1620000000 --ip <ip_address> --log-scpi

# Config file — GEO, 0.2 MHz, 15 kHz SCS
python NB_IoT/ts-36181-chapter7/test_7_2.py NB_IoT/ts-36181-chapter7/configs/7_2/0_2_mhz_15khz_geo.ini
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

Single source. **Source1** transmits the wanted NB-IoT uplink signal; the SMW's built-in AWGN
generator is added on the same output path. The AWGN bandwidth is taken from `AWGN_BANDWIDTH`
(1.08 MHz for 1.4 MHz, 180 kHz for 200 kHz) and the C/N ratio is derived from the wanted and
interfering power levels in the table.

### Parameters

All common parameters apply, plus:

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--tdd` | flag | No | off | Use Table 7.3.5-4 LEO TDD dynamic range (BW 200 kHz, SCS 15 kHz only). Applies with `--class leo`. |

`--class` selects the GEO or LEO FDD table.

### Valid BW / SCS combinations

GEO FDD from TS 36.181 Table 7.3.5-2 (`SAN_GEO_DYNAMIC_RANGE`). Standalone NB-IoT, 200 kHz only.

| BW (MHz) | SCS (kHz) | FRC | Wanted power (dBm) | Interfering power (dBm) | C/N (dB) |
|----------|-----------|-----|--------------------|------------------------|----------|
| 0.2 | 15 | FRC-A15-1 | −97.0 | −93.6 | −3.4 |
| 0.2 | 3.75 | FRC-A15-2 | −102.9 | −93.6 | −9.3 |

LEO FDD from Table 7.3.5-1 (E-UTRA 1.4 MHz) and Table 7.3.5-3 (standalone 200 kHz) / `SAN_LEO_DYNAMIC_RANGE`.

| BW (MHz) | SCS (kHz) | FRC | Wanted power (dBm) | Interfering power (dBm) | C/N (dB) |
|----------|-----------|-----|--------------------|------------------------|----------|
| 1.4 | 15 | FRC-A2-1 | −81.7 | −94.4 | 12.7 |
| 0.2 | 15 | FRC-A15-1 | −89.1 | −85.7 | −3.4 |
| 0.2 | 3.75 | FRC-A15-2 | −95.0 | −85.7 | −9.3 |

### LEO TDD (when `--tdd` is set)

TS 36.181 Table 7.3.5-4 / `SAN_LEO_TDD_DYNAMIC_RANGE`. Applies to `--class leo` with `--tdd`. A15-2 (3.75 kHz)
is FDD-only per annex A.15.

| BW (MHz) | SCS (kHz) | FRC | Wanted power (dBm) | Interfering power (dBm) | C/N (dB) |
|----------|-----------|-----|--------------------|------------------------|----------|
| 0.2 | 15 | FRC-A15-1 | −105.1 | −101.7 | −3.4 |

### Example commands

```bash
# Lookup only — LEO, 1.4 MHz, 15 kHz SCS
python NB_IoT/ts-36181-chapter7/test_7_3.py --bw 1.4 --scs 15 --class leo

# Configure SMW — GEO, 0.2 MHz, 15 kHz SCS
python NB_IoT/ts-36181-chapter7/test_7_3.py --bw 0.2 --scs 15 --class geo --ip <ip_address>

# Configure SMW — LEO TDD, 0.2 MHz, 15 kHz SCS, with SCPI log
python NB_IoT/ts-36181-chapter7/test_7_3.py --bw 0.2 --scs 15 --class leo --tdd --ip <ip_address> --log-scpi

# Config file — LEO, 1.4 MHz, 15 kHz SCS
python NB_IoT/ts-36181-chapter7/test_7_3.py NB_IoT/ts-36181-chapter7/configs/7_3/1_4_mhz_15khz_leo.ini
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

- **Source1** — wanted uplink NB-IoT signal (UL FRC, LINK UP), trigger on USER3
- **Source2** — adjacent channel interferer: E-UTRA or NB-IoT uplink PUSCH (LINK UP, no FRC), placed at the upper or lower band edge of the wanted signal

The interferer center frequency is computed automatically from the wanted frequency, channel
bandwidth, and the band-edge offset in `ACS_INTERFERER_OFFSET_MHZ` (TS 36.181 Table 7.4.1.5-1
for 1.4 MHz E-UTRA, Table 7.4.1.5-2/7.4.1.5-3 for standalone NB-IoT):

| Wanted BW (MHz) | Edge offset from band edge (MHz) | Interferer BW (MHz) | Interferer SCS (kHz) | Interferer type |
|-----------------|----------------------------------|---------------------|----------------------|-----------------|
| 1.4 | 0.7025 | 1.4 | 15 | 1.4 MHz E-UTRA |
| 0.2 | 0.1 | 0.18 | 15 | 180 kHz NB-IoT |

- `--edge upper`: interferer freq = wanted freq + BW/2 + offset
- `--edge lower`: interferer freq = wanted freq − BW/2 − offset

### Parameters

All common parameters apply, plus:

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--tdd` | flag | No | off | Use Table 7.4.1.5-3 LEO TDD ACS (BW 200 kHz, SCS 15 kHz only). Applies with `--class leo`. |
| `--edge` | `lower` \| `upper` | Yes (with `--ip`) | — | SAN RF bandwidth edge for the interferer. The script computes the interferer center frequency from the wanted frequency and this edge. |
| `--interferer-ue-id` | `int` | No | `1` | NB-IoT UE ID for the interfering signal on Source2. |

`--class` is also required when `--ip` is set.

### Valid BW / SCS combinations

Wanted power is TS 36.181 Table 7.2.5 PREFSENS plus the offset in Table 7.4.1.5
(E-UTRA: Table 7.2.5-1/7.2.5-2 + 11 dB; standalone NB-IoT FDD: Table 7.2.5-3/7.2.5-4 + 19.5 dB).
Interferer power is taken from Table 7.4.1.5-1 (E-UTRA) and Table 7.4.1.5-2 (standalone NB-IoT FDD).
Values match `SAT_GEO_ACS` and `SAT_LEO_ACS` in `tables_3gpp.py`.

| BW (MHz) | SCS (kHz) | GEO FRC | GEO wanted (dBm) | GEO interferer (dBm) | LEO FRC | LEO wanted (dBm) | LEO interferer (dBm) |
|----------|-----------|---------|------------------|----------------------|---------|------------------|----------------------|
| 1.4 | 15 | FRC-A1-1 | −92.7 | −57.6 | FRC-A1-1 | −95.8 | −60.7 |
| 0.2 | 15 | FRC-A14-1 | −104.4 | −56.6 | FRC-A14-1 | −107.5 | −59.7 |
| 0.2 | 3.75 | FRC-A14-2 | −110.4 | −56.6 | FRC-A14-2 | −113.5 | −59.7 |

### LEO TDD (when `--tdd` is set)

TS 36.181 Table 7.2.5-5 (PREFSENS + 19.5 dB) × Table 7.4.1.5-3 / `SAT_LEO_TDD_ACS`. Applies to
`--class leo` with `--tdd`. Interferer power is −85.5 dBm.

| BW (MHz) | SCS (kHz) | FRC | LEO TDD wanted (dBm) | LEO TDD interferer (dBm) |
|----------|-----------|-----|----------------------|--------------------------|
| 0.2 | 15 | FRC-A14-3 | −106.6 | −85.5 |

### Example commands

```bash
# Lookup only — LEO, 0.2 MHz, 15 kHz SCS, upper band edge
python NB_IoT/ts-36181-chapter7/test_7_4_1.py --bw 0.2 --scs 15 --class leo --edge upper

# Configure SMW — LEO FDD, 0.2 MHz, 15 kHz SCS, upper band edge
python NB_IoT/ts-36181-chapter7/test_7_4_1.py --bw 0.2 --scs 15 --class leo --edge upper --ip <ip_address>

# Configure SMW — GEO E-UTRA, 1.4 MHz, 15 kHz SCS, lower band edge
python NB_IoT/ts-36181-chapter7/test_7_4_1.py --bw 1.4 --scs 15 --class geo --edge lower --ip <ip_address>

# Wanted cell ID 150, interferer cell ID 1
python NB_IoT/ts-36181-chapter7/test_7_4_1.py --bw 0.2 --scs 15 --class leo --edge upper --cell-id 150 --interferer-cell-id 1 --ip <ip_address>

# Config file — GEO, 1.4 MHz, 15 kHz SCS, lower band edge
python NB_IoT/ts-36181-chapter7/test_7_4_1.py NB_IoT/ts-36181-chapter7/configs/7_4_1/1_4_mhz_15khz_geo_lower.ini

python NB_IoT/ts-36181-chapter7/test_7_4_1.py NB_IoT/ts-36181-chapter7/configs/7_4_1/0_2_mhz_15khz_geo_upper.ini
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

- **Source1** — wanted uplink NB-IoT signal (UL FRC), power = PREFSENS + 6 dB
- **Source2** — CW (unmodulated) interfering signal at **−44 dBm**, or **−46 dBm** with
  `--spurious-response-exception` (3.75 kHz SCS only)

The CW interferer frequency is provided by the user via `--interferer-freq`. OOB range
boundaries are derived from `OPERATING_BANDS` (or `--ful-low` / `--ful-high` overrides) before
connecting to the SMW.

### OOB frequency ranges and the sweep requirement

Per 3GPP TS 36.181 table 7.5.5-1, the CW interfering signal shall be swept with a **1 MHz
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
    python NB_IoT/ts-36181-chapter7/test_7_5.py --bw 1.4 --scs 15 --class leo --interferer-freq $f --ip <ip_address>
}

# Sweep range 2 for band n254 (F_UL,high=1626.5 MHz → range2_min=1646.5 MHz), 1 MHz steps
for ($f = 1646500000; $f -le 12750000000; $f += 1000000) {
    python NB_IoT/ts-36181-chapter7/test_7_5.py --bw 1.4 --scs 15 --class leo --interferer-freq $f --ip <ip_address>
}
```

### E-UTRA operating band presets

| Band | F_UL,low (Hz) | F_UL,high (Hz) | Range 1 max (Hz) | Range 2 min (Hz) |
|------|--------------|----------------|------------------|------------------|
| n249 | 1,616,000,000 | 1,626,500,000 | 1,596,000,000 | 1,646,500,000 |
| n252 | 2,000,000,000 | 2,020,000,000 | 1,980,000,000 | 2,040,000,000 |
| n253 | 1,668,000,000 | 1,675,000,000 | 1,648,000,000 | 1,695,000,000 |
| n254 | 1,610,000,000 | 1,626,500,000 | 1,590,000,000 | 1,646,500,000 |
| n255 | 1,626,500,000 | 1,660,500,000 | 1,606,500,000 | 1,680,500,000 |
| n256 | 1,980,000,000 | 2,010,000,000 | 1,960,000,000 | 2,030,000,000 |

n249 is defined only for TDD NB-IoT operation.

The default band is **n254**. Use `--ful-low` and/or `--ful-high` to override the band edge
frequencies manually (e.g. for non-standard configurations).

### Parameters

All common parameters apply, plus:

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--tdd` | flag | No | off | Use Table 7.5.5-1 LEO TDD OOB blocking (BW 200 kHz, SCS 15 kHz only). Applies with `--class leo`. |
| `--interferer-freq` | `int` | Yes (always) | — | CW interferer frequency in Hz. Validated against OOB ranges even without `--ip`. |
| `--band` | `n249` \| `n252` \| `n253` \| `n254` \| `n255` \| `n256` | No | `n254` | Operating band preset from `OPERATING_BANDS`. Determines OOB range boundaries. |
| `--ful-low` | `int` | No | band preset | Override F_UL,low in Hz. |
| `--ful-high` | `int` | No | band preset | Override F_UL,high in Hz. |
| `--spurious-response-exception` | flag | No | off | Table 7.5.5-1 NOTE 2 retest: set the CW interferer to −46 dBm at this `--interferer-freq`. Allowed only with SCS 3.75 kHz. |

`--class` is required when `--ip` is set.

### Valid BW / SCS combinations

Wanted power is TS 36.181 Table 7.2.5 PREFSENS plus 6 dB from Table 7.5.5-1
(E-UTRA: Table 7.2.5-1/7.2.5-2; standalone NB-IoT FDD: Table 7.2.5-3/7.2.5-4).
Interferer is a CW carrier at −44 dBm (Table 7.5.5-1). Δf_OOB is 20 MHz when
F_UL,high − F_UL,low < 100 MHz (Table 7.5.5-2). Values match `SAT_GEO_OOB`,
`SAT_LEO_OOB` and `SAT_LEO_TDD_OOB` in `tables_3gpp.py`.

For standalone NB-IoT, Table 7.5.5-1 NOTE 2 allows up to 24 spurious-response
exception **interferer** frequencies per wanted channel (1 MHz CW step, groups of
at most three contiguous steps). At those CW frequencies the first-pass −44 dBm
test may be retested at **−46 dBm for 3.75 kHz SCS only** (`--spurious-response-exception`).
The 24 / contiguous-3 counts are a DUT pass/fail rule; the script only changes
interferer power at the frequency given by `--interferer-freq`.

| BW (MHz) | SCS (kHz) | GEO FRC | GEO wanted (dBm) | LEO FRC | LEO wanted (dBm) |
|----------|-----------|---------|------------------|---------|------------------|
| 1.4 | 15 | FRC-A1-1 | −97.7 | FRC-A1-1 | −100.8 |
| 0.2 | 15 | FRC-A14-1 | −117.9 | FRC-A14-1 | −121.0 |
| 0.2 | 3.75 | FRC-A14-2 | −123.9 | FRC-A14-2 | −127.0 |

### LEO TDD (when `--tdd` is set)

TS 36.181 Table 7.2.5-5 (PREFSENS + 6 dB) × Table 7.5.5-1 / `SAT_LEO_TDD_OOB`. Applies to
`--class leo` with `--tdd`. Interferer power remains −44 dBm.

| BW (MHz) | SCS (kHz) | FRC | LEO TDD wanted (dBm) |
|----------|-----------|-----|----------------------|
| 0.2 | 15 | FRC-A14-3 | −120.1 |

### Example commands

```bash
# Lookup only — LEO, 1.4 MHz, 15 kHz SCS (checks OOB range membership)
python NB_IoT/ts-36181-chapter7/test_7_5.py --bw 1.4 --scs 15 --class leo --interferer-freq 1500000000

# Configure SMW at a specific OOB frequency — LEO, n254 band
python NB_IoT/ts-36181-chapter7/test_7_5.py --bw 1.4 --scs 15 --class leo --interferer-freq 1500000000 --ip <ip_address>

# Configure SMW with manual band-edge override
python NB_IoT/ts-36181-chapter7/test_7_5.py --bw 1.4 --scs 15 --class leo --interferer-freq 1500000000 --ful-low 1605000000 --ful-high 1630000000 --ip <ip_address>


# First pass — standalone NB-IoT 3.75 kHz, CW at −44 dBm
python NB_IoT/ts-36181-chapter7/test_7_5.py --bw 0.2 --scs 3.75 --class geo --interferer-freq 1500000000 --ip <ip_address>

# NOTE 2 retest at a failed CW frequency — 3.75 kHz only, CW at −46 dBm
python NB_IoT/ts-36181-chapter7/test_7_5.py --bw 0.2 --scs 3.75 --class geo --interferer-freq 1500000000 --spurious-response-exception --ip <ip_address>

# Config file — LEO, 1.4 MHz, 15 kHz SCS (edit band, freq, interferer_freq in the INI as needed)
python NB_IoT/ts-36181-chapter7/test_7_5.py NB_IoT/ts-36181-chapter7/configs/7_5/1_4_mhz_15khz_leo.ini
python NB_IoT/ts-36181-chapter7/test_7_5.py NB_IoT/ts-36181-chapter7/configs/7_5/0_2_mhz_3_75khz_geo.ini

```

---

## §7.8 — In-Channel Selectivity (`test_7_8.py`)

### Background

> In-channel selectivity (ICS) is a measure of the receiver ability to receive a wanted signal
> at its assigned resource block locations at the TAB connector for SAN type 1-H in the presence
> of an interfering signal received at a larger power spectral density. In this condition a
> throughput requirement shall be met for a specified reference measurement channel. The
> interfering signal shall be an E-UTRA signal which is time aligned with the wanted signal.
> For SAN type 1-H, the throughput shall be ≥ 95% of the maximum throughput of the reference
> measurement channel.

### Signal setup

Two sources are used simultaneously at the **same center frequency** (co-channel):

- **Source1** — wanted uplink E-UTRA signal (UL FRC, LINK UP)
- **Source2** — co-channel E-UTRA interferer: **16QAM PUSCH** (LINK UP, no FRC), 3 RBs at lower or higher resource blocks (`--interference-pos`)

Both signals use the same frequency (`--freq`) and SCS. Source2 is time-aligned with Source1
via the shared trigger on USER3.

The interferer is on the same channel, on different RBs. If Cell ID and RNTI (UE ID) are both
the same, the scrambling sequences match (`c_init = n_RNTI · 2^14 + … + N_ID^cell`), and the
receiver may treat the interferer as another allocation of the same UE. ICS configs therefore
use `ue_id = 1`, `interferer_ue_id = 2`, and split the Cell IDs.

### Parameters

All common parameters apply. `--class` is required when `--ip` is set.

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--interference-pos` | `lower` \| `higher` | Yes | — | Whether the interfering signal is placed at lower or higher resource blocks (VRB offset 0 or 3). |
| `--interferer-ue-id` | `int` | No | `2` | NB-IoT UE ID for the interfering signal on Source2. |

### Valid BW / SCS combinations

GEO from TS 36.181 Table 7.8.5-1 / `SAT_GEO_ICS`. LEO from Table 7.8.5-2 / `SAT_LEO_ICS`.
Interferer is a 1.4 MHz E-UTRA signal occupying 3 RBs.

| BW (MHz) | SCS (kHz) | GEO FRC | GEO wanted (dBm) | GEO interferer (dBm) | LEO FRC | LEO wanted (dBm) | LEO interferer (dBm) | Interferer RBs |
|----------|-----------|---------|------------------|----------------------|---------|------------------|----------------------|----------------|
| 1.4 | 15 | FRC-A1-4 | −103.1 | −97.6 | FRC-A1-4 | −106.2 | −88.7 | 3 |

### Example commands

```bash
# Lookup only — LEO, 1.4 MHz, 15 kHz SCS, interferer at lower RBs
python NB_IoT/ts-36181-chapter7/test_7_8.py --bw 1.4 --scs 15 --class leo --interference-pos lower

# Configure SMW — LEO, 1.4 MHz, 15 kHz SCS, interferer at lower RBs
python NB_IoT/ts-36181-chapter7/test_7_8.py --bw 1.4 --scs 15 --class leo --interference-pos lower --ip <ip_address>

# Configure SMW — GEO, 1.4 MHz, 15 kHz SCS, with SCPI log
python NB_IoT/ts-36181-chapter7/test_7_8.py --bw 1.4 --scs 15 --class geo --interference-pos lower --ip <ip_address> --log-scpi

# Wanted cell ID 150, interferer cell ID 1, interferer at higher RBs
python NB_IoT/ts-36181-chapter7/test_7_8.py --bw 1.4 --scs 15 --class leo --interference-pos higher --cell-id 150 --interferer-cell-id 1 --ip <ip_address>

# Config file — LEO, 1.4 MHz, 15 kHz SCS, interferer at lower RBs
python NB_IoT/ts-36181-chapter7/test_7_8.py NB_IoT/ts-36181-chapter7/configs/7_8/1_4_mhz_15khz_leo_lower.ini
```

---

## Shared Lookup Tables

All power levels, reference channels, operating-band presets, and interferer parameters are
defined in [`tables_3gpp.py`](tables_3gpp.py). Each script imports only the
tables it needs.

| Constant | Section | Used by |
|----------|---------|---------|
| `SAN_REF_SENS_LEVELS`, `SAN_GEO_REF_SENS_LEVELS`, `SAN_LEO_REF_SENS_LEVELS`, `SAN_LEO_TDD_REF_SENS_LEVELS` | §7.2 | `test_7_2.py` |
| `SAN_DYNAMIC_RANGE`, `SAN_GEO_DYNAMIC_RANGE`, `SAN_LEO_DYNAMIC_RANGE`, `SAN_LEO_TDD_DYNAMIC_RANGE`, `AWGN_BANDWIDTH` | §7.3 | `test_7_3.py` |
| `ACS_INTERFERER_OFFSET_MHZ`, `SAN_ACS`, `SAT_GEO_ACS`, `SAT_LEO_ACS`, `SAT_LEO_TDD_ACS` | §7.4.1 | `test_7_4_1.py` |
| `OPERATING_BANDS`, `SAN_OOB`, `SAT_GEO_OOB`, `SAT_LEO_OOB`, `SAT_LEO_TDD_OOB` | §7.5 | `test_7_5.py` |
| `SAT_GEO_ICS`, `SAT_LEO_ICS` | §7.8 | `test_7_8.py` |

`TestConfig` is also defined in `tables_3gpp.py` and imported by scripts that need it
for type annotations or to construct updated configurations.

`get_power_levels(table, bw, scs)` looks up a `TestConfig` from a chapter table for
the given bandwidth and SCS (LEO or GEO table is selected by the caller before calling).

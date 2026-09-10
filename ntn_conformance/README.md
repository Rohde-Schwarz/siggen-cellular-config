# NTN Testing

These scripts live in `ntn_conformance/` of the `siggen-cellular-config` GitHub
repository. Run setup and tests from this directory, not from the GitHub repository root.

Python scripts for configuring a **Rohde & Schwarz** signal generator to produce NTN test
cases as defined by [3GPP TS 38.181](https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=3935)
(NR SAN type 1-H, FR1-NTN) and [3GPP TS 36.181](https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=4065)
(LTE/E-UTRA SAN).

Each script looks up 3GPP-defined values (power levels, reference measurement channels), validates
the configuration, and — when an SMW IP address is provided — connects to the instrument over a raw
TCP/IP socket and applies the full signal configuration via SCPI.

Lookup tables in this folder are derived from 3GPP TS 38.181 and TS 36.181. They are provided to
configure an R&S signal generator and are not a substitute for the official specification. Verify
values against the ETSI/3GPP publication that applies to your test. See [`NOTICE`](../NOTICE) and
[`LICENSE`](../LICENSE).

---

## Requirements

- **Python 3.12 or later**
- **RsInstrument 1.124.0** (no NI-VISA installation required; uses raw socket transport)
- SMW reachable on the network at **TCP port 5025**

## Setup

From `ntn_conformance/`, create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

This creates a `.venv`, installs `RsInstrument` from `requirements.txt`, and runs `pip install -e .`
so the shared `utils` and `NR5G` packages are importable from any directory.

Run all scripts from **`ntn_conformance/`** with the virtual environment activated.

---

## Quick Start

### 1. Configure the global INI files

Before running any test, edit the two global config files in `ntn_conformance/`:

**[`instrument.ini`](instrument.ini)** — holds the SMW IP address and connection timeout used by all scripts.
Leave `ip` empty (the shipped default) to validate without connecting. Do not commit a real
instrument address. `timeout` is in seconds (converted to ms for RsInstrument at connect):

```ini
[instrument]
ip = <ip_address>   # replace with your instrument's IP address
timeout = 80        # OPC/VISA timeout in seconds (default: 80)
```

**[`NR5G/options.ini`](NR5G/options.ini)** — holds shared NR5G options:

```ini
[options]
log_scpi = true   # when true, writes every SCPI command to scpi-list.iec after each run
```

Both files are loaded automatically by every chapter script alongside the per-test INI file.
You only need to edit them once.

### 2. Understand a test-case INI file

Each test case has a pre-built INI file under the chapter's `configs/` folder. It contains
only the test-specific parameters in a `[test]` section. For example,
`configs/8_2_1/10mhz_30khz_2rx_tdla100_puschtypeA.ini`:

```ini
[test]
bw          = 10                    # channel bandwidth in MHz
scs         = 30                    # sub-carrier spacing in kHz
pusch_type  = A                     # PUSCH mapping type: A or B
num_rx      = 2                     # number of RX antennas: 1 or 2
propagation = NTN_TDLA100_200_LOW   # propagation condition
cell_id     = 0                     # NR5G cell ID
ue_id       = 0                     # NR5G UE ID
freq        = 1620000000            # RF center frequency in Hz
```

When you run a script with this file, it merges the `[instrument]` and `[options]` sections
from the global files above, so the IP address and `log_scpi` flag are picked up automatically.

Set `freq` to the RF center frequency required by the test case. Per TS 38.181, each test section
defines which **RF channels to test** apply — typically **B** (bottom), **M** (middle), and **T**
(top) of the operating band. The scripts do not select B/M/T for you; choose the frequency that
matches the channel(s) required for that section.

To bulk-update `freq` in NR5G test INIs, run from `ntn_conformance/`:

```powershell
# All NR5G test INIs
python scripts/set_rf_frequency.py --freq 1.62G

# Only §7.2 configs
python scripts/set_rf_frequency.py --section 7_2 --freq 1.62G

# §7.5: update wanted freq (and band) plus interferer frequency
python scripts/set_rf_frequency.py --section 7_5 --freq 1.62G --interferer-freq 1.5G
```

By default every test INI under `NR5G/ts-38181-chapter7/configs/` and
`NR5G/ts-38181-chapter8/configs/` with a `freq` key is updated. Use `--section` to limit changes to one config folder (e.g. `7_2`, `7_5`, `8_2_1`).
For §7.5 configs, `band` is set from the FR1 NTN table (n253–n256) when `--freq` falls inside a band; if it is outside all four
bands, `freq` is still updated but `band` is left unchanged and a warning is printed.
`--interferer-freq` is only supported with `--section 7_5`.

### 3. Run a test

Activate the virtual environment, then pass the INI file as the only argument:

```powershell
# Chapter 7 — Reference sensitivity, 10 MHz / 15 kHz, LEO
python NR5G/ts-38181-chapter7/test_7_2.py NR5G/ts-38181-chapter7/configs/7_2/10mhz_15khz_leo.ini

# Chapter 8 — PUSCH performance, 10 MHz / 30 kHz, 2 RX, TDLA100
python NR5G/ts-38181-chapter8/test_8_2_1.py NR5G/ts-38181-chapter8/configs/8_2_1/10mhz_30khz_2rx_tdla100_puschtypeA.ini
```

Or pass parameters directly on the command line (`--ip` and `--timeout` override `instrument.ini`):

```powershell
python NR5G/ts-38181-chapter7/test_7_2.py --bw 10 --scs 15 --class leo --ip <ip_address>
python NR5G/ts-38181-chapter8/test_8_2_1.py --bw 10 --scs 30 --num-rx 2 --pusch-type A --propagation NTN_TDLA100_200_LOW --ip <ip_address>
```

Omit `--ip` (and leave `instrument.ini` empty) to validate the 3GPP lookup results without
connecting to any instrument.

See the README in each chapter folder for the full parameter reference, lookup tables, and examples.

---

## Layout

| Path | Purpose |
|------|---------|
| `NR5G/utils.py` | NR5G-specific utilities (FRC map, SMW configuration functions) |
| `utils/scpi_utils.py` | SCPI write/query and command logging |
| `utils/smw_utils.py` | SMW connection and RF configuration |
| `utils/helpers.py` | Shared Python helpers (e.g. frequency parsing) |
| `scripts/set_rf_frequency.py` | Bulk-update `freq` (and optionally §7.5 `band` / `interferer_freq`) in NR5G test INIs |
| `utils/config_utils.py` | Load test parameters from INI config files |
| `instrument.ini` | SMW instrument IP and timeout (shared by all tests; ship empty, do not commit a real address) |
| `NR5G/options.ini` | Global options such as `log_scpi` |
| `NR5G/ts-38181-chapter7/` | Chapter 7 — Conducted receiver characteristics |
| `NR5G/ts-38181-chapter8/` | Chapter 8 — Conducted performance characteristics |
| `pyproject.toml` | Project metadata, dependencies, ruff/ty tooling config |
| `requirements.txt` | Pinned runtime dependencies |
| `scpi-list.iec` | Generated by `--log-scpi`; all SCPI write commands from the last run |

See [`NR5G/README.md`](NR5G/README.md) for documentation of all shared NR5G utility functions.

---

## Test Chapters

| Chapter | Folder | Description |
|---------|--------|-------------|
| 7 — Conducted receiver characteristics | [`NR5G/ts-38181-chapter7/`](NR5G/ts-38181-chapter7/) | Reference sensitivity, dynamic range, ACS, OOB blocking, ICS |
| 8 — Conducted performance characteristics | [`NR5G/ts-38181-chapter8/`](NR5G/ts-38181-chapter8/) | PUSCH, PUCCH, PRACH performance |

See [`NR5G/ts-38181-chapter7/README.md`](NR5G/ts-38181-chapter7/README.md) for Chapter 7 documentation.  
See [`NR5G/ts-38181-chapter8/README.md`](NR5G/ts-38181-chapter8/README.md) for Chapter 8 documentation,
including TS 38.181 §8.2 PUSCH and §8.3 PUCCH applicability rules.

---

## Contribution

- Follow [PEP 8](https://peps.python.org/pep-0008/). This tree is checked with
  [Ruff](https://docs.astral.sh/ruff/) as configured in `pyproject.toml`.
- Contributors must follow the Rohde & Schwarz
  [Code of Conduct](https://github.com/Rohde-Schwarz/rohde-schwarz/blob/master/code-of-conduct.md).

---

## License and notices

This GitHub repository is MIT-licensed. See [`LICENSE`](../LICENSE) and [`NOTICE`](../NOTICE) for
third-party package licenses and the 3GPP/ETSI specification disclaimer.

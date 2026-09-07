# siggen-cellular-config

Configuration scripts for cellular test applications using Rohde & Schwarz signal generators.

This repository is published under the MIT License. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Contents

| Path | Purpose |
|------|---------|
| [`ntn_conformance/`](ntn_conformance/) | NTN test-case scripts for 3GPP TS 38.181 (NR SAN) and TS 36.181 (LTE/E-UTRA SAN) |
| [`csi_report_multiplexing/`](csi_report_multiplexing/) | CSI Part 1 multiplexing example |
| [`prach_by_index/`](prach_by_index/) | PRACH configuration from 3GPP TS 38.211 tables |
| [`newradio_nb_IoT/`](newradio_nb_IoT/) | NB-IoT in NR example |

NTN scripts use [RsInstrument](https://pypi.org/project/RsInstrument/). The older examples use [PyVISA](https://pypi.org/project/PyVISA/).

## 3GPP specifications

Numeric parameters in the NTN lookup tables are derived from 3GPP TS 38.181 and TS 36.181.
This repository does not include specification documents. Confirm all values against
the official ETSI/3GPP publication that applies to your test. See [NOTICE](NOTICE).

## Contribution

- Python in this repository follows [PEP 8](https://peps.python.org/pep-0008/).
  NTN scripts under `ntn_conformance/` are additionally checked with
  [Ruff](https://docs.astral.sh/ruff/) (`ntn_conformance/pyproject.toml` and
  `ntn_conformance/.pre-commit-config.yaml`). The older example scripts in
  `csi_report_multiplexing/`, `prach_by_index/`, and `newradio_nb_IoT/` are
  short samples and are not run through that lint setup.
- Contributors must follow the Rohde & Schwarz
  [Code of Conduct](https://github.com/Rohde-Schwarz/rohde-schwarz/blob/master/code-of-conduct.md).

## License

MIT. Copyright (c) 2023-2026 Rohde & Schwarz GmbH & Co. KG.

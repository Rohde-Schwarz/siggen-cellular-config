"""SCPI write/query and command logging utilities."""

from pathlib import Path

from RsInstrument import RsInstrument

_log_scpi_commands = False
_sent_scpi_commands: list[str] = []
SCPI_LOG_FILE = Path(__file__).resolve().parent.parent / "scpi-list.iec"


def enable_scpi_logging(enabled: bool = True):
    """Enable or disable SCPI command logging for the current run."""
    global _log_scpi_commands, _sent_scpi_commands
    _log_scpi_commands = enabled
    _sent_scpi_commands = []


def write_scpi(smw: RsInstrument, command: str):
    """Send an SCPI command and optionally record it for logging."""
    smw.write_str(command)
    if _log_scpi_commands:
        _sent_scpi_commands.append(command)


def query_scpi(smw: RsInstrument, command: str):
    """Query an SCPI command without recording it in the write log."""
    return smw.query_str(command).strip()


def print_scpi_log():
    """Write all SCPI commands sent during this run to scpi-list.iec."""
    if not _sent_scpi_commands:
        SCPI_LOG_FILE.write_text("No SCPI commands were sent.\n", encoding="utf-8")
        print(f"No SCPI commands were sent. Written to {SCPI_LOG_FILE}")
        return
    SCPI_LOG_FILE.write_text("\n".join(_sent_scpi_commands) + "\n", encoding="utf-8")
    print(f"SCPI commands written to {SCPI_LOG_FILE}")

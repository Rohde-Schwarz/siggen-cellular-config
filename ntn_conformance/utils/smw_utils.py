"""Shared SMW utilities."""

from RsInstrument import RsInstrument

from utils.config_utils import resolve_smw_timeout
from utils.scpi_utils import query_scpi, write_scpi


def connect_smw(ip_address: str):
    """Connect to an SMW using RsInstrument over raw TCP/IP socket (no external VISA)."""
    resource = f"TCPIP::{ip_address}::5025::SOCKET"
    timeout_ms = resolve_smw_timeout() * 1000
    try:
        smw = RsInstrument(resource, id_query=True, reset=True,
            options=f"SelectVisa='socket',OpcTimeout={timeout_ms},VisaTimeout={timeout_ms},OpcQueryAfterWrite=True")
        print(f"Connected to {smw.idn_string}")
        print("--------------------------------")
        return smw
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to SMW at {ip_address}: {exc}") from exc


def configure_rf(smw: RsInstrument, power_dbm: float, freq: int, source: int = 1, turn_rf_on: bool = False):
    """Set RF output power and center frequency."""
    try:
        write_scpi(smw, f":SOURce{source}:POWer:POWer {power_dbm}")
        write_scpi(smw, f":SOURce{source}:FREQuency:CW {freq}")
        print(f"RF configured successfully - Source {source} (Power Level: {power_dbm} dBm, freq={freq} Hz)")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"RF configuration failed: {exc}") from exc

    if turn_rf_on:
        try:
            write_scpi(smw, f":OUTPut{source}:STATe 1")
            print(f"RF{source} is turned on successfully")
            print("--------------------------------")
        except Exception as exc:
            raise RuntimeError(f"Failed to turn on RF{source}: {exc}") from exc


def reset_smw(smw: RsInstrument):
    """Reset the SMW."""
    try:
        write_scpi(smw, "*RST")
        print("SMW reset successfully")
        print("--------------------------------")
    except Exception as exc:
        raise RuntimeError(f"Failed to reset SMW: {exc}") from exc


def is_smw_b9(smw: RsInstrument) -> bool:
    """Return True if the SMW has the B9 option installed; False means B10."""
    tokens = [t.strip() for t in query_scpi(smw, "*OPT?").upper().split(",")]
    for token in tokens:
        if token == "B9" or token.endswith("-B9"):
            return True
    for token in tokens:
        if token == "B10" or token.endswith("-B10"):
            return False
    raise RuntimeError(
        f"Cannot determine SMW variant from instrument options (expected B9 or B10): {','.join(tokens)!r}"
    )


def get_harq_connector(smw: RsInstrument) -> int:
    """Return the HARQ feedback TM input port (2 or 3) based on installed options.

    B9 hardware uses TM2; B10 hardware uses TM3.
    """
    return 2 if is_smw_b9(smw) else 3

"""Shared SMW utilities."""

from RsInstrument import RsInstrument

from utils.scpi_utils import write_scpi


def connect_smw(ip_address: str):
    """Connect to an SMW using RsInstrument over raw TCP/IP socket (no external VISA)."""
    resource = f"TCPIP::{ip_address}::5025::SOCKET"
    try:
        smw = RsInstrument(resource, id_query=True, reset=True, options="SelectVisa='socket'")
        smw.visa_timeout = 10000
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

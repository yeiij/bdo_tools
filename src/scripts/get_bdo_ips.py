"""./scripts/get_bdo_ips.py"""
import psutil


def get_bdo_ips(process_name: str = "BlackDesert64.exe"):
    """Return a set of remote IPs used by the Black Desert Online process."""
    ips = set()
    for conn in psutil.net_connections(kind="tcp"):
        try:
            if conn.pid:
                p = psutil.Process(conn.pid)
                if p.name().lower() == process_name.lower() and conn.raddr:
                    ips.add(conn.raddr.ip)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return ips
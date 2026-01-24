"""Section that displays a detailed table of network connections."""

from __future__ import annotations

from core.network.ip_utils import get_connections_for_process
from core.network.latency import tcp_ping_stats
from core.network.services import resolve_service_name
from gui.sections.base import Section


class NetworkTableSection(Section):
    """
    Renders a text-based table of active TCP connections.
    Columns: PID | Local Addr | Remote Addr | Service | Latency
    """

    def __init__(self, process_name: str, ping_count: int = 1) -> None:
        self.process_name = process_name
        self.ping_count = ping_count

    def render(self) -> str:
        """Fetch connections, measure latency, and format as a table."""
        conns = get_connections_for_process(self.process_name)
        
        if not conns:
            return "No active connections found."

        # Header
        # Adjusted widths: PID(6) | Local(21) | Remote(21) | Service(20) | Latency(8)
        header = f"{'PID':<6} {'Local Address':<21} {'Remote Address':<21} {'Service':<20} {'Latency':<8}"
        lines = [header, "-" * len(header)]

        for c in conns:
            # Measure latency using TCP ping for better accuracy on game ports
            latency_str = "..."
            if c.remote_ip and c.remote_port:
                stats = tcp_ping_stats(c.remote_ip, port=c.remote_port, count=self.ping_count, timeout=1.0)
                avg = stats.get("avg")
                latency_str = f"{avg:.0f} ms" if avg is not None else "N/A"

            local = f"{c.local_ip}:{c.local_port}"
            remote = f"{c.remote_ip}:{c.remote_port}"
            service = resolve_service_name(c.remote_port)

            line = f"{c.pid:<6} {local:<21} {remote:<21} {service:<20} {latency_str:<8}"
            # Add an extra newline for spacing as requested
            lines.append(line + "\n")

        return "\n".join(lines)

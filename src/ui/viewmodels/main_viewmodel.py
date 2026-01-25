"""Main ViewModel."""

from typing import List, Optional
from domain.models import ConnectionInfo, ProcessStatus, AppSettings
from domain.services import IProcessService, INetworkService


class MainViewModel:
    def __init__(
        self,
        process_service: IProcessService,
        network_service: INetworkService,
        settings: AppSettings
    ):
        self._process_service = process_service
        self._network_service = network_service
        self.settings = settings
        
        self.status = ProcessStatus.UNKNOWN
        self.connections: List[ConnectionInfo] = []
        self.game_latency: Optional[float] = None
        self.priority: str = "Unknown"
        self.target_priority: Optional[str] = settings.target_priority
        self.target_affinity: Optional[List[int]] = settings.target_affinity
        self.affinity: List[int] = []
        self.pid: Optional[int] = None
        
        self._refresh_count = 0
        
        self.is_admin = self._process_service.is_admin()
        
    def refresh(self):
        """Update state."""
        self._update_process_state()
        self._update_network_state()
        self._enforce_policies()
        self._calculate_metrics()

    def _update_process_state(self):
        """Update process status, PID, priority, affinity, and CPU count."""
        self.status = self._process_service.get_status(self.settings.process_name)
        self.pid = self._process_service.get_pid(self.settings.process_name)
        self.priority = self._process_service.get_priority(self.settings.process_name)
        self.affinity = self._process_service.get_affinity(self.settings.process_name)
        self.cpu_count = self._process_service.get_cpu_count()

    def _update_network_state(self):
        """Update network connections with throttling."""
        self._refresh_count += 1
        # Throttled: Every 2nd refresh (approx 10s if poll is 5s)
        if self.pid and self._refresh_count % 2 == 0:
            conns = self._network_service.get_connections(self.pid)
            # Annotate ExitLag IP
            self._annotate_connections(conns)
            self.connections = conns
        elif not self.pid:
            self.connections = []

    def _annotate_connections(self, connections: List[ConnectionInfo]):
        """Apply custom annotations to connections (e.g. ExitLag)."""
        for c in connections:
            # Heuristic: ExitLag proxies via localhost on high ports.
            # If standard web ports (80, 443) on localhost, it's likely local web server/service.
            # If non-standard port on localhost, assume it's ExitLag/Proxy for BDO.
            if c.remote_ip in ("127.0.0.1", "::1", "localhost"):
                 if c.remote_port not in (80, 443):
                     c.remote_ip = "ExitLag"
                     c.service_name = "Game Server"
            # Legacy check just in case
            elif c.remote_port == 60774:
                c.remote_ip = "ExitLag"
                c.service_name = "Game Server"

    def _enforce_policies(self):
        """Enforce target priority and affinity if they drift."""
        if self.status != ProcessStatus.RUNNING:
            return

        # Enforce Priority
        if self.target_priority and self.priority != self.target_priority:
            self._process_service.set_priority(self.settings.process_name, self.target_priority)
            self.priority = self._process_service.get_priority(self.settings.process_name)

        # Enforce Affinity
        if self.target_affinity and self.affinity and sorted(self.affinity) != sorted(self.target_affinity):
            self._process_service.set_affinity(self.settings.process_name, self.target_affinity)
            self.affinity = self._process_service.get_affinity(self.settings.process_name)

    def _calculate_metrics(self):
        """Calculate derived metrics like Game Latency."""
        from infrastructure.services_map import is_game_port
        
        game_latencies = [
            c.latency_ms for c in self.connections 
            if c.latency_ms and "Game Server" in c.service_name
        ]
        
        if game_latencies:
            self.game_latency = max(game_latencies)
        else:
            self.game_latency = None

    def set_manual_priority(self, priority: str):
        """Set a specific priority and enable enforcement."""
        self.target_priority = priority
        self.settings.target_priority = priority
        self.settings.save()
        # Apply immediately
        self._process_service.set_priority(self.settings.process_name, priority)
        self.refresh()

    def set_affinity(self, cores: List[int]) -> bool:
        if not self.pid:
            return False
            
        success = self._process_service.set_affinity(self.settings.process_name, cores)
        if success:
            self.settings.target_affinity = cores
            self.settings.save()
            self.refresh()
        return success
        


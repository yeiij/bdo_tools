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
        self.affinity: List[int] = []
        self.pid: Optional[int] = None
        
        self.is_admin = self._process_service.is_admin()
        
    def optimize_process(self) -> bool:
        """Set High Priority and exclude cores 0,1."""
        if not self.pid:
            return False
        
        # Priority
        self._process_service.set_priority(self.settings.process_name, high=True)
        
        # Affinity (Exclude 0 and 1 if we have enough cores)
        import psutil
        total_cores = psutil.cpu_count(logical=True) or 4
        if total_cores > 2:
            desired_cores = list(range(2, total_cores))
            self._process_service.set_affinity(self.settings.process_name, cores=desired_cores)
        
        self.refresh()
        return True

    def refresh(self):
        """Update state."""
        self.status = self._process_service.get_status(self.settings.process_name)
        self.pid = self._process_service.get_pid(self.settings.process_name)
        self.priority = self._process_service.get_priority(self.settings.process_name)
        self.affinity = self._process_service.get_affinity(self.settings.process_name)
        
        if self.pid:
            self.connections = self._network_service.get_connections(self.pid)
        else:
            self.connections = []

        # Calculate Game Latency
        from infrastructure.services_map import is_game_port
        
        game_latencies = [
            c.latency_ms for c in self.connections 
            if c.latency_ms and is_game_port(c.remote_port)
        ]
        
        if game_latencies:
            import statistics
            self.game_latency = statistics.mean(game_latencies)
        else:
            self.game_latency = None

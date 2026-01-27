"""Main ViewModel."""

from typing import List, Optional
from domain.models import ConnectionInfo, ProcessStatus, AppSettings
from domain.services import IProcessService, INetworkService


from infrastructure.gpu import NvidiaGpuService

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
        
        # GPU Service
        self._gpu_service = NvidiaGpuService()
        
        self.status = ProcessStatus.UNKNOWN
        self.connections: List[ConnectionInfo] = []
        self.game_latency: Optional[float] = None
        self.priority: str = "Unknown"
        self.target_priority: Optional[str] = settings.target_priority
        self.target_affinity: Optional[List[int]] = settings.target_affinity
        self.affinity: List[int] = []
        self.pid: Optional[int] = None
        self.cpu_usage_str: str = "0%"
        self.gpu_usage_str: str = "0%"
        self.ram_used_str: str = "0GB"
        self.ram_total_label: str = "/0GB RAM"
        self.vram_used_str: str = "0GB"
        self.vram_total_label: str = "/0GB vRAM"
        self._cpu_temp_str: str = "N/A"
        self._gpu_temp_str: str = "N/A"
        
        self._refresh_count = 0
        
        self.is_admin = self._process_service.is_admin()
        
    def refresh(self):
        """Update state."""
        self._update_process_state()
        self._update_network_state()
        self._enforce_policies()
        self._calculate_metrics()

    @property
    def vram_display_str(self) -> str:
        if not self._gpu_service.is_available():
            return "N/A"
        return self.vram_used_str

    @property
    def cpu_temp_str(self) -> str:
        return self._cpu_temp_str

    @property
    def gpu_temp_str(self) -> str:
        return self._gpu_temp_str

    def _update_process_state(self):
        """Update process status and System Resources."""
        # Process State
        self.status = self._process_service.get_status(self.settings.process_name)
        self.pid = self._process_service.get_pid(self.settings.process_name)
        self.priority = self._process_service.get_priority(self.settings.process_name)
        self.affinity = self._process_service.get_affinity(self.settings.process_name)
        self.cpu_count = self._process_service.get_cpu_count()
        
        # System Memory
        mem_used, mem_total = self._process_service.get_system_memory()
        self.ram_used_str = f"{mem_used / (1024**3):.0f}GB"
        self.ram_total_label = f"/{mem_total / (1024**3):.0f}GB RAM"
        
        # System CPU
        self.cpu_usage_str = f"{self._process_service.get_system_cpu():.0f}%"
        
        # System VRAM
        if self._gpu_service.is_available():
            v_used, v_total = self._gpu_service.get_system_vram_usage()
            self.vram_used_str = f"{v_used / (1024**3):.0f}GB"
            self.vram_total_label = f"/{v_total / (1024**3):.0f}GB vRAM"
            
            # GPU Temp
            g_temp = self._gpu_service.get_system_gpu_temperature()
            self._gpu_temp_str = f"{g_temp:.0f}°C" if g_temp is not None else "N/A"
            
            # GPU Usage
            g_usage = self._gpu_service.get_system_gpu_usage()
            self.gpu_usage_str = f"{g_usage:.0f}%" if g_usage is not None else "0%"
        else:
            self.vram_used_str = "0GB"
            self.vram_total_label = "/0GB vRAM"
            self._gpu_temp_str = "N/A"
            self.gpu_usage_str = "0%"

        # CPU Temp
        c_temp = self._process_service.get_system_cpu_temperature()
        self._cpu_temp_str = f"{c_temp:.0f}°C" if c_temp is not None else "N/A"

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
            self.target_affinity = cores
            self.settings.target_affinity = cores
            self.settings.save()
            self.refresh()
        return success
        


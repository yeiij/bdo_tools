"""Main ViewModel."""


from domain.models import AppSettings, ConnectionInfo, ProcessStatus
from domain.services import IGpuService, INetworkService, IProcessService, ISystemService


class MainViewModel:
    def __init__(
        self,
        process_service: IProcessService,
        network_service: INetworkService,
        system_service: ISystemService,
        gpu_service: IGpuService,
        settings: AppSettings,
    ):
        self._process_service = process_service
        self._network_service = network_service
        self._system_service = system_service
        self._gpu_service = gpu_service
        self.settings = settings

        # UI State
        self.status = ProcessStatus.UNKNOWN
        self.connections: list[ConnectionInfo] = []
        self.game_latency: float | None = None
        self.priority: str = "Unknown"
        self.affinity: list[int] = []
        self.pid: int | None = None

        # System Metrics
        self.cpu_usage_str: str = "0%"
        self.gpu_usage_str: str = "0%"
        self.ram_used_str: str = "0GB"
        self.ram_total_label: str = "/0GB RAM"
        self.vram_used_str: str = "0GB"
        self.vram_total_label: str = "/0GB vRAM"
        self._cpu_temp_str: str = "N/A"
        self._gpu_temp_str: str = "N/A"
        self.cpu_count: int = system_service.get_cpu_count()

        # Network Process State
        self.network_pid: int | None = None
        self.network_priority: str = "Unknown"
        self.network_affinity: list[int] = []

        self.is_admin = self._process_service.is_admin()
        self._refresh_count = 0

        # Cache policies for enforcement
        self.target_priority = settings.game_target_priority
        self.target_affinity = settings.game_target_affinity
        self.network_target_priority = settings.network_target_priority
        self.network_target_affinity = settings.network_target_affinity

        self.settings.save()

    def refresh(self):
        """Update all state and enforce policies."""
        self._update_processes()
        self._update_system_metrics()
        self._update_network_connections()
        self._enforce_active_policies()
        self._calculate_derived_metrics()

    @property
    def vram_display_str(self) -> str:
        """Friendly VRAM string or N/A if GPU is unavailable."""
        return self.vram_used_str if self._gpu_service.is_available() else "N/A"

    @property
    def cpu_temp_str(self) -> str:
        return self._cpu_temp_str

    @property
    def gpu_temp_str(self) -> str:
        return self._gpu_temp_str

    def _update_processes(self):
        """Update state for monitored processes."""
        # Game Process
        game_name = self.settings.game_process_name
        self.status = self._process_service.get_status(game_name)
        self.pid = self._process_service.get_pid(game_name)
        self.priority = self._process_service.get_priority(game_name)
        self.affinity = self._process_service.get_affinity(game_name)

        # Network Booster Process
        net_name = self.settings.network_process_name
        self.network_pid = self._process_service.get_pid(net_name)
        if self.network_pid:
            self.network_priority = self._process_service.get_priority(net_name)
            self.network_affinity = self._process_service.get_affinity(net_name)
        else:
            self.network_priority = "Not Running"
            self.network_affinity = []

    def _update_system_metrics(self):
        """Update global system resource usage."""
        # CPU & RAM
        mem_used, mem_total = self._system_service.get_system_memory()
        self.ram_used_str = f"{mem_used / (1024**3):.0f}GB"
        self.ram_total_label = f"/{mem_total / (1024**3):.0f}GB RAM"
        self.cpu_usage_str = f"{self._system_service.get_system_cpu():.0f}%"

        # Temperatures
        c_temp = self._system_service.get_system_cpu_temperature()
        self._cpu_temp_str = f"{c_temp:.0f}°C" if c_temp is not None else "N/A"

        # GPU Metrics
        if self._gpu_service.is_available():
            v_used, v_total = self._gpu_service.get_system_vram_usage()
            self.vram_used_str = f"{v_used / (1024**3):.0f}GB"
            self.vram_total_label = f"/{v_total / (1024**3):.0f}GB vRAM"

            g_temp = self._gpu_service.get_system_gpu_temperature()
            self._gpu_temp_str = f"{g_temp:.0f}°C" if g_temp is not None else "N/A"

            g_usage = self._gpu_service.get_system_gpu_usage()
            self.gpu_usage_str = f"{g_usage:.0f}%" if g_usage is not None else "0%"
        else:
            self.vram_used_str, self.vram_total_label = "0GB", "/0GB vRAM"
            self._gpu_temp_str, self.gpu_usage_str = "N/A", "0%"

    def _update_network_connections(self):
        """Query network connections with internal throttling."""
        self._refresh_count += 1
        # Throttled network query (approx every 8s)
        if self.pid and self._refresh_count % 2 == 0:
            conns = self._network_service.get_connections(self.pid)
            self._apply_network_annotations(conns)
            self.connections = conns
        elif not self.pid:
            self.connections = []

    def _apply_network_annotations(self, connections: list[ConnectionInfo]):
        """Identify proxy/booster traffic in connections."""
        for c in connections:
            is_local = c.remote_ip in ("127.0.0.1", "::1", "localhost")
            is_booster_port = c.remote_port not in (80, 443)

            if is_local and is_booster_port:
                c.remote_ip = "ExitLag"  # Generic annotation
                c.service_name = "Game Server"

    def _enforce_active_policies(self):
        """Enforce configured priority/affinity if they drift from targets."""
        # Game Policy
        if self.status == ProcessStatus.RUNNING:
            self._apply_policy(
                self.settings.game_process_name,
                self.target_priority,
                self.target_affinity,
                self.priority,
                self.affinity,
            )
            # Re-read to reflect actual state
            self.priority = self._process_service.get_priority(self.settings.game_process_name)
            self.affinity = self._process_service.get_affinity(self.settings.game_process_name)

        # Network Policy
        if self.network_pid:
            self._apply_policy(
                self.settings.network_process_name,
                self.network_target_priority,
                self.network_target_affinity,
                self.network_priority,
                self.network_affinity,
            )
            # Re-read to reflect actual state
            self.network_priority = self._process_service.get_priority(
                self.settings.network_process_name
            )
            self.network_affinity = self._process_service.get_affinity(
                self.settings.network_process_name
            )

    def _apply_policy(self, name, t_pri, t_aff, cur_pri, cur_aff):
        """Helper to set priority/affinity if needed."""
        if t_pri and cur_pri != t_pri:
            self._process_service.set_priority(name, t_pri)
        if t_aff and cur_aff and sorted(cur_aff) != sorted(t_aff):
            self._process_service.set_affinity(name, t_aff)

    def _calculate_derived_metrics(self):
        """Extract higher-level metrics from raw data."""
        game_latencies = [
            c.latency_ms
            for c in self.connections
            if c.latency_ms and "Game Server" in c.service_name
        ]
        self.game_latency = max(game_latencies) if game_latencies else None

    @property
    def is_network_active(self) -> bool:
        """Return True if any active connection uses a booster proxy."""
        return any(c.remote_ip == "ExitLag" for c in self.connections)

    # --- Manual Controls (Persistence + Immediate Application) ---

    def set_manual_priority(self, priority: str):
        self.target_priority = priority
        self.settings.game_target_priority = priority
        self.settings.save()
        self._process_service.set_priority(self.settings.game_process_name, priority)
        self.refresh()

    def set_network_manual_priority(self, priority: str):
        self.network_target_priority = priority
        self.settings.network_target_priority = priority
        self.settings.save()
        self._process_service.set_priority(self.settings.network_process_name, priority)
        self.refresh()

    def set_affinity(self, cores: list[int]) -> bool:
        if not self._process_service.set_affinity(self.settings.game_process_name, cores):
            return False
        self.target_affinity = cores
        self.settings.game_target_affinity = cores
        self.settings.save()
        self.refresh()
        return True

    def set_network_affinity(self, cores: list[int]) -> bool:
        if not self._process_service.set_affinity(self.settings.network_process_name, cores):
            return False
        self.network_target_affinity = cores
        self.settings.network_target_affinity = cores
        self.settings.save()
        self.refresh()
        return True

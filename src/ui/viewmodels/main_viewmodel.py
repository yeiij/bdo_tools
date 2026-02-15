"""Main ViewModel."""

import os
from collections import deque
from time import monotonic

from domain.models import AppSettings, ConnectionInfo, ProcessStatus
from domain.services import IGpuService, INetworkService, IProcessService, ISystemService


class MainViewModel:
    LATENCY_WINDOW_SECONDS = 300.0

    def __init__(
        self,
        process_service: IProcessService,
        network_service: INetworkService,
        system_service: ISystemService,
        gpu_service: IGpuService,
        settings: AppSettings,
        persist_settings_on_init: bool = True,
    ):
        self._process_service = process_service
        self._network_service = network_service
        self._system_service = system_service
        self._gpu_service = gpu_service
        self.settings = settings
        self._settings_path = AppSettings.default_path()
        self._settings_mtime: float | None = None
        if os.path.exists(self._settings_path):
            try:
                self._settings_mtime = os.path.getmtime(self._settings_path)
            except OSError:
                self._settings_mtime = None

        # UI State
        self.status = ProcessStatus.UNKNOWN
        self.connections: list[ConnectionInfo] = []
        self.network_connections: list[ConnectionInfo] = []
        self.game_latency: float | None = None
        self.game_latency_current: float | None = None
        self.game_latency_low: float | None = None
        self.game_latency_peak: float | None = None
        self._last_game_latency: float | None = None
        self._latency_history: deque[tuple[float, float]] = deque()
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

        # Cache policies for enforcement
        self.target_priority = settings.game_target_priority
        self.target_affinity = settings.game_target_affinity
        self.network_target_priority = settings.network_target_priority
        self.network_target_affinity = settings.network_target_affinity

        if persist_settings_on_init:
            self._save_settings()

    def refresh(self):
        """Update all state and enforce policies."""
        self._reload_settings_if_changed()
        self._update_processes()
        self._seed_targets_from_live_processes()
        self._update_system_metrics()
        self._update_network_connections()
        self._enforce_active_policies()
        self._calculate_derived_metrics()

    def _reload_settings_if_changed(self):
        """Reload settings from disk when external edits are detected."""
        if not os.path.exists(self._settings_path):
            return
        try:
            mtime = os.path.getmtime(self._settings_path)
        except OSError:
            return
        if self._settings_mtime is not None and mtime <= self._settings_mtime:
            return

        loaded = AppSettings.load(self._settings_path)
        for field_name in AppSettings.__dataclass_fields__.keys():
            setattr(self.settings, field_name, getattr(loaded, field_name))

        self.target_priority = self.settings.game_target_priority
        self.target_affinity = self.settings.game_target_affinity
        self.network_target_priority = self.settings.network_target_priority
        self.network_target_affinity = self.settings.network_target_affinity
        self._settings_mtime = mtime

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

    def _seed_targets_from_live_processes(self):
        """Initialize missing target policies from live processes and persist once."""
        changed = False
        valid_priorities = {"Idle", "Below Normal", "Normal", "Above Normal", "High", "Realtime"}

        if self.status == ProcessStatus.RUNNING and self.pid:
            if (
                self.settings.game_target_priority is None
                and isinstance(self.priority, str)
                and self.priority in valid_priorities
            ):
                self.settings.game_target_priority = self.priority
                self.target_priority = self.priority
                changed = True
            if (
                self.settings.game_target_affinity is None
                and isinstance(self.affinity, list)
                and self.affinity
                and all(isinstance(core, int) for core in self.affinity)
            ):
                self.settings.game_target_affinity = list(self.affinity)
                self.target_affinity = list(self.affinity)
                changed = True

        if self.network_pid:
            if (
                self.settings.network_target_priority is None
                and isinstance(self.network_priority, str)
                and self.network_priority in valid_priorities
            ):
                self.settings.network_target_priority = self.network_priority
                self.network_target_priority = self.network_priority
                changed = True
            if (
                self.settings.network_target_affinity is None
                and isinstance(self.network_affinity, list)
                and self.network_affinity
                and all(isinstance(core, int) for core in self.network_affinity)
            ):
                self.settings.network_target_affinity = list(self.network_affinity)
                self.network_target_affinity = list(self.network_affinity)
                changed = True

        if changed:
            self._save_settings()

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
        """Query network connections every refresh cycle."""
        if self.pid:
            conns = self._network_service.get_connections(self.pid)
            self._apply_network_annotations(
                conns,
                network_active=bool(self.network_pid),
                network_label=self._network_proxy_label(),
            )
            self.connections = conns
            # When network process is active, sample its external links as ping source.
            if self.network_pid and self.network_pid != self.pid:
                self.network_connections = self._network_service.get_connections(self.network_pid)
            else:
                self.network_connections = []
        elif not self.pid:
            self.connections = []
            self.network_connections = []

    def _apply_network_annotations(
        self,
        connections: list[ConnectionInfo],
        network_active: bool,
        network_label: str,
    ):
        """Identify local-proxy traffic in game connections."""
        for c in connections:
            is_remote_local = c.remote_ip in ("127.0.0.1", "::1", "localhost")
            is_non_web = c.remote_port not in (53, 80, 443)

            if network_active and is_remote_local and is_non_web:
                c.remote_ip = network_label
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
            self.network_priority = self._process_service.get_priority(self.settings.network_process_name)
            self.network_affinity = self._process_service.get_affinity(self.settings.network_process_name)

        # Other Targets Policy
        for target in self.settings.other_targets:
            if not isinstance(target, dict):
                continue
            process_name = target.get("process")
            if not isinstance(process_name, str) or not process_name:
                continue

            target_priority = target.get("priority")
            if not isinstance(target_priority, str) or not target_priority:
                target_priority = None

            raw_affinity = target.get("affinity")
            target_affinity = (
                raw_affinity
                if isinstance(raw_affinity, list) and all(isinstance(core, int) for core in raw_affinity)
                else None
            )

            self._apply_policy(
                process_name,
                target_priority,
                target_affinity,
                self._process_service.get_priority(process_name),
                self._process_service.get_affinity(process_name),
            )

    def _apply_policy(self, name, t_pri, t_aff, cur_pri, cur_aff):
        """Helper to set priority/affinity if needed."""
        if t_pri and cur_pri != t_pri:
            self._process_service.set_priority(name, t_pri)
        if t_aff and cur_aff and sorted(cur_aff) != sorted(t_aff):
            self._process_service.set_affinity(name, t_aff)

    def _calculate_derived_metrics(self):
        """Extract higher-level metrics from raw data."""
        proxy_label = self._network_proxy_label()
        loopbacks = ("127.0.0.1", "::1", "localhost")
        if self.network_pid and self.network_connections:
            direct_exitlag_non_web = [
                c.latency_ms
                for c in self.network_connections
                if c.latency_ms is not None
                and c.remote_ip not in loopbacks
                and c.remote_port not in (53, 80, 443)
            ]
            direct_exitlag_any = [
                c.latency_ms
                for c in self.network_connections
                if c.latency_ms is not None and c.remote_ip not in loopbacks
            ]
            selected_exitlag = direct_exitlag_non_web or direct_exitlag_any
            if selected_exitlag:
                self._set_game_latency_from_candidates(selected_exitlag)
                return

        game_latencies = [
            c.latency_ms
            for c in self.connections
            if c.latency_ms is not None and "Game Server" in c.service_name
        ]
        direct_latencies = [
            c.latency_ms
            for c in self.connections
            if c.latency_ms is not None and "Game Server" in c.service_name and c.remote_ip != proxy_label
        ]

        selected = direct_latencies
        if not selected:
            proxy_latencies = [
                c.latency_ms
                for c in self.connections
                if c.latency_ms is not None
                and "Game Server" in c.service_name
                and c.remote_ip == proxy_label
            ]
            # Loopback connect latency from proxy hops is often near-zero and not representative.
            if self.network_pid:
                selected = [lat for lat in proxy_latencies if lat >= 5.0]
            else:
                selected = proxy_latencies or game_latencies

        if selected:
            self._set_game_latency_from_candidates(selected)
        elif self.pid and self._last_game_latency is not None:
            self.game_latency_current = self._last_game_latency
            self.game_latency = self._last_game_latency
            self.game_latency_low = self._last_game_latency
            self.game_latency_peak = self._last_game_latency
        else:
            self.game_latency = None
            self.game_latency_current = None
            self.game_latency_low = None
            self.game_latency_peak = None
            self._latency_history.clear()

    @property
    def is_network_active(self) -> bool:
        """Return True if any active connection uses a booster proxy."""
        return any(c.remote_ip == self._network_proxy_label() for c in self.connections)

    def _network_proxy_label(self) -> str:
        """Return the label used for local proxy hops in connection rows."""
        return self.settings.network_process_name or "Network Proxy"

    def _set_game_latency_from_candidates(self, candidates: list[float]) -> None:
        """Update current/stable/peak ping from current candidates and short-term history."""
        candidates.sort()
        current_median = candidates[len(candidates) // 2]
        now = monotonic()
        self._latency_history.append((now, current_median))
        self._prune_latency_history(now)
        recent = [value for _, value in self._latency_history]
        self.game_latency_current = current_median
        self.game_latency_low = min(recent)
        self.game_latency_peak = max(recent)
        # Backward-compatible alias
        self.game_latency = self.game_latency_current
        self._last_game_latency = self.game_latency_current

    def _prune_latency_history(self, now: float) -> None:
        cutoff = now - self.LATENCY_WINDOW_SECONDS
        while self._latency_history and self._latency_history[0][0] < cutoff:
            self._latency_history.popleft()

    # --- Manual Controls (Persistence + Immediate Application) ---

    def set_manual_priority(self, priority: str) -> bool:
        if not self._process_service.set_priority(self.settings.game_process_name, priority):
            self.refresh()
            return False
        self.target_priority = priority
        self.settings.game_target_priority = priority
        self._save_settings()
        self.refresh()
        return True

    def set_network_manual_priority(self, priority: str) -> bool:
        if not self._process_service.set_priority(self.settings.network_process_name, priority):
            self.refresh()
            return False
        self.network_target_priority = priority
        self.settings.network_target_priority = priority
        self._save_settings()
        self.refresh()
        return True

    def set_affinity(self, cores: list[int]) -> bool:
        if not self._process_service.set_affinity(self.settings.game_process_name, cores):
            return False
        self.target_affinity = cores
        self.settings.game_target_affinity = cores
        self._save_settings()
        self.refresh()
        return True

    def set_network_affinity(self, cores: list[int]) -> bool:
        if not self._process_service.set_affinity(self.settings.network_process_name, cores):
            return False
        self.network_target_affinity = cores
        self.settings.network_target_affinity = cores
        self._save_settings()
        self.refresh()
        return True

    def _save_settings(self) -> None:
        self.settings.save(self._settings_path)
        try:
            self._settings_mtime = os.path.getmtime(self._settings_path)
        except OSError:
            pass

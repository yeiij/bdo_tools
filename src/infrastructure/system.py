"""System infrastructure services."""

import ctypes
import os
import platform
import subprocess

import psutil

from domain.models import ProcessStatus
from domain.services import IProcessService, ISystemService


class PsutilProcessService(IProcessService):
    def __init__(self):
        pass

    def _get_matching_pids(self, process_name: str) -> list[int]:
        """Return all PIDs matching a process name (case-insensitive)."""
        pids: list[int] = []
        try:
            iterator = psutil.process_iter(["name", "pid"])
        except Exception:
            return pids
        try:
            for proc in iterator:
                try:
                    proc_name = proc.info.get("name")
                    pid = proc.info.get("pid")
                    if (
                        isinstance(proc_name, str)
                        and isinstance(pid, int)
                        and proc_name.lower() == process_name.lower()
                    ):
                        pids.append(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                    continue
        except Exception:
            return pids
        return pids

    def _get_target_pids(self, process_name: str) -> list[int]:
        """Resolve target PIDs for operations; includes all matching processes when available."""
        pids = self._get_matching_pids(process_name)
        if pids:
            return pids
        # Compatibility fallback used heavily by tests/mocks.
        pid = self.get_pid(process_name)
        return [pid] if pid else []

    def get_pid(self, process_name: str) -> int | None:
        """Return the PID of the first process matching process_name."""
        pids = self._get_matching_pids(process_name)
        return pids[0] if pids else None

    def get_status(self, process_name: str) -> ProcessStatus:
        """Return the status of the process."""
        pid = self.get_pid(process_name)
        if pid:
            try:
                p = psutil.Process(pid)
                if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                    return ProcessStatus.RUNNING
            except psutil.NoSuchProcess:
                pass
        return ProcessStatus.NOT_RUNNING

    def get_priority(self, process_name: str) -> str:
        """Return the process priority class as a string."""
        pid = self.get_pid(process_name)
        if not pid:
            return "Unknown"

        try:
            p = psutil.Process(pid)
            if platform.system() == "Windows":
                mapping = {
                    psutil.IDLE_PRIORITY_CLASS: "Idle",
                    psutil.BELOW_NORMAL_PRIORITY_CLASS: "Below Normal",
                    psutil.NORMAL_PRIORITY_CLASS: "Normal",
                    psutil.ABOVE_NORMAL_PRIORITY_CLASS: "Above Normal",
                    psutil.HIGH_PRIORITY_CLASS: "High",
                    psutil.REALTIME_PRIORITY_CLASS: "Realtime",
                }
                return mapping.get(p.nice(), "Unknown")
            return str(p.nice())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Unknown"

    def get_affinity(self, process_name: str) -> list[int]:
        """Return the list of CPUs the process is pinned to."""
        pid = self.get_pid(process_name)
        if not pid:
            return []

        try:
            p = psutil.Process(pid)
            affinity = getattr(p, "cpu_affinity", None)
            if not callable(affinity):
                return []
            return list(affinity())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    def set_priority(self, process_name: str, priority: str) -> bool:
        """Set priority class on all processes matching name."""
        pids = self._get_target_pids(process_name)
        if not pids:
            return False

        changed_any = False
        failed_any = False
        try:
            if platform.system() == "Windows":
                mapping = {
                    "Idle": psutil.IDLE_PRIORITY_CLASS,
                    "Below Normal": psutil.BELOW_NORMAL_PRIORITY_CLASS,
                    "Normal": psutil.NORMAL_PRIORITY_CLASS,
                    "Above Normal": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                    "High": psutil.HIGH_PRIORITY_CLASS,
                    "Realtime": psutil.REALTIME_PRIORITY_CLASS,
                }
                target_val = mapping.get(priority)
                if target_val is None:
                    return False
            else:
                target_val = 0 if priority.lower() == "normal" else -10

            for pid in pids:
                try:
                    psutil.Process(pid).nice(target_val)
                    changed_any = True
                except (psutil.AccessDenied, psutil.NoSuchProcess, ValueError):
                    failed_any = True
                    continue
            return changed_any and not failed_any
        except Exception:
            return False

    def set_affinity(self, process_name: str, cores: list[int]) -> bool:
        """Set CPU affinity on all processes matching name."""
        pids = self._get_target_pids(process_name)
        if not pids:
            return False

        changed_any = False
        failed_any = False
        for pid in pids:
            try:
                p = psutil.Process(pid)
                affinity = getattr(p, "cpu_affinity", None)
                if not callable(affinity):
                    failed_any = True
                    continue
                affinity(cores)
                changed_any = True
            except (psutil.AccessDenied, psutil.NoSuchProcess, ValueError):
                failed_any = True
                continue
        return changed_any and not failed_any

    def is_admin(self) -> bool:
        """Check if the current process has administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False


class PsutilSystemService(ISystemService):
    def get_cpu_count(self) -> int:
        """Return the number of logical CPUs in the system."""
        return psutil.cpu_count(logical=True) or 1

    def get_system_memory(self) -> tuple[float, float]:
        """Return (used_bytes, total_bytes) for the system."""
        mem = psutil.virtual_memory()
        return mem.used, mem.total

    def get_system_cpu(self) -> float:
        """Return system-wide CPU usage percentage."""
        return psutil.cpu_percent(interval=None)

    def get_system_cpu_temperature(self) -> float | None:
        """Return CPU temperature in Celsius (Windows only)."""
        # 1. Try PowerShell (Modern Windows)
        try:
            cmd = (
                'powershell -Command "Get-CimInstance -Namespace root\\wmi '
                "-ClassName MSAcpi_ThermalZoneTemperature | "
                'Select-Object -ExpandProperty CurrentTemperature"'
            )

            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            output = subprocess.check_output(cmd, startupinfo=startupinfo, text=True, stderr=subprocess.DEVNULL)
            if output.strip():
                temp_k10 = float(output.strip())
                return (temp_k10 / 10.0) - 273.15
        except Exception:
            pass

        # 2. Try WMIC (Legacy Windows)
        try:
            cmd = "wmic /namespace:\\\\root\\wmi PATH MSAcpi_ThermalZoneTemperature get CurrentTemperature"
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            lines = output.strip().splitlines()
            if len(lines) > 1:
                temp_k10 = float(lines[1].strip())
                return (temp_k10 / 10.0) - 273.15
        except Exception:
            pass

        return None

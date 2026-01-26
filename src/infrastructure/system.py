"""System infrastructure services."""

import psutil
import platform
import ctypes
from typing import Optional, List

from domain.models import ProcessStatus
from domain.services import IProcessService


class PsutilProcessService(IProcessService):
    def __init__(self):
        self._proc_cache = {}

    def get_pid(self, process_name: str) -> Optional[int]:
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None


    def get_status(self, process_name: str) -> ProcessStatus:
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
        pid = self.get_pid(process_name)
        if not pid:
            return "Unknown"
        
        try:
            p = psutil.Process(pid)
            if platform.system() == "Windows":
                # Map psutil constants to string
                mapping = {
                    psutil.IDLE_PRIORITY_CLASS: "Idle",
                    psutil.BELOW_NORMAL_PRIORITY_CLASS: "Below Normal",
                    psutil.NORMAL_PRIORITY_CLASS: "Normal",
                    psutil.ABOVE_NORMAL_PRIORITY_CLASS: "Above Normal",
                    psutil.HIGH_PRIORITY_CLASS: "High",
                    psutil.REALTIME_PRIORITY_CLASS: "Realtime"
                }
                return mapping.get(p.nice(), "Unknown")
            return str(p.nice())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Unknown"

    def get_affinity(self, process_name: str) -> List[int]:
        pid = self.get_pid(process_name)
        if not pid:
            return []
            
        try:
            p = psutil.Process(pid)
            return p.cpu_affinity()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

    def set_priority(self, process_name: str, priority: str) -> bool:
        pid = self.get_pid(process_name)
        if not pid:
            return False
        
        try:
            p = psutil.Process(pid)
            if platform.system() == "Windows":
                mapping = {
                    "Idle": psutil.IDLE_PRIORITY_CLASS,
                    "Below Normal": psutil.BELOW_NORMAL_PRIORITY_CLASS,
                    "Normal": psutil.NORMAL_PRIORITY_CLASS,
                    "Above Normal": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
                    "High": psutil.HIGH_PRIORITY_CLASS,
                    "Realtime": psutil.REALTIME_PRIORITY_CLASS
                }
                # Case-insensitive lookup
                target_val = None
                for k, v in mapping.items():
                    if k.lower() == priority.lower():
                        target_val = v
                        break
                
                if target_val is None:
                    # Fallback or error? defaulting to Normal if unknown is safer, 
                    # but returning False is more correct for "invalid input"
                    return False
                    
                p.nice(target_val)
            else:
                # Unix fallback (simple)
                p.nice(0 if priority.lower() == "normal" else -10)
                
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, ValueError):
            return False

    def set_affinity(self, process_name: str, cores: List[int]) -> bool:
        pid = self.get_pid(process_name)
        if not pid:
            return False
            
        try:
            p = psutil.Process(pid)
            p.cpu_affinity(cores)
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, ValueError):
            return False

    def is_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def get_memory_usage(self, process_name: str) -> float:
        pid = self.get_pid(process_name)
        if not pid:
            return 0.0
        try:
            p = psutil.Process(pid)
            # Try to get Unique Set Size (USS) which matches Task Manager "Private working set"
            # This is more accurate than RSS (includes shared) or Private (Commit Size)
            try:
                return p.memory_full_info().uss
            except (psutil.AccessDenied, AttributeError):
                return p.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def get_cpu_percent(self, process_name: str) -> float:
        pid = self.get_pid(process_name)
        if not pid:
            return 0.0
        
        try:
            # Use cached process to allow cpu_percent to calculate delta from last call
            proc = self._proc_cache.get(pid)
            if not proc:
                proc = psutil.Process(pid)
                self._proc_cache[pid] = proc
                # First call always returns 0.0, so we might return 0.0 initially
            
            # interval=None calculates since last call (non-blocking)
            val = proc.cpu_percent(interval=None)
            return val or 0.0
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process died, remove from cache
            if pid in self._proc_cache:
                del self._proc_cache[pid]
            return 0.0

    def get_cpu_count(self) -> int:
        return psutil.cpu_count(logical=True) or 1

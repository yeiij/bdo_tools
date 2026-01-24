"""System infrastructure services."""

import psutil
import platform
import ctypes
from typing import Optional, List

from domain.models import ProcessStatus
from domain.services import IProcessService


class PsutilProcessService(IProcessService):
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

    def set_priority(self, process_name: str, high: bool) -> bool:
        pid = self.get_pid(process_name)
        if not pid:
            return False
        
        try:
            p = psutil.Process(pid)
            if high:
                if platform.system() == "Windows":
                    p.nice(psutil.HIGH_PRIORITY_CLASS)
                else:
                    p.nice(-10) # Unix high priority (requires root usually, unlikely to work without sudo)
            else:
                if platform.system() == "Windows":
                    p.nice(psutil.NORMAL_PRIORITY_CLASS)
                else:
                    p.nice(0)
            return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
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

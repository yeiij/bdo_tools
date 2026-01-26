import os
import ctypes
from typing import Optional

try:
    import pynvml
except ImportError:
    pynvml = None

class NvidiaGpuService:
    def __init__(self):
        self._available = False
        self._handle = None
        
        if not pynvml:
            return

        try:
            pynvml.nvmlInit()
            self._available = True
        except pynvml.NVMLError:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def get_vram_usage(self, pid: int) -> float:
        """Returns VRAM usage in bytes for the given PID."""
        if not self._available:
            return 0.0
        
        try:
            # NVML allows getting compute processes for a device.
            # We must iterate all devices to find where the process is running.
            device_count = pynvml.nvmlDeviceGetCount()
            total_mem = 0
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # Get compute processes (games often show up here or graphics processes)
                try:
                    procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                    for p in procs:
                        if p.pid == pid:
                            # p.usedGpuMemory is in bytes
                            total_mem += (p.usedGpuMemory or 0)
                except pynvml.NVMLError:
                    pass
                    
                # Also check graphics processes (for some games)
                try:
                    procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)
                    for p in procs:
                        if p.pid == pid:
                            total_mem += (p.usedGpuMemory or 0)
                except pynvml.NVMLError:
                    pass
                    
            return float(total_mem)
            
        except pynvml.NVMLError:
            return 0.0

    def shutdown(self):
        if self._available:
            try:
                pynvml.nvmlShutdown()
            except pynvml.NVMLError:
                pass

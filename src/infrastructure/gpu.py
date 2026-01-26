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
        # Method 1: NVML
        vram_nvml = 0.0
        if self._available:
            try:
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    
                    # Compute
                    try:
                        procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                        for p in procs:
                            if p.pid == pid:
                                vram_nvml += (p.usedGpuMemory or 0)
                    except pynvml.NVMLError:
                        pass
                        
                    # Graphics
                    try:
                        procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle)
                        for p in procs:
                            if p.pid == pid:
                                vram_nvml += (p.usedGpuMemory or 0)
                    except pynvml.NVMLError:
                        pass
            except pynvml.NVMLError:
                pass

        if vram_nvml > 0:
            return float(vram_nvml)
            
        # Method 2: Windows Performance Counters (PDH) via typeperf
        # Fallback for WDDM/Windows where NVML might not expose process memory
        return self._get_vram_from_pdh(pid)

    def _get_vram_from_pdh(self, pid: int) -> float:
        try:
            import subprocess
            # Query "GPU Process Memory" for the PID instance (local usage = dedicated/VRAM)
            # Wildcard 'pid_PID*' matches the instance name which includes LUID
            cmd = f'typeperf "\\GPU Process Memory(pid_{pid}*)\\Local Usage" -sc 1 -y'
            
            # Use CREATE_NO_WINDOW to hide console window
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            output = subprocess.check_output(cmd, startupinfo=startupinfo, text=True, stderr=subprocess.DEVNULL)
            
            # Parse CSV output
            # "(PDH-CSV 4.0)","..."
            # "timestamp","value"
            lines = output.strip().splitlines()
            if len(lines) >= 2:
                parts = lines[1].split(',')
                if len(parts) >= 2:
                    val_str = parts[-1].replace('"', '')
                    return float(val_str)
        except Exception:
            pass
            
        return 0.0

    def shutdown(self):
        if self._available:
            try:
                pynvml.nvmlShutdown()
            except pynvml.NVMLError:
                pass

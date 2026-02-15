"""GPU infrastructure services."""

from typing import Any

_pynvml: Any = None
try:
    import pynvml as imported_pynvml
    _pynvml = imported_pynvml
except ImportError:
    pass

pynvml: Any = _pynvml

from domain.services import IGpuService


class NvidiaGpuService(IGpuService):
    def __init__(self):
        self._available = False
        self._nvml: Any | None = None

        if pynvml is None:
            return
        self._nvml = pynvml

        try:
            self._nvml.nvmlInit()
            self._available = True
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        """Return True if NVIDIA GPU monitoring is available."""
        return self._available

    def shutdown(self) -> None:
        """Shutdown the NVML library."""
        if self._available and self._nvml is not None:
            try:
                self._nvml.nvmlShutdown()
            except Exception:
                pass

    def get_system_vram_usage(self) -> tuple[float, float]:
        """Return (used_bytes, total_bytes) for all NVIDIA GPUs."""
        if not self._available or self._nvml is None:
            return 0.0, 0.0

        total_used = 0.0
        total_memory = 0.0

        try:
            device_count = self._nvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = self._nvml.nvmlDeviceGetHandleByIndex(i)
                mem = self._nvml.nvmlDeviceGetMemoryInfo(handle)
                total_used += mem.used
                total_memory += mem.total
        except Exception:
            pass

        return total_used, total_memory

    def get_system_gpu_temperature(self) -> float | None:
        """Return the temperature of the primary NVIDIA GPU in Celsius."""
        if not self._available or self._nvml is None:
            return None
        try:
            handle = self._nvml.nvmlDeviceGetHandleByIndex(0)
            return float(self._nvml.nvmlDeviceGetTemperature(handle, self._nvml.NVML_TEMPERATURE_GPU))
        except Exception:
            return None

    def get_system_gpu_usage(self) -> float | None:
        """Return the utilization percentage of the primary NVIDIA GPU."""
        if not self._available or self._nvml is None:
            return None
        try:
            handle = self._nvml.nvmlDeviceGetHandleByIndex(0)
            rates = self._nvml.nvmlDeviceGetUtilizationRates(handle)
            return float(rates.gpu)
        except Exception:
            return None

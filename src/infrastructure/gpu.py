"""GPU infrastructure services."""


try:
    import pynvml
except ImportError:
    pynvml = None

from domain.services import IGpuService


class NvidiaGpuService(IGpuService):
    def __init__(self):
        self._available = False

        if not pynvml:
            return

        try:
            pynvml.nvmlInit()
            self._available = True
        except pynvml.NVMLError:
            self._available = False

    def is_available(self) -> bool:
        """Return True if NVIDIA GPU monitoring is available."""
        return self._available

    def shutdown(self) -> None:
        """Shutdown the NVML library."""
        if self._available:
            try:
                pynvml.nvmlShutdown()
            except pynvml.NVMLError:
                pass

    def get_system_vram_usage(self) -> tuple[float, float]:
        """Return (used_bytes, total_bytes) for all NVIDIA GPUs."""
        if not self._available:
            return 0.0, 0.0

        total_used = 0.0
        total_memory = 0.0

        try:
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_used += mem.used
                total_memory += mem.total
        except pynvml.NVMLError:
            pass

        return total_used, total_memory

    def get_system_gpu_temperature(self) -> float | None:
        """Return the temperature of the primary NVIDIA GPU in Celsius."""
        if not self._available:
            return None
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            return float(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
        except (pynvml.NVMLError, IndexError):
            return None

    def get_system_gpu_usage(self) -> float | None:
        """Return the utilization percentage of the primary NVIDIA GPU."""
        if not self._available:
            return None
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return float(rates.gpu)
        except (pynvml.NVMLError, IndexError):
            return None

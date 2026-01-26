
import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock pynvml before importing infrastructure.gpu
# We need to ensure we can import the module even if pynvml is missing in the test environment (though we added it)
# But for unit tests, we want to mock its behavior.

class TestNvidiaGpuService(unittest.TestCase):
    def setUp(self):
        # We'll patch pynvml in each test or setup
        pass

    def test_initialization_success(self):
        with patch('infrastructure.gpu.pynvml') as mock_nvml:
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService()
            mock_nvml.nvmlInit.assert_called_once()
            self.assertTrue(service.is_available())

    def test_initialization_failure(self):
        with patch('infrastructure.gpu.pynvml') as mock_nvml:
            # Simulate import success but init failure
            mock_nvml.nvmlInit.side_effect = Exception("Init failed") # Actually NVMLError but generic exception works for now if code catches specific?
            # Code catches pynvml.NVMLError. We need to match that.
            # We can mock NVMLError class on the mock object.
            
            # Better approach:
            # The module 'infrastructure.gpu' imports pynvml.
            # If we patch 'infrastructure.gpu.pynvml', we control it.
            # We need to ensure infrastructure.gpu has pynvml.NVMLError available.
            
            # Let's assume proper mocking of the exception class is needed.
            mock_nvml.NVMLError = Exception
            mock_nvml.nvmlInit.side_effect = mock_nvml.NVMLError
            
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService()
            self.assertFalse(service.is_available())

    def test_get_vram_usage_success(self):
        with patch('infrastructure.gpu.pynvml') as mock_nvml:
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService() # Init success
            
            # Setup mock devices
            mock_nvml.nvmlDeviceGetCount.return_value = 1
            handle = MagicMock()
            mock_nvml.nvmlDeviceGetHandleByIndex.return_value = handle
            
            # Compute Procs
            proc1 = MagicMock()
            proc1.pid = 123
            proc1.usedGpuMemory = 1024 * 1024 * 1024 # 1GB
            mock_nvml.nvmlDeviceGetComputeRunningProcesses.return_value = [proc1]
            
            # Graphics Procs
            mock_nvml.nvmlDeviceGetGraphicsRunningProcesses.return_value = []
            
            usage = service.get_vram_usage(123)
            self.assertEqual(usage, 1073741824.0)

    def test_get_vram_usage_not_available(self):
        with patch('infrastructure.gpu.pynvml') as mock_nvml:
            mock_nvml.nvmlInit.side_effect = Exception("Fail")
            mock_nvml.NVMLError = Exception
            
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService()
            self.assertEqual(service.get_vram_usage(123), 0.0)

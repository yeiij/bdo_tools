
import unittest
from unittest.mock import MagicMock, patch


class TestNvidiaGpuService(unittest.TestCase):
    def setUp(self):
        pass

    def test_initialization_success(self):
        with patch('infrastructure.gpu.pynvml') as mock_nvml:
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService()
            mock_nvml.nvmlInit.assert_called_once()
            self.assertTrue(service.is_available())

    def test_initialization_failure(self):
        with patch('infrastructure.gpu.pynvml') as mock_nvml:
            mock_nvml.NVMLError = Exception
            mock_nvml.nvmlInit.side_effect = mock_nvml.NVMLError
            
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService()
            self.assertFalse(service.is_available())




    def test_get_system_vram_usage(self):
        with patch('infrastructure.gpu.pynvml') as mock_nvml:
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService()
            
            mock_nvml.nvmlDeviceGetCount.return_value = 2
            
            # Setup handle mocks
            h1 = MagicMock()
            h2 = MagicMock()
            mock_nvml.nvmlDeviceGetHandleByIndex.side_effect = [h1, h2]
            
            # Setup memory info mocks
            mem1 = MagicMock()
            mem1.used = 2 * 1024**3
            mem1.total = 8 * 1024**3
            
            mem2 = MagicMock()
            mem2.used = 1 * 1024**3
            mem2.total = 8 * 1024**3
            
            mock_nvml.nvmlDeviceGetMemoryInfo.side_effect = [mem1, mem2]
            
            used, total = service.get_system_vram_usage()
            self.assertEqual(used, 3 * 1024**3)
            self.assertEqual(total, 16 * 1024**3)

    def test_shutdown_not_available(self):
        # Branch 32: Test shutdown when GPU not available (early return)
        with patch('infrastructure.gpu.pynvml'):
            from infrastructure.gpu import NvidiaGpuService
            service = NvidiaGpuService()
            service._available = False
            service.shutdown()  # Should do nothing when not available

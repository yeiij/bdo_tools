
import unittest
from unittest.mock import MagicMock, patch
from ui.viewmodels.main_viewmodel import MainViewModel
from domain.models import AppSettings, ConnectionInfo, ProcessStatus

class TestMainViewModel(unittest.TestCase):
    def setUp(self):
        self.mock_process = MagicMock()
        self.mock_network = MagicMock()
        self.settings = AppSettings("Test.exe", [])
        
        # Setup default mock behavior
        self.mock_process.is_admin.return_value = True
        self.mock_process.get_memory_usage.return_value = 0
        self.mock_process.get_cpu_percent.return_value = 0.0
        self.mock_process.get_system_memory.return_value = (8*1024**3, 16*1024**3)
        self.mock_process.get_system_cpu.return_value = 25.0
        self.mock_process.get_system_cpu_temperature.return_value = 45.0
        
        # Patch GPU Service
        patcher = patch('ui.viewmodels.main_viewmodel.NvidiaGpuService')
        self.MockGpuService = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_gpu = self.MockGpuService.return_value
        self.mock_gpu.is_available.return_value = True
        self.mock_gpu.get_system_vram_usage.return_value = (4*1024**3, 8*1024**3)
        self.mock_gpu.get_system_gpu_temperature.return_value = 55.0
        self.mock_gpu.get_system_gpu_usage.return_value = 50.0
        
        self.vm = MainViewModel(self.mock_process, self.mock_network, self.settings)

    def test_initial_state(self):
        self.assertEqual(self.vm.status, ProcessStatus.UNKNOWN)
        self.assertTrue(self.vm.is_admin)

    def test_refresh_running(self):
        # Setup mocks
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING
        self.mock_process.get_pid.return_value = 1234
        self.mock_process.get_priority.return_value = "Normal"
        self.mock_process.get_affinity.return_value = [0, 1, 2, 3]
        self.mock_process.get_memory_usage.return_value = 1073741824 # 1 GB
        self.mock_process.get_cpu_percent.return_value = 12.5
        
        conn = ConnectionInfo(
            pid=1234,
            local_ip="1.1.1.1", 
            local_port=100, 
            remote_ip="2.2.2.2", 
            remote_port=8888, 
            status="EST", 
            service_name="Game Server", 
            latency_ms=50.0
        )
        self.mock_network.get_connections.return_value = [conn]
        
        # Action (Call twice because network is throttled to every 2nd refresh)
        self.vm.refresh()
        self.vm.refresh()
        
        # Assert
        self.assertEqual(self.vm.status, ProcessStatus.RUNNING)
        self.assertEqual(self.vm.pid, 1234)
        self.assertEqual(self.vm.game_latency, 50.0)
        self.assertEqual(len(self.vm.connections), 1)
        self.assertEqual(self.vm.ram_used_str, "8GB")
        self.assertEqual(self.vm.cpu_usage_str, "25%")
        self.assertEqual(self.vm.vram_display_str, "4GB")
        self.assertEqual(self.vm.gpu_usage_str, "50%")

    def test_refresh_not_running(self):
        self.mock_process.get_status.return_value = ProcessStatus.NOT_RUNNING
        self.mock_process.get_pid.return_value = None
        
        self.vm.refresh()
        
        self.assertEqual(self.vm.status, ProcessStatus.NOT_RUNNING)
        self.assertIsNone(self.vm.pid)
        self.assertEqual(self.vm.connections, [])

    def test_refresh_throttling_logic(self):
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING
        self.mock_process.get_pid.return_value = 123
        self.mock_network.get_connections.return_value = []
        
        # 1st refresh: count=1, 1%2 != 0 -> No network poll
        self.vm.refresh()
        self.mock_network.get_connections.assert_not_called()
        
        # 2nd refresh: count=2, 2%2 == 0 -> Network poll
        self.vm.refresh()
        self.mock_network.get_connections.assert_called_once()

    def test_exitlag_annotation(self):
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING
        self.mock_process.get_pid.return_value = 123
        
        
        # Case 1: Dynamic Port (Localhost + Random High Port)
        conn1 = ConnectionInfo(123, "127.0.0.1", 50000, "127.0.0.1", 53600, "EST", "Unknown") # ExitLag
        # Case 2: Standard Localhost (Web/Auth) -> Should remain IP
        conn2 = ConnectionInfo(123, "127.0.0.1", 50000, "127.0.0.1", 443, "EST", "Web") # Not ExitLag
        # Case 3: Legacy Fixed Port
        conn3 = ConnectionInfo(123, "127.0.0.1", 50000, "10.0.0.5", 60774, "EST", "Old") # Legacy
        
        self.mock_network.get_connections.return_value = [conn1, conn2, conn3]
        
        # Refresh 2 times to trigger network update
        self.vm.refresh()
        self.vm.refresh()
        
        self.assertEqual(self.vm.connections[0].remote_ip, "ExitLag")
        self.assertEqual(self.vm.connections[0].service_name, "Game Server")
        
        self.assertEqual(self.vm.connections[1].remote_ip, "127.0.0.1")
        self.assertNotEqual(self.vm.connections[1].service_name, "Game Server")
        
        self.assertEqual(self.vm.connections[2].remote_ip, "ExitLag")
        self.assertEqual(self.vm.connections[2].service_name, "Game Server")

    def test_priority_watchdog(self):
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING
        self.vm.target_priority = "High"
        self.vm.priority = "Normal" # Drift
        
        self.vm.refresh()
        
        self.mock_process.set_priority.assert_called_with(self.settings.process_name, "High")

    def test_affinity_watchdog(self):
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING
        self.vm.target_affinity = [0, 1]
        self.vm.affinity = [0, 1, 2, 3] # Drift
        
        self.vm.refresh()
        
        self.mock_process.set_affinity.assert_called_with(self.settings.process_name, [0, 1])

    def test_set_manual_priority(self):
        with patch.object(self.settings, 'save') as mock_save:
            self.vm.set_manual_priority("High")
            self.assertEqual(self.vm.target_priority, "High")
            self.assertEqual(self.settings.target_priority, "High")
            mock_save.assert_called_once()
            self.mock_process.set_priority.assert_called_with(self.settings.process_name, "High")

    def test_set_affinity_success(self):
        self.vm.pid = 123
        self.mock_process.set_affinity.return_value = True
        with patch.object(self.settings, 'save') as mock_save:
            result = self.vm.set_affinity([2, 3])
            self.assertTrue(result)
            self.assertEqual(self.settings.target_affinity, [2, 3])
            self.assertEqual(self.vm.target_affinity, [2, 3]) # Verify runtime update
            mock_save.assert_called_once()

    def test_set_affinity_no_pid(self):
        self.vm.pid = None
        result = self.vm.set_affinity([0])
        self.assertFalse(result)

    def test_viewmodel_properties(self):
        # Line 54, 59, 63 coverage
        with patch('ui.viewmodels.main_viewmodel.NvidiaGpuService') as MockGpu:
            MockGpu.return_value.is_available.return_value = True
            
            vm = MainViewModel(self.mock_process, self.mock_network, self.settings)
            vm.vram_used_str = "4GB"
            vm._cpu_temp_str = "45°C"
            vm._gpu_temp_str = "50°C"
            
            self.assertEqual(vm.vram_display_str, "4GB")
            self.assertEqual(vm.cpu_temp_str, "45°C")
            self.assertEqual(vm.gpu_temp_str, "50°C")
            
            # Line 92-94 (GPU unavailable during refresh)
            MockGpu.return_value.is_available.return_value = False
            self.assertEqual(vm.vram_display_str, "N/A")

    def test_refresh_gpu_unavailable(self):
        # Explicit test for lines 92-94
        self.mock_gpu.is_available.return_value = False
        self.vm.refresh()
        self.assertEqual(self.vm.vram_used_str, "0GB")
        self.assertEqual(self.vm.vram_total_label, "/0GB vRAM")
        self.assertEqual(self.vm.gpu_usage_str, "0%")


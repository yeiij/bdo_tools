
import unittest
from unittest.mock import MagicMock, patch

from domain.models import AppSettings, ConnectionInfo, ProcessStatus
from ui.viewmodels.main_viewmodel import MainViewModel


class TestMainViewModel(unittest.TestCase):
    def setUp(self):
        self.mock_process = MagicMock()
        self.mock_network = MagicMock()
        self.mock_system = MagicMock()
        self.mock_gpu = MagicMock()
        self.settings = AppSettings(game_process_name="Test.exe", game_target_affinity=[])
        
        # Setup process service mock behavior
        self.mock_process.is_admin.return_value = True
        self.mock_process.get_memory_usage.return_value = 0
        self.mock_process.get_cpu_percent.return_value = 0.0
        
        # Setup system service mock behavior
        self.mock_system.get_cpu_count.return_value = 16
        self.mock_system.get_system_memory.return_value = (8*1024**3, 16*1024**3)
        self.mock_system.get_system_cpu.return_value = 25.0
        self.mock_system.get_system_cpu_temperature.return_value = 45.0
        
        # Setup GPU service mock behavior
        self.mock_gpu.is_available.return_value = True
        self.mock_gpu.get_system_vram_usage.return_value = (4*1024**3, 8*1024**3)
        self.mock_gpu.get_system_gpu_temperature.return_value = 55.0
        self.mock_gpu.get_system_gpu_usage.return_value = 50.0
        
        self.vm = MainViewModel(
            self.mock_process,
            self.mock_network,
            self.mock_system,
            self.mock_gpu,
            self.settings,
            persist_settings_on_init=False,
        )

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
        
        def pid_for_name(name):
            if name == self.settings.game_process_name:
                return 123
            if name == self.settings.network_process_name:
                return 999
            return None

        self.mock_process.get_pid.side_effect = pid_for_name
        
        
        # Case 1: Dynamic Port (Localhost + Random High Port) -> ExitLag
        conn1 = ConnectionInfo(123, "127.0.0.1", 50000, "127.0.0.1", 53600, "EST", "Unknown")
        # Case 2: Standard Localhost (Web/Auth on port 443) -> Should remain IP
        conn2 = ConnectionInfo(123, "127.0.0.1", 50000, "127.0.0.1", 443, "EST", "Web")
        # Case 3: NOT localhost, so no ExitLag annotation
        conn3 = ConnectionInfo(123, "127.0.0.1", 50000, "10.0.0.5", 60774, "EST", "Old")
        
        self.mock_network.get_connections.return_value = [conn1, conn2, conn3]
        
        # Refresh 2 times to trigger network update
        self.vm.refresh()
        self.vm.refresh()
        
        # Conn1: localhost with high port -> ExitLag
        self.assertEqual(self.vm.connections[0].remote_ip, "ExitLag")
        self.assertEqual(self.vm.connections[0].service_name, "Game Server")
        
        # Conn2: localhost but port 443 (not booster) -> keeps IP
        self.assertEqual(self.vm.connections[1].remote_ip, "127.0.0.1")
        self.assertEqual(self.vm.connections[1].service_name, "Web")
        
        # Conn3: NOT localhost -> no annotation, keeps original IP
        self.assertEqual(self.vm.connections[2].remote_ip, "10.0.0.5")
        self.assertEqual(self.vm.connections[2].service_name, "Old")

    def test_exitlag_annotation_requires_exitlag_running(self):
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING

        def pid_for_name(name):
            if name == self.settings.game_process_name:
                return 123
            if name == self.settings.network_process_name:
                return None
            return None

        self.mock_process.get_pid.side_effect = pid_for_name

        conn = ConnectionInfo(123, "127.0.0.1", 50000, "127.0.0.1", 53600, "EST", "Unknown")
        self.mock_network.get_connections.return_value = [conn]

        self.vm.refresh()
        self.vm.refresh()

        self.assertEqual(self.vm.connections[0].remote_ip, "127.0.0.1")
        self.assertEqual(self.vm.connections[0].service_name, "Unknown")

    def test_priority_watchdog(self):
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING
        self.vm.target_priority = "High"
        self.vm.priority = "Normal" # Drift
        
        self.vm.refresh()
        
        self.mock_process.set_priority.assert_called_with(self.settings.game_process_name, "High")

    def test_affinity_watchdog(self):
        self.mock_process.get_status.return_value = ProcessStatus.RUNNING
        self.vm.target_affinity = [0, 1]
        self.vm.affinity = [0, 1, 2, 3] # Drift
        
        self.vm.refresh()
        
        self.mock_process.set_affinity.assert_called_with(self.settings.game_process_name, [0, 1])

    def test_set_manual_priority(self):
        with patch.object(self.settings, 'save') as mock_save:
            self.mock_process.set_priority.return_value = True
            result = self.vm.set_manual_priority("High")
            self.assertTrue(result)
            self.assertEqual(self.vm.target_priority, "High")
            self.assertEqual(self.settings.game_target_priority, "High")
            mock_save.assert_called_once()
            self.mock_process.set_priority.assert_called_with(self.settings.game_process_name, "High")

    def test_set_manual_priority_failure(self):
        self.vm.target_priority = "Normal"
        self.settings.game_target_priority = "Normal"
        self.mock_process.set_priority.return_value = False

        with patch.object(self.settings, 'save') as mock_save:
            result = self.vm.set_manual_priority("High")
            self.assertFalse(result)
            self.assertEqual(self.vm.target_priority, "Normal")
            self.assertEqual(self.settings.game_target_priority, "Normal")
            mock_save.assert_not_called()

    def test_set_affinity_success(self):
        self.vm.pid = 123
        self.mock_process.set_affinity.return_value = True
        with patch.object(self.settings, 'save') as mock_save:
            result = self.vm.set_affinity([2, 3])
            self.assertTrue(result)
            self.assertEqual(self.settings.game_target_affinity, [2, 3])
            self.assertEqual(self.vm.target_affinity, [2, 3]) # Verify runtime update
            mock_save.assert_called_once()

    def test_set_affinity_no_pid(self):
        # When process service returns False (e.g., no PID), set_affinity should return False
        self.mock_process.set_affinity.return_value = False
        result = self.vm.set_affinity([0])
        self.assertFalse(result)

    def test_viewmodel_properties(self):
        # Test vram_display_str property with GPU available
        self.mock_gpu.is_available.return_value = True
        self.vm.vram_used_str = "4GB"
        self.assertEqual(self.vm.vram_display_str, "4GB")
        
        # Test vram_display_str property with GPU unavailable
        self.mock_gpu.is_available.return_value = False
        self.assertEqual(self.vm.vram_display_str, "N/A")
        
        # Reset and test temperature properties
        self.mock_gpu.is_available.return_value = True
        self.vm._cpu_temp_str = "45°C"
        self.vm._gpu_temp_str = "50°C"
        
        self.assertEqual(self.vm.cpu_temp_str, "45°C")
        self.assertEqual(self.vm.gpu_temp_str, "50°C")

    def test_refresh_gpu_unavailable(self):
        # Explicit test for lines 92-94
        self.mock_gpu.is_available.return_value = False
        self.vm.refresh()
        self.assertEqual(self.vm.vram_used_str, "0GB")
        self.assertEqual(self.vm.vram_total_label, "/0GB vRAM")
        self.assertEqual(self.vm.vram_total_label, "/0GB vRAM")
        self.assertEqual(self.vm.gpu_usage_str, "0%")

    def test_network_controls(self):
        # Setup Network Running
        self.vm.network_pid = 999 

        # Test Set Priority
        with patch.object(self.settings, 'save') as mock_save:
            self.mock_process.set_priority.return_value = True
            result = self.vm.set_network_manual_priority("High")
            self.assertTrue(result)
            
            self.assertEqual(self.vm.network_target_priority, "High")
            self.mock_process.set_priority.assert_called_with(self.settings.network_process_name, "High")
            mock_save.assert_called()
            
        # Test Set Affinity
        self.mock_process.set_affinity.return_value = True
        with patch.object(self.settings, 'save') as mock_save:
            self.vm.set_network_affinity([0, 1])
            
            self.assertEqual(self.vm.network_target_affinity, [0, 1])
            self.mock_process.set_affinity.assert_called_with(self.settings.network_process_name, [0, 1])
            mock_save.assert_called()

    def test_set_network_manual_priority_failure(self):
        self.vm.network_target_priority = "Normal"
        self.settings.network_target_priority = "Normal"
        self.mock_process.set_priority.return_value = False

        with patch.object(self.settings, 'save') as mock_save:
            result = self.vm.set_network_manual_priority("High")
            self.assertFalse(result)
            self.assertEqual(self.vm.network_target_priority, "Normal")
            self.assertEqual(self.settings.network_target_priority, "Normal")
            mock_save.assert_not_called()
            
    def test_network_enforcement(self):
        self.vm.status = ProcessStatus.RUNNING
        self.vm.network_pid = 999
        self.vm.network_priority = "Normal"
        self.vm.network_target_priority = "High"
        
        # Trigger enforcement via the private method
        self.vm._enforce_active_policies()
        
        self.mock_process.set_priority.assert_called_with(self.settings.network_process_name, "High")


    def test_is_network_active_property(self):
        # Line 198 coverage:  Test is_network_active property
        from domain.models import ConnectionInfo
        conn1 = ConnectionInfo(123, '127.0.0.1', 50000, 'ExitLag', 53600, 'EST', 'Game Server')
        conn2 = ConnectionInfo(123, '127.0.0.1', 50001, '8.8.8.8', 443, 'EST', 'Web')
        self.vm.connections = [conn1, conn2]
        self.assertTrue(self.vm.is_network_active)
        self.vm.connections = [conn2]
        self.assertFalse(self.vm.is_network_active)

    def test_set_network_affinity_failure(self):
        # Line 227 coverage: Test set_network_affinity when set_affinity fails
        self.mock_process.set_affinity.return_value = False
        result = self.vm.set_network_affinity([0, 1])
        self.assertFalse(result)

    def test_game_latency_prefers_direct_over_exitlag(self):
        self.vm.pid = 123
        self.vm.connections = [
            ConnectionInfo(123, "127.0.0.1", 50000, "ExitLag", 53600, "EST", "Game Server", latency_ms=1.0),
            ConnectionInfo(123, "127.0.0.1", 50001, "10.0.0.5", 60774, "EST", "Game Server", latency_ms=25.0),
        ]
        self.vm._calculate_derived_metrics()
        self.assertEqual(self.vm.game_latency, 25.0)

    def test_game_latency_keeps_last_value_when_temporarily_missing(self):
        self.vm.pid = 123
        self.vm.connections = [
            ConnectionInfo(123, "127.0.0.1", 50001, "10.0.0.5", 60774, "EST", "Game Server", latency_ms=25.0),
        ]
        self.vm._calculate_derived_metrics()
        self.assertEqual(self.vm.game_latency, 25.0)

        self.vm.connections = []
        self.vm._calculate_derived_metrics()
        self.assertEqual(self.vm.game_latency, 25.0)

    def test_game_latency_ignores_near_zero_proxy_when_exitlag_active(self):
        self.vm.pid = 123
        self.vm.network_pid = 999
        self.vm.connections = [
            ConnectionInfo(123, "127.0.0.1", 50000, "ExitLag", 53600, "EST", "Game Server", latency_ms=1.0),
            ConnectionInfo(123, "127.0.0.1", 50001, "ExitLag", 53601, "EST", "Game Server", latency_ms=25.0),
        ]
        self.vm._calculate_derived_metrics()
        self.assertEqual(self.vm.game_latency, 25.0)

    def test_game_latency_prefers_exitlag_process_external_links(self):
        self.vm.pid = 123
        self.vm.network_pid = 999
        self.vm.connections = [
            ConnectionInfo(123, "127.0.0.1", 50000, "ExitLag", 53600, "EST", "Game Server", latency_ms=1.0),
            ConnectionInfo(123, "127.0.0.1", 50001, "ExitLag", 53601, "EST", "Game Server", latency_ms=10.0),
        ]
        self.vm.network_connections = [
            ConnectionInfo(999, "10.0.0.3", 52000, "45.223.19.187", 60774, "EST", "Unknown", latency_ms=25.0),
            ConnectionInfo(999, "10.0.0.3", 52001, "45.223.19.188", 60774, "EST", "Unknown", latency_ms=27.0),
        ]
        self.vm._calculate_derived_metrics()
        self.assertEqual(self.vm.game_latency, 27.0)

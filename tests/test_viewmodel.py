
import unittest
from unittest.mock import MagicMock
from ui.viewmodels.main_viewmodel import MainViewModel
from domain.models import AppSettings, ConnectionInfo, ProcessStatus

class TestMainViewModel(unittest.TestCase):
    def setUp(self):
        self.mock_process = MagicMock()
        self.mock_network = MagicMock()
        self.settings = AppSettings("Test.exe", [])
        
        # Setup default mock behavior
        self.mock_process.is_admin.return_value = True
        
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
        
        conn = ConnectionInfo(
            pid=1234,
            local_ip="1.1.1.1", 
            local_port=100, 
            remote_ip="2.2.2.2", 
            remote_port=8888, 
            status="EST", 
            service_name="Game", 
            latency_ms=50.0
        )
        self.mock_network.get_connections.return_value = [conn]
        
        # Action
        self.vm.refresh()
        
        # Assert
        self.assertEqual(self.vm.status, ProcessStatus.RUNNING)
        self.assertEqual(self.vm.pid, 1234)
        self.assertEqual(self.vm.game_latency, 50.0)
        self.assertEqual(len(self.vm.connections), 1)

    def test_refresh_not_running(self):
        self.mock_process.get_status.return_value = ProcessStatus.NOT_RUNNING
        self.mock_process.get_pid.return_value = None
        
        self.vm.refresh()
        
        self.assertEqual(self.vm.status, ProcessStatus.NOT_RUNNING)
        self.assertIsNone(self.vm.pid)
        self.assertEqual(self.vm.connections, [])

    def test_optimize_success(self):
        self.vm.pid = 1234 # Must be set to allow optimization
        self.mock_process.set_priority.return_value = True
        self.mock_process.set_affinity.return_value = True
        
        # Mock psutil.cpu_count for affinity logic
        # Since the code imports psutil inside the method, patching psutil.cpu_count visible to that import is tricky
        # if the test runner has already imported psutil.
        # But usually patch('psutil.cpu_count') works if we do it globally.
        
        from unittest.mock import patch
        with patch('psutil.cpu_count', return_value=8):
            result = self.vm.optimize_process()
            self.assertTrue(result)
            self.mock_process.set_priority.assert_called_with("Test.exe", high=True)
            self.mock_process.set_affinity.assert_called()

    def test_optimize_fail_no_pid(self):
        self.vm.pid = None
        result = self.vm.optimize_process()
        self.assertFalse(result)

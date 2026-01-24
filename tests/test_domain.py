
import unittest
from domain.models import ConnectionInfo, ProcessStatus, AppSettings

class TestDomainModels(unittest.TestCase):
    def test_connection_info_initialization(self):
        conn = ConnectionInfo(
            pid=1000,
            local_ip="127.0.0.1",
            local_port=1234,
            remote_ip="8.8.8.8",
            remote_port=443,
            status="ESTABLISHED",
            service_name="Web",
            latency_ms=15.5
        )
        self.assertEqual(conn.local_ip, "127.0.0.1")
        self.assertEqual(conn.latency_ms, 15.5)

    def test_app_settings(self):
        settings = AppSettings(process_name="Test.exe", poll_interval_ms=5000)
        self.assertEqual(settings.process_name, "Test.exe")
        self.assertEqual(settings.poll_interval_ms, 5000)

    def test_process_status_enum(self):
        self.assertIsInstance(ProcessStatus.RUNNING, ProcessStatus)
        self.assertNotEqual(ProcessStatus.RUNNING, ProcessStatus.NOT_RUNNING)

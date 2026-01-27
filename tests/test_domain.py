
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

    def test_app_settings_save_load(self):
        import os
        test_path = "test_settings.json"
        try:
            settings = AppSettings(process_name="NewProcess.exe", poll_interval_ms=1234)
            settings.save(test_path)
            
            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.process_name, "NewProcess.exe")
            self.assertEqual(loaded.poll_interval_ms, 1234)
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_load_invalid_json(self):
        import os
        test_path = "invalid.json"
        try:
            with open(test_path, "w") as f:
                f.write("{invalid: json}")
            
            loaded = AppSettings.load(test_path)
            # Should return defaults
            self.assertEqual(loaded.process_name, "BlackDesert64.exe")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_load_not_exists(self):
        loaded = AppSettings.load("non_existent.json")
        self.assertEqual(loaded.process_name, "BlackDesert64.exe")

    def test_app_settings_save_error(self):
        # Test saving to a directory or invalid path to trigger exception
        settings = AppSettings()
        # This might not raise on all systems depending on permissions, 
        # but we can try an empty filename or similar
        settings.save("") # Should fail silently as per code

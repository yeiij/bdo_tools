import unittest
from unittest.mock import patch

from domain.models import AppSettings, ConnectionInfo


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
            settings = AppSettings(game_process_name="NewProcess.exe", poll_interval_ms=1234)
            settings.save(test_path)
            
            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.game_process_name, "NewProcess.exe")
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
            self.assertEqual(loaded.game_process_name, "BlackDesert64.exe")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_load_not_exists(self):
        loaded = AppSettings.load("non_existent.json")
        self.assertEqual(loaded.game_process_name, "BlackDesert64.exe")

    def test_app_settings_load_legacy_keys(self):
        # Test that old key names get mapped to new key names (covers lines 74-76)
        import os
        test_path = "legacy_settings.json"
        try:
            # Create JSON with old key names
            with open(test_path, "w") as f:
                f.write('{"process_name": "OldGame.exe", "target_priority": "High", '
                       '"exitlag_process_name": "OldExitLag.exe"}')
            
            loaded = AppSettings.load(test_path)
            # Verify old keys mapped to new keys
            self.assertEqual(loaded.game_process_name, "OldGame.exe")
            self.assertEqual(loaded.game_target_priority, "High")
            self.assertEqual(loaded.network_process_name, "OldExitLag.exe")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_save_default_path(self):
        settings = AppSettings()
        with patch.object(AppSettings, "default_path", return_value="test_default_settings.json"):
            settings.save()
            loaded = AppSettings.load("test_default_settings.json")
            self.assertEqual(loaded.game_process_name, "BlackDesert64.exe")
        import os
        if os.path.exists("test_default_settings.json"):
            os.remove("test_default_settings.json")
    def test_app_settings_load_legacy_keys_no_overwrite(self):
        # Test branch 75: when new key already exists, don't overwrite
        import os
        test_path = 'legacy_no_overwrite.json'
        try:
            # JSON has both old and new keys - new key should win
            with open(test_path, 'w') as f:
                f.write('{\"process_name\": \"Old.exe\", \"game_process_name\": \"New.exe\"}')
            loaded = AppSettings.load(test_path)
            # Should keep new key value, not overwrite with old
            self.assertEqual(loaded.game_process_name, 'New.exe')
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

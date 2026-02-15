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
            settings = AppSettings(game_process_name="NewProcess.exe", interval=1234)
            settings.save(test_path)
            
            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.game_process_name, "NewProcess.exe")
            self.assertEqual(loaded.interval, 1234)
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

    def test_app_settings_load_legacy_keys_ignored(self):
        import os
        test_path = "legacy_settings.json"
        try:
            with open(test_path, "w") as f:
                f.write('{"process_name": "OldGame.exe", "target_priority": "High", '
                       '"exitlag_process_name": "OldExitLag.exe"}')
            
            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.game_process_name, "BlackDesert64.exe")
            self.assertIsNone(loaded.game_target_priority)
            self.assertEqual(loaded.network_process_name, "ExitLag.exe")
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
    def test_app_settings_load_legacy_keys_do_not_override_targets(self):
        import os
        test_path = 'legacy_no_overwrite.json'
        try:
            with open(test_path, 'w') as f:
                f.write(
                    '{"process_name":"Old.exe","targets":['
                    '{"process":"New.exe","role":"game","priority":"High","affinity":[2,3]},'
                    '{"process":"ExitLag.exe","role":"network","priority":"Normal","affinity":[0,1]}]}'
                )
            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.game_process_name, 'New.exe')
            self.assertEqual(loaded.game_target_priority, 'High')
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_save_uses_targets_schema(self):
        import os
        test_path = "targets_schema.json"
        try:
            settings = AppSettings(
                game_process_name="BlackDesert64.exe",
                network_process_name="ExitLag.exe",
                game_target_priority="High",
                game_target_affinity=[2, 3],
                network_target_priority="Above Normal",
                network_target_affinity=[0, 1],
            )
            settings.save(test_path)
            with open(test_path, encoding="utf-8") as f:
                data = __import__("json").load(f)

            self.assertIn("targets", data)
            self.assertNotIn("network_process_name", data)
            self.assertEqual(data["targets"][0]["process"], "BlackDesert64.exe")
            self.assertEqual(data["targets"][1]["process"], "ExitLag.exe")
            self.assertEqual(data["targets"][0]["role"], "game")
            self.assertEqual(data["targets"][1]["role"], "network")
            self.assertEqual(data["targets"][0]["priority"], "High")
            self.assertEqual(data["targets"][1]["priority"], "Above Normal")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_load_targets_schema(self):
        import os
        test_path = "targets_load.json"
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(
                    '{"interval":4000,"theme":"dark","targets":['
                    '{"process":"BlackDesert64.exe","role":"game","priority":"High","affinity":[2,3]},'
                    '{"process":"ExitLag.exe","role":"network","priority":"Above Normal","affinity":[0,1]}]}'
                )

            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.game_process_name, "BlackDesert64.exe")
            self.assertEqual(loaded.network_process_name, "ExitLag.exe")
            self.assertEqual(loaded.game_target_priority, "High")
            self.assertEqual(loaded.network_target_priority, "Above Normal")
            self.assertEqual(loaded.game_target_affinity, [2, 3])
            self.assertEqual(loaded.network_target_affinity, [0, 1])
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_load_targets_schema_by_role_over_position(self):
        import os
        test_path = "targets_by_role.json"
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(
                    '{"interval":4000,"theme":"dark","targets":['
                    '{"process":"ExitLag.exe","role":"network","priority":"Above Normal","affinity":[0,1]},'
                    '{"process":"BlackDesert64.exe","role":"game","priority":"High","affinity":[2,3]},'
                    '{"process":"Discord.exe","role":"other","priority":null,"affinity":null}'
                    ']}'
                )

            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.game_process_name, "BlackDesert64.exe")
            self.assertEqual(loaded.network_process_name, "ExitLag.exe")
            self.assertEqual(loaded.other_targets[0]["process"], "Discord.exe")
            self.assertEqual(loaded.other_targets[0]["role"], "other")
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_load_targets_requires_process_key(self):
        import os
        test_path = "targets_requires_process_key.json"
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(
                    '{"interval":4000,"theme":"dark","targets":['
                    '{"process":"BlackDesert64.exe","role":"game","priority":"High","affinity":[2,3]},'
                    '{"process":"ExitLag.exe","role":"NETWORK","priority":"Above Normal","affinity":[0,1]},'
                    '{"process_name":"Discord.exe","role":"other","priority":"Below Normal","affinity":[4,5]}'
                    ']}'
                )

            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.game_process_name, "BlackDesert64.exe")
            self.assertEqual(loaded.network_process_name, "ExitLag.exe")
            self.assertEqual(loaded.other_targets, [])
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_app_settings_ignores_extra_target_fields(self):
        import os
        import json
        test_path = "targets_ignore_extra_fields.json"
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(
                    '{"interval":4000,"theme":"dark","targets":['
                    '{"process":"BlackDesert64.exe","role":"game","priority":"High","affinity":[2,3],"extra":"x"},'
                    '{"process":"ExitLag.exe","role":"network","priority":"Above Normal","affinity":[0,1],"foo":123},'
                    '{"process":"Discord.exe","role":"other","priority":"Below Normal","affinity":[4,5],"bar":{"x":1}}'
                    ']}'
                )

            loaded = AppSettings.load(test_path)
            self.assertEqual(loaded.other_targets[0], {
                "process": "Discord.exe",
                "role": "other",
                "priority": "Below Normal",
                "affinity": [4, 5],
            })

            loaded.save(test_path)
            with open(test_path, encoding="utf-8") as f:
                out = json.load(f)
            self.assertEqual(set(out["targets"][0].keys()), {"process", "role", "priority", "affinity"})
            self.assertEqual(set(out["targets"][1].keys()), {"process", "role", "priority", "affinity"})
            self.assertEqual(set(out["targets"][2].keys()), {"process", "role", "priority", "affinity"})
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

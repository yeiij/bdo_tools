"""Domain models."""

import json
import os
from dataclasses import asdict, dataclass
from enum import Enum, auto


class ProcessStatus(Enum):
    RUNNING = auto()
    NOT_RUNNING = auto()
    UNKNOWN = auto()


@dataclass
class ConnectionInfo:
    pid: int
    local_ip: str
    local_port: int
    remote_ip: str
    remote_port: int
    status: str
    service_name: str
    latency_ms: float | None = None


@dataclass
class AppSettings:
    game_process_name: str = "BlackDesert64.exe"
    network_process_name: str = "ExitLag.exe"
    poll_interval_ms: int = 4000
    theme: str = "dark"
    game_target_priority: str | None = None
    game_target_affinity: list[int] | None = None
    network_target_priority: str | None = None
    network_target_affinity: list[int] | None = None

    def save(self, path: str = "game.monitor.json"):
        """Save settings to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4)

    @classmethod
    def load(cls, path: str = "game.monitor.json") -> AppSettings:
        """Load settings from a JSON file."""
        data = {}
        # Try new path first, then fallback to old path for migration
        search_paths = [path, "bdo.monitor.json"]

        for p in search_paths:
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        data = json.load(f)
                    break  # Stop at first found file
                except Exception:
                    continue

        if data:
            # Mapping old keys to new keys for backward compatibility
            mapping = {
                "process_name": "game_process_name",
                "target_priority": "game_target_priority",
                "target_affinity": "game_target_affinity",
                "exitlag_process_name": "network_process_name",
                "exitlag_target_priority": "network_target_priority",
                "exitlag_target_affinity": "network_target_affinity",
            }

            # Apply mapping: move old key values to new keys if they exist
            for old, new in mapping.items():
                if old in data:
                    val = data.pop(old)
                    if new not in data:
                        data[new] = val

            # Enforce safety limits
            if "poll_interval_ms" in data:
                data["poll_interval_ms"] = max(data["poll_interval_ms"], 1000)

            # Filter keys to match dataclass fields
            valid_keys = cls.__dataclass_fields__.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered_data)

        return cls()

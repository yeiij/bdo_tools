"""Domain models."""

import json
from dataclasses import dataclass, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List


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
    latency_ms: Optional[float] = None


@dataclass
class AppSettings:
    process_name: str = "BlackDesert64.exe"
    poll_interval_ms: int = 5000
    theme: str = "dark"
    target_priority: Optional[str] = None
    target_affinity: Optional[List[int]] = None

    def save(self, path: str = "bdo.monitor.json"):
        """Save settings to a JSON file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=4)
        except Exception:
            pass # Fail silently for simplicity in this utility

    @classmethod
    def load(cls, path: str = "bdo.monitor.json") -> "AppSettings":
        """Load settings from a JSON file if it exists."""
        if Path(path).exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Filter keys to match dataclass fields
                    valid_keys = cls.__dataclass_fields__.keys()
                    filtered_data = {k: v for k, v in data.items() if k in valid_keys}
                    return cls(**filtered_data)
            except Exception:
                pass
        return cls()

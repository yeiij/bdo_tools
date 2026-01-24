"""Domain models."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class ProcessStatus(Enum):
    RUNNING = auto()
    NOT_RUNNING = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
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
    poll_interval_ms: int = 1000
    theme: str = "dark"

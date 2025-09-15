"""Application configuration helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Mapping


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the application."""

    process_name: str = "BlackDesert64.exe"
    port: int = 443
    refresh_ms: int = 2000
    poll_ms: int = 250

    _FIELD_TYPES: ClassVar[dict[str, type]] = {
        "process_name": str,
        "port": int,
        "refresh_ms": int,
        "poll_ms": int,
    }
    _ENV_TO_FIELD: ClassVar[dict[str, str]] = {
        "BDO_PROCESS_NAME": "process_name",
        "BDO_PORT": "port",
        "BDO_REFRESH_MS": "refresh_ms",
        "BDO_POLL_MS": "poll_ms",
    }

    @classmethod
    def load(
        cls,
        *,
        config_path: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> "Settings":
        """Load configuration from JSON file and environment variables."""

        env = os.environ if env is None else env

        values: dict[str, Any] = {}
        values.update(cls._load_from_file(config_path))
        values.update(cls._load_from_env(env))
        return cls(**values)

    @classmethod
    def _load_from_file(
        cls,
        config_path: str | Path | None,
    ) -> dict[str, Any]:
        candidates = cls._candidate_paths(config_path)
        for path in candidates:
            if not path.is_file():
                continue
            try:
                with path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path!s}: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError(f"Configuration file {path!s} must contain an object")
            return cls._filter_and_convert(data)
        return {}

    @classmethod
    def _load_from_env(cls, env: Mapping[str, str]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for env_key, field in cls._ENV_TO_FIELD.items():
            if env_key in env:
                values[field] = cls._convert_value(field, env[env_key])
        return values

    @classmethod
    def _filter_and_convert(cls, data: Mapping[str, Any]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for field, field_type in cls._FIELD_TYPES.items():
            if field in data:
                values[field] = cls._convert_value(field, data[field])
        return values

    @classmethod
    def _convert_value(cls, field: str, value: Any) -> Any:
        expected = cls._FIELD_TYPES[field]
        if expected is int:
            return cls._to_int(field, value)
        if expected is str:
            return cls._to_str(value)
        return value

    @staticmethod
    def _to_int(field: str, value: Any) -> int:
        if isinstance(value, bool):
            raise ValueError(f"Invalid boolean value for {field!r}")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if not value.is_integer():
                raise ValueError(f"Invalid non-integer number for {field!r}")
            return int(value)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError(f"Empty string is not a valid value for {field!r}")
            return int(value, 0)
        raise ValueError(f"Unsupported value for {field!r}: {value!r}")

    @staticmethod
    def _to_str(value: Any) -> str:
        if isinstance(value, (str, int, float)):
            return str(value)
        raise ValueError(f"Unsupported value for string field: {value!r}")

    @staticmethod
    def _candidate_paths(config_path: str | Path | None) -> list[Path]:
        if config_path is not None:
            return [Path(config_path)]

        candidates = []
        env_path = os.environ.get("BDO_CONFIG_FILE")
        if env_path:
            candidates.append(Path(env_path))
        candidates.append(Path.cwd() / "config.json")
        candidates.append(Path(__file__).resolve().with_name("config.json"))
        return candidates

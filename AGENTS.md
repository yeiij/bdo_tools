# AGENTS Guide

This repository is a Windows desktop monitor for Black Desert Online (BDO), built with Python and a hexagonal architecture.

## Scope

- App name: `GamerMonitor`
- Domain focus: process optimization + telemetry (CPU/GPU/RAM/VRAM + network latency)
- Primary target: Windows with optional ExitLag integration

## Architecture

- Entry point: `main.py`
- Core model/interfaces:
  - `src/domain/models.py`
  - `src/domain/services.py`
- Adapters:
  - `src/infrastructure/system.py` (`psutil`, process + system metrics)
  - `src/infrastructure/gpu.py` (`pynvml`)
  - `src/infrastructure/network.py` (TCP connection latency sampling)
- UI:
  - `src/ui/viewmodels/main_viewmodel.py`
  - `src/ui/views/main_window.py`

The `MainViewModel` is the main orchestration layer. UI should not directly depend on infrastructure implementations.

## Settings and Persistence

- Default settings file:
  - Windows: `%LOCALAPPDATA%/GamerMonitor/settings.json`
- Important:
  - The app does not overwrite an existing settings file on startup.
  - `MainViewModel(..., persist_settings_on_init=True)` writes settings on init.
  - In tests, use `persist_settings_on_init=False` to avoid writing test values to real config.
  - `targets` entries are strict and only support:
    - `process`
    - `role`
    - `priority`
    - `affinity`
  - Extra fields are ignored.

## Ping Logic (Current)

- Network adapter measures TCP connect-time (not ICMP).
- Ping source precedence:
  1. If the `network` role process is active: use its external connections (non-loopback), median latency.
  2. Otherwise use game connections classified as `Game Server`.
  3. Keep last valid ping as carry when a sample is temporarily missing.
- Local proxy hops (`127.0.0.1`/`::1`) are annotated to `Game Server` in the viewmodel when applicable.
- UI ping metrics:
  - `Ping Now`: current value
  - `Ping Low`: min over a 5-minute rolling window
  - `Ping Peak`: max over a 5-minute rolling window

## Developer Commands

- Install deps: `uv sync --extra dev`
- Run app: `make run`
- Tests:
  - `make test` (no coverage)
  - `make coverage` (HTML coverage)
- Quality:
  - `make lint`
  - `make typecheck` (`ty`)
  - `make check-all`
- Ping telemetry:
  - `make ping-trace`
  - `make ping-summary`

## Testing Notes

- Unit/integration tests run with `--no-cov` in `Makefile`; coverage has separate target.
- Type checking uses `ty` with config in `ty.toml`.
- Keep tests deterministic and avoid reading/writing user-local runtime config unless explicitly testing persistence paths.

## Change Guidelines

- Preserve interface boundaries (domain protocols should remain framework-independent).
- Avoid UI thread blocking in telemetry paths.
- Prefer additive, reversible changes for ping heuristics and keep tests aligned with behavior.
- If changing ping behavior, update:
  - `src/ui/viewmodels/main_viewmodel.py`
  - `scripts/ping_trace.py`
  - relevant tests under `tests/unit` and `tests/integration`.

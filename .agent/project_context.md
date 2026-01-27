# Project Context

## Overview
**GameMonitor** (BDO Tools) is a high-performance network analyzer and process optimizer for **Black Desert Online**. It helps players monitor real-time latency by filtering game traffic from background web services and provides system optimizations to reduce jitter.

## Architecture
The application follows a modular structure inspired by Clean Architecture and SOLID principles.

### Key Directories
- **`src/domain`**: Contains the core business logic and entities. This layer is independent of external frameworks.
    - `models.py`: Data structures (e.g., `Connection`, `ProcessInfo`).
    - `services.py`: Abstract interfaces for services.
- **`src/infrastructure`**: Implementations of interfaces defined in the domain layer.
    - `system.py`: System interactions (process priority, affinity) using `psutil`.
    - `network.py`: Network monitoring and connection analysis.
    - `gpu.py`: GPU information retrieval.
- **`src/ui`**: The user interface layer, built with **Tkinter**.
    - `viewmodels/`: ViewModels that handle UI logic and bind data to views.
    - `views/`: Tkinter widgets and window definitions.
    - `tray.py`: System tray icon integration.
- **`src/utils`**: Helper functions and utilities.

## Technology Stack
- **Language**: Python 3.10+
- **GUI Framework**: Tkinter (with custom "Sun Valley" dark theme)
- **System Monitoring**: `psutil`
- **Build Tool**: `uv` (recommended), `pip`
- **Packaging**: `PyInstaller` (via `build_exe.py`)

## Key Features
1.  **Smart Latency**: Filters traffic to show "Real Ping" to game servers (ports 8888, 8889, etc.).
2.  **Process Optimization**: Sets High Priority and CPU Affinity (excluding cores 0/1).
3.  **Modern UI**: Dark themed UI that mimics modern Windows aesthetics.

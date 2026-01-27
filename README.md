# GameMonitor

![Version](https://img.shields.io/badge/version-1.1.1-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Coverage](https://img.shields.io/badge/coverage-99.59%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-88%20passed-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

![Screenshot](resources/bdo_monitor.png)

**GameMonitor** is a high-performance network analyzer and process optimizer specifically designed for **Black Desert Online**. Built with clean hexagonal architecture, it provides real-time latency monitoring, intelligent traffic filtering, and one-click system optimizations.

---

## ✨ Features

### 🎯 Core Functionality
- **Smart Latency Monitoring**: Automatically detects game server connections (configurable ports) and calculates real ping, filtering out web/auth traffic
- **Process Optimization**:
  - **CPU Priority**: Manual configuration to set BDO process to High Priority
  - **CPU Affinity**: Manually configurable to exclude specific cores (e.g., cores 0 and 1) to reduce system jitter
- **Network Detection**: Monitors ExitLag or other VPN processes with dedicated metrics

### 📊 System Monitoring
- **Real-time Metrics**:
  - CPU/GPU usage and temperature
  - RAM/VRAM utilization
  - Network latency per connection
- **Multi-Process Tracking**: Monitors both game and network optimization processes simultaneously

### 🎨 User Interface
- **Modern Dark Theme**: Sun Valley (Windows 11 style) UI
- **System Tray Integration**: Minimize to tray with quick access
- **Admin Detection**: Auto-disables optimization controls when not running as administrator
- **Responsive Design**: Updates every 4 seconds (configurable)

---

## 🏗️ Architecture

This project follows **Hexagonal Architecture** (Ports & Adapters):

```
┌─────────────────────────────────────────┐
│              UI Layer                   │
│  ┌──────────────────────────────────┐   │
│  │      MainViewModel               │   │ ← Pure business logic
│  │  (Depends only on Interfaces)    │   │
│  └────────────┬─────────────────────┘   │
└───────────────┼──────────────────────────┘
                │
       ┌────────▼────────┐
       │  Domain Layer   │  ← Core (Ports)
       │   - Models      │
       │   - Interfaces  │
       └────────┬────────┘
                │
┌───────────────┼──────────────────────────┐
│    Infrastructure Layer (Adapters)       │
│  ┌────────────▼─────────────────┐        │
│  │ • PsutilProcessService       │        │
│  │ • PsutilSystemService        │        │
│  │ • NvidiaGpuService (pynvml)  │        │
│  │ • TcpNetworkService          │        │
│  └──────────────────────────────┘        │
└──────────────────────────────────────────┘
```

### Directory Structure

```
bdo_tools/
├── src/
│   ├── domain/              # 🎯 Core Business Logic
│   │   ├── models.py       # Entities (ProcessStatus, ConnectionInfo, AppSettings)
│   │   └── services.py     # Ports (Interface definitions using Protocol)
│   │
│   ├── infrastructure/      # 🔌 Adapters (External dependencies)
│   │   ├── system.py       # psutil adapters (Process & System metrics)
│   │   ├── gpu.py          # NVIDIA GPU monitoring (pynvml)
│   │   ├── network.py      # TCP connection monitoring
│   │   └── services_map.py # Port → Service name mapping
│   │
│   └── ui/                  # 🖥️ User Interface
│       ├── viewmodels/     # Application logic (MainViewModel)
│       └── views/          # Tkinter GUI (main_window.py, tray.py)
│
├── tests/                   # 🧪 Test Suite (99.59% coverage)
│   ├── unit/               # Fast isolated tests
│   ├── integration/        # Infrastructure adapter tests
│   └── functional/         # UI smoke tests
│
├── resources/              # 🎨 Assets (icons, images)
├── main.py                 # 🚀 Application entry point
└── build_exe.py           # 📦 PyInstaller build script
```

### Key Design Decisions

1. **Dependency Inversion**: `MainViewModel` depends on `Protocol` interfaces, not concrete implementations
2. **Testability**: High test coverage with comprehensive test suite (unit, integration, functional)
3. **Separation of Concerns**: Clean boundaries between domain, infrastructure, and UI layers
4. **Configuration**: All settings persisted in `AppSettings` with JSON serialization

---

## 🛠️ Tech Stack

| Layer          | Technology                                      |
|----------------|-------------------------------------------------|
| **UI**         | Tkinter (ttk), Sun Valley theme, pystray       |
| **Domain**     | Pure Python 3.9+ with `dataclasses`, `Protocol`|
| **System**     | `psutil` (process/system metrics)              |
| **GPU**        | `nvidia-ml-py` (pynvml - NVIDIA GPU monitoring)|
| **Network**    | `socket`, `psutil` (TCP connection tracking)   |
| **Build**      | PyInstaller (single executable)                |
| **Testing**    | pytest, pytest-cov, unittest.mock              |
| **Linting**    | ruff (fast Python linter)                      |

---

## 🚀 Quick Start

### For End Users (Windows)

#### Option 1: Download Pre-built Executable
1. Download `GameMonitor.exe` from [Releases](https://github.com/yeiij/bdo_tools/releases)
2. **Right-click** → **Run as Administrator**
3. Done! The app will appear in your system tray

#### Option 2: Build from Source
```powershell
# 1. Install Python 3.14+
# Download from https://www.python.org/downloads/
# IMPORTANT: Check "Add Python to PATH" during installation

# 2. Clone repository
git clone https://github.com/yeiij/bdo_tools
cd bdo_tools

# 3. Install uv (package manager)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 4. Build executable
uv run python build_exe.py

# 5. Find executable in dist/GameMonitor.exe
```

---

## 💻 Development

### Prerequisites
- Python 3.14+
- `uv` package manager (recommended) or `pip`
- Windows 10/11 (for build)

### Setup Development Environment

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install dependencies
uv sync

# Run application
make run
# or
uv run python main.py
```

### Available Make Commands

```bash
make run          # Run the application
make test         # Run all tests (unit + integration + functional)
make test-unit    # Run only unit tests
make coverage     # Run tests with coverage report (99.59%)
make build        # Build standalone executable
make lint         # Run ruff linter
```

### Running Tests

```bash
# All tests (88 tests)
make test

# With coverage report
make coverage

# Specific test categories
make test-unit         # 23 unit tests
make test-integration  # 65 integration tests
make test-functional   # 2 functional tests
```

Run `make coverage` to see current coverage statistics.

---

## 📝 Configuration

### Application Settings

Settings are auto-saved to `%LOCALAPPDATA%/GameMonitor/settings.json`:

```json
{
  "game_process_name": "BlackDesert64.exe",
  "network_process_name": "ExitLag.exe",
  "poll_interval_ms": 4000,
  "target_game_priority": "High",
  "target_game_affinity": [2, 3, 4, 5, 6, 7],
  "target_network_priority": "High",
  "target_network_affinity": [2, 3, 4, 5, 6, 7]
}
```

### Customization

Edit settings via the application or directly modify the JSON file:
- **Process Names**: Change to monitor different processes
- **Poll Interval**: Adjust refresh rate (default: 4000ms)
- **CPU Affinity**: Customize which cores to use (default: excludes 0 and 1)

---

## 🧪 Testing Philosophy

This project maintains **high test coverage** with three test categories:

### Test Structure
```
tests/
├── unit/                    # Fast, isolated tests (23 tests)
│   ├── test_domain_models.py
│   └── test_viewmodel.py
│
├── integration/             # Infrastructure tests (65 tests)
│   ├── test_services_integration.py
│   ├── test_gpu_integration.py
│   └── test_network_integration.py
│
└── functional/              # End-to-end tests (2 tests)
    └── test_ui_functional.py
```

### Coverage Configuration

Configurations in separate files (not `pyproject.toml`):
- **ruff.toml**: Linting rules
- **coverage.toml**: Coverage settings (excludes UI code)
- **pytest.ini**: Test discovery and markers
- **pyrightconfig.json**: Type checking (optional)

---

## 🔧 Build Configuration

### Building Executable

```bash
make build
# or
uv run python build_exe.py
```

**Build options** (in `build_exe.py`):
- `--onefile`: Single executable
- `--windowed`: No console window
- `--icon`: Custom icon
- `--add-data`: Include resources folder
- `--collect-all=sv_ttk`: Sun Valley theme

**Output**: `dist/GameMonitor.exe` (~15MB)

---

## 🐛 Troubleshooting

### "Optimize button is disabled"
→ Run the application as **Administrator** (required for process priority/affinity changes)

### "GPU metrics show N/A"
→ Requires NVIDIA GPU with drivers installed. AMD/Intel GPUs not currently supported

### "Network process not detected"
→ Ensure the network process name in settings matches your VPN (e.g., `ExitLag.exe`)

### Application doesn't minimize to tray
→ Check if `resources/icon.ico` exists. Rebuild with `make build`

---

## 🤝 Contributing

Contributions welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests**: Maintain >95% coverage
4. **Run linter**: `make lint` (must pass)
5. **Run tests**: `make test` (all must pass)
6. **Commit**: Use conventional commits (e.g., `feat:`, `fix:`, `test:`)
7. **Push**: `git push origin feature/amazing-feature`
8. **Submit PR**: With clear description

### Code Quality Standards
- ✅ Test coverage > 95%
- ✅ All tests passing
- ✅ Ruff linter clean
- ✅ Follow hexagonal architecture
- ✅ Type hints on public APIs

---

## 📊 Project Stats

| Metric            | Value          |
|-------------------|----------------|
| **Lines of Code** | ~2,000        |
| **Test Coverage** | 99.59%        |
| **Tests**         | 88 (all passing)|
| **Dependencies**  | 7 core + 4 dev |
| **Build Size**    | ~15MB         |
| **Python**        | 3.9+          |

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Created by**: Yeiij  
**Project**: GameMonitor (BDO Tools)  
**Repository**: [github.com/yeiij/bdo_tools](https://github.com/yeiij/bdo_tools)

---

## 🙏 Acknowledgments

- **Sun Valley ttk theme** - Modern Windows 11-style UI
- **psutil** - Cross-platform process and system monitoring
- **pynvml** - NVIDIA GPU monitoring
- **PyInstaller** - Executable building
- **Astral (ruff/uv)** - Fast Python tooling

---

## 📚 Additional Resources

- **Architecture Documentation**: See `docs/architecture.md` (if available)
- **API Reference**: See inline docstrings
- **Workflows**: `.agent/workflows/` for development guides
- **Changelog**: See commit history or CHANGELOG.md

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

![BDO](https://img.shields.io/badge/Black%20Desert%20Online-Optimized-orange)
![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red)

</div>

# BDO Monitor

![Screenshot](resources/bdo_monitor.png)

**BDO Monitor** is a modern, high-performance network analyzer and process optimizer specifically designed for **Black Desert Online**. 

It provides real-time latency monitoring by distinguishing actual game traffic from background web services and offers one-click system optimizations.



## ✨ Features

-   **Smart Latency Display**: Automatically identifies Game Server connections (ports 8888, 8889, etc.) and calculates the "Real Ping", filtering out web/auth traffic.
-   **Process Optimization**:
    -   **Priority**: Sets the BDO process to **High Priority**.
    -   **Affinity**: Automatically excludes CPU Cores 0 and 1 to reduce system jitter and improve stability.
-   **Modern UI**: Built with a clean Dark Mode utilizing the **Sun Valley** theme (Windows 11 style).
-   **Admin-Safe**: Optimization controls are disabled if the application is not run with Administrator privileges.
-   **Portable**: Can be compiled into a single standalone `.exe`.

## 🛠️ Requirements

-   **OS**: Windows 10/11
-   **Python**: 3.10 or higher
-   **Package Manager**: `uv` (recommended) or `pip`

## How to Build (For Windows Users)

If you want to compile the BDO Monitor executable yourself, follow these steps. No programming knowledge is required!

### ⚡ Quick Guide (Windows)

1.  **Download Source**:
    ```powershell
    git clone https://github.com/yeiij/bdo_tools
    cd bdo_tools
    ```
2.  **Install Python 3.14**
- Go to [python.org/downloads](https://www.python.org/downloads/windows/) and download the **Python 3.14** installer.
- **IMPORTANT**: During installation, check the box that says **"Add Python to PATH"**.

### 3. Install Project Manager (uv)
- Open **PowerShell** (Click Start, type `powershell`).
- Copy and paste the following command and hit Enter:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- Restart PowerShell after it completes.

### 3. Compile the App
- Open PowerShell in the folder where you downloaded the BDO Tools source code.
- Run the following command to start the build:
  ```powershell
  uv run python build_exe.py
  ```
- Once it finishes, you will find your executable in the `dist` folder named **"BDO Monitor.exe"**.

---

## Development

If you are a developer, you can use the provided `Makefile` for standard tasks:
- `make run`: Run the application.
- `make test`: Run unit tests.
- `make coverage`: Check test coverage.
- `make build`: Compile the executable.

## ▶️ Usage

### Running from Code
To launch the application directly from the source code:

```bash
make run
```

### Building the Executable
To compile the application into a standalone `.exe` (includes icon and theme):

```bash
make build
```

The executable will be generated in the `dist` folder:
`dist/BDO Monitor.exe`

> **Note**: To use the **Optimize** button, you must run the application (or the `.exe`) as **Administrator**.

## 🏗️ Project Structure

-   `src/domain`: Core business logic and interfaces (SOLID).
-   `src/infrastructure`: System-level implementations (psutil, network).
-   `src/ui`: ViewModel and Tkinter View definitions.
-   `resources`: Icons and assets.
-   `build_exe.py`: PyInstaller build script with resource handling.

## 👤 Credits

**Created by**: JasonREDUX

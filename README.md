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

## 🚀 Installation (Source)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yeiij/bdo_tools.git
    cd bdo_tools
    ```

2.  **Install dependencies**:
    ```bash
    make install
    # OR using pip directly:
    # pip install -r requirements.txt
    ```

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

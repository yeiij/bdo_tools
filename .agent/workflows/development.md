---
description: Development setup and running the application
---

# Setup

1.  **Install Python 3.10+**
2.  **Install `uv`**:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
3.  **Install Application Dependencies**:
    ```bash
    make install
    ```
    // turbo
    Or:
    ```bash
    uv sync --extra dev
    ```

# Running the Application

To start the application from source:

```bash
make run
```
// turbo
Or:
```bash
uv run python main.py
```

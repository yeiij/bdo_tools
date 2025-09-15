# BDO Tools

## Development

Install the project in editable mode together with the development extras:

```bash
pip install -e .[dev]
```

### Run the test-suite

Execute the unit tests with `pytest` from the repository root:

```bash
pytest
```

### Build the package

Use the standard Python build frontend (install it once with `pip install build`)
to generate an sdist and wheel in the `dist/` directory:

```bash
python -m build
```

## Build executable

The project can also be bundled into a standalone executable with PyInstaller:

```bash
pyinstaller -F -w -n BDOMonitor --uac-admin src/main.py
```

## Command line interface

The project ships with a small CLI that exposes the networking helpers used by
the GUI.

```
python -m src.cli --help
```

### Ping a host

Measure the average round trip time reported by the system `ping` command:

```
python -m src.cli ping na.playblackdesert.com --count 10
```

### List remote IPs for the game client

Show the public IPs currently used by the Black Desert Online process. You can
target a different executable with `--process` and include private/local
addresses with `--include-private` if needed.

```
python -m src.cli ips
python -m src.cli ips --process BlackDesert64.exe --include-private
```

## GUI sections

The GUI is composed of small "sections" that render text blocks. Each
section subclasses `Section` from `src/gui/sections/base.py` and exposes a
`render()` method returning a string with the content to display.

### Registering a new section

1. Create a subclass of `Section` (for example inside `src/gui/sections/`).
   Implement the `render()` method with the text you want to show in the UI.
2. Instantiate your new section inside `AppWindow` (see
   `src/gui/window.py`). The window concatenates the output of every section in
   the order they appear in the `self.sections` list.
3. If the section needs configuration values, accept them in the constructor so
   that `AppWindow` can pass the relevant settings when creating it.

With this setup you can extend the GUI by adding new section classes without
changing the rendering loop.

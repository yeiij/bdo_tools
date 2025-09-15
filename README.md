# BDO Tools

## Build

```bash
pyinstaller -F -w -n BDOMonitor --uac-admin src/main.py
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

import psutil

# Ensure priority constants exist even on non-Windows platforms so the module imports.
PRIORITY_CONSTANTS = {
    "IDLE_PRIORITY_CLASS": 64,
    "BELOW_NORMAL_PRIORITY_CLASS": 16384,
    "NORMAL_PRIORITY_CLASS": 32,
    "ABOVE_NORMAL_PRIORITY_CLASS": 32768,
    "HIGH_PRIORITY_CLASS": 128,
    "REALTIME_PRIORITY_CLASS": 256,
}
for name, value in PRIORITY_CONSTANTS.items():
    if not hasattr(psutil, name):
        setattr(psutil, name, value)

from core.process import priority


class DummyProcess:
    def __init__(self, nice_value):
        self._nice_value = nice_value
        self.set_calls = []

    def nice(self, value=None):
        if value is None:
            return self._nice_value
        self._nice_value = value
        self.set_calls.append(value)
        return value


def test_get_priority_label_windows_known_class(monkeypatch):
    proc = DummyProcess(priority.psutil.HIGH_PRIORITY_CLASS)
    monkeypatch.setattr(priority.platform, "system", lambda: "Windows")

    assert priority.get_priority_label(proc) == "HIGH"


def test_get_priority_label_unix_ranges(monkeypatch):
    proc = DummyProcess(-12)
    monkeypatch.setattr(priority.platform, "system", lambda: "Linux")

    assert priority.get_priority_label(proc) == "ABOVE(-12)"

    proc_low = DummyProcess(10)
    assert priority.get_priority_label(proc_low) == "BELOW(10)"

    proc_high = DummyProcess(-20)
    assert priority.get_priority_label(proc_high) == "HI(-20)"


def test_get_priority_label_handles_errors(monkeypatch):
    class FailingProcess:
        def nice(self):
            raise priority.psutil.AccessDenied(pid=1, name="proc")

    monkeypatch.setattr(priority.platform, "system", lambda: "Linux")
    assert priority.get_priority_label(FailingProcess()) == "UNKNOWN"


def test_get_priority_by_name_uses_helper(monkeypatch):
    proc = DummyProcess(priority.psutil.NORMAL_PRIORITY_CLASS)
    monkeypatch.setattr(priority, "find_process_by_name", lambda name: proc if name == "client" else None)
    monkeypatch.setattr(priority.platform, "system", lambda: "Windows")

    assert priority.get_priority_by_name("client") == "NORMAL"
    assert priority.get_priority_by_name("missing") is None

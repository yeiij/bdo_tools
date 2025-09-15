import psutil

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

from core.process import priority, utils


class NamedProcess:
    def __init__(self, name, *, raise_exc=None):
        self._name = name
        self._raise_exc = raise_exc
        self._info = {"name": name}

    @property
    def info(self):
        if self._raise_exc is not None:
            raise self._raise_exc
        return self._info

    def name(self):
        return self._name

    def nice(self, value=None):
        if value is None:
            return 0
        return value


def test_find_process_by_name_returns_first_match(monkeypatch):
    def fake_iter(attrs):
        access_denied = priority.psutil.AccessDenied(pid=2, name="denied")
        return iter(
            [
                NamedProcess("other"),
                NamedProcess("blocked", raise_exc=access_denied),
                NamedProcess("Target"),
            ]
        )

    monkeypatch.setattr(utils.psutil, "process_iter", fake_iter)

    proc = utils.find_process_by_name("target")
    assert proc is not None
    assert proc.info["name"].lower() == "target"


def test_find_process_by_name_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr(utils.psutil, "process_iter", lambda attrs: iter([]))
    assert utils.find_process_by_name("missing") is None


class AdjustableProcess(NamedProcess):
    def __init__(self, name, nice_value=0):
        super().__init__(name)
        self._nice_value = nice_value
        self.set_calls = []

    def nice(self, value=None):
        if value is None:
            return self._nice_value
        self._nice_value = value
        self.set_calls.append(value)
        return value


def test_ensure_high_priority_windows(monkeypatch):
    proc = AdjustableProcess("client", nice_value=0)
    monkeypatch.setattr(utils, "find_process_by_name", lambda name: proc)
    monkeypatch.setattr(utils.platform, "system", lambda: "Windows")
    monkeypatch.setattr(utils.psutil, "HIGH_PRIORITY_CLASS", 128, raising=False)

    call_count = {"value": 0}

    def fake_get_priority(process):
        call_count["value"] += 1
        return "NORMAL" if call_count["value"] == 1 else "HIGH"

    monkeypatch.setattr(priority, "get_priority_label", fake_get_priority)

    assert utils.ensure_high_priority("client") is True
    assert proc.set_calls == [128]


def test_ensure_high_priority_unix(monkeypatch):
    proc = AdjustableProcess("client", nice_value=10)
    monkeypatch.setattr(utils, "find_process_by_name", lambda name: proc)
    monkeypatch.setattr(utils.platform, "system", lambda: "Linux")

    def fake_get_priority(process):
        return "NORMAL" if process._nice_value > -10 else "HI(-10)"

    monkeypatch.setattr(priority, "get_priority_label", fake_get_priority)

    assert utils.ensure_high_priority("client") is True
    assert proc._nice_value == -10


def test_ensure_high_priority_returns_false_when_process_missing(monkeypatch):
    monkeypatch.setattr(utils, "find_process_by_name", lambda name: None)
    assert utils.ensure_high_priority("missing") is False

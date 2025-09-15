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

from core.process import affinity


class DummyProcess:
    def __init__(self, mask=None, *, get_exc=None, set_exc=None):
        self._mask = list(mask or [])
        self._get_exc = get_exc
        self._set_exc = set_exc
        self.set_calls = []

    def cpu_affinity(self, mask=None):
        if mask is None:
            if self._get_exc is not None:
                raise self._get_exc
            return list(self._mask)
        if self._set_exc is not None:
            raise self._set_exc
        self._mask = list(mask)
        self.set_calls.append(list(mask))


def test_get_affinity_returns_sorted_values():
    proc = DummyProcess(mask=[3, 1, 2])
    assert affinity.get_affinity(proc) == [1, 2, 3]


def test_get_affinity_handles_errors(monkeypatch):
    proc_attr = DummyProcess(get_exc=AttributeError())
    assert affinity.get_affinity(proc_attr) is None

    access_error = affinity.psutil.AccessDenied(pid=123, name="demo")
    proc_denied = DummyProcess(get_exc=access_error)
    assert affinity.get_affinity(proc_denied) is None


def test_format_affinity_short_formats_ranges(monkeypatch):
    monkeypatch.setattr(affinity.psutil, "cpu_count", lambda logical=True: 4)

    assert affinity.format_affinity_short(None) == "N/A"
    assert affinity.format_affinity_short([0, 1, 2, 3]) == "ALL (4)"
    assert affinity.format_affinity_short([0, 1, 3]) == "0-1,3 (3)"


def test_set_affinity_range_sets_expected_mask(monkeypatch):
    monkeypatch.setattr(affinity.psutil, "cpu_count", lambda logical=True: 8)
    proc = DummyProcess(mask=[0])

    assert affinity.set_affinity_range(proc, 2, 4) is True
    assert proc.set_calls[-1] == [2, 3, 4]


def test_set_affinity_range_rejects_invalid(monkeypatch):
    monkeypatch.setattr(affinity.psutil, "cpu_count", lambda logical=True: None)
    proc = DummyProcess(mask=[0])

    assert affinity.set_affinity_range(proc, 1, 2) is False


def test_ensure_affinity_range_by_name_adjusts_process(monkeypatch):
    monkeypatch.setattr(affinity.psutil, "cpu_count", lambda logical=True: 6)
    proc = DummyProcess(mask=[0, 1])
    monkeypatch.setattr(affinity, "find_process_by_name", lambda name: proc if name == "game" else None)

    assert affinity.ensure_affinity_range_by_name("game", start_core=2, end_core=3) is True
    assert affinity.get_affinity(proc) == [2, 3]


def test_ensure_affinity_range_by_name_returns_false_when_missing(monkeypatch):
    monkeypatch.setattr(affinity, "find_process_by_name", lambda name: None)
    assert affinity.ensure_affinity_range_by_name("unknown") is False

from types import SimpleNamespace

from core.network import latency


class DummySocket:
    attempts = []

    def __init__(self, *args, **kwargs):
        self.timeout = None
        self.closed = False

    def settimeout(self, value):
        self.timeout = value

    def connect(self, address):
        DummySocket.attempts.append(address)

    def close(self):
        self.closed = True


def test_tcp_ping_collects_samples(monkeypatch):
    DummySocket.attempts = []
    monkeypatch.setattr(latency.socket, "socket", lambda *args, **kwargs: DummySocket())

    times = iter([1.0, 1.05, 2.0, 2.1, 3.0, 3.5])
    monkeypatch.setattr(latency.time, "perf_counter", lambda: next(times))

    samples = latency.tcp_ping("example.com", port=80, count=3, timeout=1.0)
    assert len(samples) == 3
    assert DummySocket.attempts == [("example.com", 80)] * 3


def test_tcp_ping_stats_returns_expected_keys(monkeypatch):
    monkeypatch.setattr(latency, "tcp_ping", lambda host, port, count, timeout: [10.0, 30.0, 50.0])
    stats = latency.tcp_ping_stats("example.com")
    assert stats["samples"] == 3.0
    assert stats["avg"] == 30.0
    assert "median" in stats and "p95" in stats


def test_ping_host_parses_platform_specific_output(monkeypatch):
    monkeypatch.setattr(latency.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        latency.subprocess,
        "run",
        lambda cmd, capture_output, text: SimpleNamespace(stdout="Average = 42ms"),
    )
    assert latency.ping_host("example.com", count=2) == 42.0

    monkeypatch.setattr(latency.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        latency.subprocess,
        "run",
        lambda cmd, capture_output, text: SimpleNamespace(stdout="round-trip avg = 10.0/35.5/60.0/"),
    )
    assert latency.ping_host("example.com", count=2) == 35.5


def test_ping_host_returns_negative_when_unmatched(monkeypatch):
    monkeypatch.setattr(latency.platform, "system", lambda: "Linux")
    monkeypatch.setattr(latency.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=""))
    assert latency.ping_host("example.com") == -1.0

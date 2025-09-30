import statistics
from types import SimpleNamespace

import pytest

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
    assert stats["median"] == 30.0
    assert stats["p95"] == statistics.quantiles([10.0, 30.0, 50.0], n=100, method="inclusive")[94]


def test_tcp_ping_stats_handles_single_sample(monkeypatch):
    monkeypatch.setattr(latency, "tcp_ping", lambda host, port, count, timeout: [42.0])
    stats = latency.tcp_ping_stats("example.com")
    assert stats["samples"] == 1.0
    assert stats["avg"] == 42.0
    assert stats["median"] == 42.0
    assert stats["p95"] == 42.0


@pytest.mark.parametrize(
    ("system", "output", "expected"),
    [
        (
            "Linux",
            """64 bytes from 1.1.1.1: icmp_seq=1 ttl=57 time=11.2 ms\nrtt min/avg/max/mdev = 11.200/42.000/73.000/8.500 ms\n""",
            42.0,
        ),
        (
            "Darwin",
            """--- example.com ping statistics ---\nround-trip min/avg/max/stddev = 13.843/16.988/20.038/2.546 ms\n""",
            16.988,
        ),
        (
            "Windows",
            """Ping statistics for 8.8.8.8:\n    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\nApproximate round trip times in milli-seconds:\n    Minimum = 30ms, Maximum = 54ms, Average = 42ms\n""",
            42.0,
        ),
        (
            "Windows",
            """Estadísticas de ping para 8.8.8.8:\n    Paquetes: enviados = 4, recibidos = 4, perdidos = 0 (0% perdidos),\nTiempos aproximados de ida y vuelta en milisegundos:\n    Mínimo = 30ms, Máximo = 54ms, Promedio = 37ms\n""",
            37.0,
        ),
        (
            "Windows",
            """Estatísticas de ping para 8.8.8.8:\n    Pacotes: Enviados = 4, Recebidos = 4, Perdidos = 0 (0% perda),\nAproximar tempos de ida e volta em milissegundos:\n    Mínimo = 10ms, Máximo = 30ms, Média = 17,5ms\n""",
            17.5,
        ),
    ],
)
def test_ping_host_parses_platform_specific_output(monkeypatch, system, output, expected):
    monkeypatch.setattr(latency.platform, "system", lambda: system)
    monkeypatch.setattr(
        latency.subprocess,
        "run",
        lambda cmd, capture_output, text: SimpleNamespace(stdout=output),
    )
    assert latency.ping_host("example.com", count=2) == expected


def test_ping_host_returns_negative_when_unmatched(monkeypatch):
    monkeypatch.setattr(latency.platform, "system", lambda: "Linux")
    monkeypatch.setattr(latency.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=""))
    assert latency.ping_host("example.com") == -1.0

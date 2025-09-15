from types import SimpleNamespace

from core.network import ip_utils


def test_is_private_ip():
    assert ip_utils.is_private_ip("192.168.0.1") is True
    assert ip_utils.is_private_ip("8.8.8.8") is False
    assert ip_utils.is_private_ip("invalid") is False


def test_get_remote_ips_for_process_filters_by_name(monkeypatch):
    established = ip_utils.psutil.CONN_ESTABLISHED
    connections = [
        SimpleNamespace(
            pid=100,
            status=established,
            raddr=SimpleNamespace(ip="203.0.113.10"),
        ),
        SimpleNamespace(pid=101, status=established, raddr=None),
        SimpleNamespace(
            pid=None,
            status=established,
            raddr=SimpleNamespace(ip="198.51.100.2"),
        ),
        SimpleNamespace(
            pid=102,
            status=established,
            raddr=SimpleNamespace(ip="10.0.0.1"),
        ),
        SimpleNamespace(
            pid=103,
            status=ip_utils.psutil.CONN_SYN_SENT,
            raddr=SimpleNamespace(ip="192.0.2.1"),
        ),
    ]

    process_map = {
        100: SimpleNamespace(name=lambda: "Game.exe"),
        102: SimpleNamespace(name=lambda: "Other.exe"),
        103: SimpleNamespace(name=lambda: "Game.exe"),
    }

    monkeypatch.setattr(ip_utils.psutil, "net_connections", lambda kind: connections)
    monkeypatch.setattr(ip_utils.psutil, "Process", lambda pid: process_map[pid])

    ips = ip_utils.get_remote_ips_for_process("Game.exe")
    assert ips == {"203.0.113.10"}


def test_get_process_ips_excludes_private_by_default(monkeypatch):
    monkeypatch.setattr(
        ip_utils,
        "get_remote_ips_for_process",
        lambda name: {"8.8.8.8", "192.168.1.50"},
    )

    assert ip_utils.get_process_ips("proc") == {"8.8.8.8"}
    assert ip_utils.get_process_ips("proc", include_private=True) == {
        "8.8.8.8",
        "192.168.1.50",
    }


def test_get_bdo_ips_uses_default_process(monkeypatch):
    monkeypatch.setattr(ip_utils, "get_process_ips", lambda name, include_private: {name, include_private})
    assert ip_utils.get_bdo_ips() == {"BlackDesert64.exe", True}

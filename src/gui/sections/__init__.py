"""Utilities to build GUI text sections."""

from .base import Section
from .process import ProcessSection
from .priority import PrioritySection
from .affinity import AffinitySection
from .ip_resolver import IPResolverSection
from .latency import LatencySection
from .ping import PingSection

__all__ = [
    "Section",
    "ProcessSection",
    "PrioritySection",
    "AffinitySection",
    "IPResolverSection",
    "LatencySection",
    "PingSection",
]

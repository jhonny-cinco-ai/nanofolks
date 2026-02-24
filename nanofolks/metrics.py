"""Lightweight metrics sink for internal telemetry."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Iterable


@dataclass(frozen=True)
class MetricKey:
    name: str
    tags: tuple[tuple[str, str], ...] = ()


class MetricsSink:
    """In-memory metrics sink (counters + gauges)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[MetricKey, int] = defaultdict(int)
        self._gauges: dict[MetricKey, float] = {}

    def incr(self, name: str, count: int = 1, tags: dict[str, Any] | None = None) -> None:
        key = MetricKey(name=name, tags=_normalize_tags(tags))
        with self._lock:
            self._counters[key] += count

    def set_gauge(self, name: str, value: float, tags: dict[str, Any] | None = None) -> None:
        key = MetricKey(name=name, tags=_normalize_tags(tags))
        with self._lock:
            self._gauges[key] = value

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            counters = {self._key_to_str(k): v for k, v in self._counters.items()}
            gauges = {self._key_to_str(k): v for k, v in self._gauges.items()}
        return {"counters": counters, "gauges": gauges}

    @staticmethod
    def _key_to_str(key: MetricKey) -> str:
        if not key.tags:
            return key.name
        tags = ",".join(f"{k}={v}" for k, v in key.tags)
        return f"{key.name}|{tags}"


_metrics: MetricsSink | None = None


def get_metrics() -> MetricsSink:
    """Get the global metrics sink."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsSink()
    return _metrics


def _normalize_tags(tags: dict[str, Any] | None) -> tuple[tuple[str, str], ...]:
    if not tags:
        return ()
    items: Iterable[tuple[str, str]] = ((str(k), str(v)) for k, v in tags.items())
    return tuple(sorted(items))


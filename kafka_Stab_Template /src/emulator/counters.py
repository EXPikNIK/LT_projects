from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass
class CounterSnapshot:
    values: Dict[str, int]
    since_sec: float


class CounterRegistry:
    def __init__(self, enabled: Iterable[str]) -> None:
        self._enabled = set(enabled)
        self._values: Dict[str, int] = {name: 0 for name in self._enabled}
        self._lock = threading.Lock()
        self._start = time.perf_counter()

    def inc(self, name: str, value: int = 1) -> None:
        if name not in self._enabled:
            return
        with self._lock:
            self._values[name] = self._values.get(name, 0) + value

    def set(self, name: str, value: int) -> None:
        if name not in self._enabled:
            return
        with self._lock:
            self._values[name] = value

    def snapshot(self) -> CounterSnapshot:
        with self._lock:
            values = dict(self._values)
        since = time.perf_counter() - self._start
        return CounterSnapshot(values=values, since_sec=since)

    def render(self) -> str:
        snap = self.snapshot()
        parts = [f"uptime={snap.since_sec:.1f}s"]
        for key in sorted(snap.values):
            parts.append(f"{key}={snap.values[key]}")
        return " ".join(parts)

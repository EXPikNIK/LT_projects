from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import AppConfig


@dataclass
class Message:
    key: Optional[bytes]
    value: bytes
    headers: list[tuple[str, bytes]]


class BaseLogic:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def build_message(self, seq: int, ts_ms: int) -> Message:
        raise NotImplementedError

    def on_delivery(self, record_metadata: object) -> None:
        # Override if you want to track per-message delivery metadata.
        return


class ExampleLogic(BaseLogic):
    def build_message(self, seq: int, ts_ms: int) -> Message:
        payload = self.config.load.payload_template.format(seq=seq, ts=ts_ms)
        payload_bytes = payload.encode("utf-8")
        if len(payload_bytes) < self.config.load.message_size_bytes:
            pad_len = self.config.load.message_size_bytes - len(payload_bytes)
            payload_bytes += b"x" * pad_len
        key = f"{self.config.load.key_prefix}{seq}".encode("utf-8")
        headers = [("ts", str(ts_ms).encode("utf-8"))]
        return Message(key=key, value=payload_bytes, headers=headers)

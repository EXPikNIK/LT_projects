from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class SaslConfig:
    mechanism: str = ""
    username: str = ""
    password: str = ""


@dataclass
class KafkaConfig:
    bootstrap_servers: List[str] = field(default_factory=lambda: ["localhost:9092"])
    client_id: str = "kafka-load-emulator"
    security_protocol: str = "PLAINTEXT"
    sasl: SaslConfig = field(default_factory=SaslConfig)


@dataclass
class ProducerConfig:
    topic: str = "load-topic"
    acks: str = "1"
    linger_ms: int = 5
    batch_size: int = 16384
    compression_type: str = ""
    timeout_ms: int = 30000
    retries: int = 3


@dataclass
class LoadConfig:
    rps: int = 100
    duration_sec: int = 60
    message_size_bytes: int = 256
    key_prefix: str = "key-"
    payload_template: str = "{ts}|{seq}"
    concurrency: int = 1
    max_in_flight: int = 1000
    warmup_sec: int = 0
    dry_run: bool = False


@dataclass
class CountersConfig:
    enabled: List[str] = field(default_factory=lambda: [
        "sent",
        "send_errors",
        "acked",
        "throughput_bytes",
    ])
    report_interval_sec: int = 5


@dataclass
class AppConfig:
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    producer: ProducerConfig = field(default_factory=ProducerConfig)
    load: LoadConfig = field(default_factory=LoadConfig)
    counters: CountersConfig = field(default_factory=CountersConfig)

    @staticmethod
    def load(path: str | Path) -> "AppConfig":
        raw = yaml.safe_load(Path(path).read_text()) or {}
        return AppConfig(
            kafka=_load_kafka(raw.get("kafka", {})),
            producer=_load_producer(raw.get("producer", {})),
            load=_load_load(raw.get("load", {})),
            counters=_load_counters(raw.get("counters", {})),
        )

    def validate(self) -> None:
        if self.load.rps <= 0:
            raise ValueError("load.rps must be > 0")
        if self.load.duration_sec <= 0:
            raise ValueError("load.duration_sec must be > 0")
        if self.load.concurrency <= 0:
            raise ValueError("load.concurrency must be > 0")
        if self.load.max_in_flight <= 0:
            raise ValueError("load.max_in_flight must be > 0")
        if not self.producer.topic:
            raise ValueError("producer.topic must be set")


def _load_kafka(data: Dict[str, Any]) -> KafkaConfig:
    sasl_data = data.get("sasl", {}) or {}
    return KafkaConfig(
        bootstrap_servers=list(data.get("bootstrap_servers", ["localhost:9092"])),
        client_id=str(data.get("client_id", "kafka-load-emulator")),
        security_protocol=str(data.get("security_protocol", "PLAINTEXT")),
        sasl=SaslConfig(
            mechanism=str(sasl_data.get("mechanism", "")),
            username=str(sasl_data.get("username", "")),
            password=str(sasl_data.get("password", "")),
        ),
    )


def _load_producer(data: Dict[str, Any]) -> ProducerConfig:
    return ProducerConfig(
        topic=str(data.get("topic", "load-topic")),
        acks=str(data.get("acks", "1")),
        linger_ms=int(data.get("linger_ms", 5)),
        batch_size=int(data.get("batch_size", 16384)),
        compression_type=str(data.get("compression_type", "")),
        timeout_ms=int(data.get("timeout_ms", 30000)),
        retries=int(data.get("retries", 3)),
    )


def _load_load(data: Dict[str, Any]) -> LoadConfig:
    return LoadConfig(
        rps=int(data.get("rps", 100)),
        duration_sec=int(data.get("duration_sec", 60)),
        message_size_bytes=int(data.get("message_size_bytes", 256)),
        key_prefix=str(data.get("key_prefix", "key-")),
        payload_template=str(data.get("payload_template", "{ts}|{seq}")),
        concurrency=int(data.get("concurrency", 1)),
        max_in_flight=int(data.get("max_in_flight", 1000)),
        warmup_sec=int(data.get("warmup_sec", 0)),
        dry_run=bool(data.get("dry_run", False)),
    )


def _load_counters(data: Dict[str, Any]) -> CountersConfig:
    enabled = data.get("enabled", None)
    if enabled is None:
        enabled = ["sent", "send_errors", "acked", "throughput_bytes"]
    return CountersConfig(
        enabled=list(enabled),
        report_interval_sec=int(data.get("report_interval_sec", 5)),
    )

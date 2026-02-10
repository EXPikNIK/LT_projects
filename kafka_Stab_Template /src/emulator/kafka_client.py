from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from kafka import KafkaProducer

from .config import AppConfig


class KafkaClient:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._producer = KafkaProducer(
            bootstrap_servers=config.kafka.bootstrap_servers,
            client_id=config.kafka.client_id,
            security_protocol=config.kafka.security_protocol,
            sasl_mechanism=config.kafka.sasl.mechanism or None,
            sasl_plain_username=config.kafka.sasl.username or None,
            sasl_plain_password=config.kafka.sasl.password or None,
            acks=config.producer.acks,
            linger_ms=config.producer.linger_ms,
            batch_size=config.producer.batch_size,
            compression_type=config.producer.compression_type or None,
            request_timeout_ms=config.producer.timeout_ms,
            retries=config.producer.retries,
            value_serializer=lambda v: v,
            key_serializer=lambda v: v,
        )

    def send(
        self,
        topic: str,
        value: bytes,
        key: Optional[bytes] = None,
        headers: Optional[list[tuple[str, bytes]]] = None,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[BaseException], None]] = None,
    ) -> None:
        future = self._producer.send(topic, value=value, key=key, headers=headers)
        if on_success is not None:
            future.add_callback(on_success)
        if on_error is not None:
            future.add_errback(on_error)

    def flush(self) -> None:
        self._producer.flush()

    def close(self) -> None:
        self._producer.close()

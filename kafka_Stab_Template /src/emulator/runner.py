from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional

from .config import AppConfig
from .counters import CounterRegistry
from .kafka_client import KafkaClient
from .logic import BaseLogic, Message

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, rps: int) -> None:
        self._interval = 1.0 / float(rps)
        self._next = time.perf_counter()

    def wait(self) -> None:
        now = time.perf_counter()
        if now < self._next:
            time.sleep(self._next - now)
        self._next = max(self._next + self._interval, time.perf_counter())


@dataclass
class WorkItem:
    seq: int
    ts_ms: int
    message: Message


class LoadRunner:
    def __init__(self, config: AppConfig, logic: BaseLogic) -> None:
        self._config = config
        self._logic = logic
        self._counters = CounterRegistry(config.counters.enabled)
        self._queue: queue.Queue[Optional[WorkItem]] = queue.Queue(
            maxsize=config.load.max_in_flight
        )
        self._stop_event = threading.Event()

    def run(self) -> None:
        self._config.validate()
        if self._config.load.dry_run:
            logger.info("dry_run enabled: no Kafka traffic will be sent")

        threads = [
            threading.Thread(target=self._worker, name=f"worker-{i}", daemon=True)
            for i in range(self._config.load.concurrency)
        ]
        for t in threads:
            t.start()

        reporter = threading.Thread(target=self._reporter, name="reporter", daemon=True)
        reporter.start()

        limiter = RateLimiter(self._config.load.rps)
        start = time.perf_counter()
        deadline = start + self._config.load.duration_sec
        seq = 0

        if self._config.load.warmup_sec > 0:
            logger.info("warmup for %ss", self._config.load.warmup_sec)
            time.sleep(self._config.load.warmup_sec)

        try:
            while time.perf_counter() < deadline:
                limiter.wait()
                seq += 1
                ts_ms = int(time.time() * 1000)
                message = self._logic.build_message(seq=seq, ts_ms=ts_ms)
                work = WorkItem(seq=seq, ts_ms=ts_ms, message=message)
                self._queue.put(work)
        finally:
            self._stop_event.set()
            for _ in threads:
                self._queue.put(None)
            for t in threads:
                t.join()
            reporter.join(timeout=1)
            logger.info("run complete: %s", self._counters.render())

    def _worker(self) -> None:
        client = None
        if not self._config.load.dry_run:
            client = KafkaClient(self._config)
        try:
            while not self._stop_event.is_set():
                work = self._queue.get()
                if work is None:
                    return
                self._handle_work(client, work)
        finally:
            if client is not None:
                client.flush()
                client.close()

    def _handle_work(self, client: Optional[KafkaClient], work: WorkItem) -> None:
        self._counters.inc("sent")
        self._counters.inc("throughput_bytes", len(work.message.value))
        if self._config.load.dry_run:
            return

        def on_success(metadata: object) -> None:
            self._counters.inc("acked")
            self._logic.on_delivery(metadata)

        def on_error(exc: BaseException) -> None:
            logger.exception("send error", exc_info=exc)
            self._counters.inc("send_errors")

        assert client is not None
        client.send(
            topic=self._config.producer.topic,
            value=work.message.value,
            key=work.message.key,
            headers=work.message.headers,
            on_success=on_success,
            on_error=on_error,
        )

    def _reporter(self) -> None:
        interval = max(1, self._config.counters.report_interval_sec)
        while not self._stop_event.wait(interval):
            logger.info("counters: %s", self._counters.render())

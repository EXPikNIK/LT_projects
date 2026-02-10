# Config Reference

Все настройки лежат в YAML (см. `config.example.yaml`).

## kafka
- `bootstrap_servers`: список брокеров
- `client_id`: идентификатор клиента
- `security_protocol`: `PLAINTEXT`, `SASL_PLAINTEXT`, `SASL_SSL`
- `sasl.mechanism`: например `PLAIN`, `SCRAM-SHA-256`
- `sasl.username`
- `sasl.password`

## producer
- `topic`: топик для отправки
- `acks`: уровень подтверждений (`0`, `1`, `all`)
- `linger_ms`, `batch_size`, `compression_type`, `timeout_ms`, `retries`

## load
- `rps`: целевая скорость отправки
- `duration_sec`: продолжительность теста
- `message_size_bytes`: минимальный размер payload
- `key_prefix`: префикс ключа
- `payload_template`: шаблон строки, поддерживает `{ts}` и `{seq}`
- `concurrency`: число потоков отправки
- `max_in_flight`: размер очереди на отправку
- `warmup_sec`: задержка перед стартом
- `dry_run`: если `true`, не отправлять в Kafka

## counters
- `enabled`: список имен счетчиков
- `report_interval_sec`: интервал логирования счетчиков

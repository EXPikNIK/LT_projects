# Kafka Load Emulator (Template)

Цель: минимальный и расширяемый эмулятор нагрузки для Kafka на Python. Конфиги вынесены в YAML, счетчики настраиваются, логика сообщений изолирована и легко расширяется.

## Быстрый старт

1. Установить зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Запустить:

```bash
python run_emulator.py --config config.example.yaml
```

## Конфиг

Основные секции:
- `kafka`: подключение (bootstrap servers, security, sasl)
- `producer`: параметры продьюсера
- `load`: параметры нагрузки
- `counters`: список счетчиков и интервал репортинга

См. `config.example.yaml` для полного списка.

## Расширение логики

Базовая логика находится в `src/emulator/logic.py`.

1. Создайте класс, наследующий `BaseLogic`.
2. Переопределите `build_message`.
3. При необходимости переопределите `on_delivery`.
4. Подключите ваш класс в `src/emulator/main.py`.

## Счетчики

По умолчанию поддерживаются:
- `sent`
- `acked`
- `send_errors`
- `throughput_bytes`

Можно добавлять свои. Главное, чтобы их имена были в `counters.enabled` и вы инкрементировали их в нужных местах.

## Структура

- `src/emulator/config.py` — конфиги
- `src/emulator/counters.py` — счетчики
- `src/emulator/kafka_client.py` — тонкая обертка продьюсера
- `src/emulator/logic.py` — шаблон логики сообщений
- `src/emulator/runner.py` — раннер нагрузки
- `src/emulator/main.py` — точка входа

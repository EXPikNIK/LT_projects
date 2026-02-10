from __future__ import annotations

import argparse
import logging
import sys

from .config import AppConfig
from .logic import ExampleLogic
from .runner import LoadRunner


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kafka load emulator")
    parser.add_argument(
        "--config",
        default="config.example.yaml",
        help="Path to YAML config",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    config = AppConfig.load(args.config)
    logic = ExampleLogic(config)
    runner = LoadRunner(config, logic)
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

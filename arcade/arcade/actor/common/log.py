#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from loguru import logger

from arcade.actor.core.conf import settings

actor_log_path = os.path.join(settings.WORK_DIR, "actor_logs")


if TYPE_CHECKING:
    import loguru


class Logger:
    def __init__(self):
        self.log_path = actor_log_path

    def log(self) -> loguru.Logger:
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path, exist_ok=True)

        log_stdout_file = os.path.join(self.log_path, settings.LOG_STDOUT_FILENAME)
        log_stderr_file = os.path.join(self.log_path, settings.LOG_STDERR_FILENAME)

        log_config = {
            "rotation": "10 MB",
            "retention": "15 days",
            "compression": "tar.gz",
            "enqueue": True,
        }
        # stdout
        logger.add(
            log_stdout_file,
            level="INFO",
            filter=lambda record: record["level"].name == "INFO" or record["level"].no <= 25,
            **log_config,
            backtrace=False,
            diagnose=False,
        )
        # stderr
        logger.add(
            log_stderr_file,
            level="ERROR",
            filter=lambda record: record["level"].name == "ERROR" or record["level"].no >= 30,
            **log_config,
            backtrace=True,
            diagnose=True,
        )

        return logger


log = Logger().log()

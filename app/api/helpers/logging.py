import json
import logging

import stackprinter
from loguru import logger

from app.settings import settings

LOG_LEVEL = logging.getLevelName(settings.log_level)
JSON_LOGS = settings.json_logs


class LogCorrelationHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def diagnose():
    return LOG_LEVEL <= logging.DEBUG


def formatter(record):
    format_ = "{time} | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}"  # noqa

    if record["exception"] is not None:
        record["extra"]["stack"] = stackprinter.format(
            record["exception"], style="darkbg2"
        )
        format_ += "\n{extra[stack]}\n"

    return format_


def serialize(record):
    dd = {}
    exception = None
    if record["extra"] and "dd" in record["extra"]:
        dd = {
            "trace_id": record["extra"]["dd"].get("trace_id"),
            "span_id": record["extra"]["dd"].get("span_id"),
        }
    if record["exception"] is not None:
        show_vals = "like_source" if diagnose() else None
        exception = stackprinter.format(
            record["exception"], show_vals=show_vals
        )
    subset = {
        "time": record["time"].strftime("%Y-%m-%dT%H:%M:%S"),
        "level": {
            "icon": record["level"].icon,
            "name": record["level"].name,
        },
        "name": record["name"],
        "function": record["function"],
        "line": record["line"],
        "dd": dd,
        "message": record["message"],
        "exception": exception,
    }
    return json.dumps(subset)


def sink(message):
    serialized = serialize(message.record) if JSON_LOGS else message
    print(serialized)


def setup_logging():
    # intercept everything at the root logger
    logging.root.handlers = [LogCorrelationHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # configure loguru
    logger.configure(
        handlers=[
            {
                "sink": sink,
                "level": LOG_LEVEL,
                "format": formatter,
                "diagnose": diagnose(),
                "colorize": True,
            }
        ]
    )

import logging
import os.path as p

import pytest
from conman.logger import _select_log_level
from conman.logger import _setup_logs_dir
from conman.logger import _skip_output_logs
from conman.logger import create_logger


@pytest.mark.parametrize(
    ("override", "path", "expected"),
    (
        (True, None, None),
        (False, None, p.join(p.expanduser("~"), ".conman", "session.log")),
        ("TRUE", None, None),
    ),
)
def test_setup_logs_dir(override, path, expected):
    assert _setup_logs_dir(override, path) == expected


@pytest.mark.parametrize(("choice", "expected"), ((True, True), (False, False)))
def test_skip_output_logs_no_env(choice, expected):
    assert _skip_output_logs(choice) == expected


def test_skip_output_logs_with_env(monkeypatch):
    monkeypatch.setenv("CONMAN_SKIP_LOGGING", "TRUE")
    assert _skip_output_logs(True) == True
    assert _skip_output_logs(False) == True


@pytest.mark.parametrize(
    ("level", "expected"), (("WARNING", 30), (20, 20), (1, 20))
)
def test_select_log_level_no_env(level, expected):
    assert _select_log_level(level) == expected


def test_select_log_level_with_env(monkeypatch):
    monkeypatch.setenv("CONMAN_LOGGING_LEVEL", "WARNING")
    assert _select_log_level("INFO") == 30


# TODO (xames3): Use fixtures instead.
def test_create_logger_message(caplog):
    logger = create_logger(skip_logging=False)
    logger.info("Hello hello world!")
    assert ["Hello hello world!"] == [rec.message for rec in caplog.records]


def test_create_logger_level(caplog):
    logger = create_logger(skip_logging=False, level=logging.DEBUG)
    logger.info("Hello hello world!")
    logger.warning("This is ConMan.")
    assert [20, 30] == [rec.levelno for rec in caplog.records]

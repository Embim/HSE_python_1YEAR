import logging
import sys
from pathlib import Path

_FMT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _file_handler(filename: str) -> logging.FileHandler:
    Path("logs").mkdir(exist_ok=True)
    h = logging.FileHandler(f"logs/{filename}", encoding="utf-8")
    h.setFormatter(logging.Formatter(_FMT, _DATE_FMT))
    return h


def _console_handler() -> logging.StreamHandler:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter(_FMT, _DATE_FMT))
    return h


def setup_logging() -> None:
    api = logging.getLogger("api")
    if not api.handlers:
        api.setLevel(logging.INFO)
        api.addHandler(_file_handler("api.log"))
        api.addHandler(_console_handler())
        api.propagate = False

    db = logging.getLogger("db")
    if not db.handlers:
        db.setLevel(logging.INFO)
        db.addHandler(_file_handler("db.log"))
        db.addHandler(_console_handler())
        db.propagate = False

    sa = logging.getLogger("sqlalchemy.engine")
    if not sa.handlers:
        sa.setLevel(logging.INFO)
        sa.addHandler(_file_handler("db.log"))
        sa.propagate = False

api_logger = logging.getLogger("api")
db_logger = logging.getLogger("db")

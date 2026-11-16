import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "Goofy Mendeleev"


def database_path():
    override = os.environ.get("GOOFY_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        directory = Path.home() / "Library" / "Application Support" / APP_NAME
    elif sys.platform == "win32":
        local_data = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        directory = Path(local_data) / APP_NAME
    else:
        local_data = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
        directory = Path(local_data).expanduser() / "goofy-mendeleev"
    return directory / "tracker.db"


def import_legacy_database(source):
    source = Path(source).expanduser().resolve(strict=True)
    destination = database_path()
    if destination.exists():
        raise FileExistsError(f"Database already exists at {destination}")
    if not source.is_file():
        raise ValueError(f"Choose a legacy SQLite database file: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, staging_name = tempfile.mkstemp(prefix=".tracker-import-", dir=destination.parent)
    os.close(fd)
    staging = Path(staging_name)
    try:
        with closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as original:
            tables = {
                row[0] for row in original.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            if not {"tasks", "habits", "settings"}.issubset(tables):
                raise ValueError(f"This file does not contain a Goofy Mendeleev database: {source}")
            with closing(sqlite3.connect(staging)) as copied:
                original.backup(copied)
                if copied.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise ValueError(f"The SQLite copy failed its integrity check: {source}")
        os.link(staging, destination)
    finally:
        staging.unlink(missing_ok=True)
    return destination

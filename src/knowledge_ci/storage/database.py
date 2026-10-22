"""SQLite engine, short transactions with write-lock retry, and the migration entry point.

SQLite allows one writer at a time; WAL lets readers continue meanwhile. Writers take the
lock at BEGIN (BEGIN IMMEDIATE), so a busy database is detected before any work is done and
can be retried safely. Bodies are never replayed: an error inside a transaction rolls it back
and propagates. Network calls and file IO stay outside transactions.
"""

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy import URL, Connection, Engine, create_engine, event
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

DATABASE_FILE = Path("db") / "knowledge_ci.sqlite3"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

DEFAULT_LOCK_TIMEOUT = 5.0  # seconds SQLite waits for the write lock per attempt
DEFAULT_LOCK_RETRIES = 3  # further attempts after the first, each on a fresh connection
_RETRY_BACKOFF = 0.05  # seconds, multiplied by the attempt number
_READ_ONLY = "knowledge_ci_read_only"  # execution option selecting the reader BEGIN


class StorageError(Exception):
    """Storage is unavailable or inconsistent. Messages never include paths or SQL."""


class StorageBusyError(StorageError):
    """The write lock stayed taken after all retries; the operation may be retried later."""


def database_path(data_dir: Path) -> Path:
    return data_dir / DATABASE_FILE


def _is_busy(exc: DBAPIError) -> bool:
    code = getattr(exc.orig, "sqlite_errorcode", None)
    return code is not None and code & 0xFF in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)


def create_sqlite_engine(
    path: Path, *, lock_timeout: float = DEFAULT_LOCK_TIMEOUT, foreign_keys: bool = True
) -> Engine:
    """Engine whose transactions start with BEGIN IMMEDIATE, or BEGIN plus query_only when
    the connection carries the read-only execution option."""
    engine = create_engine(
        URL.create("sqlite", database=str(path)),
        connect_args={"timeout": lock_timeout},
    )

    @event.listens_for(engine, "connect")
    def _configure(dbapi_connection: Any, _record: Any) -> None:
        dbapi_connection.isolation_level = None  # SQLAlchemy emits BEGIN below
        cursor = dbapi_connection.cursor()
        cursor.execute(f"PRAGMA foreign_keys = {'ON' if foreign_keys else 'OFF'}")
        cursor.execute("PRAGMA journal_mode = WAL")  # persistent; synchronous stays FULL
        cursor.close()

    @event.listens_for(engine, "begin")
    def _begin(connection: Connection) -> None:
        read_only = connection.get_execution_options().get(_READ_ONLY, False)
        connection.exec_driver_sql(f"PRAGMA query_only = {'ON' if read_only else 'OFF'}")
        connection.exec_driver_sql("BEGIN" if read_only else "BEGIN IMMEDIATE")

    return engine


class Database:
    """Opens an initialized database file; run upgrade() first to create or migrate it."""

    def __init__(
        self,
        path: Path,
        *,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
        lock_retries: int = DEFAULT_LOCK_RETRIES,
    ) -> None:
        if not path.is_file():
            raise StorageError("Database is not initialized; run `knowledge-ci migrate`")
        self.engine = create_sqlite_engine(path, lock_timeout=lock_timeout)
        self._reader = self.engine.execution_options(**{_READ_ONLY: True})
        self._lock_retries = lock_retries

    def close(self) -> None:
        self.engine.dispose()

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Write transaction: commit on success, roll back on any exception."""
        session = self._begin()
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def read(self) -> Iterator[Session]:
        """Consistent read-only snapshot; never takes the write lock, writes are refused."""
        session = Session(self._reader)
        try:
            try:
                session.connection()
            except DBAPIError as exc:
                raise StorageError("Database could not start a read") from exc
            yield session
        finally:
            session.close()

    def revision(self) -> str | None:
        """Applied migration revision, or None for a file without migrations."""
        with self.read() as session:
            return MigrationContext.configure(session.connection()).get_current_revision()

    def _begin(self) -> Session:
        for attempt in range(self._lock_retries + 1):
            session = Session(self.engine)
            try:
                session.connection()  # emits BEGIN IMMEDIATE and waits up to lock_timeout
                return session
            except DBAPIError as exc:
                session.close()
                if not _is_busy(exc):
                    raise StorageError("Database could not start a transaction") from exc
                if attempt == self._lock_retries:
                    raise StorageBusyError("Database is busy; retry later") from exc
                time.sleep(_RETRY_BACKOFF * (attempt + 1))
        raise AssertionError("unreachable")


def alembic_config(connection: Connection | None = None) -> Config:
    config = Config()
    # ConfigParser interpolation: a literal "%" in the install path must be doubled.
    config.set_main_option("script_location", str(MIGRATIONS_DIR).replace("%", "%%"))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


@contextmanager
def migration_connection(path: Path, *, lock_timeout: float) -> Iterator[Connection]:
    """One exclusive transaction for a migration run. Foreign keys are off while tables are
    rebuilt (SQLite batch mode) and checked before commit."""
    engine = create_sqlite_engine(path, lock_timeout=lock_timeout, foreign_keys=False)
    try:
        with engine.begin() as connection:
            yield connection
            if connection.exec_driver_sql("PRAGMA foreign_key_check").first() is not None:
                raise StorageError("Migration left rows with broken references")
    finally:
        engine.dispose()


def upgrade(path: Path, *, lock_timeout: float = DEFAULT_LOCK_TIMEOUT) -> str:
    """Create or migrate the database at path to the latest revision and return it."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with migration_connection(path, lock_timeout=lock_timeout) as connection:
            command.upgrade(alembic_config(connection), "head")
            revision = MigrationContext.configure(connection).get_current_revision()
    except DBAPIError as exc:
        if _is_busy(exc):
            raise StorageBusyError("Database is busy; retry later") from exc
        raise StorageError("Database migration failed") from exc
    except CommandError as exc:
        raise StorageError("Database revision is unknown to this application version") from exc
    except OSError as exc:
        raise StorageError("Database location is not accessible") from exc
    assert revision is not None
    return revision


def head_revision() -> str:
    head = ScriptDirectory.from_config(alembic_config()).get_current_head()
    assert head is not None
    return head

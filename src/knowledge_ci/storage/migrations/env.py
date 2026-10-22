"""Alembic environment. The application passes an open connection (storage.database.upgrade);
authoring a revision from the command line passes a database migrated to head instead:

    alembic -x db=<sqlite file> revision --autogenerate --rev-id 0002 -m "add knowledge"
"""

from pathlib import Path
from typing import Any

from alembic import context
from sqlalchemy import Connection

from knowledge_ci.storage.database import DEFAULT_LOCK_TIMEOUT, migration_connection
from knowledge_ci.storage.models import Base, UtcDateTime


def _render_item(type_: str, obj: Any, autogen_context: Any) -> str | bool:
    """Write UtcDateTime as a plain DateTime so revisions never import application code."""
    if type_ == "type" and isinstance(obj, UtcDateTime):
        return "sa.DateTime()"
    return False


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        render_as_batch=True,  # SQLite rebuilds tables for most ALTER operations
        render_item=_render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Offline SQL generation is not supported; migrate a database file")

_connection = context.config.attributes.get("connection")
if _connection is not None:
    _run(_connection)
else:
    _db = context.get_x_argument(as_dictionary=True).get("db")
    if not _db:
        raise RuntimeError("Pass the SQLite file with -x db=<path>")
    with migration_connection(Path(_db), lock_timeout=DEFAULT_LOCK_TIMEOUT) as _cli_connection:
        _run(_cli_connection)

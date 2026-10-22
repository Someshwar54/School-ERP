"""Database engine, sessions and tenant context.

Every tenant-owned table is protected by PostgreSQL row-level security keyed on
the transaction-local setting `app.school_id`. The tenant id is attached to the
SQLAlchemy session (`session.info["school_id"]`) and re-applied at the start of
every transaction, so a commit never silently drops the tenant context.
"""

from collections.abc import Iterator
from uuid import UUID

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, SessionTransaction, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().database_url, pool_pre_ping=True, pool_size=10, max_overflow=10)
    return _engine


def session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


@event.listens_for(Session, "after_begin")
def _apply_tenant(session: Session, _tx: SessionTransaction, connection: Connection) -> None:
    school_id = session.info.get("school_id")
    if school_id:
        connection.execute(text("SELECT set_config('app.school_id', :sid, true)"), {"sid": school_id})


def set_tenant(db: Session, school_id: UUID) -> None:
    """Bind the session to one school for the rest of its lifetime."""
    db.info["school_id"] = str(school_id)
    db.execute(text("SELECT set_config('app.school_id', :sid, true)"), {"sid": str(school_id)})


def get_db() -> Iterator[Session]:
    db = session_factory()()
    try:
        yield db
    finally:
        db.close()

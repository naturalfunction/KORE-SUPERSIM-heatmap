from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text
from sqlmodel import Session, select
from app.models.connection_event import ConnectionEvent


class EventsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_events(
        self,
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[ConnectionEvent]:
        limit = max(1, min(1000, limit))
        stmt = select(ConnectionEvent)
        if start:
            stmt = stmt.where(ConnectionEvent.event_time >= start)
        if end:
            stmt = stmt.where(ConnectionEvent.event_time <= end)
        stmt = stmt.order_by(ConnectionEvent.event_time.desc()).limit(limit)
        return self.session.exec(stmt).all()

    def purge_by_source(self, source: str) -> int:
        """Delete events whose JSON payload.root.source equals the given value.

        Uses SQLite JSON1 function json_extract; works on SQLite and may be
        adapted by SQLAlchemy on other backends that support similar JSON ops.
        Returns number of rows deleted.
        """
        # SQLModel default table name is the lowercased class name
        stmt = text(
            "DELETE FROM connectionevent WHERE json_extract(payload, '$.source') = :src"
        ).bindparams(src=source)
        result = self.session.exec(stmt)
        # In SQLAlchemy 2.0, rowcount is available on the CursorResult
        try:
            deleted = result.rowcount or 0
        except Exception:
            deleted = 0
        self.session.commit()
        return deleted

    def list_with_coords(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[ConnectionEvent]:
        stmt = select(ConnectionEvent).where(
            ConnectionEvent.latitude.is_not(None),
            ConnectionEvent.longitude.is_not(None),
        )
        if start:
            stmt = stmt.where(ConnectionEvent.event_time >= start)
        if end:
            stmt = stmt.where(ConnectionEvent.event_time <= end)
        return self.session.exec(stmt).all()

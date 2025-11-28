from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.db import get_session
from app.models.connection_event import ConnectionEvent
from app.repositories.events_repo import EventsRepository


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=List[ConnectionEvent])
def list_events(
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    session: Session = Depends(get_session),
) -> List[ConnectionEvent]:
    repo = EventsRepository(session)
    return repo.list_events(limit, start_time, end_time)

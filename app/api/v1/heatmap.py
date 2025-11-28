from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.repositories.events_repo import EventsRepository
from app.schemas.heatmap import HeatmapResponse
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/heatmap", tags=["heatmap"])


@router.get("", response_model=HeatmapResponse)
def heatmap(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    session: Session = Depends(get_session),
) -> HeatmapResponse:
    repo = EventsRepository(session)
    events = repo.list_with_coords(start_time, end_time)
    svc = AnalyticsService()
    return svc.build_heatmap(events)

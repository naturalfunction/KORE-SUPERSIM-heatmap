"""FastAPI application exposing the webhook, API, and frontend."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .database import get_session, init_db
from .models import ConnectionEvent
from .schemas import HeatmapPoint, HeatmapResponse, SuperSimEvent

ONLINE_EVENT_TYPES = {
    "com.twilio.iot.supersim.connection.data-session.started",
    "com.twilio.iot.supersim.connection.data-session.updated",
}
OFFLINE_EVENT_TYPES = {
    "com.twilio.iot.supersim.connection.data-session.ended",
}

app = FastAPI(title="Super SIM Heatmap", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/webhooks/supersim")
def ingest_events(
    events: List[SuperSimEvent],
    session: Session = Depends(get_session),
) -> JSONResponse:
    if not events:
        return JSONResponse({"stored": 0})

    stored = 0
    for event in events:
        data = event.data
        location = data.location
        network = data.network
        record = ConnectionEvent(
            event_sid=data.event_sid,
            event_type=data.event_type,
            event_time=data.timestamp,
            sim_iccid=data.sim_iccid,
            sim_unique_name=data.sim_unique_name,
            sim_sid=data.sim_sid,
            fleet_sid=data.fleet_sid,
            apn=data.apn,
            imei=data.imei,
            imsi=data.imsi,
            rat_type=data.rat_type,
            ip_address=data.ip_address,
            account_sid=data.account_sid,
            network_mcc=network.mcc if network else None,
            network_mnc=network.mnc if network else None,
            network_name=network.friendly_name if network else None,
            network_iso_country=network.iso_country if network else None,
            lac=location.lac if location else None,
            cell_id=location.cell_id if location else None,
            latitude=location.lat if location else None,
            longitude=location.lon if location else None,
            data_total=data.data_total,
            data_upload=data.data_upload,
            data_download=data.data_download,
            payload=event.model_dump(mode="json"),
        )
        session.add(record)
        stored += 1

    try:
        session.commit()
    except IntegrityError as exc:  # pragma: no cover - quick feedback for duplicates
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return JSONResponse({"stored": stored})


@app.get("/events", response_model=List[ConnectionEvent])
def list_events(
    limit: int = 100,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    session: Session = Depends(get_session),
) -> List[ConnectionEvent]:
    limit = max(1, min(1000, limit))
    stmt = select(ConnectionEvent)
    if start_time:
        stmt = stmt.where(ConnectionEvent.event_time >= start_time)
    if end_time:
        stmt = stmt.where(ConnectionEvent.event_time <= end_time)
    stmt = stmt.order_by(ConnectionEvent.event_time.desc()).limit(limit)
    results = session.exec(stmt).all()
    return results


@app.get("/heatmap", response_model=HeatmapResponse)
def heatmap(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    session: Session = Depends(get_session),
) -> HeatmapResponse:
    stmt = select(ConnectionEvent).where(
        ConnectionEvent.latitude.is_not(None), ConnectionEvent.longitude.is_not(None)
    )
    if start_time:
        stmt = stmt.where(ConnectionEvent.event_time >= start_time)
    if end_time:
        stmt = stmt.where(ConnectionEvent.event_time <= end_time)

    events = session.exec(stmt).all()
    online_points: List[HeatmapPoint] = []
    offline_points: List[HeatmapPoint] = []

    for event in events:
        if event.latitude is None or event.longitude is None:
            continue
        event_type = (event.event_type or "").lower()
        status = "offline" if event_type in OFFLINE_EVENT_TYPES else "online"
        point = HeatmapPoint(
            lat=event.latitude,
            lon=event.longitude,
            intensity=max(1.0, float(event.data_total or 1) / 1024.0),
            timestamp=event.event_time,
            iccid=event.sim_iccid,
            status=status,
        )
        if status == "offline":
            offline_points.append(point)
        else:
            online_points.append(point)

    return HeatmapResponse(online=online_points, offline=offline_points)

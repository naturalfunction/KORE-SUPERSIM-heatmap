from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from app.core.db import get_session
from app.models.connection_event import ConnectionEvent
from app.schemas.events import SuperSimEvent


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/supersim")
def ingest_events(
    events: List[SuperSimEvent],
    session: Session = Depends(get_session),
):
    if not events:
        return {"stored": 0}

    stored = 0
    for event in events:
        d = event.data
        loc = d.location
        net = d.network
        rec = ConnectionEvent(
            event_sid=d.event_sid,
            event_type=d.event_type,
            event_time=d.timestamp,
            sim_iccid=d.sim_iccid,
            sim_unique_name=d.sim_unique_name,
            sim_sid=d.sim_sid,
            fleet_sid=d.fleet_sid,
            apn=d.apn,
            imei=d.imei,
            imsi=d.imsi,
            rat_type=d.rat_type,
            ip_address=d.ip_address,
            account_sid=d.account_sid,
            network_mcc=net.mcc if net else None,
            network_mnc=net.mnc if net else None,
            network_name=net.friendly_name if net else None,
            network_iso_country=net.iso_country if net else None,
            lac=loc.lac if loc else None,
            cell_id=loc.cell_id if loc else None,
            latitude=loc.lat if loc else None,
            longitude=loc.lon if loc else None,
            data_total=d.data_total,
            data_upload=d.data_upload,
            data_download=d.data_download,
            payload=event.model_dump(mode="json"),
        )
        session.add(rec)
        stored += 1

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    return {"stored": stored}

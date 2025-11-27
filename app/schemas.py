"""Pydantic schemas for request/response bodies."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from typing_extensions import Literal

from pydantic import BaseModel, Field


class NetworkInfo(BaseModel):
    mcc: Optional[str] = None
    mnc: Optional[str] = None
    sid: Optional[str] = None
    iso_country: Optional[str] = None
    friendly_name: Optional[str] = None


class LocationInfo(BaseModel):
    lac: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    cell_id: Optional[str] = Field(default=None, alias="cell_id")


class EventData(BaseModel):
    apn: Optional[str] = None
    imei: Optional[str] = None
    imsi: Optional[str] = None
    network: Optional[NetworkInfo] = None
    sim_sid: Optional[str] = None
    location: Optional[LocationInfo] = None
    rat_type: Optional[str] = None
    event_sid: str
    fleet_sid: Optional[str] = None
    sim_iccid: str
    timestamp: datetime
    data_total: Optional[int] = None
    event_type: str
    ip_address: Optional[str] = None
    account_sid: Optional[str] = None
    data_upload: Optional[int] = None
    data_download: Optional[int] = None
    sim_unique_name: Optional[str] = None
    data_session_sid: Optional[str] = None


class SuperSimEvent(BaseModel):
    data: EventData
    id: str
    time: datetime
    type: str
    source: Optional[str] = None
    dataschema: Optional[str] = None
    specversion: Optional[str] = None
    datacontenttype: Optional[str] = None


class HeatmapPoint(BaseModel):
    lat: float
    lon: float
    intensity: float = 1.0
    timestamp: datetime
    iccid: Optional[str] = None
    status: Literal["online", "offline"]


class HeatmapResponse(BaseModel):
    online: List[HeatmapPoint] = []
    offline: List[HeatmapPoint] = []

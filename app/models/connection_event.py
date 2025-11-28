"""ConnectionEvent SQLModel definition."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class ConnectionEvent(SQLModel, table=True):
    """Stores a flattened snapshot of a Super SIM connection event."""

    id: Optional[int] = Field(default=None, primary_key=True)
    event_sid: str = Field(index=True)
    event_type: str = Field(index=True)
    event_time: datetime = Field(index=True)

    sim_iccid: str = Field(index=True)
    sim_unique_name: Optional[str] = Field(default=None, index=True)
    sim_sid: Optional[str] = Field(default=None, index=True)
    fleet_sid: Optional[str] = Field(default=None, index=True)

    apn: Optional[str] = None
    imei: Optional[str] = Field(default=None, index=True)
    imsi: Optional[str] = Field(default=None, index=True)

    rat_type: Optional[str] = Field(default=None, index=True)
    ip_address: Optional[str] = None
    account_sid: Optional[str] = Field(default=None, index=True)

    network_mcc: Optional[str] = Field(default=None, index=True)
    network_mnc: Optional[str] = Field(default=None, index=True)
    network_name: Optional[str] = None
    network_iso_country: Optional[str] = None

    lac: Optional[str] = Field(default=None, index=True)
    cell_id: Optional[str] = Field(default=None, index=True)
    latitude: Optional[float] = Field(default=None, index=True)
    longitude: Optional[float] = Field(default=None, index=True)

    data_total: Optional[int] = None
    data_upload: Optional[int] = None
    data_download: Optional[int] = None

    payload: Optional[dict] = Field(sa_column=Column(JSON), default=None)

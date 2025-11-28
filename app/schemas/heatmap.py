from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from typing_extensions import Literal

from pydantic import BaseModel


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

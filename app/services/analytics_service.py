from __future__ import annotations

from typing import List

from app.models.connection_event import ConnectionEvent
from app.schemas.heatmap import HeatmapPoint, HeatmapResponse


ONLINE_TYPES = {
    "com.twilio.iot.supersim.connection.data-session.started",
    "com.twilio.iot.supersim.connection.data-session.updated",
}
OFFLINE_TYPES = {"com.twilio.iot.supersim.connection.data-session.ended"}


class AnalyticsService:
    def build_heatmap(self, events: List[ConnectionEvent]) -> HeatmapResponse:
        online_points: List[HeatmapPoint] = []
        offline_points: List[HeatmapPoint] = []

        for e in events:
            if e.latitude is None or e.longitude is None:
                continue
            event_type = (e.event_type or "").lower()
            status = "offline" if event_type in OFFLINE_TYPES else "online"
            point = HeatmapPoint(
                lat=e.latitude,
                lon=e.longitude,
                intensity=max(1.0, float(e.data_total or 1) / 1024.0),
                timestamp=e.event_time,
                iccid=e.sim_iccid,
                status=status,
            )
            (offline_points if status == "offline" else online_points).append(point)

        return HeatmapResponse(online=online_points, offline=offline_points)

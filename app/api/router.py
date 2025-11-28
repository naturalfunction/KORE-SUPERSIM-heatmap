from fastapi import APIRouter
from .v1 import events, heatmap, webhooks
from app.demo import demo

api = APIRouter()
api.include_router(webhooks.router)
api.include_router(events.router)
api.include_router(heatmap.router)
api.include_router(demo.router)

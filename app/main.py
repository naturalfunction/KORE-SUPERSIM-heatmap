"""FastAPI app wiring using modular routers and core DB."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Ensure models are imported so SQLModel metadata is populated before init_db
from app.models import connection_event  # noqa: F401

from app.core.db import init_db
from app.api.router import api
from app.web.pages import router as pages_router


app = FastAPI(title="Super SIM Heatmap", version="0.1.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# Pages and APIs
app.include_router(pages_router)
app.include_router(api)

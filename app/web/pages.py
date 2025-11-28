from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.core.db import get_session
from app.repositories.events_repo import EventsRepository


templates = Jinja2Templates(directory="templates")
router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    # As requested, refreshing the page should delete demo data
    EventsRepository(session).purge_by_source("demo-seeder")
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/health", response_class=PlainTextResponse)
def health() -> PlainTextResponse:
    """Simple health endpoint for container checks.

    Returns 200 OK without touching demo data, so Docker healthchecks
    don't inadvertently purge seeded rows.
    """
    return PlainTextResponse("ok")

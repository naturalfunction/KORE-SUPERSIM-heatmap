from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.db import get_session
from app.repositories.events_repo import EventsRepository


DEMO_SOURCE = "demo-seeder"

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/start")
def start_demo(session: Session = Depends(get_session)) -> dict:
    """Run the seeder to populate demo data.

    Spawns a subprocess using the current Python interpreter to execute
    scripts/seed_events.py, targeting the local webhook endpoint and tagging
    events with a special 'source' so they can be purged later.
    """
    # Ensure any previous demo data is cleared first
    EventsRepository(session).purge_by_source(DEMO_SOURCE)

    # Seeder is colocated under app/demo/utils/seed_events.py
    script_path = Path(__file__).resolve().parent / "utils" / "seed_events.py"
    if not script_path.exists():
        raise HTTPException(status_code=500, detail="Seeder script not found")

    try:
        # Reasonable defaults for a lightweight demo; keep it quick
        cmd = [
            sys.executable,
            str(script_path),
            "--devices",
            "15",
            "--count",
            "120",
            "--batch-size",
            "40",
            "--source",
            DEMO_SOURCE,
            "--url",
            "http://127.0.0.1:8000/webhooks/supersim",
        ]
        # Run synchronously so the UI can refresh immediately after the call
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=exc.stderr or str(exc))

    return {"status": "ok", "output": result.stdout}


@router.post("/stop")
def stop_demo(session: Session = Depends(get_session)) -> dict:
    repo = EventsRepository(session)
    deleted = repo.purge_by_source(DEMO_SOURCE)
    return {"status": "ok", "deleted": deleted}

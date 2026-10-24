"""
SlothDesk: Open-source local-first desktop and downloads clutter janitor.
FastAPI Application and CLI entrypoint.
"""

import os
import sys
import uuid
from typing import List, Optional
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.models import (
    DrawerType,
    FileDescriptor,
    ClassificationResult,
    OrganizationPlan,
    DRAWER_METADATA,
)
from app.janitor import SlothJanitorService, CHAOTIC_SANDBOX_FILES
from app.classifier import get_classifier

app = FastAPI(
    title="SlothDesk",
    description="The Open-Source Local AI Janitor for Chaotic Desktops and Downloads",
    version="1.0.0",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
janitor_service = SlothJanitorService()
classifier = get_classifier()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Renders the SlothDesk dashboard."""
    drawers_data = [d.model_dump() for d in DRAWER_METADATA.values()]
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "drawers": drawers_data,
            "default_files": [f.model_dump() for f in CHAOTIC_SANDBOX_FILES],
        },
    )


@app.get("/api/drawers")
def get_drawers():
    """Returns metadata for all organizing drawers."""
    return {k.value: v.model_dump() for k, v in DRAWER_METADATA.items()}


@app.get("/api/sandbox/default")
def get_sandbox_default():
    """Returns default messy desktop files."""
    return [f.model_dump() for f in CHAOTIC_SANDBOX_FILES]


@app.post("/api/sandbox/messify")
def messify_sandbox():
    """
    Generates a fresh set of messy desktop files with randomized timestamps
    and messy variations for live testing.
    """
    import random
    scrambled = []
    for f in CHAOTIC_SANDBOX_FILES:
        f_copy = f.model_copy()
        f_copy.id = f"f-{uuid.uuid4().hex[:6]}"
        if random.random() > 0.5 and "(" not in f_copy.original_name:
            base, ext = os.path.splitext(f_copy.original_name)
            f_copy.original_name = f"{base} ({random.randint(1, 4)}){ext}"
        scrambled.append(f_copy)
    random.shuffle(scrambled)
    return [f.model_dump() for f in scrambled]


class TidyRequest(BaseModel):
    files: Optional[List[FileDescriptor]] = None


@app.post("/api/sandbox/tidy", response_model=OrganizationPlan)
def tidy_sandbox(payload: Optional[TidyRequest] = None):
    """
    Runs the full local semantic AI classifier over the provided or default messy files.
    Returns categorized drawers, smart renamed files, and sloth metrics.
    """
    files = payload.files if payload and payload.files else CHAOTIC_SANDBOX_FILES
    plan = janitor_service.plan_sandbox_organization(files)
    return plan


@app.post("/api/upload-analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Inspects an uploaded file directly in-memory, classifies its domain drawer,
    and proposes a clean normalized name with zero cloud egress.
    """
    content_bytes = await file.read()
    filename = file.filename or "unknown_file"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    preview_text = ""
    try:
        preview_text = content_bytes[:4000].decode("utf-8", errors="ignore")
    except Exception:
        pass

    descriptor = FileDescriptor(
        id=f"up-{uuid.uuid4().hex[:6]}",
        original_name=filename,
        extension=ext,
        size_bytes=len(content_bytes),
        mime_type=file.content_type or "application/octet-stream",
        preview_text=preview_text,
    )

    result = classifier.classify(descriptor)
    return result.model_dump()


class ScanLocalRequest(BaseModel):
    path: str
    dry_run: bool = True


@app.post("/api/local/scan")
def scan_local_folder(req: ScanLocalRequest):
    """
    Inspects a local folder on the machine.
    Safe default is dry_run=True.
    """
    try:
        res = janitor_service.organize_real_directory(req.path, dry_run=req.dry_run)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filesystem scan error: {str(e)}")


@app.get("/favicon.ico")
def favicon():
    """Silences browser favicon requests."""
    from fastapi import Response
    return Response(status_code=204)


@app.get("/health")
def health_check():
    """Health check endpoint for Render."""
    return {"status": "ok", "app": "SlothDesk", "sloth_status": "happily_napping"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🦥 Starting SlothDesk on http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

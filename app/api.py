"""
FastAPI backend for the Weekly Intelligence Pipeline.

Endpoints:
  GET  /health              — liveness check
  POST /upload              — receive and store a CSV file
  POST /run                 — execute the pipeline (synchronous, ~60-120 s)
  GET  /outputs             — retrieve output paths for a completed batch
  GET  /files/{file_path}   — serve a file for download
"""

import asyncio
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config
from app.services.pipeline_runner import get_outputs, run_pipeline

# ── Directory setup ────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).parent.parent
UPLOAD_DIR = _PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Weekly Intelligence Pipeline API",
    description="Upload a CSV, trigger analysis, download Excel + blog + video outputs.",
    version="1.0.0",
)

# ── Request / Response models ──────────────────────────────────────────────────


class RunRequest(BaseModel):
    file_path: str
    date: str
    resume: bool = False
    model: str = config.DEFAULT_MODEL


class OutputsResponse(BaseModel):
    batch_id: str
    output_dir: str
    workbook: str | None
    blogs: list[str]
    video_script: str | None


# ── Endpoints ──────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Accept a CSV upload and save it to the uploads/ directory.
    Returns the saved file path so the client can pass it to /run.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Sanitise filename and prepend a UUID to prevent collisions
    safe_name = Path(file.filename).name  # strip any path components
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    dest = UPLOAD_DIR / unique_name

    content = await file.read()
    dest.write_bytes(content)

    return {"file_path": str(dest)}


@app.post("/run", response_model=OutputsResponse)
async def run(request: RunRequest):
    """
    Trigger the full pipeline for a given CSV file and date.
    Execution is synchronous on a thread pool (~60-120 seconds).
    Returns output paths when complete.
    """
    # Resolve file path — accept either absolute paths or paths relative to project root
    input_path = Path(request.file_path)
    if not input_path.is_absolute():
        input_path = _PROJECT_ROOT / input_path
    if not input_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Input file not found: {request.file_path}",
        )

    try:
        result = await asyncio.to_thread(
            run_pipeline,
            str(input_path),
            request.date,
            request.model,
            request.resume,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    return OutputsResponse(**result)


@app.get("/outputs", response_model=OutputsResponse)
def outputs(date: str):
    """
    Return output paths for an already-completed batch without re-running.
    Query param: ?date=YYYY-MM-DD
    """
    try:
        result = get_outputs(date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return OutputsResponse(**result)


@app.get("/files/{file_path:path}")
def serve_file(file_path: str):
    """
    Serve a file from the output or uploads directories for download.
    Path traversal protection: only files within OUTPUT_DIR or UPLOAD_DIR are served.
    """
    requested = Path(file_path)
    if not requested.is_absolute():
        # Try resolving relative to project root
        requested = (_PROJECT_ROOT / requested).resolve()
    else:
        requested = requested.resolve()

    # Enforce allowed roots
    allowed_roots = [
        config.OUTPUT_DIR.resolve(),
        UPLOAD_DIR.resolve(),
    ]
    if not any(str(requested).startswith(str(root)) for root in allowed_roots):
        raise HTTPException(
            status_code=403,
            detail="Access denied: file is outside allowed directories.",
        )

    if not requested.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path=str(requested),
        filename=requested.name,
        media_type=_media_type(requested.suffix),
    )


# ── Helpers ────────────────────────────────────────────────────────────────────


def _media_type(suffix: str) -> str:
    return {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".json": "application/json",
    }.get(suffix.lower(), "application/octet-stream")

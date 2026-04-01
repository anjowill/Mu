"""
Pipeline runner service.

Single importable function that wraps the full orchestrator pipeline.
Called by the FastAPI layer — never invoked directly by end users.

Returns a dict of output paths that the API layer serialises to JSON.
"""

import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

import config
from ingestion.parser import parse_csv
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.state_manager import StateManager

# Load .env from project root (one level above this file's parent)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def run_pipeline(
    input_path: str,
    date_str: str,
    model: str = config.DEFAULT_MODEL,
    resume: bool = False,
) -> dict:
    """
    Execute the full weekly intelligence pipeline.

    Args:
        input_path: Absolute or relative path to the input CSV file.
        date_str:   Batch date in YYYY-MM-DD format.
        model:      Claude model identifier (defaults to config.DEFAULT_MODEL).
        resume:     If True, skip stages whose outputs already exist on disk.

    Returns:
        {
            "batch_id":    "weekly_batch_2026_03_31",
            "output_dir":  "/abs/path/output/weekly_batch_2026_03_31",
            "workbook":    "/abs/path/workbook_2026_03_31.xlsx" or None,
            "blogs":       ["/abs/path/blog_market_pulse.md", ...],
            "video_script":"/abs/path/video_script.md" or None,
        }

    Raises:
        ValueError: On missing API key or invalid date format.
        Exception:  Any pipeline failure bubbles up to the API layer.
    """
    # 1. Validate API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file in the project root."
        )

    # 2. Validate date
    if not _DATE_RE.match(date_str):
        raise ValueError(f"date_str must be YYYY-MM-DD, got: {date_str!r}")
    year, month, day = map(int, date_str.split("-"))
    input_date = date(year, month, day)

    # 3. Batch ID and state manager
    batch_id = f"weekly_batch_{date_str.replace('-', '_')}"
    state_manager = StateManager(batch_id)

    # 4. Parse CSV
    csv_path = Path(input_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    raw_batch = parse_csv(csv_path, input_date)

    # 5. Run orchestrator (always non-interactive from the API layer)
    client = anthropic.Anthropic(api_key=api_key)
    orchestrator = PipelineOrchestrator(client, state_manager, model)
    orchestrator.run(
        raw_batch=raw_batch,
        interactive=False,
        resume=resume,
        sheets_only=None,
    )

    # 6. Collect output paths
    return _collect_outputs(batch_id, state_manager)


def get_outputs(date_str: str) -> dict:
    """
    Retrieve output paths for an already-completed batch without re-running.

    Raises:
        ValueError: On invalid date format.
        FileNotFoundError: If the batch output directory does not exist.
    """
    if not _DATE_RE.match(date_str):
        raise ValueError(f"date_str must be YYYY-MM-DD, got: {date_str!r}")

    batch_id = f"weekly_batch_{date_str.replace('-', '_')}"
    batch_dir = config.OUTPUT_DIR / batch_id
    if not batch_dir.exists():
        raise FileNotFoundError(f"No output found for batch: {batch_id}")

    state_manager = StateManager(batch_id)
    return _collect_outputs(batch_id, state_manager)


def _collect_outputs(batch_id: str, state_manager: StateManager) -> dict:
    """Scan the batch output directory and return a path dict."""
    output_dir = state_manager.batch_dir
    content_dir = output_dir / "content"

    # Excel workbook
    workbook_path = state_manager.workbook_path()
    workbook: Optional[str] = str(workbook_path) if workbook_path.exists() else None

    # Blog markdown files
    blogs: list[str] = sorted(
        str(p) for p in content_dir.glob("blog_*.md")
    ) if content_dir.exists() else []

    # Video script
    video_path = content_dir / "video_script.md"
    video_script: Optional[str] = str(video_path) if video_path.exists() else None

    return {
        "batch_id": batch_id,
        "output_dir": str(output_dir),
        "workbook": workbook,
        "blogs": blogs,
        "video_script": video_script,
    }

"""
Pipeline state manager.

Saves and loads every intermediate output to disk as JSON, keyed by batch_id.
Enables resume-from-checkpoint: if a stage's output already exists on disk,
the orchestrator can skip re-running that agent.

Directory layout:
    output/weekly_batch_YYYY_MM_DD/
        state.json                     ← full consolidated state
        sheets/
            sheet1_output.json
            ...
            sheet6_output.json
        briefs/
            topic_candidates.json
            selected_briefs.json
        content/
            blog_<id>.json
            video_script.json
        workbook_YYYY_MM_DD.xlsx       ← written by ExcelExporter
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import config
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import SheetOutput
from schemas.aggregated_schemas import AggregatedInsights
from schemas.brief_schemas import TopicCandidates, SelectedBriefs
from schemas.content_schemas import BlogPerspective, VideoScript, ContentBundle


class StateManager:
    def __init__(self, batch_id: str, output_root: Path = config.OUTPUT_DIR):
        self.batch_id = batch_id
        self.batch_dir = output_root / batch_id
        self._sheets_dir = self.batch_dir / "sheets"
        self._briefs_dir = self.batch_dir / "briefs"
        self._content_dir = self.batch_dir / "content"

        for d in (self.batch_dir, self._sheets_dir, self._briefs_dir, self._content_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ── NormalizedBatch ────────────────────────────────────────────────────────

    def save_normalized_batch(self, batch: NormalizedBatch) -> None:
        self._write(self.batch_dir / "normalized_batch.json", batch.model_dump(mode="json"))

    def load_normalized_batch(self) -> Optional[NormalizedBatch]:
        data = self._read(self.batch_dir / "normalized_batch.json")
        return NormalizedBatch.model_validate(data) if data else None

    # ── SheetOutput ────────────────────────────────────────────────────────────

    def save_sheet_output(self, sheet_id: str, output: SheetOutput) -> None:
        self._write(self._sheets_dir / f"{sheet_id}_output.json", output.model_dump(mode="json"))

    def load_sheet_output(self, sheet_id: str) -> Optional[SheetOutput]:
        data = self._read(self._sheets_dir / f"{sheet_id}_output.json")
        return SheetOutput.model_validate(data) if data else None

    def all_sheets_complete(self, sheet_ids: list[str]) -> bool:
        return all(self.load_sheet_output(sid) is not None for sid in sheet_ids)

    # ── AggregatedInsights ────────────────────────────────────────────────────

    def save_aggregated_insights(self, insights: AggregatedInsights) -> None:
        self._write(self.batch_dir / "aggregated_insights.json", insights.model_dump(mode="json"))

    def load_aggregated_insights(self) -> Optional[AggregatedInsights]:
        data = self._read(self.batch_dir / "aggregated_insights.json")
        return AggregatedInsights.model_validate(data) if data else None

    # ── TopicCandidates ───────────────────────────────────────────────────────

    def save_topic_candidates(self, candidates: TopicCandidates) -> None:
        self._write(self._briefs_dir / "topic_candidates.json", candidates.model_dump(mode="json"))

    def load_topic_candidates(self) -> Optional[TopicCandidates]:
        data = self._read(self._briefs_dir / "topic_candidates.json")
        return TopicCandidates.model_validate(data) if data else None

    # ── SelectedBriefs ────────────────────────────────────────────────────────

    def save_selected_briefs(self, selected: SelectedBriefs) -> None:
        self._write(self._briefs_dir / "selected_briefs.json", selected.model_dump(mode="json"))

    def load_selected_briefs(self) -> Optional[SelectedBriefs]:
        data = self._read(self._briefs_dir / "selected_briefs.json")
        return SelectedBriefs.model_validate(data) if data else None

    # ── ContentBundle ─────────────────────────────────────────────────────────

    def save_content_bundle(self, bundle: ContentBundle) -> None:
        self._write(self.batch_dir / "content_bundle.json", bundle.model_dump(mode="json"))

    def load_content_bundle(self) -> Optional[ContentBundle]:
        data = self._read(self.batch_dir / "content_bundle.json")
        return ContentBundle.model_validate(data) if data else None

    # ── Consolidated state snapshot ───────────────────────────────────────────

    def save_full_state(self, state: dict[str, Any]) -> None:
        self._write(self.batch_dir / "state.json", state)

    # ── Excel workbook path ───────────────────────────────────────────────────

    def workbook_path(self) -> Path:
        date_str = self.batch_id.replace("weekly_batch_", "").replace("_", "-")
        return self.batch_dir / f"workbook_{date_str}.xlsx"

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _write(self, path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, indent=2, default=_json_default), encoding="utf-8")

    def _read(self, path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

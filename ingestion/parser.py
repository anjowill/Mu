"""
Layer 1 — Input Ingestion.

Converts raw CSV file or multi-line paste into a RawBatch.
Both paths produce the same output type so the normalizer never
needs to know which source was used.
"""

import csv
import io
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from schemas.input_schemas import RawBatch, RawDeal

# Expected CSV column names (case-insensitive, stripped)
_COLUMN_ALIASES: dict[str, str] = {
    "company": "company_name",
    "company name": "company_name",
    "name": "company_name",
    "deal size": "deal_size_raw",
    "deal_size": "deal_size_raw",
    "deal size ($ mn)": "deal_size_raw",
    "size": "deal_size_raw",
    "amount": "deal_size_raw",
    "stage": "stage",
    "funding stage": "stage",
    "industry": "industry",
    "sector": "industry",
    "investors": "investors",
    "investor": "investors",
    "investor names": "investors",
    "business model": "business_model",
    "model": "business_model",
    "b2b/b2c": "business_model",
}

_REQUIRED_FIELDS = {"company_name"}


def parse_csv(path: Path, input_date: date) -> RawBatch:
    """Parse a CSV file into a RawBatch."""
    raw_text = path.read_text(encoding="utf-8-sig")  # strip BOM if present
    return _build_batch(raw_text, input_date, source="csv")


def parse_paste(input_date: date, text: Optional[str] = None) -> RawBatch:
    """
    Accept multi-line tab- or comma-delimited paste from stdin (or `text` arg).
    Reads until EOF (Ctrl-Z on Windows / Ctrl-D on Unix).
    """
    if text is None:
        print("Paste your weekly data below, then press Ctrl-Z (Windows) or Ctrl-D (Unix) + Enter:")
        lines = sys.stdin.readlines()
        text = "".join(lines)
    return _build_batch(text, input_date, source="paste")


def _build_batch(raw_text: str, input_date: date, source: str) -> RawBatch:
    checksum = RawBatch.compute_checksum(raw_text)
    batch_id = f"weekly_batch_{input_date.strftime('%Y_%m_%d')}"

    # Detect delimiter: tab if any tab found in first line, else comma
    first_line = raw_text.splitlines()[0] if raw_text.strip() else ""
    delimiter = "\t" if "\t" in first_line else ","

    reader = csv.DictReader(io.StringIO(raw_text), delimiter=delimiter)
    headers = {_normalise_key(k): k for k in (reader.fieldnames or [])}

    deals: list[RawDeal] = []
    for row_idx, row in enumerate(reader, start=2):  # 1-based; row 1 = header
        mapped = _map_row(row, headers)
        if not mapped.get("company_name", "").strip():
            continue  # Skip blank company rows silently
        deals.append(
            RawDeal(
                company_name=mapped.get("company_name", "").strip(),
                deal_size_raw=mapped.get("deal_size_raw") or None,
                stage=mapped.get("stage") or None,
                industry=mapped.get("industry") or None,
                investors=mapped.get("investors") or None,
                business_model=mapped.get("business_model") or None,
                source_row=row_idx,
            )
        )

    return RawBatch(
        batch_id=batch_id,
        input_date=input_date,
        raw_deals=deals,
        input_source=source,  # type: ignore[arg-type]
        input_checksum=checksum,
    )


def _normalise_key(key: str) -> str:
    return key.strip().lower()


def _map_row(row: dict, headers: dict[str, str]) -> dict[str, str]:
    """Map a CSV row to canonical field names using _COLUMN_ALIASES."""
    result: dict[str, str] = {}
    for raw_key, raw_val in row.items():
        normalised = _normalise_key(raw_key)
        canonical = _COLUMN_ALIASES.get(normalised)
        if canonical:
            result[canonical] = (raw_val or "").strip()
    return result

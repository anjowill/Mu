"""
Parse markdown tables produced by LLM responses.

Both functions return plain list[dict[str, str]] — column headers as keys,
cell text as values. Downstream agents validate these dicts into Pydantic models.
"""

import re
from typing import Optional


def parse_markdown_table(text: str) -> tuple[list[dict[str, str]], list[str]]:
    """
    Extract the first markdown table found in `text`.

    Returns:
        rows     — list of {header: cell_value} dicts (separator row excluded)
        warnings — list of any non-fatal issues encountered
    """
    warnings: list[str] = []
    lines = [ln.rstrip() for ln in text.splitlines()]

    # Find the header row (first line containing '|')
    header_idx: Optional[int] = None
    for i, line in enumerate(lines):
        if "|" in line:
            header_idx = i
            break

    if header_idx is None:
        warnings.append("No markdown table found in response.")
        return [], warnings

    headers = _split_row(lines[header_idx])
    if not headers:
        warnings.append("Table header row is empty.")
        return [], warnings

    # Skip separator row (---|---)
    data_start = header_idx + 1
    if data_start < len(lines) and re.match(r"^\s*[\|:]?[-:]+[\|:-]+", lines[data_start]):
        data_start += 1

    rows: list[dict[str, str]] = []
    for line in lines[data_start:]:
        if "|" not in line:
            # Blank line or non-table line signals end of table
            if line.strip() == "":
                continue
            break
        cells = _split_row(line)
        # Pad or trim to match header count
        while len(cells) < len(headers):
            cells.append("")
        cells = cells[: len(headers)]
        rows.append(dict(zip(headers, cells)))

    if not rows:
        warnings.append("Table header found but no data rows parsed.")

    return rows, warnings


def parse_multi_table(text: str, table_count: int) -> tuple[list[list[dict[str, str]]], list[str]]:
    """
    Split text containing `table_count` markdown tables into separate tables.

    Detects boundaries by:
      1. Lines matching "Table N" or "TABLE N" headers
      2. Double blank lines between tables
      3. Bold sub-header lines (**Table N**)

    Returns:
        tables   — list of length table_count, each element is a list of row dicts
        warnings — aggregated warnings
    """
    all_warnings: list[str] = []

    # Strategy: split on "Table N" anchors first
    table_anchors = _find_table_anchors(text, table_count)

    if len(table_anchors) == table_count:
        segments = _split_on_anchors(text, table_anchors)
    else:
        all_warnings.append(
            f"Expected {table_count} table anchors, found {len(table_anchors)}. "
            "Falling back to sequential parsing."
        )
        segments = _split_sequentially(text, table_count)

    tables: list[list[dict[str, str]]] = []
    for i, segment in enumerate(segments):
        rows, warnings = parse_markdown_table(segment)
        if warnings:
            all_warnings.extend([f"[Table {i + 1}] {w}" for w in warnings])
        tables.append(rows)

    # Pad with empty lists if fewer segments than expected
    while len(tables) < table_count:
        all_warnings.append(f"Table {len(tables) + 1} could not be parsed — empty.")
        tables.append([])

    return tables, all_warnings


# ── Internal helpers ───────────────────────────────────────────────────────────

def _split_row(line: str) -> list[str]:
    """Split a markdown table row on '|', strip whitespace, drop empty edge tokens."""
    parts = line.split("|")
    # Remove leading/trailing empty strings from outer pipes
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def _find_table_anchors(text: str, expected: int) -> list[int]:
    """Return character positions of each 'Table N' marker in text."""
    pattern = re.compile(
        r"(?:^|\n)\s*(?:\*{1,2})?\s*[Tt]able\s+\d+[\.\:]?(?:\*{1,2})?",
        re.MULTILINE,
    )
    return [m.start() for m in pattern.finditer(text)]


def _split_on_anchors(text: str, anchors: list[int]) -> list[str]:
    """Slice text into segments using anchor positions."""
    segments: list[str] = []
    for i, start in enumerate(anchors):
        end = anchors[i + 1] if i + 1 < len(anchors) else len(text)
        segments.append(text[start:end])
    return segments


def _split_sequentially(text: str, table_count: int) -> list[str]:
    """
    Fallback: find all markdown table blocks (separated by blank lines)
    and return the first `table_count` of them.
    """
    # Split on two or more consecutive blank lines
    blocks = re.split(r"\n{2,}", text)
    table_blocks = [b for b in blocks if "|" in b and "---" in b]
    return table_blocks[:table_count]

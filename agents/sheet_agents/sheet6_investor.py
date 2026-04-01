"""
Sheet 6 Agent — Investor Intelligence & Thesis Mapping.

Input:  NormalizedBatch only (investor names extracted Python-side)
Output: SheetOutput with rows parsed into Sheet6Row objects

Deduplication of investor names happens before the Claude call,
not delegated to the LLM.
"""

from datetime import datetime, timezone

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import Sheet6Row, SheetOutput
from utils.console import print_agent_start
from utils.table_parser import parse_markdown_table


class Sheet6Agent(BaseAgent):
    SHEET_ID = "sheet_6"
    SHEET_NAME = "Investor Intelligence & Thesis Mapping"

    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=config.PROMPTS_DIR / config.PROMPT_FILES[6],
            temperature=config.SHEET_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_SHEET,
        )

    @property
    def agent_name(self) -> str:
        return "Sheet 6 — Investor Intelligence"

    def run(self, batch: NormalizedBatch) -> SheetOutput:
        print_agent_start(self.agent_name)

        unique_investors = self._deduplicate_investors(batch)
        user_message = self._build_user_message(batch, unique_investors)
        raw_response, usage = self._call_claude(user_message)

        rows, warnings = parse_markdown_table(raw_response)
        validated_rows = self._validate_rows(rows, warnings)

        return SheetOutput(
            sheet_id=self.SHEET_ID,
            sheet_name=self.SHEET_NAME,
            batch_id=batch.batch_id,
            agent_model=self.model,
            generated_at=datetime.now(timezone.utc),
            raw_llm_response=raw_response,
            rows=validated_rows,
            parse_warnings=warnings,
        )

    def _deduplicate_investors(self, batch: NormalizedBatch) -> list[str]:
        """Extract and deduplicate all institutional investors across all deals."""
        seen: set[str] = set()
        result: list[str] = []
        for deal in batch.deals:
            for investor in deal.investors_list:
                key = investor.lower().strip()
                if key and key not in seen:
                    seen.add(key)
                    result.append(investor.strip())
        return sorted(result)

    def _build_user_message(self, batch: NormalizedBatch, investors: list[str]) -> str:
        investor_list = "\n".join(f"- {inv}" for inv in investors) if investors else "- (No investors disclosed)"

        raw_table = self.batch_to_markdown_table(batch)

        return (
            f"CURRENT_WEEK_RAW_TABLE:\n\n{raw_table}\n\n"
            f"UNIQUE INVESTORS THIS WEEK ({len(investors)} after deduplication):\n{investor_list}\n\n"
            "Please complete the Sheet 6 Investor Intelligence & Thesis Mapping as specified. "
            "Include only verifiable institutional investors from the list above."
        )

    def _validate_rows(self, rows: list[dict], warnings: list[str]) -> list[dict]:
        validated = []
        valid_categories = {
            "VC", "CVC", "PE", "Angel", "Accelerator",
            "Strategic", "Asset Manager", "Family Office",
        }
        for row in rows:
            investor_name = row.get("Investor", "?")
            try:
                category = row.get("Category (VC / CVC / PE / Angel / Accelerator / Strategic / Asset Manager / Family Office)", "")
                # Normalise: extract the actual category word from the column value
                category = _extract_category(category, valid_categories)
                if category not in valid_categories:
                    warnings.append(f"[{investor_name}] Unknown category '{category}' — keeping raw.")

                obj = Sheet6Row(
                    investor=investor_name,
                    category=category if category in valid_categories else "VC",
                    industry_focus=row.get("Public industry focus / sectors (short)", ""),
                    portfolio_positioning=row.get("Representative portfolio / positioning (public example(s))", ""),
                    thesis_points=row.get("Up to three public investment thesis points (each thesis — cited)", ""),
                )
                validated.append(obj.model_dump())
            except Exception as e:
                warnings.append(f"Row validation failed for '{investor_name}': {e}")
                validated.append(row)
        return validated


def _extract_category(raw: str, valid_categories: set[str]) -> str:
    """Extract the first matching category keyword from a cell value."""
    if not raw:
        return ""
    for cat in valid_categories:
        if cat.lower() in raw.lower():
            return cat
    return raw.strip()

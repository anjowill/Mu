"""
Sheet 1 Agent — Use of Funds & Strategic Intent.

Input:  NormalizedBatch
Output: SheetOutput with rows parsed into Sheet1Row objects
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import Sheet1Row, SheetOutput
from utils.console import print_agent_start
from utils.table_parser import parse_markdown_table


class Sheet1Agent(BaseAgent):
    SHEET_ID = "sheet_1"
    SHEET_NAME = "Use of Funds"

    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=config.PROMPTS_DIR / config.PROMPT_FILES[1],
            temperature=config.SHEET_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_SHEET,
        )

    @property
    def agent_name(self) -> str:
        return "Sheet 1 — Use of Funds"

    def run(self, batch: NormalizedBatch) -> SheetOutput:
        print_agent_start(self.agent_name)

        user_message = self._build_user_message(batch)
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

    def _build_user_message(self, batch: NormalizedBatch) -> str:
        table = self.batch_to_markdown_table(batch)
        return (
            f"CURRENT_WEEK_RAW_TABLE:\n\n{table}\n\n"
            f"Total deals: {batch.total_deals}\n"
            f"Total disclosed capital: ${batch.total_disclosed_capital_mn:.1f} Mn\n\n"
            "Please complete the Sheet 1 analysis as specified."
        )

    def _validate_rows(self, rows: list[dict], warnings: list[str]) -> list[dict]:
        validated = []
        for row in rows:
            try:
                obj = Sheet1Row(
                    company_name=row.get("Company Name", ""),
                    what_company_does=row.get("What the company does (1 line)", ""),
                    reported_use_of_funds=row.get("Reported use of funds (with citation)", ""),
                    use_of_funds_classification=row.get("Use-of-funds classification", ""),
                    deal_size_mn=_parse_float(row.get("Deal Size ($ Mn)")),
                    stage=row.get("Stage of Funding", ""),
                    industry=row.get("Industry", ""),
                    source_tier_used=row.get("Source Tier Used", ""),
                )
                validated.append(obj.model_dump())
            except Exception as e:
                warnings.append(f"Row validation failed for '{row.get('Company Name', '?')}': {e}")
                validated.append(row)  # Keep raw row so data isn't lost
        return validated


def _parse_float(val: Optional[str]) -> Optional[float]:
    if not val or val.strip() in {"", "–", "-", "N/A"}:
        return None
    try:
        return float(val.replace(",", "").replace("$", "").strip())
    except ValueError:
        return None

"""
Sheet 2 Agent — Founder-Lens Capital Analysis.

Input:  NormalizedBatch + SheetOutput (from Sheet 1)
Output: SheetOutput with rows parsed into Sheet2Row objects

Depends on Sheet 1: the weekly funding table fed to this agent
is the structured Sheet 1 output, not the raw normalized data.
"""

from datetime import datetime, timezone

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import Sheet2Row, SheetOutput
from utils.console import print_agent_start
from utils.table_parser import parse_markdown_table


class Sheet2Agent(BaseAgent):
    SHEET_ID = "sheet_2"
    SHEET_NAME = "Founder-Lens Capital Analysis"

    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=config.PROMPTS_DIR / config.PROMPT_FILES[2],
            temperature=config.SHEET_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_SHEET,
        )

    @property
    def agent_name(self) -> str:
        return "Sheet 2 — Founder-Lens"

    def run(self, batch: NormalizedBatch, sheet1_output: SheetOutput) -> SheetOutput:
        print_agent_start(self.agent_name)

        user_message = self._build_user_message(batch, sheet1_output)
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

    def _build_user_message(self, batch: NormalizedBatch, sheet1: SheetOutput) -> str:
        # Build the weekly funding table from Sheet 1 structured output
        lines = [
            "| Company | Use-of-funds classification | Deal Size ($ Mn) | Stage | Industry | Investors |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for row in sheet1.rows:
            size = row.get("deal_size_mn", "–") or "–"
            size_str = f"{size:.1f}" if isinstance(size, float) else str(size)
            lines.append(
                f"| {row.get('company_name', '')} "
                f"| {row.get('use_of_funds_classification', '')} "
                f"| {size_str} "
                f"| {row.get('stage', '')} "
                f"| {row.get('industry', '')} "
                f"| – |"
            )
        funding_table = "\n".join(lines)

        return (
            f"WEEKLY_FUNDING_TABLE (Structured output from Sheet 1):\n\n{funding_table}\n\n"
            "Please complete the Sheet 2 Founder-Lens Capital Analysis as specified."
        )

    def _validate_rows(self, rows: list[dict], warnings: list[str]) -> list[dict]:
        validated = []
        for row in rows:
            try:
                obj = Sheet2Row(
                    company=row.get("Company", ""),
                    strategy_signal=row.get("Strategy Signal (Evidence + Citation)", ""),
                    capital_signal=row.get("Capital Signal (Evidence + Citation)", ""),
                    execution_signal=row.get("Execution Signal (Evidence + Citation)", ""),
                    founder_learning_insight=row.get("Founder Learning Insight", ""),
                )
                validated.append(obj.model_dump())
            except Exception as e:
                warnings.append(f"Row validation failed for '{row.get('Company', '?')}': {e}")
                validated.append(row)
        return validated

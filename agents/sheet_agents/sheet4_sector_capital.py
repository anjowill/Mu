"""
Sheet 4 Agent — Sector Capital Priority Map.

Input:  NormalizedBatch + SheetOutput (from Sheet 1)
Output: SheetOutput wrapping a Sheet4Output (3 sub-tables)

Parses 3 markdown tables from the LLM response.
"""

import json
from datetime import datetime, timezone

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import (
    Sheet4Output,
    Sheet4SectorCapitalRow,
    Sheet4PriorityRow,
    Sheet4ScorecardRow,
    SheetOutput,
)
from utils.console import print_agent_start
from utils.table_parser import parse_multi_table


class Sheet4Agent(BaseAgent):
    SHEET_ID = "sheet_4"
    SHEET_NAME = "Sector Capital Priority Map"

    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=config.PROMPTS_DIR / config.PROMPT_FILES[4],
            temperature=config.SHEET_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_SHEET,
        )

    @property
    def agent_name(self) -> str:
        return "Sheet 4 — Sector Capital Map"

    def run(self, batch: NormalizedBatch, sheet1_output: SheetOutput) -> SheetOutput:
        print_agent_start(self.agent_name)

        user_message = self._build_user_message(batch, sheet1_output)
        raw_response, usage = self._call_claude(user_message)

        tables, warnings = parse_multi_table(raw_response, table_count=3)
        sheet4_output = self._validate_tables(tables, warnings)

        return SheetOutput(
            sheet_id=self.SHEET_ID,
            sheet_name=self.SHEET_NAME,
            batch_id=batch.batch_id,
            agent_model=self.model,
            generated_at=datetime.now(timezone.utc),
            raw_llm_response=raw_response,
            rows=[sheet4_output.model_dump()],  # Stored as single row containing 3 sub-tables
            parse_warnings=warnings,
        )

    def _build_user_message(self, batch: NormalizedBatch, sheet1: SheetOutput) -> str:
        raw_table = self.batch_to_markdown_table(batch)

        uof_lines = [
            "| Company Name | Use-of-funds classification | Sector | Deal Size ($ Mn) |",
            "| --- | --- | --- | --- |",
        ]
        for row in sheet1.rows:
            size = row.get("deal_size_mn", "–") or "–"
            size_str = f"{size:.1f}" if isinstance(size, float) else str(size)
            uof_lines.append(
                f"| {row.get('company_name', '')} "
                f"| {row.get('use_of_funds_classification', '')} "
                f"| {row.get('industry', '')} "
                f"| {size_str} |"
            )
        uof_table = "\n".join(uof_lines)

        total_capital = sum(
            d.deal_size_mn for d in batch.deals if d.deal_size_mn is not None
        )

        return (
            f"CURRENT_WEEK_RAW_TABLE:\n\n{raw_table}\n\n"
            f"USE_OF_FUNDS_TABLE (from Sheet 1):\n\n{uof_table}\n\n"
            f"Total disclosed capital: ${total_capital:.1f} Mn | Total deals: {batch.total_deals}\n\n"
            "Please generate all three tables as specified in Sheet 4."
        )

    def _validate_tables(
        self, tables: list[list[dict]], warnings: list[str]
    ) -> Sheet4Output:
        t1_rows, t2_rows, t3_rows = tables[0], tables[1], tables[2]

        sector_capital = []
        for r in t1_rows:
            try:
                sector_capital.append(Sheet4SectorCapitalRow(
                    sector=r.get("Sector", ""),
                    deals=_to_int(r.get("Deals", "0")),
                    pct_by_deal_count=_to_float(r.get("% by deal count", "0")),
                    capital_mn=_to_float(r.get("Capital ($ Mn)", "0")),
                    pct_of_capital=_to_float(r.get("% of Capital", "0")),
                ))
            except Exception as e:
                warnings.append(f"Table 1 row error: {e} — {r}")

        priority = []
        for r in t2_rows:
            try:
                priority.append(Sheet4PriorityRow(
                    rank=_to_int(r.get("Rank", "0")),
                    sector=r.get("Sector", ""),
                    capital_mn=_to_float(r.get("Capital ($ Mn)", "0")),
                    pct_of_total=_to_float(r.get("% of Total", "0")),
                    deals=_to_int(r.get("Deals", "0")),
                    priority_tier=r.get("Priority Tier", ""),
                    interpretation=r.get("Interpretation", ""),
                ))
            except Exception as e:
                warnings.append(f"Table 2 row error: {e} — {r}")

        scorecard = []
        for r in t3_rows:
            try:
                scorecard.append(Sheet4ScorecardRow(
                    sector=r.get("Sector", ""),
                    stage_profile=r.get("Stage Profile", ""),
                    capital_quality=r.get("Capital Quality", ""),
                    capital_intent=r.get("Capital Intent", ""),
                    overall_character=r.get("Overall Character", ""),
                ))
            except Exception as e:
                warnings.append(f"Table 3 row error: {e} — {r}")

        return Sheet4Output(
            sector_capital_table=sector_capital,
            sector_priority_table=priority,
            sector_scorecard_table=scorecard,
        )


def _to_int(val: str) -> int:
    try:
        return int(str(val).replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0


def _to_float(val: str) -> float:
    try:
        return float(str(val).replace(",", "").replace("%", "").strip())
    except (ValueError, AttributeError):
        return 0.0

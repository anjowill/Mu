"""
Sheet 5 Agent — Structural Market Distribution.

Input:  NormalizedBatch only (no Sheet 1 dependency — pure computation)
Output: SheetOutput wrapping a Sheet5Output (3 sub-tables)

Pure computation: stage distribution, B2B/B2C split, ticket size buckets.
"""

from datetime import datetime, timezone

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import (
    Sheet5Output,
    Sheet5StageRow,
    Sheet5ModelRow,
    Sheet5TicketRow,
    SheetOutput,
)
from utils.console import print_agent_start
from utils.table_parser import parse_multi_table


class Sheet5Agent(BaseAgent):
    SHEET_ID = "sheet_5"
    SHEET_NAME = "Structural Market Distribution"

    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=config.PROMPTS_DIR / config.PROMPT_FILES[5],
            temperature=config.SHEET_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_SHEET,
        )

    @property
    def agent_name(self) -> str:
        return "Sheet 5 — Structural Market Distribution"

    def run(self, batch: NormalizedBatch) -> SheetOutput:
        print_agent_start(self.agent_name)

        user_message = self._build_user_message(batch)
        raw_response, usage = self._call_claude(user_message)

        # Sheet 5 has Tables 2, 3, 4 per the prompt's numbering — we parse 3 tables
        tables, warnings = parse_multi_table(raw_response, table_count=3)
        sheet5_output = self._validate_tables(tables, warnings)

        return SheetOutput(
            sheet_id=self.SHEET_ID,
            sheet_name=self.SHEET_NAME,
            batch_id=batch.batch_id,
            agent_model=self.model,
            generated_at=datetime.now(timezone.utc),
            raw_llm_response=raw_response,
            rows=[sheet5_output.model_dump()],
            parse_warnings=warnings,
        )

    def _build_user_message(self, batch: NormalizedBatch) -> str:
        raw_table = self.batch_to_markdown_table(batch)
        return (
            f"CURRENT_WEEK_RAW_TABLE:\n\n{raw_table}\n\n"
            f"Total deals: {batch.total_deals} | "
            f"Total disclosed capital: ${batch.total_disclosed_capital_mn:.1f} Mn\n\n"
            "Please generate all three structural distribution tables as specified in Sheet 5."
        )

    def _validate_tables(
        self, tables: list[list[dict]], warnings: list[str]
    ) -> Sheet5Output:
        t_stage, t_model, t_ticket = tables[0], tables[1], tables[2]

        by_stage = []
        for r in t_stage:
            try:
                by_stage.append(Sheet5StageRow(
                    stage=r.get("Stage", ""),
                    capital_mn=_to_float(r.get("Capital ($ Mn)", "0")),
                    pct_of_total=_to_float(r.get("% of Total", "0")),
                    deals=_to_int(r.get("Deals", "0")),
                ))
            except Exception as e:
                warnings.append(f"Stage table row error: {e}")

        by_model = []
        for r in t_model:
            try:
                by_model.append(Sheet5ModelRow(
                    business_model=r.get("Business Model", ""),
                    capital_mn=_to_float(r.get("Capital ($ Mn)", "0")),
                    pct_of_total=_to_float(r.get("% of Total", "0")),
                    deals=_to_int(r.get("Deals", "0")),
                ))
            except Exception as e:
                warnings.append(f"B2B/B2C table row error: {e}")

        by_ticket = []
        for r in t_ticket:
            try:
                by_ticket.append(Sheet5TicketRow(
                    ticket_size=r.get("Ticket Size", ""),
                    deals=_to_int(r.get("Deals", "0")),
                    capital_share_pct=_to_float(r.get("Capital Share", "0")),
                ))
            except Exception as e:
                warnings.append(f"Ticket size table row error: {e}")

        return Sheet5Output(
            capital_by_stage=by_stage,
            b2b_b2c_split=by_model,
            ticket_size_buckets=by_ticket,
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

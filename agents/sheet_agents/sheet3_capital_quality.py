"""
Sheet 3 Agent — Capital Quality Scoring Engine.

Input:  NormalizedBatch + SheetOutput (from Sheet 1)
Output: SheetOutput with rows parsed into Sheet3Row objects

Scores five dimensions (1–5) per company; computes total; maps to tier.
Validates that all scores are in range 1–5.
"""

from datetime import datetime, timezone
from typing import Optional

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import Sheet3Row, SheetOutput
from utils.console import print_agent_start
from utils.table_parser import parse_markdown_table


class Sheet3Agent(BaseAgent):
    SHEET_ID = "sheet_3"
    SHEET_NAME = "Capital Quality Scoring Engine"

    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=config.PROMPTS_DIR / config.PROMPT_FILES[3],
            temperature=config.SHEET_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_SHEET,
        )

    @property
    def agent_name(self) -> str:
        return "Sheet 3 — Capital Quality Scoring"

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
        raw_table = self.batch_to_markdown_table(batch)

        # Build use-of-funds table from Sheet 1
        uof_lines = [
            "| Company Name | Use-of-funds classification | Deal Size ($ Mn) | Stage |",
            "| --- | --- | --- | --- |",
        ]
        for row in sheet1.rows:
            size = row.get("deal_size_mn", "–") or "–"
            size_str = f"{size:.1f}" if isinstance(size, float) else str(size)
            uof_lines.append(
                f"| {row.get('company_name', '')} "
                f"| {row.get('use_of_funds_classification', '')} "
                f"| {size_str} "
                f"| {row.get('stage', '')} |"
            )
        uof_table = "\n".join(uof_lines)

        return (
            f"CURRENT_WEEK_RAW_TABLE:\n\n{raw_table}\n\n"
            f"USE_OF_FUNDS_TABLE (from Sheet 1):\n\n{uof_table}\n\n"
            "Please complete the Sheet 3 Capital Quality Scoring as specified."
        )

    def _validate_rows(self, rows: list[dict], warnings: list[str]) -> list[dict]:
        validated = []
        for row in rows:
            name = row.get("Name", "?")
            try:
                maturity = _to_int(row.get("Maturity"), name, "Maturity", warnings)
                market = _to_int(row.get("Market"), name, "Market", warnings)
                investors = _to_int(row.get("Investors"), name, "Investors", warnings)
                stage_fit = _to_int(row.get("Stage Fit"), name, "Stage Fit", warnings)
                purpose = _to_int(row.get("Purpose"), name, "Purpose", warnings)

                for score, label in [
                    (maturity, "Maturity"), (market, "Market"),
                    (investors, "Investors"), (stage_fit, "Stage Fit"), (purpose, "Purpose"),
                ]:
                    if score is not None and score not in range(1, 6):
                        warnings.append(f"[{name}] {label} score {score} out of range 1–5, capping.")

                # Clamp to 1–5
                def clamp(v: Optional[int]) -> int:
                    if v is None:
                        return 1
                    return max(1, min(5, v))

                m, mk, iv, sf, pu = clamp(maturity), clamp(market), clamp(investors), clamp(stage_fit), clamp(purpose)
                total = m + mk + iv + sf + pu
                tier = _score_to_tier(total)

                obj = Sheet3Row(
                    name=name,
                    stage=row.get("Stage", ""),
                    maturity_score=m,
                    market_score=mk,
                    investor_score=iv,
                    stage_fit_score=sf,
                    purpose_score=pu,
                    total_score=total,
                    total_tier=tier,
                    short_rationale=row.get("Short Rationale", ""),
                )
                validated.append(obj.model_dump())
            except Exception as e:
                warnings.append(f"Row validation failed for '{name}': {e}")
                validated.append(row)
        return validated


def _to_int(val: Optional[str], company: str, field: str, warnings: list[str]) -> Optional[int]:
    if val is None or str(val).strip() in {"", "–", "-"}:
        warnings.append(f"[{company}] Missing {field} score — defaulting to 1.")
        return None
    try:
        return int(str(val).strip())
    except ValueError:
        warnings.append(f"[{company}] Non-integer {field} score '{val}' — defaulting to 1.")
        return None


def _score_to_tier(total: int) -> str:
    for low, high, label in config.CAPITAL_QUALITY_TIERS:
        if low <= total <= high:
            return label
    return "Weak / survival capital"

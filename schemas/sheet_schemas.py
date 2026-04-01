from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator


class SheetOutput(BaseModel):
    sheet_id: str                   # e.g. "sheet_1"
    sheet_name: str
    batch_id: str
    agent_model: str
    generated_at: datetime
    raw_llm_response: str           # Full LLM text, always preserved for audit
    rows: list[dict[str, Any]]      # Parsed table rows as plain dicts
    parse_warnings: list[str] = []  # Any issues encountered during parsing


# ── Sheet 1: Use of Funds ──────────────────────────────────────────────────────

class Sheet1Row(BaseModel):
    company_name: str
    what_company_does: str
    reported_use_of_funds: str       # With inline citations
    use_of_funds_classification: str
    deal_size_mn: Optional[float] = None
    stage: str
    industry: str
    source_tier_used: str


# ── Sheet 2: Founder-Lens Capital Analysis ─────────────────────────────────────

class Sheet2Row(BaseModel):
    company: str
    strategy_signal: str             # Evidence + citation
    capital_signal: str
    execution_signal: str
    founder_learning_insight: str


# ── Sheet 3: Capital Quality Scoring Engine ────────────────────────────────────

VALID_SCORE_RANGE = range(1, 6)  # 1–5 inclusive

class Sheet3Row(BaseModel):
    name: str
    stage: str
    maturity_score: int
    market_score: int
    investor_score: int
    stage_fit_score: int
    purpose_score: int
    total_score: int
    total_tier: str
    short_rationale: str

    @field_validator("maturity_score", "market_score", "investor_score",
                     "stage_fit_score", "purpose_score")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if v not in VALID_SCORE_RANGE:
            raise ValueError(f"Score must be 1–5, got {v}")
        return v


# ── Sheet 4: Sector Capital Priority Map ───────────────────────────────────────

class Sheet4SectorCapitalRow(BaseModel):
    sector: str
    deals: int
    pct_by_deal_count: float
    capital_mn: float
    pct_of_capital: float

class Sheet4PriorityRow(BaseModel):
    rank: int
    sector: str
    capital_mn: float
    pct_of_total: float
    deals: int
    priority_tier: str
    interpretation: str

class Sheet4ScorecardRow(BaseModel):
    sector: str
    stage_profile: str
    capital_quality: str
    capital_intent: str
    overall_character: str

class Sheet4Output(BaseModel):
    sector_capital_table: list[Sheet4SectorCapitalRow]
    sector_priority_table: list[Sheet4PriorityRow]
    sector_scorecard_table: list[Sheet4ScorecardRow]


# ── Sheet 5: Structural Market Distribution ────────────────────────────────────

class Sheet5StageRow(BaseModel):
    stage: str
    capital_mn: float
    pct_of_total: float
    deals: int

class Sheet5ModelRow(BaseModel):
    business_model: str
    capital_mn: float
    pct_of_total: float
    deals: int

class Sheet5TicketRow(BaseModel):
    ticket_size: str
    deals: int
    capital_share_pct: float

class Sheet5Output(BaseModel):
    capital_by_stage: list[Sheet5StageRow]
    b2b_b2c_split: list[Sheet5ModelRow]
    ticket_size_buckets: list[Sheet5TicketRow]


# ── Sheet 6: Investor Intelligence & Thesis Mapping ───────────────────────────

INVESTOR_CATEGORIES = {
    "VC", "CVC", "PE", "Angel", "Accelerator",
    "Strategic", "Asset Manager", "Family Office",
}

class Sheet6Row(BaseModel):
    investor: str
    category: str
    industry_focus: str
    portfolio_positioning: str
    thesis_points: str              # Up to 3 cited thesis statements

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        if v not in INVESTOR_CATEGORIES:
            raise ValueError(f"Invalid investor category: {v!r}")
        return v

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class RankedInsight(BaseModel):
    rank: int
    title: str
    evidence_summary: str            # Drawn only from sheet outputs
    source_sheets: list[str]         # e.g. ["sheet_1", "sheet_4"]
    novelty_score: float             # 0.0–1.0
    business_relevance_score: float  # 0.0–1.0
    evidence_strength_score: float   # 0.0–1.0
    composite_score: float           # 0.35*novelty + 0.40*evidence + 0.25*relevance
    blog_suitable: bool              # True if composite_score >= 0.60

    @field_validator("novelty_score", "business_relevance_score",
                     "evidence_strength_score", "composite_score")
    @classmethod
    def score_bounded(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Score must be 0.0–1.0, got {v}")
        return round(v, 4)


class AggregatedInsights(BaseModel):
    batch_id: str
    generated_at: datetime
    ranked_insights: list[RankedInsight]      # Sorted by composite_score desc
    top_sectors: list[str]                    # Tier 1 sectors from sheet 4
    top_companies_by_quality: list[str]       # Companies with sheet 3 score >= 22
    week_narrative_facts: list[str]           # Bullet facts for grounding content
    cross_sheet_contradictions: list[str]     # Flagged inconsistencies

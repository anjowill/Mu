from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class NarrativeBeat(BaseModel):
    order: int
    beat_title: str        # e.g. "Opening hook", "Core evidence", "Strategic implication"
    description: str       # What this beat covers — 1-2 sentences
    data_points: list[str] # Insight titles or specific fact strings (no invented facts)


class ContentBrief(BaseModel):
    brief_id: str                           # e.g. "brief_founder_lens", "brief_video"
    format: Literal["blog", "video"]
    title: str
    subtitle: str
    angle: str                              # "This brief argues that..." — 1 sentence
    target_audience: str
    opening_hook: str                       # First sentence or scene hook
    core_claim: str                         # Central argument — 1 sentence
    narrative_flow: list[NarrativeBeat]     # Ordered beats: 3-6 for blog, 4-8 for video
    supporting_insights: list[int]          # Ranks from AggregatedInsights.ranked_insights
    estimated_length: str                   # "700-900 words" or "3-4 minutes"
    storytelling_style: Optional[str] = None  # Video only: "explainer", "data narrative", etc.
    priority_score: float                   # 0.0–1.0 assigned by BriefingAgent


class TopicCandidates(BaseModel):
    batch_id: str
    generated_at: datetime
    briefs: list[ContentBrief]   # 5 blog briefs + 1 video brief


class SelectedBriefs(BaseModel):
    batch_id: str
    selected: list[ContentBrief]
    selection_mode: Literal["auto", "interactive"]
    user_notes: Optional[str] = None   # Captured if user annotates in interactive mode

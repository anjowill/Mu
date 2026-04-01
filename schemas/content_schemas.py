from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BlogSection(BaseModel):
    heading: str
    body: str
    grounded_in: list[str]   # Insight titles that back this section


class BlogPerspective(BaseModel):
    perspective_id: str      # Matches ContentBrief.brief_id
    title: str
    subtitle: str
    target_audience: str
    angle: str
    sections: list[BlogSection]
    word_count: int
    source_insights_used: list[int]   # Ranks from AggregatedInsights
    batch_id: str
    generated_at: datetime


class VideoScriptScene(BaseModel):
    scene_number: int
    narration: str
    visual_suggestion: str


class VideoScript(BaseModel):
    hook: str                          # Opening 10-15 seconds
    core_message: str
    scenes: list[VideoScriptScene]
    call_to_action: str
    storytelling_style: str
    estimated_duration: str            # e.g. "3-4 minutes"
    batch_id: str
    generated_at: datetime


class ContentBundle(BaseModel):
    batch_id: str
    blog_perspectives: list[BlogPerspective]
    video_script: VideoScript           # Always present — mandatory deliverable

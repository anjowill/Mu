"""
Briefing Agent — Topic Selection & Content Brief generation.

This is the critical planning layer between analysis and content generation.
It receives AggregatedInsights (structured JSON) and produces ContentBrief
objects — one per blog perspective plus one mandatory video brief.

No content is written here. Briefs define:
- what to write about (title, angle, core_claim)
- how to structure it (narrative_flow with ordered beats)
- which data to use (supporting_insights by rank)
- the storytelling approach (storytelling_style for video)

Temperature: 0.3 — enough strategic judgment, tight enough for schema compliance.
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.aggregated_schemas import AggregatedInsights
from schemas.brief_schemas import ContentBrief, NarrativeBeat, TopicCandidates
from utils.console import print_agent_start


_BRIEFING_SYSTEM_PROMPT = """You are a strategic content planning intelligence.

Your role is to examine a week's validated startup funding analysis and generate structured ContentBriefs — NOT to write the content itself.

## What you receive
- A JSON object containing ranked insights, top sectors, top companies, narrative facts, and any contradictions.
- These are the ONLY facts you may reference. Do not introduce external knowledge.

## What you must produce
Exactly 6 ContentBriefs as a JSON array:
- 5 blog briefs (one per perspective: founder_lens, sector_capital, investor_thesis, capital_quality, market_structure)
- 1 video brief (brief_id: "brief_video")

## JSON schema for each ContentBrief
{
  "brief_id": "brief_founder_lens",          // or brief_sector_capital, brief_investor_thesis, brief_capital_quality, brief_market_structure, brief_video
  "format": "blog",                           // or "video"
  "title": "...",
  "subtitle": "...",
  "angle": "This brief argues that ...",      // 1 sentence
  "target_audience": "...",
  "opening_hook": "...",                      // First sentence or scene hook
  "core_claim": "...",                        // Central argument — 1 sentence
  "narrative_flow": [
    {
      "order": 1,
      "beat_title": "Opening hook",
      "description": "...",                   // 1-2 sentences on what this beat covers
      "data_points": ["insight title 1", "fact string 2"]  // ONLY from provided data
    },
    ...
  ],
  "supporting_insights": [1, 3, 5],          // Ranks from ranked_insights (integers)
  "estimated_length": "700-900 words",        // or "3-4 minutes" for video
  "storytelling_style": null,                 // ONLY for video: "explainer", "data narrative", "case study"
  "priority_score": 0.82                      // 0.0-1.0 your assessment of this brief's strength
}

## Rules
- narrative_flow: 3-6 beats for blog, 4-8 beats for video
- For the video brief: storytelling_style must be set (not null)
- Every data_point in narrative_flow MUST be traceable to the provided facts or insight titles
- Do not invent metrics, company names, or claims not in the input
- The video brief should focus on the SINGLE strongest insight cluster, not recap all blogs
- Return ONLY the JSON array — no prose, no markdown fencing
"""


class BriefingAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=None,  # System prompt is hardcoded here (not a sheet prompt file)
            temperature=config.BRIEFING_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_BRIEFING,
        )
        self.system_prompt = _BRIEFING_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "Briefing Agent — Topic Selection"

    def run(self, insights: AggregatedInsights) -> TopicCandidates:
        print_agent_start(self.agent_name)

        user_message = self._build_user_message(insights)
        raw_response, usage = self._call_claude(user_message)

        briefs = self._parse_briefs(raw_response, insights.batch_id)

        return TopicCandidates(
            batch_id=insights.batch_id,
            generated_at=datetime.now(timezone.utc),
            briefs=briefs,
        )

    def _build_user_message(self, insights: AggregatedInsights) -> str:
        # Pass only the validated structured data — no prose added
        payload = {
            "batch_id": insights.batch_id,
            "ranked_insights": [
                {
                    "rank": ri.rank,
                    "title": ri.title,
                    "evidence_summary": ri.evidence_summary,
                    "source_sheets": ri.source_sheets,
                    "composite_score": ri.composite_score,
                    "blog_suitable": ri.blog_suitable,
                }
                for ri in insights.ranked_insights
                if ri.blog_suitable
            ],
            "top_sectors": insights.top_sectors,
            "top_companies_by_quality": insights.top_companies_by_quality,
            "week_narrative_facts": insights.week_narrative_facts,
            "cross_sheet_contradictions": insights.cross_sheet_contradictions,
            "blog_brief_ids_required": config.BLOG_BRIEF_IDS,
            "video_brief_id_required": config.VIDEO_BRIEF_ID,
        }
        return (
            "VALIDATED_WEEKLY_ANALYSIS:\n\n"
            + json.dumps(payload, indent=2)
            + "\n\nGenerate exactly 6 ContentBriefs (5 blog + 1 video) as a JSON array."
        )

    def _parse_briefs(self, raw_response: str, batch_id: str) -> list[ContentBrief]:
        # Strip any markdown fencing the model may have added
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_response).strip().rstrip("`")

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try extracting just the JSON array
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                raise ValueError(
                    "BriefingAgent: Could not parse JSON array from response. "
                    f"Raw response (first 500 chars): {raw_response[:500]}"
                )

        briefs: list[ContentBrief] = []
        for item in data:
            try:
                # Parse NarrativeBeat sub-objects
                flow = [
                    NarrativeBeat(
                        order=beat.get("order", i + 1),
                        beat_title=beat.get("beat_title", ""),
                        description=beat.get("description", ""),
                        data_points=beat.get("data_points", []),
                    )
                    for i, beat in enumerate(item.get("narrative_flow", []))
                ]
                brief = ContentBrief(
                    brief_id=item.get("brief_id", ""),
                    format=item.get("format", "blog"),
                    title=item.get("title", ""),
                    subtitle=item.get("subtitle", ""),
                    angle=item.get("angle", ""),
                    target_audience=item.get("target_audience", ""),
                    opening_hook=item.get("opening_hook", ""),
                    core_claim=item.get("core_claim", ""),
                    narrative_flow=flow,
                    supporting_insights=item.get("supporting_insights", []),
                    estimated_length=item.get("estimated_length", ""),
                    storytelling_style=item.get("storytelling_style"),
                    priority_score=float(item.get("priority_score", 0.5)),
                )
                briefs.append(brief)
            except Exception as e:
                raise ValueError(f"BriefingAgent: Failed to parse brief '{item.get('brief_id', '?')}': {e}")

        # Ensure video brief is always present
        has_video = any(b.brief_id == config.VIDEO_BRIEF_ID for b in briefs)
        if not has_video:
            raise ValueError(
                f"BriefingAgent: Response missing mandatory video brief ('{config.VIDEO_BRIEF_ID}')"
            )

        return briefs

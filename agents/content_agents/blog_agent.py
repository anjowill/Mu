"""
Blog Agent — generates one blog draft per ContentBrief.

Receives a ContentBrief (not raw insights) and follows its narrative_flow
as a structural guide. The agent cannot deviate from the planned structure
or introduce facts not present in brief.supporting_insights data_points.

One separate Claude call is made per blog brief.
Temperature: 0.7 for creative but grounded output.
"""

import json
from datetime import datetime, timezone

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.aggregated_schemas import AggregatedInsights
from schemas.brief_schemas import ContentBrief
from schemas.content_schemas import BlogPerspective, BlogSection
from utils.console import print_agent_start


_BLOG_SYSTEM_PROMPT = """You are a professional capital-markets and startup-ecosystem writer.

You write fact-based, analyst-grade blog posts for a specific target audience.

## Your governing rules
1. Use ONLY the facts provided in the user message JSON. Do not introduce external knowledge.
2. Follow the narrative_flow beats IN ORDER. Each beat becomes a section.
3. Every major claim must trace to one of the data_points listed in the corresponding beat.
4. Do not overstate certainty. Distinguish between confirmed data and interpretations.
5. Use clear headings (##) for each section.
6. Write for the stated target_audience — adjust tone and technicality accordingly.
7. Open with the provided opening_hook exactly as stated (you may expand it by 1-2 sentences).
8. The core_claim must appear clearly in the introduction.

## Output format (strict)
Return a JSON object with this structure:
{
  "title": "...",
  "subtitle": "...",
  "sections": [
    {
      "heading": "...",
      "body": "...",       // 100-200 words per section
      "grounded_in": ["insight title or fact string used"]
    },
    ...
  ]
}

Return ONLY the JSON object. No markdown fencing.
"""


class BlogAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=None,
            temperature=config.CONTENT_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_BLOG,
        )
        self.system_prompt = _BLOG_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "Blog Agent"

    def run(
        self,
        brief: ContentBrief,
        insights: AggregatedInsights,
    ) -> BlogPerspective:
        print_agent_start(f"Blog Agent — {brief.brief_id}")

        user_message = self._build_user_message(brief, insights)
        raw_response, usage = self._call_claude(user_message)

        sections = self._parse_sections(raw_response, brief)
        word_count = sum(len(s.body.split()) for s in sections)

        return BlogPerspective(
            perspective_id=brief.brief_id,
            title=brief.title,
            subtitle=brief.subtitle,
            target_audience=brief.target_audience,
            angle=brief.angle,
            sections=sections,
            word_count=word_count,
            source_insights_used=brief.supporting_insights,
            batch_id=insights.batch_id,
            generated_at=datetime.now(timezone.utc),
        )

    def _build_user_message(self, brief: ContentBrief, insights: AggregatedInsights) -> str:
        # Extract only the insights this brief relies on
        relevant_insights = [
            {
                "rank": ri.rank,
                "title": ri.title,
                "evidence_summary": ri.evidence_summary,
            }
            for ri in insights.ranked_insights
            if ri.rank in brief.supporting_insights
        ]

        payload = {
            "brief_id": brief.brief_id,
            "title": brief.title,
            "subtitle": brief.subtitle,
            "angle": brief.angle,
            "target_audience": brief.target_audience,
            "opening_hook": brief.opening_hook,
            "core_claim": brief.core_claim,
            "estimated_length": brief.estimated_length,
            "narrative_flow": [
                {
                    "order": beat.order,
                    "beat_title": beat.beat_title,
                    "description": beat.description,
                    "data_points": beat.data_points,
                }
                for beat in brief.narrative_flow
            ],
            "available_evidence": relevant_insights,
            "week_narrative_facts": insights.week_narrative_facts,
        }

        return (
            "CONTENT_BRIEF_AND_EVIDENCE:\n\n"
            + json.dumps(payload, indent=2)
            + "\n\nWrite the blog post following the narrative_flow exactly. "
            "Return only the JSON object."
        )

    def _parse_sections(self, raw_response: str, brief: ContentBrief) -> list[BlogSection]:
        import re
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_response).strip().rstrip("`")

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                # Fallback: create sections from narrative_flow beats with raw text
                return [
                    BlogSection(
                        heading=beat.beat_title,
                        body=raw_response,  # Dump raw response into first section
                        grounded_in=beat.data_points,
                    )
                    for beat in brief.narrative_flow[:1]
                ]

        sections = []
        for s in data.get("sections", []):
            sections.append(BlogSection(
                heading=s.get("heading", ""),
                body=s.get("body", ""),
                grounded_in=s.get("grounded_in", []),
            ))
        return sections

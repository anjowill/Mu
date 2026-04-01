"""
Video Script Agent — mandatory core deliverable.

Receives the video ContentBrief and generates a structured VideoScript:
- Hook (10-15 seconds)
- Scenes with narration + visual suggestion
- Call to action

Uses brief.narrative_flow for scene structure and brief.storytelling_style
for tone. Always runs — never optional.

Temperature: 0.7 for engaging narrative, grounded in brief data only.
"""

import json
import re
from datetime import datetime, timezone

import anthropic

import config
from agents.base_agent import BaseAgent
from schemas.aggregated_schemas import AggregatedInsights
from schemas.brief_schemas import ContentBrief
from schemas.content_schemas import VideoScript, VideoScriptScene
from utils.console import print_agent_start


_VIDEO_SYSTEM_PROMPT = """You are a professional video content scriptwriter specialising in financial and startup ecosystem explainers.

You write tight, engaging scripts for short-form educational videos (3-5 minutes).

## Your governing rules
1. Use ONLY the facts provided in the user message JSON. Do not add external examples or data.
2. Follow the narrative_flow beats IN ORDER — each beat becomes one or more scenes.
3. Keep language simple, direct, and explanatory. Avoid jargon unless explained.
4. Separate narration from visual suggestions clearly.
5. The hook must be under 15 seconds when read aloud (~25-35 words).
6. Each scene's narration should be 40-90 words (20-45 seconds at normal speaking pace).
7. Apply the stated storytelling_style throughout.

## Output format (strict)
Return a JSON object with this structure:
{
  "hook": "...",                       // 25-35 words max
  "core_message": "...",               // 1 sentence summary of the video's argument
  "scenes": [
    {
      "scene_number": 1,
      "narration": "...",              // 40-90 words
      "visual_suggestion": "..."       // what to show on screen (text, animation, chart type)
    },
    ...
  ],
  "call_to_action": "...",
  "storytelling_style": "...",
  "estimated_duration": "..."          // e.g. "3-4 minutes"
}

Return ONLY the JSON object. No markdown fencing.
"""


class VideoScriptAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic, model: str = config.DEFAULT_MODEL):
        super().__init__(
            client=client,
            model=model,
            prompt_path=None,
            temperature=config.CONTENT_AGENT_TEMPERATURE,
            max_tokens=config.MAX_TOKENS_VIDEO,
        )
        self.system_prompt = _VIDEO_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "Video Script Agent"

    def run(
        self,
        brief: ContentBrief,
        insights: AggregatedInsights,
    ) -> VideoScript:
        print_agent_start(self.agent_name)

        user_message = self._build_user_message(brief, insights)
        raw_response, usage = self._call_claude(user_message)

        return self._parse_script(raw_response, brief, insights.batch_id)

    def _build_user_message(self, brief: ContentBrief, insights: AggregatedInsights) -> str:
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
            "angle": brief.angle,
            "opening_hook": brief.opening_hook,
            "core_claim": brief.core_claim,
            "storytelling_style": brief.storytelling_style or "explainer",
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
            "VIDEO_CONTENT_BRIEF_AND_EVIDENCE:\n\n"
            + json.dumps(payload, indent=2)
            + "\n\nWrite the video script following the narrative_flow as scene structure. "
            "Return only the JSON object."
        )

    def _parse_script(
        self, raw_response: str, brief: ContentBrief, batch_id: str
    ) -> VideoScript:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_response).strip().rstrip("`")

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                # Fallback: wrap entire raw response as a single scene
                return VideoScript(
                    hook=brief.opening_hook,
                    core_message=brief.core_claim,
                    scenes=[VideoScriptScene(
                        scene_number=1,
                        narration=raw_response[:500],
                        visual_suggestion="(parsing error — review raw output)",
                    )],
                    call_to_action="",
                    storytelling_style=brief.storytelling_style or "explainer",
                    estimated_duration=brief.estimated_length,
                    batch_id=batch_id,
                    generated_at=datetime.now(timezone.utc),
                )

        scenes = [
            VideoScriptScene(
                scene_number=s.get("scene_number", i + 1),
                narration=s.get("narration", ""),
                visual_suggestion=s.get("visual_suggestion", ""),
            )
            for i, s in enumerate(data.get("scenes", []))
        ]

        return VideoScript(
            hook=data.get("hook", brief.opening_hook),
            core_message=data.get("core_message", brief.core_claim),
            scenes=scenes,
            call_to_action=data.get("call_to_action", ""),
            storytelling_style=data.get("storytelling_style", brief.storytelling_style or "explainer"),
            estimated_duration=data.get("estimated_duration", brief.estimated_length),
            batch_id=batch_id,
            generated_at=datetime.now(timezone.utc),
        )

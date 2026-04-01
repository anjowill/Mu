"""
Pipeline Orchestrator — chains all agents in dependency order.

Execution sequence:
  Stage 0: Normalize
  Stage 1: Sheet 1 (no upstream dependency)
  Stage 2: Sheets 2, 3, 4 (depend on Sheet 1) + Sheets 5, 6 (NormalizedBatch only)
  Stage 3: Aggregator (pure Python — all 6 sheets)
  Stage 4: Briefing Agent (topic selection + content brief generation)
  Stage 5: User Review Gate (--interactive or --auto)
  Stage 6: Blog Agent × N + Video Script Agent (always)
  Stage 7: Export (Excel + Markdown)

Resume behavior: checks state on disk before calling each agent.
If state exists and resume=True, that stage is skipped.
"""

from pathlib import Path
from typing import Optional

import anthropic

import config
from agents.aggregator_agent import aggregate
from agents.briefing_agent import BriefingAgent
from agents.content_agents.blog_agent import BlogAgent
from agents.content_agents.video_script_agent import VideoScriptAgent
from agents.sheet_agents.sheet1_use_of_funds import Sheet1Agent
from agents.sheet_agents.sheet2_founder_lens import Sheet2Agent
from agents.sheet_agents.sheet3_capital_quality import Sheet3Agent
from agents.sheet_agents.sheet4_sector_capital import Sheet4Agent
from agents.sheet_agents.sheet5_structural_market import Sheet5Agent
from agents.sheet_agents.sheet6_investor import Sheet6Agent
from exporters.excel_exporter import ExcelExporter
from exporters.markdown_exporter import MarkdownExporter
from ingestion.normalizer import normalize
from pipeline.state_manager import StateManager
from schemas.brief_schemas import SelectedBriefs, ContentBrief
from schemas.content_schemas import ContentBundle
from schemas.input_schemas import RawBatch
from utils.console import (
    get_console,
    print_briefs_table,
    print_error,
    print_final_summary,
    print_section,
    print_warning,
)

_console = get_console()

SHEET_IDS = ["sheet_1", "sheet_2", "sheet_3", "sheet_4", "sheet_5", "sheet_6"]


class PipelineOrchestrator:
    def __init__(
        self,
        client: anthropic.Anthropic,
        state_manager: StateManager,
        model: str = config.DEFAULT_MODEL,
    ):
        self.client = client
        self.sm = state_manager
        self.model = model

    def run(
        self,
        raw_batch: RawBatch,
        interactive: bool = False,
        resume: bool = False,
        sheets_only: Optional[list[int]] = None,
    ) -> ContentBundle:
        """
        Run the full pipeline.

        Args:
            raw_batch:    The parsed weekly input.
            interactive:  If True, pause after briefing for user review.
            resume:       If True, skip stages with existing state.
            sheets_only:  If set, run only the specified sheet numbers (1-6).
        """
        # ── Stage 0: Normalize ────────────────────────────────────────────────
        print_section("Stage 0: Normalizing input data")
        batch = self.sm.load_normalized_batch() if resume else None
        if batch is None:
            batch = normalize(raw_batch)
            self.sm.save_normalized_batch(batch)
        else:
            _console.print("[dim]Normalized batch loaded from state (skipping).[/dim]")

        if sheets_only:
            _console.print(f"[yellow]--sheets mode: running only sheets {sheets_only}[/yellow]")

        # ── Stage 1: Sheet 1 ──────────────────────────────────────────────────
        print_section("Stage 1: Sheet 1 — Use of Funds")
        sheet1 = self.sm.load_sheet_output("sheet_1") if resume else None
        if sheet1 is None and (sheets_only is None or 1 in sheets_only):
            agent = Sheet1Agent(self.client, self.model)
            sheet1 = agent.run(batch)
            self.sm.save_sheet_output("sheet_1", sheet1)
            _print_warnings(sheet1.parse_warnings)
        elif sheet1:
            _console.print("[dim]Sheet 1 loaded from state (skipping).[/dim]")

        if sheet1 is None:
            raise RuntimeError("Sheet 1 output is required for downstream sheets. Run without --resume or include sheet 1.")

        # ── Stage 2: Sheets 2–6 ───────────────────────────────────────────────
        print_section("Stage 2: Sheets 2–6 (parallel-eligible; running sequentially)")

        sheet_outputs: dict = {"sheet_1": sheet1}

        # Sheet 2 (depends on sheet 1)
        s2 = self.sm.load_sheet_output("sheet_2") if resume else None
        if s2 is None and (sheets_only is None or 2 in sheets_only):
            s2 = Sheet2Agent(self.client, self.model).run(batch, sheet1)
            self.sm.save_sheet_output("sheet_2", s2)
            _print_warnings(s2.parse_warnings)
        elif s2:
            _console.print("[dim]Sheet 2 loaded from state.[/dim]")
        if s2:
            sheet_outputs["sheet_2"] = s2

        # Sheet 3 (depends on sheet 1)
        s3 = self.sm.load_sheet_output("sheet_3") if resume else None
        if s3 is None and (sheets_only is None or 3 in sheets_only):
            s3 = Sheet3Agent(self.client, self.model).run(batch, sheet1)
            self.sm.save_sheet_output("sheet_3", s3)
            _print_warnings(s3.parse_warnings)
        elif s3:
            _console.print("[dim]Sheet 3 loaded from state.[/dim]")
        if s3:
            sheet_outputs["sheet_3"] = s3

        # Sheet 4 (depends on sheet 1)
        s4 = self.sm.load_sheet_output("sheet_4") if resume else None
        if s4 is None and (sheets_only is None or 4 in sheets_only):
            s4 = Sheet4Agent(self.client, self.model).run(batch, sheet1)
            self.sm.save_sheet_output("sheet_4", s4)
            _print_warnings(s4.parse_warnings)
        elif s4:
            _console.print("[dim]Sheet 4 loaded from state.[/dim]")
        if s4:
            sheet_outputs["sheet_4"] = s4

        # Sheet 5 (NormalizedBatch only)
        s5 = self.sm.load_sheet_output("sheet_5") if resume else None
        if s5 is None and (sheets_only is None or 5 in sheets_only):
            s5 = Sheet5Agent(self.client, self.model).run(batch)
            self.sm.save_sheet_output("sheet_5", s5)
            _print_warnings(s5.parse_warnings)
        elif s5:
            _console.print("[dim]Sheet 5 loaded from state.[/dim]")
        if s5:
            sheet_outputs["sheet_5"] = s5

        # Sheet 6 (NormalizedBatch only)
        s6 = self.sm.load_sheet_output("sheet_6") if resume else None
        if s6 is None and (sheets_only is None or 6 in sheets_only):
            s6 = Sheet6Agent(self.client, self.model).run(batch)
            self.sm.save_sheet_output("sheet_6", s6)
            _print_warnings(s6.parse_warnings)
        elif s6:
            _console.print("[dim]Sheet 6 loaded from state.[/dim]")
        if s6:
            sheet_outputs["sheet_6"] = s6

        # ── Stage 3: Aggregator ───────────────────────────────────────────────
        print_section("Stage 3: Aggregating insights (pure Python)")
        insights = self.sm.load_aggregated_insights() if resume else None
        if insights is None:
            insights = aggregate(batch, sheet_outputs)
            self.sm.save_aggregated_insights(insights)
            _console.print(
                f"[green]✓ Aggregator[/green]  "
                f"[dim]{len(insights.ranked_insights)} insights ranked, "
                f"{sum(1 for i in insights.ranked_insights if i.blog_suitable)} blog-suitable[/dim]"
            )
        else:
            _console.print("[dim]Aggregated insights loaded from state.[/dim]")

        # ── Stage 4: Briefing ─────────────────────────────────────────────────
        print_section("Stage 4: Briefing — Topic Selection & Content Briefs")
        selected = self.sm.load_selected_briefs() if resume else None

        if selected is None:
            candidates = self.sm.load_topic_candidates() if resume else None
            if candidates is None:
                candidates = BriefingAgent(self.client, self.model).run(insights)
                self.sm.save_topic_candidates(candidates)

            # ── Stage 5: User Review Gate ──────────────────────────────────────
            if interactive:
                selected = _interactive_review(candidates, self.sm.batch_id)
            else:
                selected = SelectedBriefs(
                    batch_id=batch.batch_id,
                    selected=candidates.briefs,
                    selection_mode="auto",
                )
            self.sm.save_selected_briefs(selected)
        else:
            _console.print("[dim]Selected briefs loaded from state (skipping briefing).[/dim]")

        # ── Stage 6: Content Generation ───────────────────────────────────────
        print_section("Stage 6: Generating blog drafts and video script")
        bundle = self.sm.load_content_bundle() if resume else None

        if bundle is None:
            blog_briefs = [b for b in selected.selected if b.format == "blog"]
            video_brief = next((b for b in selected.selected if b.format == "video"), None)

            blogs = []
            blog_agent = BlogAgent(self.client, self.model)
            for brief in blog_briefs:
                blog = blog_agent.run(brief, insights)
                blogs.append(blog)

            if video_brief is None:
                print_warning("No video brief found in selected briefs — video script will not be generated.")
                raise RuntimeError("Video brief is mandatory. Check BriefingAgent output.")

            video_script = VideoScriptAgent(self.client, self.model).run(video_brief, insights)

            bundle = ContentBundle(
                batch_id=batch.batch_id,
                blog_perspectives=blogs,
                video_script=video_script,
            )
            self.sm.save_content_bundle(bundle)
        else:
            _console.print("[dim]Content bundle loaded from state.[/dim]")

        # ── Stage 7: Export ───────────────────────────────────────────────────
        print_section("Stage 7: Exporting workbook and markdown files")

        workbook_path = self.sm.workbook_path()
        ExcelExporter().export(sheet_outputs, workbook_path, batch.batch_id)

        content_dir = self.sm.batch_dir / "content"
        md_paths = MarkdownExporter().export(bundle, content_dir)

        # Consolidated state snapshot
        self.sm.save_full_state({
            "batch_id": batch.batch_id,
            "total_deals": batch.total_deals,
            "total_disclosed_capital_mn": batch.total_disclosed_capital_mn,
            "sheets_completed": list(sheet_outputs.keys()),
            "insights_count": len(insights.ranked_insights),
            "blog_count": len(bundle.blog_perspectives),
            "video_script": "generated",
            "workbook": str(workbook_path),
        })

        output_paths = {"Excel Workbook": str(workbook_path), **md_paths}
        print_final_summary(batch.batch_id, output_paths)

        return bundle


# ── Interactive review gate ────────────────────────────────────────────────────

def _interactive_review(candidates, batch_id: str) -> SelectedBriefs:
    from schemas.brief_schemas import TopicCandidates
    print_section("Stage 5: Interactive Brief Review")
    print_briefs_table(candidates.briefs)

    _console.print("\nEnter the numbers of briefs to INCLUDE (comma-separated), or press Enter to include ALL:")
    _console.print(f"[dim]Available: 1–{len(candidates.briefs)} | Video brief is mandatory[/dim]")

    raw = input("> ").strip()
    user_notes = ""

    if not raw:
        selected_briefs = candidates.briefs
    else:
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",")]
            selected_briefs = [candidates.briefs[i] for i in indices if 0 <= i < len(candidates.briefs)]
        except (ValueError, IndexError):
            print_warning("Invalid selection — including all briefs.")
            selected_briefs = candidates.briefs

    # Always ensure video brief is included
    video_brief = next((b for b in candidates.briefs if b.format == "video"), None)
    has_video = any(b.format == "video" for b in selected_briefs)
    if video_brief and not has_video:
        selected_briefs.append(video_brief)
        _console.print("[yellow]Video brief added automatically (mandatory).[/yellow]")

    _console.print("\nAdd any notes for this selection (optional, press Enter to skip):")
    user_notes = input("> ").strip()

    return SelectedBriefs(
        batch_id=batch_id,
        selected=selected_briefs,
        selection_mode="interactive",
        user_notes=user_notes or None,
    )


def _print_warnings(warnings: list[str]) -> None:
    for w in warnings:
        print_warning(w)

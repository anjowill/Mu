"""
Weekly Intelligence Pipeline — CLI entry point.

Usage examples:
    python main.py --input data.csv --date 2026-04-03
    python main.py --paste --date 2026-04-03
    python main.py --input data.csv --date 2026-04-03 --interactive
    python main.py --date 2026-04-03 --resume
    python main.py --date 2026-04-03 --resume --export-only
    python main.py --input data.csv --date 2026-04-03 --sheets 1 3
    python main.py --input data.csv --date 2026-04-03 --model claude-sonnet-4-6
"""

import argparse
import os
import sys
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import anthropic

import config
from ingestion.parser import parse_csv, parse_paste
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.state_manager import StateManager
from utils.console import get_console, print_error, print_section

_console = get_console()


def main() -> int:
    args = _parse_args()

    # ── Resolve date ──────────────────────────────────────────────────────────
    try:
        input_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print_error(f"Invalid date format: '{args.date}'. Use YYYY-MM-DD.")
        return 1

    batch_id = f"weekly_batch_{input_date.strftime('%Y_%m_%d')}"

    # ── API key ───────────────────────────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print_error(
            "ANTHROPIC_API_KEY not set.\n"
            "Add it to a .env file or set it as an environment variable.\n"
            "Copy .env.example to .env and fill in your key."
        )
        return 1

    client = anthropic.Anthropic(api_key=api_key)
    model = args.model or config.DEFAULT_MODEL

    # ── Output directory ──────────────────────────────────────────────────────
    output_root = Path(args.output_dir) if args.output_dir else config.OUTPUT_DIR
    state_manager = StateManager(batch_id, output_root)

    _console.print(f"\n[bold]Weekly Intelligence Pipeline[/bold]")
    _console.print(f"Batch: [cyan]{batch_id}[/cyan]  |  Model: [cyan]{model}[/cyan]")
    _console.print(f"Output: [dim]{state_manager.batch_dir}[/dim]\n")

    # ── Export-only mode ──────────────────────────────────────────────────────
    if args.export_only:
        return _run_export_only(state_manager)

    # ── Parse input ───────────────────────────────────────────────────────────
    if not args.resume:
        if args.input:
            input_path = Path(args.input)
            if not input_path.exists():
                print_error(f"Input file not found: {input_path}")
                return 1
            print_section("Parsing CSV input")
            raw_batch = parse_csv(input_path, input_date)
        elif args.paste:
            print_section("Accepting paste input")
            raw_batch = parse_paste(input_date)
        else:
            print_error("Provide --input <file.csv> or --paste. Use --resume to continue from saved state.")
            return 1

        _console.print(f"[green]✓[/green] Parsed {len(raw_batch.raw_deals)} deals  "
                       f"[dim](checksum: {raw_batch.input_checksum[:12]}…)[/dim]")
    else:
        # Resume: load existing normalized batch; we need a placeholder RawBatch
        existing = state_manager.load_normalized_batch()
        if existing is None:
            print_error("No existing state found for this batch. Run without --resume first.")
            return 1
        # Create a minimal RawBatch so the orchestrator can proceed
        from schemas.input_schemas import RawBatch, RawDeal
        raw_batch = RawBatch(
            batch_id=batch_id,
            input_date=input_date,
            raw_deals=[],
            input_source="csv",
            input_checksum="(resumed)",
        )
        _console.print(f"[dim]Resuming from existing state: {state_manager.batch_dir}[/dim]")

    # ── Run pipeline ──────────────────────────────────────────────────────────
    orchestrator = PipelineOrchestrator(client, state_manager, model)

    sheets_only = [int(s) for s in args.sheets] if args.sheets else None

    try:
        orchestrator.run(
            raw_batch=raw_batch,
            interactive=args.interactive,
            resume=args.resume,
            sheets_only=sheets_only,
        )
    except KeyboardInterrupt:
        _console.print("\n[yellow]Pipeline interrupted by user.[/yellow]")
        _console.print(f"[dim]Partial state saved to: {state_manager.batch_dir}[/dim]")
        return 1
    except Exception as e:
        print_error(f"Pipeline error: {e}")
        import traceback
        _console.print(traceback.format_exc())
        return 1

    return 0


def _run_export_only(state_manager: StateManager) -> int:
    """Re-run exporters only, using existing state."""
    from exporters.excel_exporter import ExcelExporter
    from exporters.markdown_exporter import MarkdownExporter
    from utils.console import print_final_summary

    print_section("Export-only mode")

    sheet_outputs = {}
    for sheet_id in ["sheet_1", "sheet_2", "sheet_3", "sheet_4", "sheet_5", "sheet_6"]:
        output = state_manager.load_sheet_output(sheet_id)
        if output:
            sheet_outputs[sheet_id] = output

    if not sheet_outputs:
        print_error("No sheet outputs found in state. Run the full pipeline first.")
        return 1

    bundle = state_manager.load_content_bundle()
    if bundle is None:
        print_error("No content bundle found in state. Run the full pipeline first.")
        return 1

    workbook_path = state_manager.workbook_path()
    ExcelExporter().export(sheet_outputs, workbook_path, state_manager.batch_id)

    content_dir = state_manager.batch_dir / "content"
    md_paths = MarkdownExporter().export(bundle, content_dir)

    print_final_summary(state_manager.batch_id, {"Excel Workbook": str(workbook_path), **md_paths})
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Weekly Intelligence Pipeline — transforms startup funding data into analysis and content.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--input", metavar="FILE", help="Path to CSV input file")
    input_group.add_argument("--paste", action="store_true", help="Accept multi-line paste from stdin")

    # Run control
    parser.add_argument(
        "--date", default=date.today().isoformat(),
        help="ISO date for batch_id (default: today). Format: YYYY-MM-DD"
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume pipeline from saved state (skip completed stages)"
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Pause after briefing for user review and brief selection"
    )
    parser.add_argument(
        "--sheets", nargs="+", metavar="N",
        help="Run only specified sheet numbers (1-6). E.g. --sheets 1 3 5"
    )
    parser.add_argument(
        "--export-only", action="store_true",
        help="Re-run exporters only using existing state (no API calls)"
    )

    # Model / output
    parser.add_argument("--model", metavar="MODEL", help=f"Claude model to use (default: {config.DEFAULT_MODEL})")
    parser.add_argument("--output-dir", metavar="DIR", help="Override default output/ directory")

    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())

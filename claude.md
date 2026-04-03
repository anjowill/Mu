# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Spice Route Intelligence — a weekly content-intelligence pipeline that ingests startup funding CSVs, runs multi-agent analysis across 6 analytical dimensions, produces an Excel workbook, blog drafts, and a video script. A FastAPI + Streamlit web layer wraps the CLI pipeline.

---

## Running the system

### CLI (primary interface)

```bash
# Full run
python main.py --input data.csv --date 2026-04-03

# Interactive mode — pauses after briefing for topic review
python main.py --input data.csv --date 2026-04-03 --interactive

# Resume a partially completed batch
python main.py --date 2026-04-03 --resume

# Re-export only (no API calls)
python main.py --date 2026-04-03 --export-only

# Run specific sheets only
python main.py --input data.csv --date 2026-04-03 --sheets 1 3 5

# Paste CSV from stdin
python main.py --paste --date 2026-04-03

# Override model
python main.py --input data.csv --date 2026-04-03 --model claude-sonnet-4-6
```

### Web interface (two terminals required)

```bash
# Terminal 1 — FastAPI backend
uvicorn app.api:app --reload --port 8000

# Terminal 2 — Streamlit UI
streamlit run app/ui.py
```

UI is at `http://localhost:8501`. API at `http://localhost:8000`.

### Environment

Copy `.env.example` → `.env` in the project root and set:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Both `main.py` and `app/services/pipeline_runner.py` load `.env` from `Path(__file__).parent / ".env"` at module load time.

---

## Architecture

### Pipeline execution order

```
CSV / paste
  → Parser (RawBatch)
  → Normalizer (NormalizedBatch)          ← saved: normalized_batch.json
  → Sheet1Agent                           ← saved: sheets/sheet_1_output.json
  → Sheet2–4Agent (depend on Sheet 1)     ← saved: sheets/sheet_N_output.json
  → Sheet5–6Agent (depend on normalized)  ← saved: sheets/sheet_N_output.json
  → AggregatorAgent (pure Python)         ← saved: aggregated_insights.json
  → BriefingAgent (Claude call)           ← saved: briefs/topic_candidates.json
  → [Interactive gate / auto-select]      ← saved: briefs/selected_briefs.json
  → BlogAgent × N + VideoScriptAgent      ← saved: content_bundle.json
  → ExcelExporter + MarkdownExporter      ← outputs: workbook + content/*.md
```

**Orchestrator** (`pipeline/orchestrator.py`) checks for existing checkpoint files before each stage — `--resume` skips stages whose output already exists on disk.

**StateManager** (`pipeline/state_manager.py`) owns all file I/O. Never write output files directly; use `state_manager.save_*` / `state_manager.load_*` methods. Key path: `output/weekly_batch_YYYY_MM_DD/`.

### Agent pattern

All agents extend `BaseAgent` (`agents/base_agent.py`):
- Constructor: `(client: anthropic.Anthropic, model: str, prompt_path: Path, temperature: float, max_tokens: int)`
- `_call_claude(user_message)` → `(response_text, usage_dict)` with 3× exponential-backoff retry
- Raw LLM response is always preserved in `SheetOutput.raw_llm_response` — enables re-parsing without API calls
- Subclasses implement `run(*args) -> <typed schema>`

**Temperatures:**
- Sheet agents: `0.0` (deterministic)
- BriefingAgent: `0.3`
- Blog/Video agents: `0.7`

### Web layer

`app/services/pipeline_runner.py` is the **only** integration point between FastAPI and the pipeline. It calls `parse_csv()` + `PipelineOrchestrator.run()` and returns a path dict. FastAPI offloads it via `asyncio.to_thread()`.

Streamlit (`app/ui.py`) reads output files directly from the filesystem (same machine as API) rather than routing through `/files/` endpoint.

---

## Configuration (`config.py`)

| Constant | Value |
|----------|-------|
| `DEFAULT_MODEL` | `"claude-opus-4-6"` |
| `OUTPUT_DIR` | `<root>/output/` |
| `PROMPTS_DIR` | `<root>/prompts/` |
| `MAX_TOKENS_SHEET` | `8192` |
| `MAX_TOKENS_BLOG` | `4096` |
| `MAX_RETRIES` | `3` |

Capital quality tiers, sector priority tiers, stage/sector normalization maps, and ticket size buckets are all defined in `config.py` — edit there, not in agent code.

---

## Prompt files

Prompts live in `prompts/` as `.md` files and are loaded from disk at runtime via `utils/prompt_loader.py`. Editing a prompt file takes effect on the next run — no code change needed.

| File | Sheet |
|------|-------|
| `sheet_1_Use of Funds.md` | Use of funds allocation |
| `sheet_2_Founder-Lens.md` | Founder background signals |
| `sheet_3_Capital Quality.md` | Deal quality scoring (1–5 per criterion) |
| `sheet_4_Sector Capital.md` | Sector-level capital flows |
| `sheet_5_Structural Market.md` | Market structure analysis |
| `sheet_6_Investor.md` | Investor intelligence |

---

## CSV input format

The parser (`ingestion/parser.py`) accepts flexible column aliases (case-insensitive):

| Field | Accepted column names |
|-------|-----------------------|
| Company | `company`, `company name`, `name` |
| Deal size | `deal size`, `deal_size`, `deal size ($ mn)`, `amount` |
| Stage | `stage`, `funding stage` |
| Sector | `industry`, `sector` |
| Investors | `investors`, `investor`, `investor names` |
| Business model | `business model`, `model`, `b2b/b2c` |

Only `company` is required. Delimiter is auto-detected (tab or comma).

---

## Output structure

```
output/weekly_batch_YYYY_MM_DD/
  ├── normalized_batch.json
  ├── aggregated_insights.json
  ├── content_bundle.json
  ├── state.json
  ├── workbook_YYYY-MM-DD.xlsx
  ├── sheets/
  │   └── sheet_{1-6}_output.json
  ├── briefs/
  │   ├── topic_candidates.json   ← 5 blog briefs + 1 video brief
  │   └── selected_briefs.json    ← after interactive review or auto-select
  └── content/
      ├── blog_*.md
      └── video_script.md
```

---

## Core constraints

- **Never invent facts.** All agent outputs must be grounded in the provided source data. BriefingAgent outputs `ContentBrief` objects with `supporting_insights` references; Blog/Video agents may only draw from those references.
- **Aggregator has no LLM call.** `AggregatorAgent` is pure Python scoring (`composite = 0.35·novelty + 0.40·evidence + 0.25·relevance`). Keep it that way.
- **Video is mandatory.** `VideoScriptAgent` always runs; it is not optional.
- **Do not modify pipeline files** when making changes to the web layer. `app/` is a thin wrapper — the pipeline under `agents/`, `pipeline/`, `ingestion/`, `exporters/` is the stable core.
- **Out of scope until explicitly requested:** web scraping, scheduling, CMS publishing, direct video rendering, database persistence, auth.

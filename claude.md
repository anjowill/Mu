# CLAUDE.md

# Project: Weekly Intelligence Pipeline

## 1) Project goal

Build a weekly content-intelligence system that transforms source data into:
1. structured analysis,
2. Excel-ready outputs across multiple sheets,
3. blog drafts,
4. optional explainer-video scripts.

The current phase is manual data input + automated analysis/content generation.
The future phase will add web extraction and scheduled ingestion.

## 2) Current scope

### In scope now
- Accept weekly source data manually from the user
- Parse and normalize the data into a structured internal format
- Run multiple analysis modules that correspond to the Excel sheets
- Produce outputs suitable for:
  - Excel workbook generation
  - blog topic selection
  - blog drafting
  - video script drafting

### Out of scope for now
- Web scraping
- Automated scheduling
- API-based live ingestion
- Publishing to CMS
- Direct video rendering

Do not implement future-phase automation unless explicitly asked.

## 3) Core operating principles

- Never invent facts that are not in the provided source data.
- Distinguish clearly between:
  - raw source facts,
  - derived insights,
  - editorial interpretation,
  - recommendations.
- Prefer deterministic structured output over free-form prose.
- When information is ambiguous, ask for clarification instead of guessing.
- Preserve traceability from source data to analysis output.
- Keep the system modular so each sheet/analysis step can be changed independently.

## 4) Product workflow

The pipeline is:

1. Receive weekly input data
2. Normalize the data
3. Run sheet-level analyses
4. Aggregate findings across sheets
5. Rank candidate blog topics
6. Draft blog outline
7. Draft blog article
8. Draft explainer-video script if requested

## 5) Data contract

### Input
The user will provide weekly source data manually.
Treat that input as the only source of truth for the current run.

### Internal format
Use structured objects, tables, or JSON-like schemas internally.
Prefer explicit fields such as:
- title
- date
- company
- category
- metric
- source
- note
- confidence
- tags

### Output expectations
Outputs should be reproducible and machine-readable where possible.

## 6) Excel workbook rules

The workbook has multiple sheets, each with a dedicated prompt and purpose.
Do not collapse everything into one sheet.

For each sheet:
- preserve the sheet’s unique objective,
- generate only the content relevant to that sheet,
- keep output clean and structured,
- avoid mixing commentary with data unless the sheet requires it.

If a sheet prompt is missing, request it before generating final sheet content.

## 7) Blog-generation rules

When selecting topics for the blog:
- prioritize novelty,
- prioritize business relevance,
- prioritize evidence strength,
- avoid weak or speculative themes.

The blog should:
- be fact-based,
- be readable for a general professional audience,
- use clear headings,
- tie every major claim back to the analysis.

Do not overstate certainty.

## 8) Video-script rules

Video output is optional and should be created only when requested.
When generating a video script:
- create a concise hook,
- define the core message,
- break the script into scenes or beats,
- keep language simple and explanatory,
- separate narration from visual suggestions.

## 9) Quality standards

Before finishing any task, verify:
- the output uses only the provided input,
- the output matches the requested format,
- the logic is consistent across sheets,
- no contradictions exist between analysis and blog conclusions,
- terminology is used consistently.

## 10) Coding standards

- Prefer small, testable modules.
- Keep transformation logic separate from rendering logic.
- Use typed schemas where practical.
- Add validation for required fields.
- Make outputs easy to inspect and debug.
- Write code that is easy to extend from manual input to web ingestion later.

## 11) Preferred architecture

Build the system in layers:

### Layer 1: Input ingestion
Accept weekly data and prompts.

### Layer 2: Normalization
Convert source data into a structured canonical format.

### Layer 3: Sheet analyzers
One analyzer per sheet or analytical dimension.

### Layer 4: Insight aggregator
Merge sheet outputs into ranked insights.

### Layer 5: Content generator
Create blog outline, blog draft, and video script.

### Layer 6: Exporter
Generate Excel, markdown, or other final formats.

## 12) Naming conventions

Use stable names for:
- weekly batches,
- sheet outputs,
- insight objects,
- blog topics,
- script sections.

Example:
- weekly_batch_2026_04_03
- sheet_funding_analysis
- insight_ranked_topics
- blog_draft_v1
- video_script_v1

## 13) Default behavior when uncertain

If the next step is unclear:
1. inspect the existing project structure,
2. infer the most likely intended workflow from nearby files,
3. ask a focused question only if needed.

Do not make broad assumptions about the business logic.

## 14) For this project specifically

Remember that the long-term plan is:
- start with manual weekly input,
- stabilize Excel analysis,
- generate blogs from selected insights,
- later add web extraction,
- later automate the weekly publication cycle.

Optimize for a reliable MVP first.

## 15) What to ask for when needed

If necessary, ask for:
- one sample weekly dataset,
- one sheet prompt,
- one example of a good Excel output,
- one previous blog draft,
- one example explainer-video topic.

Prefer concrete examples over abstract descriptions.
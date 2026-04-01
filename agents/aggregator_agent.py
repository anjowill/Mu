"""
Aggregator Agent — pure Python, no LLM call.

Cross-joins all 6 sheet outputs into a ranked list of insights.
Prevents hallucination at the synthesis layer by keeping this layer
entirely deterministic.

Scoring formula:
    composite = 0.35 * novelty + 0.40 * evidence_strength + 0.25 * business_relevance

Insights with composite_score >= 0.60 are marked blog_suitable.
"""

from datetime import datetime, timezone
from typing import Optional

import config
from schemas.aggregated_schemas import AggregatedInsights, RankedInsight
from schemas.normalized_schemas import NormalizedBatch
from schemas.sheet_schemas import SheetOutput


def aggregate(
    batch: NormalizedBatch,
    sheet_outputs: dict[str, SheetOutput],
) -> AggregatedInsights:
    """
    Merge all sheet outputs into AggregatedInsights.

    Args:
        batch:         The NormalizedBatch for this week.
        sheet_outputs: Dict keyed by sheet_id ("sheet_1"…"sheet_6").
    """
    candidates = []
    candidates.extend(_insights_from_sheet4(sheet_outputs))
    candidates.extend(_insights_from_sheet3(sheet_outputs))
    candidates.extend(_insights_from_sheet2(sheet_outputs))
    candidates.extend(_insights_from_sheet5(sheet_outputs))
    candidates.extend(_insights_from_cross_sheets(sheet_outputs, batch))

    # Deduplicate by title (case-insensitive)
    seen: set[str] = set()
    unique: list[dict] = []
    for c in candidates:
        key = c["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Score and rank
    for c in unique:
        c["composite_score"] = round(
            0.35 * c["novelty_score"]
            + 0.40 * c["evidence_strength_score"]
            + 0.25 * c["business_relevance_score"],
            4,
        )
        c["blog_suitable"] = c["composite_score"] >= 0.60

    unique.sort(key=lambda x: x["composite_score"], reverse=True)

    ranked_insights = [
        RankedInsight(rank=i + 1, **c) for i, c in enumerate(unique)
    ]

    return AggregatedInsights(
        batch_id=batch.batch_id,
        generated_at=datetime.now(timezone.utc),
        ranked_insights=ranked_insights,
        top_sectors=_extract_top_sectors(sheet_outputs),
        top_companies_by_quality=_extract_top_companies(sheet_outputs),
        week_narrative_facts=_build_narrative_facts(batch, sheet_outputs),
        cross_sheet_contradictions=_detect_contradictions(sheet_outputs),
    )


# ── Insight extraction from individual sheets ──────────────────────────────────

def _insights_from_sheet4(outputs: dict) -> list[dict]:
    """Extract sector-level insights from Sheet 4 priority table."""
    s4 = outputs.get("sheet_4")
    if not s4 or not s4.rows:
        return []

    sheet4_data = s4.rows[0] if s4.rows else {}
    priority_table = sheet4_data.get("sector_priority_table", [])
    insights = []

    for row in priority_table:
        if isinstance(row, dict):
            tier = row.get("priority_tier", "")
            sector = row.get("sector", "")
            capital = row.get("capital_mn", 0)
            pct = row.get("pct_of_total", 0)
            interpretation = row.get("interpretation", "")

            if not sector or sector.lower() in {"total", ""}:
                continue

            novelty = 0.7 if tier == "Tier 1" else (0.5 if tier == "Tier 2" else 0.35)
            evidence = 0.9  # Computed from disclosed capital — high evidence
            relevance = 0.8 if tier in ("Tier 1", "Tier 2") else 0.5

            insights.append({
                "title": f"{sector} captured {pct:.1f}% of total capital ({tier})",
                "evidence_summary": (
                    f"{sector} attracted ${capital:.1f} Mn ({pct:.1f}% of weekly disclosed capital). "
                    f"Priority classification: {tier}. Interpretation: {interpretation}."
                ),
                "source_sheets": ["sheet_4"],
                "novelty_score": novelty,
                "evidence_strength_score": evidence,
                "business_relevance_score": relevance,
            })

    return insights


def _insights_from_sheet3(outputs: dict) -> list[dict]:
    """Extract capital quality distribution insights from Sheet 3."""
    s3 = outputs.get("sheet_3")
    if not s3 or not s3.rows:
        return []

    tier_counts: dict[str, list[str]] = {}
    for row in s3.rows:
        if isinstance(row, dict):
            tier = row.get("total_tier", "Unknown")
            company = row.get("name", "Unknown")
            tier_counts.setdefault(tier, []).append(company)

    insights = []
    for tier, companies in tier_counts.items():
        if len(companies) == 0:
            continue
        is_high = "High-quality" in tier or "Solid growth" in tier
        novelty = 0.6 if is_high else 0.5
        evidence = 0.85
        relevance = 0.75 if is_high else 0.6

        insights.append({
            "title": f"{len(companies)} deal(s) classified as '{tier}'",
            "evidence_summary": (
                f"Capital quality analysis (Sheet 3) classified {len(companies)} deal(s) "
                f"as '{tier}': {', '.join(companies[:5])}{'...' if len(companies) > 5 else ''}."
            ),
            "source_sheets": ["sheet_3"],
            "novelty_score": novelty,
            "evidence_strength_score": evidence,
            "business_relevance_score": relevance,
        })

    return insights


def _insights_from_sheet2(outputs: dict) -> list[dict]:
    """Extract founder-lens insights from Sheet 2."""
    s2 = outputs.get("sheet_2")
    if not s2 or not s2.rows:
        return []

    insights = []
    for row in s2.rows:
        if not isinstance(row, dict):
            continue
        company = row.get("company", "")
        insight_text = row.get("founder_learning_insight", "")
        if not company or not insight_text:
            continue

        insights.append({
            "title": f"Founder signal: {company}",
            "evidence_summary": insight_text,
            "source_sheets": ["sheet_2"],
            "novelty_score": 0.55,
            "evidence_strength_score": 0.70,
            "business_relevance_score": 0.80,
        })

    return insights


def _insights_from_sheet5(outputs: dict) -> list[dict]:
    """Extract structural market insights from Sheet 5."""
    s5 = outputs.get("sheet_5")
    if not s5 or not s5.rows:
        return []

    sheet5_data = s5.rows[0] if s5.rows else {}
    insights = []

    # B2B vs B2C split
    b2b_b2c = sheet5_data.get("b2b_b2c_split", [])
    for row in b2b_b2c:
        if isinstance(row, dict) and row.get("business_model", "").upper() in ("B2B", "B2C"):
            model = row["business_model"]
            pct = row.get("pct_of_total", 0)
            capital = row.get("capital_mn", 0)
            insights.append({
                "title": f"{model} captured {pct:.1f}% of capital this week",
                "evidence_summary": (
                    f"Structural split: {model} attracted ${capital:.1f} Mn "
                    f"({pct:.1f}% of disclosed capital)."
                ),
                "source_sheets": ["sheet_5"],
                "novelty_score": 0.45,
                "evidence_strength_score": 0.90,
                "business_relevance_score": 0.60,
            })

    return insights


def _insights_from_cross_sheets(
    outputs: dict, batch: NormalizedBatch
) -> list[dict]:
    """Generate cross-sheet composite insights."""
    s3 = outputs.get("sheet_3")
    s4 = outputs.get("sheet_4")
    if not s3 or not s4:
        return []

    # Cross: high-quality capital in Tier 1 sector
    top_sectors = _extract_top_sectors(outputs)
    high_quality_companies: list[str] = []
    for row in (s3.rows or []):
        if isinstance(row, dict) and row.get("total_score", 0) >= 22:
            high_quality_companies.append(row.get("name", "?"))

    if top_sectors and high_quality_companies:
        return [{
            "title": f"High-quality capital concentrated in Tier 1 sectors this week",
            "evidence_summary": (
                f"Sheet 3 identifies {len(high_quality_companies)} high-quality-capital company(ies) "
                f"({', '.join(high_quality_companies[:3])}), "
                f"while Sheet 4 confirms top sectors: {', '.join(top_sectors[:3])}."
            ),
            "source_sheets": ["sheet_3", "sheet_4"],
            "novelty_score": 0.75,
            "evidence_strength_score": 0.80,
            "business_relevance_score": 0.85,
        }]

    return []


# ── Supporting data extraction ────────────────────────────────────────────────

def _extract_top_sectors(outputs: dict) -> list[str]:
    """Return Tier 1 sectors from Sheet 4 priority table."""
    s4 = outputs.get("sheet_4")
    if not s4 or not s4.rows:
        return []
    sheet4_data = s4.rows[0] if s4.rows else {}
    priority_table = sheet4_data.get("sector_priority_table", [])
    return [
        r["sector"]
        for r in priority_table
        if isinstance(r, dict)
        and r.get("priority_tier") == "Tier 1"
        and r.get("sector", "").lower() != "total"
    ]


def _extract_top_companies(outputs: dict) -> list[str]:
    """Return companies with Sheet 3 total_score >= 22 (High-quality scale capital)."""
    s3 = outputs.get("sheet_3")
    if not s3:
        return []
    return [
        r["name"]
        for r in (s3.rows or [])
        if isinstance(r, dict) and r.get("total_score", 0) >= 22
    ]


def _build_narrative_facts(
    batch: NormalizedBatch, outputs: dict
) -> list[str]:
    """Build bullet facts for grounding blog and video content."""
    facts: list[str] = [
        f"Total deals this week: {batch.total_deals}",
        f"Total disclosed capital: ${batch.total_disclosed_capital_mn:.1f} Mn",
    ]

    top_sectors = _extract_top_sectors(outputs)
    if top_sectors:
        facts.append(f"Tier 1 sectors (>10% of capital): {', '.join(top_sectors)}")

    top_companies = _extract_top_companies(outputs)
    if top_companies:
        facts.append(f"Highest capital quality companies (score ≥22): {', '.join(top_companies)}")

    # Stage distribution headline from Sheet 5
    s5 = outputs.get("sheet_5")
    if s5 and s5.rows:
        by_stage = s5.rows[0].get("capital_by_stage", [])
        for row in by_stage:
            if isinstance(row, dict) and row.get("stage", "").lower() not in {"total", ""}:
                facts.append(
                    f"Stage '{row['stage']}': {row.get('deals', 0)} deals, "
                    f"${row.get('capital_mn', 0):.1f} Mn ({row.get('pct_of_total', 0):.1f}%)"
                )

    return facts


def _detect_contradictions(outputs: dict) -> list[str]:
    """
    Flag companies where Sheet 3 score is low but Sheet 2 signals are strong,
    or vice versa.
    """
    s2 = outputs.get("sheet_2")
    s3 = outputs.get("sheet_3")
    if not s2 or not s3:
        return []

    # Build a name → total_score map from Sheet 3
    score_map: dict[str, int] = {
        r["name"].lower(): r.get("total_score", 0)
        for r in (s3.rows or [])
        if isinstance(r, dict) and r.get("name")
    }

    contradictions: list[str] = []
    for row in (s2.rows or []):
        if not isinstance(row, dict):
            continue
        company = row.get("company", "").lower()
        score = score_map.get(company)
        if score is None:
            continue

        exec_signal = row.get("execution_signal", "")
        has_strong_execution = exec_signal and "no independently verifiable" not in exec_signal.lower()

        if score <= 13 and has_strong_execution:
            contradictions.append(
                f"{row.get('company', '?')}: Sheet 2 shows strong execution signal but Sheet 3 "
                f"scores only {score} (Low-conviction or below)."
            )
        elif score >= 22 and not has_strong_execution:
            contradictions.append(
                f"{row.get('company', '?')}: Sheet 3 scores {score} (High-quality) but Sheet 2 "
                "lacks independently verifiable execution metrics."
            )

    return contradictions

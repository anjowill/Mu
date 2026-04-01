"""
Layer 2 — Normalization.

Converts a RawBatch into a NormalizedBatch with canonical types:
- deal sizes parsed and converted to $ Mn
- stages mapped to canonical buckets
- sectors mapped to canonical names
- business model inferred or defaulted
- investor lists split and deduplicated
"""

import re
from typing import Optional

import config
from schemas.input_schemas import RawBatch, RawDeal
from schemas.normalized_schemas import NormalizedBatch, NormalizedDeal


def normalize(batch: RawBatch) -> NormalizedBatch:
    deals: list[NormalizedDeal] = [_normalize_deal(d) for d in batch.raw_deals]
    disclosed = [d.deal_size_mn for d in deals if d.deal_size_disclosed and d.deal_size_mn is not None]
    return NormalizedBatch(
        batch_id=batch.batch_id,
        input_date=batch.input_date,
        total_deals=len(deals),
        total_disclosed_capital_mn=round(sum(disclosed), 2),
        deals=deals,
    )


def _normalize_deal(raw: RawDeal) -> NormalizedDeal:
    deal_size_mn, disclosed = _parse_deal_size(raw.deal_size_raw)
    return NormalizedDeal(
        company_name=raw.company_name.strip(),
        deal_size_mn=deal_size_mn,
        deal_size_disclosed=disclosed,
        stage_normalized=_normalize_stage(raw.stage),
        sector_normalized=_normalize_sector(raw.industry),
        business_model=_normalize_business_model(raw.business_model),
        investors_list=_split_investors(raw.investors),
        source_row=raw.source_row,
    )


# ── Deal size parsing ──────────────────────────────────────────────────────────

_SIZE_PATTERN = re.compile(
    r"[\$₹€£]?\s*([\d,]+(?:\.\d+)?)\s*(k|mn?|m|bn?|b|cr|crore|lakh|l)?",
    re.IGNORECASE,
)

def _parse_deal_size(raw: Optional[str]) -> tuple[Optional[float], bool]:
    """Return (size_in_mn, is_disclosed). Returns (None, False) for undisclosed."""
    if not raw or raw.strip() in {"", "–", "-", "NA", "N/A", "Undisclosed", "undisclosed"}:
        return None, False

    match = _SIZE_PATTERN.search(raw.replace(",", ""))
    if not match:
        return None, False

    value = float(match.group(1))
    unit = (match.group(2) or "mn").lower()

    if unit in ("k",):
        value = value / 1_000        # K → Mn
    elif unit in ("b", "bn"):
        value = value * 1_000        # Bn → Mn
    elif unit in ("cr", "crore"):
        value = value / 83.0 * 10   # Crore INR → $ Mn (approx; ~83 INR/USD, 1Cr=10Mn INR)
    elif unit in ("l", "lakh"):
        value = value / 83.0 * 0.1  # Lakh INR → $ Mn
    # else: already in Mn

    return round(value, 2), True


# ── Stage normalization ────────────────────────────────────────────────────────

def _normalize_stage(raw: Optional[str]) -> str:
    if not raw or not raw.strip():
        return config.STAGE_DEFAULT
    key = raw.strip().lower()
    # Direct match
    if key in config.STAGE_MAP:
        return config.STAGE_MAP[key]
    # Partial match
    for pattern, canonical in config.STAGE_MAP.items():
        if pattern in key:
            return canonical
    return config.STAGE_DEFAULT


# ── Sector normalization ───────────────────────────────────────────────────────

def _normalize_sector(raw: Optional[str]) -> str:
    if not raw or not raw.strip():
        return config.SECTOR_DEFAULT
    key = raw.strip().lower()
    if key in config.SECTOR_MAP:
        return config.SECTOR_MAP[key]
    for pattern, canonical in config.SECTOR_MAP.items():
        if pattern in key:
            return canonical
    # Return title-cased original as a new sector (allowed by Sheet 4 rules)
    return raw.strip().title()


# ── Business model normalization ───────────────────────────────────────────────

def _normalize_business_model(raw: Optional[str]) -> str:
    if not raw or not raw.strip():
        return "B2B"  # Default per Sheet 5 rules
    key = raw.strip().upper()
    if "B2C" in key and "B2B" not in key:
        return "B2C"
    return "B2B"  # B2B2C → classify by primary GTM → B2B


# ── Investor list splitting ────────────────────────────────────────────────────

_INVESTOR_SEPARATORS = re.compile(r"[,;/|]|\band\b", re.IGNORECASE)

def _split_investors(raw: Optional[str]) -> list[str]:
    if not raw or not raw.strip():
        return []
    parts = _INVESTOR_SEPARATORS.split(raw)
    seen: set[str] = set()
    result: list[str] = []
    for p in parts:
        name = p.strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            result.append(name)
    return result

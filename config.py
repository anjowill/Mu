from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent
PROMPTS_DIR = ROOT_DIR / "prompts"
OUTPUT_DIR = ROOT_DIR / "output"

# ── Model ──────────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "claude-opus-4-6"

# ── Temperature per agent class ────────────────────────────────────────────────
SHEET_AGENT_TEMPERATURE = 0.0      # Fully deterministic for analysis
BRIEFING_AGENT_TEMPERATURE = 0.3   # Structured but allows strategic judgment
CONTENT_AGENT_TEMPERATURE = 0.7    # Creative latitude for blogs/video

# ── Token limits ───────────────────────────────────────────────────────────────
MAX_TOKENS_SHEET = 8192
MAX_TOKENS_BRIEFING = 4096
MAX_TOKENS_BLOG = 4096
MAX_TOKENS_VIDEO = 2048

# ── Retry policy ───────────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 2.0

# ── Prompt file mapping (sheet number → filename) ──────────────────────────────
PROMPT_FILES = {
    1: "sheet_1_Use of Funds.md",
    2: "sheet_2_Founder-Lens.md",
    3: "sheet_3_Capital Quality.md",
    4: "sheet_4_Sector Capital.md",
    5: "sheet_5_Structural Market.md",
    6: "sheet_6_Investor.md",
}

# ── Stage normalization map (raw → canonical) ──────────────────────────────────
STAGE_MAP = {
    "pre-seed": "Pre-Seed / Pre-Series A",
    "pre seed": "Pre-Seed / Pre-Series A",
    "pre-series a": "Pre-Seed / Pre-Series A",
    "seed": "Seed",
    "series a": "Series A",
    "series b": "Series B",
    "series c": "Series C",
    "series d": "Series C",   # Collapse D+ into C for structural tables
    "series e": "Series C",
    "growth": "Series C",
    "late stage": "Series C",
}
STAGE_DEFAULT = "Unspecified / Others"

# ── Sector normalization map (raw keyword → canonical) ─────────────────────────
SECTOR_MAP = {
    "ecommerce": "Ecommerce / D2C",
    "e-commerce": "Ecommerce / D2C",
    "d2c": "Ecommerce / D2C",
    "direct to consumer": "Ecommerce / D2C",
    "enterprise tech": "Enterprise Tech / SaaS",
    "enterprise software": "Enterprise Tech / SaaS",
    "saas": "Enterprise Tech / SaaS",
    "b2b saas": "Enterprise Tech / SaaS",
    "cleantech": "Cleantech / EV",
    "clean tech": "Cleantech / EV",
    "ev": "Cleantech / EV",
    "electric vehicle": "Cleantech / EV",
    "climate": "Cleantech / EV",
    "semiconductors": "Advanced Hardware / Spacetech",
    "spacetech": "Advanced Hardware / Spacetech",
    "space tech": "Advanced Hardware / Spacetech",
    "advanced hardware": "Advanced Hardware / Spacetech",
    "deep tech": "Advanced Hardware / Spacetech",
    "deeptech": "Advanced Hardware / Spacetech",
    "ai": "AI (Application Layer)",
    "artificial intelligence": "AI (Application Layer)",
    "machine learning": "AI (Application Layer)",
    "ml": "AI (Application Layer)",
    "fintech": "Fintech",
    "financial technology": "Fintech",
    "healthtech": "Healthtech",
    "health tech": "Healthtech",
    "healthcare": "Healthtech",
    "edtech": "Edtech",
    "education technology": "Edtech",
    "agritech": "Agritech",
    "agriculture": "Agritech",
    "logistics": "Logistics / Supply Chain",
    "supply chain": "Logistics / Supply Chain",
}
SECTOR_DEFAULT = "Other"

# ── Capital Quality tier thresholds (Sheet 3) ──────────────────────────────────
CAPITAL_QUALITY_TIERS = [
    (22, 25, "High-quality scale capital"),
    (18, 21, "Solid growth capital"),
    (14, 17, "Mixed-quality execution capital"),
    (10, 13, "Low-conviction capital"),
    (0,  9,  "Weak / survival capital"),
]

# ── Sector priority tier thresholds (Sheet 4, % of total capital) ──────────────
SECTOR_PRIORITY_TIERS = [
    (10.0, float("inf"), "Tier 1"),
    (6.0,  10.0,         "Tier 2"),
    (3.0,  6.0,          "Tier 3"),
    (0.0,  3.0,          "Tier 4"),
]

# ── Ticket size buckets (Sheet 5, $ Mn) ───────────────────────────────────────
TICKET_SIZE_BUCKETS = [
    (20.0,  float("inf"), ">20"),
    (10.0,  20.0,         "10–20"),
    (5.0,   10.0,         "5–10"),
    (1.0,   5.0,          "1–5"),
    (0.0,   1.0,          "<1"),
]

# ── Blog brief IDs (order matters — briefing agent uses these as anchors) ──────
BLOG_BRIEF_IDS = [
    "brief_founder_lens",
    "brief_sector_capital",
    "brief_investor_thesis",
    "brief_capital_quality",
    "brief_market_structure",
]
VIDEO_BRIEF_ID = "brief_video"

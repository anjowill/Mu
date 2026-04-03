"""
Module 2 — Investor Database

Static dataset of India-focused VCs with filter-and-display UI.
No backend calls — pure frontend with rule-based matching.
"""

import streamlit as st

# ── Dataset ────────────────────────────────────────────────────────────────────

INVESTORS = [
    {
        "name": "Peak XV Partners",
        "description": "One of India's most active multi-stage funds, formerly Sequoia Capital India.",
        "sectors": ["Enterprise Tech / SaaS", "Fintech", "Consumer / D2C", "Healthtech", "Edtech", "AI"],
        "stages": ["Series A", "Series B", "Series C+"],
        "states": ["Pan-India"],
        "ticket_min": 5.0, "ticket_max": 50.0,
        "thesis": "Backs exceptional founders solving large market problems across consumer and enterprise.",
    },
    {
        "name": "Accel India",
        "description": "Early-stage VC fund focused on technology companies with global ambitions.",
        "sectors": ["Enterprise Tech / SaaS", "Fintech", "Consumer / D2C", "AI"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 1.0, "ticket_max": 20.0,
        "thesis": "Partners with founders early to build category-defining, global technology companies.",
    },
    {
        "name": "Blume Ventures",
        "description": "India's leading seed-to-Series A fund backing technology from the earliest stage.",
        "sectors": ["Enterprise Tech / SaaS", "Fintech", "AI", "Advanced Hardware / Spacetech", "Healthtech"],
        "stages": ["Pre-Seed", "Seed", "Series A"],
        "states": ["Pan-India"],
        "ticket_min": 0.5, "ticket_max": 5.0,
        "thesis": "High-conviction bets in deep tech and B2B software at the earliest stages.",
    },
    {
        "name": "Nexus Venture Partners",
        "description": "US-India fund focused on technology companies serving Indian and global markets.",
        "sectors": ["Enterprise Tech / SaaS", "Healthtech", "Consumer / D2C", "Fintech"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 1.0, "ticket_max": 10.0,
        "thesis": "Invests in technology companies that can scale globally, with a focus on product-led growth.",
    },
    {
        "name": "Elevation Capital",
        "description": "Early-stage VC with a strong focus on consumer internet and fintech.",
        "sectors": ["Fintech", "Consumer / D2C", "Edtech", "Enterprise Tech / SaaS"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 1.0, "ticket_max": 20.0,
        "thesis": "Supports founders building for the next billion Indian internet users.",
    },
    {
        "name": "Lightspeed India",
        "description": "Global multi-stage VC with deep India focus across consumer, enterprise, and fintech.",
        "sectors": ["Enterprise Tech / SaaS", "Fintech", "Edtech", "Consumer / D2C", "AI"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 1.0, "ticket_max": 20.0,
        "thesis": "Partners with exceptional founders from day one to build market leaders.",
    },
    {
        "name": "Matrix Partners India",
        "description": "Early-stage venture fund focused on B2B and consumer technology.",
        "sectors": ["Enterprise Tech / SaaS", "Consumer / D2C", "Fintech"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 1.0, "ticket_max": 10.0,
        "thesis": "Backs founders building enduring businesses with strong unit economics.",
    },
    {
        "name": "Kalaari Capital",
        "description": "Bangalore-based VC fund focused on Indian consumer and tech-enabled businesses.",
        "sectors": ["Consumer / D2C", "Fintech", "Edtech", "Healthtech"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Karnataka", "Pan-India"],
        "ticket_min": 1.0, "ticket_max": 15.0,
        "thesis": "Invests in founders building for the Indian consumer with a long-term partnership approach.",
    },
    {
        "name": "3one4 Capital",
        "description": "Bangalore-based early-stage fund focused on deep tech and B2B software.",
        "sectors": ["AI", "Enterprise Tech / SaaS", "Advanced Hardware / Spacetech", "Fintech"],
        "stages": ["Pre-Seed", "Seed", "Series A"],
        "states": ["Karnataka", "Pan-India"],
        "ticket_min": 0.5, "ticket_max": 5.0,
        "thesis": "Backs principled founders building defensible technology with global potential.",
    },
    {
        "name": "Stellaris Venture Partners",
        "description": "India-focused early-stage fund with a strong B2B SaaS and fintech thesis.",
        "sectors": ["Enterprise Tech / SaaS", "Fintech", "AI"],
        "stages": ["Pre-Seed", "Seed", "Series A"],
        "states": ["Pan-India"],
        "ticket_min": 0.5, "ticket_max": 5.0,
        "thesis": "Invests in product-first founders building software for global markets from India.",
    },
    {
        "name": "Fireside Ventures",
        "description": "India's leading consumer brand-focused venture fund.",
        "sectors": ["Consumer / D2C", "Ecommerce / D2C"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 1.0, "ticket_max": 10.0,
        "thesis": "Partners with founders building iconic Indian consumer brands with differentiated products.",
    },
    {
        "name": "Omnivore Partners",
        "description": "India's dedicated agri and food systems venture fund.",
        "sectors": ["Agritech", "Logistics / Supply Chain"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 0.5, "ticket_max": 5.0,
        "thesis": "Backs entrepreneurs transforming Indian agriculture with technology and innovative business models.",
    },
    {
        "name": "Avaana Capital",
        "description": "Impact-first fund focused on climate, sustainability, and clean energy.",
        "sectors": ["Cleantech / EV", "Agritech"],
        "stages": ["Seed", "Series A"],
        "states": ["Pan-India"],
        "ticket_min": 1.0, "ticket_max": 10.0,
        "thesis": "Invests in founders building solutions to climate change and resource scarcity in emerging markets.",
    },
    {
        "name": "pi Ventures",
        "description": "Deep tech and AI-focused early-stage fund.",
        "sectors": ["AI", "Advanced Hardware / Spacetech", "Healthtech", "Enterprise Tech / SaaS"],
        "stages": ["Pre-Seed", "Seed", "Series A"],
        "states": ["Pan-India"],
        "ticket_min": 0.3, "ticket_max": 3.0,
        "thesis": "Backs AI-first products at the intersection of data science and domain expertise.",
    },
    {
        "name": "SIDBI Venture Capital",
        "description": "Government-backed fund focused on MSME and technology-enabled businesses.",
        "sectors": ["Other", "Ecommerce / D2C", "Logistics / Supply Chain"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Pan-India"],
        "ticket_min": 0.5, "ticket_max": 10.0,
        "thesis": "Supports MSMEs and tech companies driving India's economic development.",
    },
]

_ALL_SECTORS = sorted({s for inv in INVESTORS for s in inv["sectors"]})
_ALL_STAGES  = ["Pre-Seed", "Seed", "Series A", "Series B", "Series C+"]
_ALL_STATES  = sorted({s for inv in INVESTORS for s in inv["states"] if s != "Pan-India"})


# ── Matching ───────────────────────────────────────────────────────────────────


def _matches(inv: dict, sector: str, stage: str, state: str) -> bool:
    sector_ok = (not sector) or (sector in inv["sectors"])
    stage_ok  = (not stage)  or (stage in inv["stages"])
    state_ok  = (not state)  or ("Pan-India" in inv["states"]) or (state in inv["states"])
    return sector_ok and stage_ok and state_ok


# ── Card renderer ──────────────────────────────────────────────────────────────


def _investor_card(inv: dict) -> str:
    sector_badges = "".join(f"<span class='srf-badge'>{s}</span>" for s in inv["sectors"])
    stage_badges  = "".join(f"<span class='srf-badge-neutral'>{s}</span>" for s in inv["stages"])
    ticket = f"${inv['ticket_min']}M – ${inv['ticket_max']}M"
    return f"""
    <div class='srf-card'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px'>
            <div>
                <p class='srf-card-title'>{inv['name']}</p>
                <p class='srf-card-meta'>{inv['description']}</p>
            </div>
            <span class='srf-ticket'>{ticket}</span>
        </div>
        <p class='srf-card-thesis'>{inv['thesis']}</p>
        <div style='margin-bottom:6px'><strong style='color:#8892A4; font-size:0.78rem'>SECTORS &nbsp;</strong>{sector_badges}</div>
        <div><strong style='color:#8892A4; font-size:0.78rem'>STAGES &nbsp;&nbsp;</strong>{stage_badges}</div>
    </div>
    """


# ── Page render ────────────────────────────────────────────────────────────────


def render() -> None:
    if "inv_searched" not in st.session_state:
        st.session_state.inv_searched = False

    st.markdown("<p class='srf-page-cap'>Find relevant investors for your startup based on sector, stage, and location.</p>",
                unsafe_allow_html=True)

    st.markdown("<div class='srf-section-head'>Filter Investors</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        sector = st.selectbox("Sector", ["All Sectors"] + _ALL_SECTORS, index=0)
    with col2:
        stage = st.selectbox("Stage", ["All Stages"] + _ALL_STAGES, index=0)
    with col3:
        state = st.selectbox("State", ["All States"] + _ALL_STATES, index=0)

    find_clicked = st.button("Find Investors", type="primary")
    if find_clicked:
        st.session_state.inv_searched = True

    if not st.session_state.inv_searched:
        st.markdown(
            "<div class='srf-placeholder'>"
            "<div class='srf-placeholder-icon'>🏦</div>"
            f"<p class='srf-placeholder-text'>Example: {len(INVESTORS)} investors available — select filters and click <strong>Find Investors</strong></p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    sel_sector = "" if sector == "All Sectors" else sector
    sel_stage  = "" if stage  == "All Stages"  else stage
    sel_state  = "" if state  == "All States"  else state

    matches = [inv for inv in INVESTORS if _matches(inv, sel_sector, sel_stage, sel_state)]

    st.divider()

    if matches:
        st.markdown(
            f"<p class='srf-result-count'>Example: {len(matches)} investor{'s' if len(matches) != 1 else ''}</p>",
            unsafe_allow_html=True,
        )
        for inv in matches:
            st.markdown(_investor_card(inv), unsafe_allow_html=True)
    else:
        st.markdown(
            "<p class='srf-empty'>No investors match the selected filters. Try broadening your criteria.</p>",
            unsafe_allow_html=True,
        )

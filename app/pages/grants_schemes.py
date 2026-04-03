"""
Module 3 — Grants & Schemes Database

Static dataset of Indian government schemes with filter-and-display UI.
No backend calls — pure frontend with rule-based matching.
"""

import streamlit as st

# ── Dataset ────────────────────────────────────────────────────────────────────

SCHEMES = [
    {
        "name": "Startup India Seed Fund Scheme (SISFS)",
        "ministry": "DPIIT — Ministry of Commerce & Industry",
        "sectors": [],  # all sectors
        "stages": ["Pre-Seed", "Seed"],
        "states": [],   # Pan-India
        "benefit": "Grant + Soft Loan",
        "amount": "Up to ₹50L grant / ₹5Cr debt",
        "description": (
            "Provides financial assistance to DPIIT-recognised startups for proof of concept, "
            "prototype development, product trials, market entry, and commercialization."
        ),
    },
    {
        "name": "DPIIT Startup Recognition",
        "ministry": "DPIIT — Ministry of Commerce & Industry",
        "sectors": [],
        "stages": [],  # all stages
        "states": [],
        "benefit": "Tax Benefits + Fast-track IPR",
        "amount": "Income tax exemption (3 years) + LTCG waiver",
        "description": (
            "Official recognition that unlocks income tax exemptions, faster patent and trademark "
            "processing at 80% rebate, and eligibility for government procurement without prior turnover."
        ),
    },
    {
        "name": "Atal Innovation Mission (AIM) — Grants",
        "ministry": "NITI Aayog",
        "sectors": ["AI", "Advanced Hardware / Spacetech", "Healthtech", "Agritech", "Cleantech / EV"],
        "stages": ["Pre-Seed", "Seed"],
        "states": [],
        "benefit": "Grant",
        "amount": "Up to ₹1Cr per cohort",
        "description": (
            "Supports deep-tech and innovation-driven startups via Atal Incubation Centres (AICs) "
            "and targeted grant programs with mentorship and industry access."
        ),
    },
    {
        "name": "NIDHI-TBI (Technology Business Incubators)",
        "ministry": "Department of Science & Technology",
        "sectors": ["AI", "Advanced Hardware / Spacetech", "Healthtech"],
        "stages": ["Pre-Seed", "Seed"],
        "states": [],
        "benefit": "Grant + Incubation + Lab Access",
        "amount": "Up to ₹25L (PRAYAS) / ₹1Cr (SSH TBI)",
        "description": (
            "Supports R&D-intensive startups through government-funded technology business incubators "
            "with grants, mentorship, and wet lab / prototyping infrastructure."
        ),
    },
    {
        "name": "Production Linked Incentive (PLI) Scheme",
        "ministry": "Ministry of Heavy Industries / Sector Ministries",
        "sectors": ["Advanced Hardware / Spacetech", "Cleantech / EV", "Other"],
        "stages": ["Series B", "Series C+"],
        "states": ["Gujarat", "Maharashtra", "Tamil Nadu", "Andhra Pradesh", "Karnataka"],
        "benefit": "Production-linked Subsidy",
        "amount": "4–20% of incremental sales (sector-dependent)",
        "description": (
            "Incentivizes domestic manufacturing in 14 key sectors including electronics, EVs, "
            "pharmaceuticals, and advanced chemistry cells, tied to incremental production targets."
        ),
    },
    {
        "name": "PM MUDRA Yojana (PMMY)",
        "ministry": "Ministry of Finance",
        "sectors": [],
        "stages": ["Seed", "Series A"],
        "states": [],
        "benefit": "Collateral-free Loan",
        "amount": "₹10L (Shishu) → ₹20L (Tarun Plus)",
        "description": (
            "Provides micro-finance to small businesses and early-revenue startups without collateral "
            "across three tiers: Shishu (≤₹50K), Kishore (₹50K–₹5L), Tarun (₹5L–₹20L)."
        ),
    },
    {
        "name": "National Agriculture Market + AGRI Fund",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "sectors": ["Agritech", "Logistics / Supply Chain"],
        "stages": ["Seed", "Series A"],
        "states": [],
        "benefit": "Grant + Market Access",
        "amount": "Up to ₹5Cr project grant",
        "description": (
            "Supports agritech startups building digital market infrastructure, supply chain "
            "solutions, and farmer-facing platforms linked to e-NAM marketplace integration."
        ),
    },
    {
        "name": "Meity Startup Hub — TIDE 2.0",
        "ministry": "Ministry of Electronics & IT",
        "sectors": ["AI", "Enterprise Tech / SaaS", "Fintech", "Edtech", "Healthtech"],
        "stages": ["Pre-Seed", "Seed"],
        "states": [],
        "benefit": "Grant + Incubation",
        "amount": "Up to ₹75L per startup",
        "description": (
            "Funds ICT-driven startups in AI, IoT, blockchain, and social impact through "
            "incubation hubs across India with milestone-linked disbursements."
        ),
    },
    {
        "name": "National Clean Energy Fund (NCEF) / MNRE",
        "ministry": "Ministry of New & Renewable Energy",
        "sectors": ["Cleantech / EV"],
        "stages": ["Seed", "Series A", "Series B"],
        "states": ["Gujarat", "Rajasthan", "Tamil Nadu"],
        "benefit": "Subsidy + Viability Gap Funding",
        "amount": "Project-specific (₹1Cr – ₹50Cr)",
        "description": (
            "Supports clean energy technology startups in solar, wind, EV infrastructure, "
            "and green hydrogen with viability gap funding and production subsidies."
        ),
    },
    {
        "name": "BioNEST — Biotech Startup Incubation",
        "ministry": "Department of Biotechnology",
        "sectors": ["Healthtech", "Agritech"],
        "stages": ["Pre-Seed", "Seed", "Series A"],
        "states": [],
        "benefit": "Grant + Incubation + Equipment Access",
        "amount": "Up to ₹50L grant",
        "description": (
            "Incubates biotech and medtech startups with access to wet labs, regulatory guidance, "
            "BIRAC funding, and government research infrastructure across 15+ bio-incubators."
        ),
    },
]

_ALL_SECTORS = sorted({s for sch in SCHEMES for s in sch["sectors"]})
_ALL_STAGES  = ["Pre-Seed", "Seed", "Series A", "Series B", "Series C+"]
_ALL_STATES  = sorted({s for sch in SCHEMES for s in sch["states"]})


# ── Matching ───────────────────────────────────────────────────────────────────


def _matches(sch: dict, sector: str, stage: str, state: str) -> bool:
    sector_ok = (not sector) or (not sch["sectors"]) or (sector in sch["sectors"])
    stage_ok  = (not stage)  or (not sch["stages"])  or (stage in sch["stages"])
    state_ok  = (not state)  or (not sch["states"])  or (state in sch["states"])
    return sector_ok and stage_ok and state_ok


# ── Card renderer ──────────────────────────────────────────────────────────────


def _scheme_card(sch: dict) -> str:
    sector_badges = (
        "".join(f"<span class='srf-badge'>{s}</span>" for s in sch["sectors"])
        if sch["sectors"] else "<span class='srf-badge'>All Sectors</span>"
    )
    stage_badges = (
        "".join(f"<span class='srf-badge-neutral'>{s}</span>" for s in sch["stages"])
        if sch["stages"] else "<span class='srf-badge-neutral'>All Stages</span>"
    )
    benefit_html = f"<span class='srf-ticket'>{sch['benefit']}</span>"
    return f"""
    <div class='srf-card'>
        <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px'>
            <div>
                <p class='srf-card-title'>{sch['name']}</p>
                <p class='srf-card-meta'>{sch['ministry']}</p>
            </div>
            <div style='text-align:right'>
                {benefit_html}<br>
                <span style='color:#8892A4; font-size:0.8rem'>{sch['amount']}</span>
            </div>
        </div>
        <p class='srf-card-thesis'>{sch['description']}</p>
        <div style='margin-bottom:6px'><strong style='color:#8892A4; font-size:0.78rem'>SECTORS &nbsp;</strong>{sector_badges}</div>
        <div><strong style='color:#8892A4; font-size:0.78rem'>STAGES &nbsp;&nbsp;</strong>{stage_badges}</div>
    </div>
    """


# ── Page render ────────────────────────────────────────────────────────────────


def render() -> None:
    if "grants_searched" not in st.session_state:
        st.session_state.grants_searched = False

    st.markdown("<p class='srf-page-cap'>Discover Indian government grants and schemes relevant to your startup's sector, stage, and location.</p>",
                unsafe_allow_html=True)

    st.markdown("<div class='srf-section-head'>Filter Schemes</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        sector = st.selectbox("Sector ", ["All Sectors"] + _ALL_SECTORS, index=0)
    with col2:
        stage = st.selectbox("Stage ", ["All Stages"] + _ALL_STAGES, index=0)
    with col3:
        state = st.selectbox("State ", ["All States"] + _ALL_STATES, index=0)

    check_clicked = st.button("Run Eligibility Check", type="primary")
    if check_clicked:
        st.session_state.grants_searched = True

    if not st.session_state.grants_searched:
        st.markdown(
            "<div class='srf-placeholder'>"
            "<div class='srf-placeholder-icon'>🏛</div>"
            f"<p class='srf-placeholder-text'>Example: {len(SCHEMES)} schemes available — select filters and click <strong>Run Eligibility Check</strong></p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    sel_sector = "" if sector == "All Sectors" else sector
    sel_stage  = "" if stage  == "All Stages"  else stage
    sel_state  = "" if state  == "All States"  else state

    matches = [sch for sch in SCHEMES if _matches(sch, sel_sector, sel_stage, sel_state)]

    st.divider()

    if matches:
        st.markdown(
            f"<p class='srf-result-count'>Example: {len(matches)} scheme{'s' if len(matches) != 1 else ''}</p>",
            unsafe_allow_html=True,
        )
        for sch in matches:
            st.markdown(_scheme_card(sch), unsafe_allow_html=True)
    else:
        st.markdown(
            "<p class='srf-empty'>No schemes match the selected filters. Try broadening your criteria.</p>",
            unsafe_allow_html=True,
        )

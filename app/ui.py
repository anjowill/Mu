"""
SRF Capital Studio — Main Streamlit entry point.

Run with:
    streamlit run app/ui.py

Requires:
    - FastAPI backend:  uvicorn app.api:app --reload --port 8000
    - First user:       python scripts/create_user.py
    - Logo (optional):  copy your PNG to app/assets/srf_logo.png
    - Email (optional): set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so app.* imports resolve correctly
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

# ── set_page_config must be the FIRST Streamlit call ──────────────────────────
# We split layout: "centered" for the login page, "wide" for the dashboard.
# Session state is safe to read before set_page_config.

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.set_page_config(
        page_title="Sign In — SRF Capital Studio",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
else:
    st.set_page_config(
        page_title="SRF Capital Studio",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

# ── Remaining imports (after page config) ─────────────────────────────────────

from app.auth.auth import logout, require_auth          # noqa: E402
from app.components.styles import inject_css            # noqa: E402
from app.database.db import init_db                     # noqa: E402
from app.pages import grants_schemes, investor_database, weekly_analysis  # noqa: E402

_LOGO_PATH = Path(__file__).parent / "assets" / "srf_logo.png"
API_BASE        = "http://localhost:8000"
REQUEST_TIMEOUT = 300

# ── Bootstrap ──────────────────────────────────────────────────────────────────

init_db()       # creates users.db + tables if absent
require_auth()  # renders login page + st.stop() if not authenticated

# ── Everything below executes only when authenticated ──────────────────────────

inject_css()

# ── Dashboard header ───────────────────────────────────────────────────────────

h_logo, h_title, h_spacer, h_user = st.columns([1, 5, 6, 2])

with h_logo:
    if _LOGO_PATH.exists():
        st.image(str(_LOGO_PATH), width=96)
    else:
        st.markdown(
            "<span style='font-size:1.5rem; font-weight:900; color:#1B5E4B;"
            " letter-spacing:-0.5px'>SRF</span>",
            unsafe_allow_html=True,
        )

with h_title:
    st.markdown(
        "<p class='srf-header-title'>SRF Capital Studio</p>"
        "<p class='srf-header-sub'>Weekly Intelligence · Investor Database · Grants & Schemes</p>",
        unsafe_allow_html=True,
    )

with h_user:
    username = st.session_state.get("username", "User")
    user_col, menu_col = st.columns([3, 1])
    with user_col:
        st.markdown(
            f"<div style='text-align:right; padding-top:10px; color:#475569;"
            f" font-size:0.88rem; font-weight:500'>{username}</div>",
            unsafe_allow_html=True,
        )
    with menu_col:
        with st.popover("⋮", help="Account options"):
            st.markdown(
                f"<p style='font-size:0.82rem; color:#64748B; margin:0 0 8px 0'>"
                f"Signed in as <strong>{username}</strong></p>",
                unsafe_allow_html=True,
            )
            if st.button("Sign Out", key="logout_btn", use_container_width=True):
                logout()
            st.divider()
            st.caption("More options coming soon")

st.markdown(
    "<hr style='border:none; border-top:1px solid rgba(27,94,75,0.15); margin:8px 0 20px 0'>",
    unsafe_allow_html=True,
)

# ── Tab navigation ─────────────────────────────────────────────────────────────

tab_analysis, tab_investors, tab_grants = st.tabs([
    "📊  Weekly Analysis",
    "🏦  Investor Database",
    "🏛  Grants & Schemes",
])

with tab_analysis:
    weekly_analysis.render(API_BASE, REQUEST_TIMEOUT)

with tab_investors:
    investor_database.render()

with tab_grants:
    grants_schemes.render()

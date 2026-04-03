"""
Global CSS injection for the SRF Capital Studio dashboard (authenticated view).

Call inject_css() once in ui.py after require_auth() passes.
This overrides the light base theme with the dark professional dashboard palette.
"""

import streamlit as st


def inject_css() -> None:
    st.markdown("""
    <style>

    /* ── Hide Streamlit chrome ────────────────────────────────────────────── */
    #MainMenu           { visibility: hidden; }
    footer              { visibility: hidden; }
    header              { visibility: hidden; }
    [data-testid="stToolbar"]    { visibility: hidden; }
    [data-testid="stDecoration"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }

    /* ── Dark dashboard background ────────────────────────────────────────── */
    .stApp {
        background-color: #111827;
    }
    .block-container {
        padding-top: 0.75rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    /* ── Header elements ──────────────────────────────────────────────────── */
    .srf-header-title {
        color: #F1F5F9;
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: -0.3px;
        margin: 0;
        line-height: 1.2;
    }
    .srf-header-sub {
        color: #94A3B8;
        font-size: 0.78rem;
        margin: 3px 0 0 0;
    }

    /* ── Tab navigation ───────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1E2740;
        border-radius: 10px;
        padding: 5px 6px;
        gap: 4px;
        border: 1px solid rgba(45, 139, 111, 0.18);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 7px;
        color: #94A3B8;
        font-weight: 500;
        font-size: 0.88rem;
        padding: 8px 20px;
        border: none;
        transition: color 0.15s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #F1F5F9;
        background: rgba(45, 139, 111, 0.12);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1B5E4B, #2D8B6F) !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background: transparent !important; }
    .stTabs [data-baseweb="tab-border"]    { display: none; }

    /* ── Popover (3-dot menu) ─────────────────────────────────────────────── */
    [data-testid="stPopover"] button {
        background: rgba(255,255,255,0.06) !important;
        color: #CBD5E1 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 7px !important;
        font-size: 1.2rem !important;
        line-height: 1 !important;
        padding: 4px 10px !important;
    }
    [data-testid="stPopover"] button:hover {
        background: rgba(45, 139, 111, 0.2) !important;
        color: #F1F5F9 !important;
    }

    /* ── Buttons ──────────────────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #1B5E4B 0%, #2D8B6F 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 0.5rem 1.3rem;
        transition: opacity 0.15s ease, transform 0.1s ease;
    }
    .stButton > button:hover {
        opacity: 0.88;
        color: white;
        transform: translateY(-1px);
    }
    .stButton > button:active { transform: translateY(0); }
    .stButton > button:disabled {
        background: #1E2740 !important;
        color: #4B5563 !important;
        cursor: not-allowed;
        transform: none;
        opacity: 1;
    }

    /* ── Input fields ─────────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: #1E2740 !important;
        border: 1px solid rgba(45, 139, 111, 0.3) !important;
        border-radius: 8px !important;
        color: #F1F5F9 !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #2D8B6F !important;
        box-shadow: 0 0 0 2px rgba(45, 139, 111, 0.2) !important;
    }
    .stSelectbox > div > div {
        background-color: #1E2740 !important;
        border: 1px solid rgba(45, 139, 111, 0.3) !important;
        border-radius: 8px !important;
        color: #F1F5F9 !important;
    }

    /* ── Cards ────────────────────────────────────────────────────────────── */
    .srf-card {
        background: #1C2333;
        border: 1px solid rgba(45, 139, 111, 0.2);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 14px;
        transition: border-color 0.2s ease;
    }
    .srf-card:hover { border-color: rgba(45, 139, 111, 0.42); }
    .srf-card-title {
        color: #F1F5F9;
        font-size: 1.02rem;
        font-weight: 700;
        margin: 0 0 3px 0;
    }
    .srf-card-meta {
        color: #94A3B8;
        font-size: 0.8rem;
        margin: 0 0 12px 0;
    }
    .srf-card-thesis {
        color: #A0AEC0;
        font-size: 0.84rem;
        font-style: italic;
        border-left: 3px solid rgba(45, 139, 111, 0.5);
        padding-left: 10px;
        margin: 6px 0 12px 0;
        line-height: 1.5;
    }

    /* ── Badges ───────────────────────────────────────────────────────────── */
    .srf-badge {
        display: inline-block;
        background: rgba(27, 94, 75, 0.22);
        color: #4ADE80;
        border: 1px solid rgba(45, 139, 111, 0.38);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.74rem;
        font-weight: 500;
        margin: 2px 3px 2px 0;
    }
    .srf-badge-neutral {
        display: inline-block;
        background: rgba(255,255,255,0.04);
        color: #94A3B8;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.74rem;
        margin: 2px 3px 2px 0;
    }
    .srf-ticket {
        color: #34D399;
        font-weight: 700;
        font-size: 0.88rem;
    }

    /* ── Section headings ─────────────────────────────────────────────────── */
    .srf-section-head {
        color: #F1F5F9;
        font-size: 1.1rem;
        font-weight: 700;
        border-left: 3px solid #1B5E4B;
        padding-left: 12px;
        margin: 22px 0 14px 0;
    }
    .srf-page-cap {
        color: #94A3B8;
        font-size: 0.86rem;
        margin: -4px 0 18px 0;
    }
    .srf-result-count {
        color: #34D399;
        font-size: 0.84rem;
        font-weight: 600;
        margin-bottom: 16px;
    }
    .srf-placeholder {
        text-align: center;
        padding: 48px 0 32px;
        color: #4B5563;
    }
    .srf-placeholder-icon {
        font-size: 2.5rem;
        margin-bottom: 12px;
    }
    .srf-placeholder-text {
        font-size: 0.9rem;
        color: #6B7280;
        margin: 0;
    }
    .srf-empty {
        color: #4B5563;
        font-size: 0.9rem;
        text-align: center;
        padding: 40px 0;
    }

    /* ── Dividers ─────────────────────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 1px solid rgba(45, 139, 111, 0.16);
        margin: 18px 0;
    }

    /* ── Expander ─────────────────────────────────────────────────────────── */
    [data-testid="stExpander"] {
        background: #1C2333;
        border: 1px solid rgba(45, 139, 111, 0.18);
        border-radius: 10px;
    }

    /* ── File uploader ────────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background: #1C2333;
        border: 1px dashed rgba(45, 139, 111, 0.38) !important;
        border-radius: 10px;
    }

    /* ── Metric containers ────────────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: #1C2333;
        border: 1px solid rgba(45, 139, 111, 0.18);
        border-radius: 10px;
        padding: 16px;
    }

    /* ── Date input ───────────────────────────────────────────────────────── */
    [data-testid="stDateInput"] input {
        background-color: #1E2740 !important;
        border: 1px solid rgba(45, 139, 111, 0.3) !important;
        border-radius: 8px !important;
        color: #F1F5F9 !important;
    }

    /* ── Checkbox ─────────────────────────────────────────────────────────── */
    [data-testid="stCheckbox"] label {
        color: #CBD5E1 !important;
        font-size: 0.88rem !important;
    }

    /* ── Alert messages ───────────────────────────────────────────────────── */
    [data-testid="stAlert"] { border-radius: 8px; }

    </style>
    """, unsafe_allow_html=True)

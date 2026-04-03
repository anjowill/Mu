"""
Authentication layer — login page, session management, logout.

login_page() does NOT call st.set_page_config — that is handled by ui.py
so the layout (centered vs wide) can differ between login and dashboard.
"""

from pathlib import Path

import bcrypt
import streamlit as st

from app.database.db import create_access_request, get_user
from app.utils.email_sender import send_access_request_email

_LOGO_PATH = Path(__file__).parent.parent / "assets" / "srf_logo.png"


# ── Password utilities ─────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


# ── Session helpers ────────────────────────────────────────────────────────────


def logout() -> None:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()


# ── Login page CSS (light, isolated) ──────────────────────────────────────────


def _login_page_css() -> None:
    st.markdown("""
    <style>
    /* ── Completely hide sidebar and all navigation ── */
    [data-testid="stSidebar"]          { display: none !important; }
    [data-testid="stSidebarNav"]       { display: none !important; }
    [data-testid="collapsedControl"]   { display: none !important; }
    section[data-testid="stSidebarNav"] { display: none !important; }
    #MainMenu   { visibility: hidden !important; }
    footer      { visibility: hidden !important; }
    header      { visibility: hidden !important; }
    [data-testid="stToolbar"] { visibility: hidden !important; }

    /* ── Page background ── */
    .stApp {
        background: linear-gradient(145deg, #F0F4F8 0%, #FFFFFF 50%, #E8F5F0 100%);
        min-height: 100vh;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* ── Login card ── */
    .login-card {
        background: #FFFFFF;
        border: 1px solid rgba(27, 94, 75, 0.15);
        border-radius: 20px;
        padding: 40px 44px;
        margin-top: 20px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.07), 0 1px 4px rgba(0, 0, 0, 0.04);
    }
    .login-wordmark {
        text-align: center;
        font-size: 1.05rem;
        font-weight: 700;
        color: #1B5E4B;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .login-tagline {
        text-align: center;
        font-size: 0.8rem;
        color: #94A3B8;
        margin-bottom: 28px;
        letter-spacing: 0.2px;
    }
    .login-divider {
        border: none;
        border-top: 1px solid #E2E8F0;
        margin: 20px 0;
    }
    .request-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #2D3748;
        margin-bottom: 4px;
    }
    .request-note {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-bottom: 16px;
    }

    /* ── Input fields ── */
    .stTextInput > div > div > input {
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 8px !important;
        background: #F8FAFC !important;
        color: #1A202C !important;
        font-size: 0.9rem !important;
        padding: 10px 14px !important;
        transition: border-color 0.15s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1B5E4B !important;
        box-shadow: 0 0 0 3px rgba(27, 94, 75, 0.1) !important;
        background: #FFFFFF !important;
    }

    /* ── Primary button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1B5E4B 0%, #2D8B6F 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 1.5rem !important;
        letter-spacing: 0.2px !important;
        transition: opacity 0.15s ease, transform 0.1s ease !important;
        width: 100% !important;
    }
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }

    /* ── Secondary button (Request Access) ── */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #1B5E4B !important;
        border: 1.5px solid rgba(27, 94, 75, 0.35) !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        width: 100% !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(27, 94, 75, 0.06) !important;
    }

    /* ── Expander (Request Access section) ── */
    [data-testid="stExpander"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        background: #F8FAFC !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Login page ─────────────────────────────────────────────────────────────────


def login_page() -> None:
    """
    Render the full-page login UI.
    Does NOT call st.set_page_config — ui.py handles that.
    """
    _login_page_css()

    # Top spacer
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        # Logo or wordmark
        if _LOGO_PATH.exists():
            logo_col, _ = st.columns([1, 0.01])
            with logo_col:
                st.image(str(_LOGO_PATH), width=180)
        else:
            st.markdown(
                "<div style='text-align:center; margin-bottom:8px'>"
                "<span style='font-size:2rem; font-weight:900; color:#1B5E4B;"
                " letter-spacing:-1px'>SRF</span>"
                "<span style='font-size:1.1rem; font-weight:400; color:#64748B;"
                " margin-left:6px'>Capital Studio</span>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<p class='login-wordmark'>SRF Capital Studio</p>", unsafe_allow_html=True)
        st.markdown("<p class='login-tagline'>Internal Intelligence Dashboard</p>", unsafe_allow_html=True)

        # ── Sign-in form (Enter key submits) ──────────────────────────────────
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            login_submitted = st.form_submit_button(
                "Sign In", type="primary", use_container_width=True
            )

        if login_submitted:
            if not username.strip() or not password.strip():
                st.error("Please enter both username and password.")
            else:
                user = get_user(username.strip())
                if user and verify_password(password, user["password_hash"]):
                    st.session_state.authenticated = True
                    st.session_state.username = user["username"]
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        # ── Request Access section ─────────────────────────────────────────────
        st.markdown("<hr class='login-divider'>", unsafe_allow_html=True)

        with st.expander("Request Access"):
            st.markdown("<p class='request-title'>New to SRF Capital Studio?</p>", unsafe_allow_html=True)
            st.markdown(
                "<p class='request-note'>Submit your details. Access is granted after admin approval — "
                "you will be notified by email.</p>",
                unsafe_allow_html=True,
            )

            with st.form("request_access_form", clear_on_submit=True):
                req_username = st.text_input("Desired Username", placeholder="e.g. john.doe")
                req_email    = st.text_input("Email Address", placeholder="you@example.com")
                req_submitted = st.form_submit_button(
                    "Send Request", use_container_width=True
                )

            if req_submitted:
                if not req_username.strip() or not req_email.strip():
                    st.warning("Please fill in both fields.")
                elif "@" not in req_email:
                    st.warning("Please enter a valid email address.")
                else:
                    try:
                        create_access_request(req_username.strip(), req_email.strip())
                        send_access_request_email(req_username.strip(), req_email.strip())
                        st.success(
                            "Your request has been submitted. The admin will review "
                            "and reach out to you at the email provided."
                        )
                    except Exception as exc:
                        st.error(f"Could not save request: {exc}")

        st.markdown("</div>", unsafe_allow_html=True)


# ── Auth gate ──────────────────────────────────────────────────────────────────


def require_auth() -> None:
    """
    Call after set_page_config in ui.py.
    Shows login page and halts execution if not authenticated.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""

    if not st.session_state.authenticated:
        login_page()
        st.stop()

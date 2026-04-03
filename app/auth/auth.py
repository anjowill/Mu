"""
Authentication layer — login page, session management, logout.

login_page() does NOT call st.set_page_config — that is handled by ui.py
so the layout (centered vs wide) can differ between login and dashboard.
"""

from pathlib import Path

import bcrypt
import streamlit as st

from app.database.db import create_pending_user, get_user
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
    st.session_state.is_admin = False
    st.rerun()


# ── Login page CSS ─────────────────────────────────────────────────────────────


def _login_page_css() -> None:
    st.markdown("""
    <style>
    /* ── Hide all navigation and chrome ── */
    [data-testid="stSidebar"]           { display: none !important; }
    [data-testid="stSidebarNav"]        { display: none !important; }
    [data-testid="collapsedControl"]    { display: none !important; }
    section[data-testid="stSidebarNav"] { display: none !important; }
    #MainMenu                           { visibility: hidden !important; }
    footer                              { visibility: hidden !important; }
    header                              { visibility: hidden !important; }
    [data-testid="stToolbar"]           { visibility: hidden !important; }

    /* ── Page background — green-tinted gradient, no pure white ── */
    .stApp {
        background: linear-gradient(145deg, #DFF0E8 0%, #EAF4EF 45%, #E0EDE7 100%);
        min-height: 100vh;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* ── Login card — off-white with depth ── */
    .login-card {
        background: linear-gradient(180deg, #FAFFFE 0%, #F3F9F6 100%);
        border: 1px solid rgba(27, 94, 75, 0.18);
        border-radius: 20px;
        padding: 36px 44px 44px;
        box-shadow: 0 8px 32px rgba(27, 94, 75, 0.12), 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .login-wordmark {
        text-align: center;
        font-size: 1.05rem;
        font-weight: 700;
        color: #1B5E4B;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin: 0 0 4px 0;
    }
    .login-tagline {
        text-align: center;
        font-size: 0.82rem;
        color: #6B9E8C;
        margin: 0 0 24px 0;
        letter-spacing: 0.2px;
    }
    .login-divider {
        border: none;
        border-top: 1px solid rgba(27, 94, 75, 0.15);
        margin: 22px 0;
    }
    .request-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1B3A2E;
        margin-bottom: 4px;
    }
    .request-note {
        font-size: 0.8rem;
        color: #6B9E8C;
        margin-bottom: 16px;
    }

    /* ── Input fields ── */
    .stTextInput > div > div > input {
        border: 1.5px solid rgba(27, 94, 75, 0.2) !important;
        border-radius: 8px !important;
        background: #F0F9F5 !important;
        color: #1A202C !important;
        font-size: 0.9rem !important;
        padding: 10px 14px !important;
        transition: border-color 0.15s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1B5E4B !important;
        box-shadow: 0 0 0 3px rgba(27, 94, 75, 0.12) !important;
        background: #FFFFFF !important;
    }

    /* ── Primary button ── */
    .stFormSubmitButton > button,
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
    .stFormSubmitButton > button:hover,
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }

    /* ── Expander (Request Access) ── */
    [data-testid="stExpander"] {
        border: 1px solid rgba(27, 94, 75, 0.18) !important;
        border-radius: 10px !important;
        background: #F0F9F5 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Login page ─────────────────────────────────────────────────────────────────


def login_page() -> None:
    """
    Render the full-page login UI.
    Does NOT call st.set_page_config — ui.py handles that before any imports.
    """
    _login_page_css()

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        # 1. Title
        st.markdown("<p class='login-wordmark'>SRF Capital Studio</p>", unsafe_allow_html=True)

        # 2. Logo (centered, inside card)
        if _LOGO_PATH.exists():
            logo_l, logo_c, logo_r = st.columns([1, 3, 1])
            with logo_c:
                st.image(str(_LOGO_PATH), use_container_width=True)
        else:
            st.markdown(
                "<div style='text-align:center; margin:8px 0 16px'>"
                "<span style='font-size:3rem; font-weight:900; color:#1B5E4B;"
                " letter-spacing:-2px'>SRF</span>"
                "</div>",
                unsafe_allow_html=True,
            )

        # 3. Subtitle
        st.markdown("<p class='login-tagline'>Internal Intelligence Dashboard</p>", unsafe_allow_html=True)

        # 4. Sign-in form (Enter key submits via st.form)
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
                    st.session_state.is_admin = bool(user["is_admin"])
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        # 5. Request Access
        st.markdown("<hr class='login-divider'>", unsafe_allow_html=True)

        with st.expander("Request Access"):
            st.markdown("<p class='request-title'>New to SRF Capital Studio?</p>", unsafe_allow_html=True)
            st.markdown(
                "<p class='request-note'>Submit your details. Access is granted after admin "
                "approval — you will be notified at the email provided.</p>",
                unsafe_allow_html=True,
            )

            with st.form("request_access_form", clear_on_submit=True):
                req_username = st.text_input("Desired Username", placeholder="e.g. john.doe")
                req_email    = st.text_input("Email Address", placeholder="you@example.com")
                req_password = st.text_input("Password", type="password", placeholder="Choose a password")
                req_confirm  = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                req_submitted = st.form_submit_button("Send Request", use_container_width=True)

            if req_submitted:
                if not all([req_username.strip(), req_email.strip(), req_password.strip(), req_confirm.strip()]):
                    st.warning("Please fill in all fields.")
                elif "@" not in req_email:
                    st.warning("Please enter a valid email address.")
                elif req_password != req_confirm:
                    st.warning("Passwords do not match.")
                elif len(req_password) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    try:
                        pw_hash = hash_password(req_password)
                        create_pending_user(req_username.strip(), req_email.strip(), pw_hash)
                        send_access_request_email(req_username.strip(), req_email.strip())
                        st.success(
                            "Request submitted. The admin will review and reach out "
                            "to you at the email provided."
                        )
                    except Exception as exc:
                        st.error(f"Could not submit request: {exc}")

        st.markdown("</div>", unsafe_allow_html=True)


# ── Auth gate ──────────────────────────────────────────────────────────────────


def require_auth() -> None:
    """
    Call after set_page_config in ui.py.
    Shows login page and halts execution if not authenticated.
    Only users in the active `users` table can pass — pending users cannot log in.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    if not st.session_state.authenticated:
        login_page()
        st.stop()

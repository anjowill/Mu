"""
Admin Panel — view and action pending user access requests.

Only rendered when st.session_state.is_admin is True (enforced in ui.py tab logic).
Approve moves the user from pending_users → users (they can then log in).
Reject marks the request as rejected without creating an account.
"""

import streamlit as st

from app.database.db import approve_pending_user, get_pending_users, reject_pending_user


def render() -> None:
    st.markdown(
        "<p class='srf-section-head'>Admin — Pending Access Requests</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='srf-page-cap'>Approve a request to create an active account. "
        "Rejected requests are archived and the user cannot log in.</p>",
        unsafe_allow_html=True,
    )

    pending = get_pending_users()

    if not pending:
        st.markdown(
            "<div class='srf-placeholder'>"
            "<div class='srf-placeholder-icon'>✅</div>"
            "<p class='srf-placeholder-text'>No pending access requests.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<p class='srf-result-count'>{len(pending)} pending request{'s' if len(pending) != 1 else ''}</p>",
        unsafe_allow_html=True,
    )

    for user in pending:
        with st.container():
            st.markdown(
                f"<div class='srf-card'>"
                f"<p class='srf-card-title'>{user['username']}</p>"
                f"<p class='srf-card-meta'>{user['email']}</p>"
                f"<p style='color:#64748B; font-size:0.78rem; margin:0'>Requested: {user['created_at']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
            approve_col, reject_col, _ = st.columns([1.2, 1.2, 5])
            with approve_col:
                if st.button(
                    "Approve",
                    key=f"approve_{user['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        approve_pending_user(user["id"])
                        st.success(f"✓ Approved: **{user['username']}** can now log in.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not approve: {exc}")
            with reject_col:
                if st.button(
                    "Reject",
                    key=f"reject_{user['id']}",
                    use_container_width=True,
                ):
                    try:
                        reject_pending_user(user["id"])
                        st.info(f"Rejected: {user['username']}")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not reject: {exc}")

"""
Streamlit frontend for the Weekly Intelligence Pipeline.

Run with:
    streamlit run app/ui.py

Requires the FastAPI backend to be running at API_BASE (default: http://localhost:8000).
"""

from datetime import date
from pathlib import Path

import httpx
import streamlit as st

# ── Configuration ──────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"
REQUEST_TIMEOUT = 300  # 5 minutes — pipeline can take 60-120 s

# ── Page setup ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Spice Route Intelligence",
    page_icon="📊",
    layout="centered",
)

# ── Helper functions (defined before use) ─────────────────────────────────────


def _extract_title(md_content: str) -> str:
    """Return the first H1 heading from a markdown string, or empty string."""
    for line in md_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def _show_outputs(result: dict) -> None:
    """Render download buttons and inline previews for all pipeline outputs."""

    st.subheader("Outputs")
    st.caption(f"Batch: `{result.get('batch_id', '—')}`")

    # Excel workbook
    workbook = result.get("workbook")
    if workbook and Path(workbook).exists():
        with open(workbook, "rb") as f:
            wb_bytes = f.read()
        wb_filename = Path(workbook).name
        st.download_button(
            label="Download Excel Workbook",
            data=wb_bytes,
            file_name=wb_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("Excel workbook not available.")

    st.divider()

    # Blog files
    blogs = result.get("blogs", [])
    if blogs:
        st.subheader(f"Blog Drafts ({len(blogs)})")
        for blog_path in blogs:
            p = Path(blog_path)
            if not p.exists():
                continue
            content = p.read_text(encoding="utf-8")
            title = _extract_title(content) or p.stem

            col1, col2 = st.columns([3, 1])
            with col1:
                with st.expander(title):
                    st.markdown(content)
            with col2:
                st.download_button(
                    label="Download",
                    data=content.encode("utf-8"),
                    file_name=p.name,
                    mime="text/markdown",
                    key=f"dl_{p.stem}",
                )
    else:
        st.info("No blog drafts available.")

    st.divider()

    # Video script
    video_path = result.get("video_script")
    if video_path and Path(video_path).exists():
        st.subheader("Video Script")
        content = Path(video_path).read_text(encoding="utf-8")
        with st.expander("Preview video script"):
            st.markdown(content)
        st.download_button(
            label="Download Video Script",
            data=content.encode("utf-8"),
            file_name="video_script.md",
            mime="text/markdown",
            key="dl_video",
        )
    else:
        st.info("Video script not available.")


# ── Check API health ───────────────────────────────────────────────────────────

try:
    health = httpx.get(f"{API_BASE}/health", timeout=5)
    if health.status_code != 200:
        st.error("API server is not responding correctly. Start it with: uvicorn app.api:app --port 8000")
        st.stop()
except Exception:
    st.error(
        "Cannot reach the API server at http://localhost:8000. "
        "Start it in a separate terminal with:\n\n"
        "```\nuvicorn app.api:app --reload --port 8000\n```"
    )
    st.stop()

# ── Top-level navigation ───────────────────────────────────────────────────────

st.title("Spice Route Intelligence")

tab_investor, tab_grants = st.tabs([
    "Investor Insights & Database",
    "Grants & Schemes Database",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Investor Insights & Database
# ══════════════════════════════════════════════════════════════════════════════

with tab_investor:
    st.caption("Upload a CSV of weekly startup funding data, run analysis, and download outputs.")

    # ── Section 1: Upload & Run ────────────────────────────────────────────────

    st.header("Run New Analysis")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    batch_date = st.date_input("Batch date", value=date.today())
    resume = st.checkbox(
        "Resume from checkpoint",
        help="Skip stages whose outputs already exist for this date.",
    )

    run_clicked = st.button("Run Analysis", type="primary", disabled=uploaded_file is None)

    if run_clicked and uploaded_file is not None:
        # Step 1: Upload the file
        with st.spinner("Uploading file..."):
            try:
                upload_resp = httpx.post(
                    f"{API_BASE}/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                    timeout=30,
                )
                upload_resp.raise_for_status()
                file_path = upload_resp.json()["file_path"]
            except Exception as exc:
                st.error(f"Upload failed: {exc}")
                st.stop()

        # Step 2: Run the pipeline
        with st.spinner("Running pipeline... this typically takes 60–120 seconds"):
            try:
                run_resp = httpx.post(
                    f"{API_BASE}/run",
                    json={
                        "file_path": file_path,
                        "date": str(batch_date),
                        "resume": resume,
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                run_resp.raise_for_status()
                result = run_resp.json()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.json().get("detail", str(exc))
                st.error(f"Pipeline failed: {detail}")
                st.stop()
            except Exception as exc:
                st.error(f"Pipeline failed: {exc}")
                st.stop()

        st.success("Pipeline complete!")
        _show_outputs(result)

    # ── Section 2: Retrieve Previous Run ──────────────────────────────────────

    st.divider()
    st.header("Retrieve Previous Run")

    with st.form("retrieve_form"):
        past_date = st.date_input("Batch date to retrieve", value=date.today())
        fetch_clicked = st.form_submit_button("Fetch Outputs")

    if fetch_clicked:
        with st.spinner("Fetching outputs..."):
            try:
                resp = httpx.get(
                    f"{API_BASE}/outputs",
                    params={"date": str(past_date)},
                    timeout=10,
                )
                if resp.status_code == 404:
                    st.warning(f"No outputs found for {past_date}. Run the pipeline first.")
                else:
                    resp.raise_for_status()
                    _show_outputs(resp.json())
            except httpx.HTTPStatusError as exc:
                detail = exc.response.json().get("detail", str(exc))
                st.error(f"Error: {detail}")
            except Exception as exc:
                st.error(f"Error: {exc}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Grants & Schemes Database
# ══════════════════════════════════════════════════════════════════════════════

with tab_grants:
    st.caption("Policy eligibility and scheme matching for Indian startups.")

    st.header("Grants & Schemes Database")
    st.info(
        "This section will host the policy eligibility and scheme matching system. "
        "Enter your startup details below to check applicable grants and government schemes."
    )

    st.divider()

    st.subheader("Startup Profile")

    col_left, col_right = st.columns(2)

    with col_left:
        st.selectbox(
            "Sector",
            options=[
                "",
                "Agritech",
                "Cleantech / Climate",
                "Deep Tech",
                "EdTech",
                "Fintech",
                "Healthcare / MedTech",
                "Logistics",
                "Manufacturing",
                "SaaS / Enterprise",
                "Other",
            ],
            index=0,
            placeholder="Select sector",
        )

        st.selectbox(
            "Stage",
            options=["", "Idea / Pre-Seed", "Seed", "Series A", "Series B+", "Revenue Stage"],
            index=0,
            placeholder="Select stage",
        )

    with col_right:
        st.selectbox(
            "State",
            options=[
                "",
                "Andhra Pradesh",
                "Delhi / NCR",
                "Gujarat",
                "Karnataka",
                "Kerala",
                "Maharashtra",
                "Rajasthan",
                "Tamil Nadu",
                "Telangana",
                "Uttar Pradesh",
                "West Bengal",
                "Other",
            ],
            index=0,
            placeholder="Select state",
        )

        st.text_input(
            "Annual Revenue (optional)",
            placeholder="e.g. ₹50 Lakhs",
        )

    st.divider()

    st.button(
        "Run Eligibility Check",
        type="primary",
        disabled=True,
        help="Scheme matching coming soon.",
    )
    st.caption("Eligibility matching is under development and will be available in a future release.")

"""
Module 1 — Weekly Data Analysis

Handles CSV upload, pipeline execution, and output display.
Calls the FastAPI backend; never imports from the pipeline directly.
"""

from datetime import date
from pathlib import Path

import httpx
import streamlit as st


# ── Output helpers ─────────────────────────────────────────────────────────────


def _extract_title(md_content: str) -> str:
    for line in md_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def _show_outputs(result: dict) -> None:
    st.markdown("<div class='srf-section-head'>Analysis Outputs</div>", unsafe_allow_html=True)
    st.caption(f"Batch ID: `{result.get('batch_id', '—')}`")

    # Excel workbook
    workbook = result.get("workbook")
    if workbook and Path(workbook).exists():
        with open(workbook, "rb") as f:
            wb_bytes = f.read()
        wb_filename = Path(workbook).name
        st.download_button(
            label="⬇ Download Excel Workbook",
            data=wb_bytes,
            file_name=wb_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("Excel workbook not yet available.")

    st.divider()

    # Blog files
    blogs = result.get("blogs", [])
    if blogs:
        st.markdown(f"<div class='srf-section-head'>Blog Drafts ({len(blogs)})</div>",
                    unsafe_allow_html=True)
        for blog_path in blogs:
            p = Path(blog_path)
            if not p.exists():
                continue
            content = p.read_text(encoding="utf-8")
            title = _extract_title(content) or p.stem

            col1, col2 = st.columns([4, 1])
            with col1:
                with st.expander(title):
                    st.markdown(content)
            with col2:
                st.download_button(
                    label="⬇ Download",
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
        st.markdown("<div class='srf-section-head'>Video Script</div>", unsafe_allow_html=True)
        content = Path(video_path).read_text(encoding="utf-8")
        with st.expander("Preview video script"):
            st.markdown(content)
        st.download_button(
            label="⬇ Download Video Script",
            data=content.encode("utf-8"),
            file_name="video_script.md",
            mime="text/markdown",
            key="dl_video",
        )
    else:
        st.info("Video script not available.")


# ── Page render ────────────────────────────────────────────────────────────────


def render(api_base: str, request_timeout: int) -> None:
    st.markdown("<p class='srf-page-cap'>Upload weekly startup funding data, run multi-agent analysis, and download outputs.</p>",
                unsafe_allow_html=True)

    # ── API health check ───────────────────────────────────────────────────────
    try:
        health = httpx.get(f"{api_base}/health", timeout=5)
        if health.status_code != 200:
            st.error("API server is not healthy. Start it with: `uvicorn app.api:app --port 8000`")
            return
    except Exception:
        st.error(
            "Cannot reach the API at `http://localhost:8000`. "
            "Start it in a separate terminal:\n```\nuvicorn app.api:app --reload --port 8000\n```"
        )
        return

    # ── Section: Run New Analysis ──────────────────────────────────────────────
    st.markdown("<div class='srf-section-head'>Run New Analysis</div>", unsafe_allow_html=True)

    col_up, col_date = st.columns([3, 1])
    with col_up:
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"],
                                         label_visibility="collapsed")
    with col_date:
        batch_date = st.date_input("Batch date", value=date.today())

    resume = st.checkbox(
        "Resume from checkpoint",
        help="Skip pipeline stages whose outputs already exist for this batch date.",
    )

    run_clicked = st.button(
        "Run Analysis",
        type="primary",
        disabled=uploaded_file is None,
        use_container_width=False,
    )

    if uploaded_file is None:
        st.caption("Upload a CSV file to enable analysis.")

    if run_clicked and uploaded_file is not None:
        with st.spinner("Uploading file..."):
            try:
                upload_resp = httpx.post(
                    f"{api_base}/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
                    timeout=30,
                )
                upload_resp.raise_for_status()
                file_path = upload_resp.json()["file_path"]
            except Exception as exc:
                st.error(f"Upload failed: {exc}")
                return

        with st.spinner("Running pipeline… this typically takes 60–120 seconds"):
            try:
                run_resp = httpx.post(
                    f"{api_base}/run",
                    json={"file_path": file_path, "date": str(batch_date), "resume": resume},
                    timeout=request_timeout,
                )
                run_resp.raise_for_status()
                result = run_resp.json()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.json().get("detail", str(exc))
                st.error(f"Pipeline failed: {detail}")
                return
            except Exception as exc:
                st.error(f"Pipeline failed: {exc}")
                return

        st.success("Pipeline complete!")
        _show_outputs(result)

    # ── Section: Retrieve Previous Run ────────────────────────────────────────
    st.divider()
    st.markdown("<div class='srf-section-head'>Retrieve Previous Run</div>", unsafe_allow_html=True)

    with st.form("retrieve_form"):
        col_d, col_b = st.columns([3, 1])
        with col_d:
            past_date = st.date_input("Batch date to retrieve", value=date.today())
        with col_b:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            fetch_clicked = st.form_submit_button("Fetch Outputs", use_container_width=True)

    if fetch_clicked:
        with st.spinner("Fetching outputs..."):
            try:
                resp = httpx.get(
                    f"{api_base}/outputs",
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

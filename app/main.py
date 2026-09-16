"""Streamlit entry point for the Intelligent Car Dashcam demo."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

import streamlit as st
from platformdirs import user_cache_path

from app.detector import YoloObjectDetector
from app.models import DetectedEvent
from app.search import VEHICLE_LABELS, EventSearchService
from app.video_processor import (
    MAX_FILE_SIZE_BYTES,
    VideoProcessingError,
    VideoProcessor,
    VideoValidationError,
)

DATA_DIR = Path(os.environ.get("ROADLENS_DATA_DIR", user_cache_path("roadlens") / "sessions"))
DATA_DIR = DATA_DIR.resolve()


st.set_page_config(
    page_title="RoadLens | Dashcam Search",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #18221c;
        --muted: #68716b;
        --signal: #e4572e;
        --line: #dce2dd;
        --panel: #f7f9f7;
    }
    .stApp {
        color: var(--ink);
        background:
            linear-gradient(90deg, rgba(24, 34, 28, 0.035) 1px, transparent 1px),
            linear-gradient(rgba(24, 34, 28, 0.035) 1px, transparent 1px),
            #fcfdfb;
        background-size: 28px 28px;
    }
    .block-container { max-width: 1180px; padding-top: 3.4rem; padding-bottom: 4rem; }
    h1, h2, h3 {
        font-family: 'Bahnschrift', 'Trebuchet MS', sans-serif;
        letter-spacing: 0;
        color: var(--ink);
    }
    p, label, input, button {
        font-family: 'Bahnschrift', 'Trebuchet MS', sans-serif;
        letter-spacing: 0;
    }
    .brand-row { display: flex; align-items: baseline; gap: 0.8rem; margin-bottom: 0.35rem; }
    .brand {
        font-family: 'Cascadia Mono', 'Lucida Console', monospace;
        font-size: clamp(1.8rem, 4vw, 3.25rem);
        line-height: 1;
        color: var(--ink);
    }
    .brand-mark { color: var(--signal); }
    .tagline { color: var(--muted); font-size: 1.05rem; margin: 0 0 1.8rem; }
    .eyebrow {
        font-family: 'Cascadia Mono', 'Lucida Console', monospace;
        color: var(--signal);
        font-size: 0.72rem;
        text-transform: uppercase;
        margin-bottom: 0.65rem;
    }
    .step-label {
        font-family: 'Cascadia Mono', 'Lucida Console', monospace;
        font-size: 0.76rem;
        color: var(--signal);
        text-transform: uppercase;
        margin: 1.2rem 0 0.35rem;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(247, 249, 247, 0.94);
        border-color: #aeb9b1;
        border-radius: 6px;
    }
    [data-testid="stMetric"] {
        background: rgba(247, 249, 247, 0.94);
        border: 1px solid var(--line);
        padding: 0.75rem 1rem;
        border-radius: 6px;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.88);
        border-color: var(--line);
        border-radius: 6px;
    }
    .privacy-note {
        border-left: 3px solid var(--signal);
        padding: 0.7rem 0.9rem;
        color: var(--muted);
        background: rgba(247, 249, 247, 0.88);
        font-size: 0.88rem;
        margin-top: 2rem;
    }
    .stButton > button { border-radius: 5px; font-weight: 600; }
    @media (max-width: 700px) {
        .block-container { padding-top: 3rem; }
        .brand-row { display: block; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_state() -> None:
    defaults = {
        "events": [],
        "video_path": None,
        "session_dir": None,
        "original_name": None,
        "selected_timestamp": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource(show_spinner=False)
def get_detector() -> YoloObjectDetector:
    return YoloObjectDetector()


def save_upload(uploaded_file: object) -> tuple[Path, Path]:
    name = str(getattr(uploaded_file, "name", ""))
    size = int(getattr(uploaded_file, "size", 0))
    if Path(name).suffix.lower() != ".mp4":
        raise VideoValidationError("Only MP4 videos are supported for this demo.")
    if size <= 0:
        raise VideoValidationError("The uploaded video is empty.")
    if size > MAX_FILE_SIZE_BYTES:
        raise VideoValidationError("The uploaded video exceeds the 100 MB limit.")

    session_dir = DATA_DIR / uuid4().hex
    session_dir.mkdir(parents=True, exist_ok=False)
    video_path = session_dir / "upload.mp4"
    video_path.write_bytes(uploaded_file.getbuffer())
    return video_path, session_dir


def remove_session_files(session_dir_value: str | Path | None) -> None:
    if session_dir_value is None:
        return
    session_dir = Path(session_dir_value).resolve()
    if DATA_DIR not in session_dir.parents:
        raise VideoValidationError("Refusing to remove files outside the demo data directory.")
    shutil.rmtree(session_dir, ignore_errors=True)


def clear_session() -> None:
    remove_session_files(st.session_state.session_dir)
    for key in ("events", "video_path", "session_dir", "original_name"):
        st.session_state.pop(key, None)
    st.session_state.selected_timestamp = 0
    st.rerun()


def format_timestamp(seconds: float) -> str:
    minutes, remaining_seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def process_upload(uploaded_file: object) -> None:
    remove_session_files(st.session_state.session_dir)
    video_path, session_dir = save_upload(uploaded_file)
    status = st.status("Preparing local video analysis...", expanded=True)
    progress_text = st.empty()

    def show_progress(sample_count: int, complete: bool) -> None:
        if complete:
            progress_text.write(f"Analyzed {sample_count} sampled frames")
            status.update(label="Analysis complete", state="complete", expanded=False)
        else:
            progress_text.write(f"Analyzing sampled frame {sample_count}...")

    try:
        processor = VideoProcessor(get_detector())
        events = processor.process(video_path, session_dir / "thumbnails", show_progress)
    except Exception:
        remove_session_files(session_dir)
        raise

    st.session_state.events = events
    st.session_state.video_path = str(video_path)
    st.session_state.session_dir = str(session_dir)
    st.session_state.original_name = str(getattr(uploaded_file, "name", "video.mp4"))
    st.session_state.selected_timestamp = 0


def render_result(event: DetectedEvent, index: int) -> None:
    with st.container(border=True):
        thumbnail_column, detail_column, action_column = st.columns([1.2, 2.2, 0.8])
        with thumbnail_column:
            st.image(event.thumbnail_path, width="stretch")
        with detail_column:
            st.markdown(f"#### {event.description}")
            st.write(f"**Time:** {format_timestamp(event.timestamp_seconds)}")
            st.caption(f"Model confidence: {event.confidence:.0%}")
        with action_column:
            st.write("")
            if st.button("▶ Open", key=f"open-{index}", width="stretch"):
                st.session_state.selected_timestamp = int(event.timestamp_seconds)
                st.rerun()


def render_app() -> None:
    initialize_state()
    st.markdown('<div class="eyebrow">Local AI video review</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-row"><div class="brand">'
        'ROAD<span class="brand-mark">LENS</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="tagline">Find people and vehicles in dashcam footage without scrubbing.</p>',
        unsafe_allow_html=True,
    )

    control_column, viewer_column = st.columns([0.9, 1.6], gap="large")
    with control_column:
        st.markdown('<div class="step-label">01 / Upload</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Choose a short dashcam clip",
            type=["mp4"],
            help="MP4 only, maximum 100 MB and two minutes.",
        )
        if st.button(
            "Process video",
            type="primary",
            disabled=uploaded_file is None,
            width="stretch",
        ):
            try:
                process_upload(uploaded_file)
            except (VideoValidationError, VideoProcessingError) as error:
                st.error(str(error))
            except Exception:
                st.error(
                    "Video analysis failed. Confirm the model is installed and try another MP4."
                )

        if st.session_state.video_path:
            if st.button("Clear session", width="stretch"):
                clear_session()
            st.caption(f"Active clip: {st.session_state.original_name}")

    with viewer_column:
        st.markdown('<div class="step-label">02 / Review</div>', unsafe_allow_html=True)
        if st.session_state.video_path:
            st.video(
                st.session_state.video_path,
                start_time=st.session_state.selected_timestamp,
            )
            if st.session_state.selected_timestamp:
                st.caption(
                    f"Opened at {format_timestamp(st.session_state.selected_timestamp)}. "
                    "Press play to review the moment."
                )
        else:
            st.info("Upload and process an MP4 to begin local analysis.")

    events: list[DetectedEvent] = st.session_state.events
    if st.session_state.video_path:
        person_count = sum(event.label == "person" for event in events)
        vehicle_count = sum(event.label in VEHICLE_LABELS for event in events)
        metric_one, metric_two, metric_three = st.columns(3)
        metric_one.metric("Detections", len(events))
        metric_two.metric("People", person_count)
        metric_three.metric("Vehicles", vehicle_count)

        st.markdown('<div class="step-label">03 / Search</div>', unsafe_allow_html=True)
        query = st.text_input(
            "Search detected moments",
            placeholder="Try: show all vehicles",
        )
        if not events:
            st.warning("No people or vehicles were detected. Try a clearer or longer clip.")
        elif query:
            results = EventSearchService().search(query, events)
            if results:
                st.caption(f"{len(results)} matching moments, ordered by timestamp")
                for index, event in enumerate(results):
                    render_result(event, index)
            else:
                st.info("No matching detections. Try ‘people’, ‘cars’, or ‘vehicles’.")

    st.markdown(
        '<div class="privacy-note"><strong>Privacy-first demo.</strong> Processing stays on '
        "this machine. Results are model detections, not verified facts. Clear the session "
        "to remove temporary files.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    render_app()

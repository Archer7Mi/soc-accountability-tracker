from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from tracker.activity_capture import get_auto_capture_status, start_auto_capture, stop_auto_capture

from tracker.db import (
    add_artifact,
    add_focus_session,
    add_sprint_task,
    add_work_block,
    delete_artifact,
    delete_sprint_task,
    delete_work_block,
    get_active_focus_session,
    get_sprint_tasks,
    get_week_data,
    seed_14_day_plan,
    seed_module_16_lab_tasks,
    start_focus_session,
    stop_focus_session,
    update_artifact,
    update_sprint_task_status,
    update_work_block,
    upsert_daily_progress,
)
from tracker.scoring import daily_score, week_health


def apply_glass_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        :root {
            --page: #eef3f8;
            --panel: rgba(255, 255, 255, 0.78);
            --panel-strong: rgba(255, 255, 255, 0.92);
            --line: rgba(83, 108, 138, 0.16);
            --text: #17212e;
            --muted: #64748b;
            --cyan: #2d6cdf;
            --cyan-strong: #1849b8;
            --green: #0f9f79;
            --amber: #d18b17;
            --red: #d24f6b;
            --purple: #7269ef;
            --shadow: 0 18px 40px rgba(41, 60, 84, 0.10);
        }

        html, body, [class*="css"] {
            font-family: 'Rajdhani', sans-serif;
            color: var(--text);
        }

        code, pre, .mono {
            font-family: 'IBM Plex Mono', monospace;
        }

        .stApp {
            background:
                radial-gradient(900px 500px at 0% 0%, rgba(45, 108, 223, 0.14), transparent 56%),
                radial-gradient(700px 440px at 100% 0%, rgba(114, 105, 239, 0.10), transparent 58%),
                linear-gradient(180deg, #f7fafc 0%, #edf3f8 28%, #e7edf4 100%);
        }

        section[data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(250, 252, 255, 0.94), rgba(238, 244, 250, 0.96));
            border-right: 1px solid rgba(83, 108, 138, 0.10);
            box-shadow: inset -1px 0 0 rgba(255,255,255,0.45);
        }

        .stRadio > div {
            background: rgba(255,255,255,0.55);
            border: 1px solid rgba(83,108,138,0.12);
            border-radius: 16px;
            padding: 0.35rem;
            box-shadow: 0 10px 22px rgba(41, 60, 84, 0.05);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        .stRadio label {
            background: rgba(255,255,255,0.64);
            border: 1px solid transparent;
            border-radius: 12px;
            margin-bottom: 0.3rem;
            padding: 0.55rem 0.7rem !important;
            transition: border-color .15s ease, background .15s ease, transform .15s ease;
        }

        .stRadio label:hover {
            transform: translateX(2px);
            border-color: rgba(45,108,223,0.18);
            background: rgba(245,249,255,0.95);
        }

        .stRadio label[data-baseweb="radio"]:has(input:checked) {
            background: linear-gradient(135deg, rgba(45,108,223,0.12), rgba(114,105,239,0.08));
            border-color: rgba(45,108,223,0.30);
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.45);
        }

        .main .block-container {
            padding-top: 1.2rem;
            max-width: 1380px;
        }

        .stButton > button {
            background: linear-gradient(135deg, rgba(45, 108, 223, 0.98), rgba(33, 85, 185, 0.98));
            color: white;
            border: 1px solid rgba(24, 73, 184, 0.22);
            border-radius: 12px;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            min-height: 3rem;
            box-shadow: 0 14px 28px rgba(45, 108, 223, 0.18);
            transition: transform .16s ease, box-shadow .16s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 18px 36px rgba(45, 108, 223, 0.24);
        }

        .stTextInput input, .stTextArea textarea, .stNumberInput input, div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.88) !important;
            border: 1px solid rgba(83, 108, 138, 0.16) !important;
            color: var(--text) !important;
            border-radius: 12px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.62);
        }

        .stDateInput input {
            background: rgba(255,255,255,0.88) !important;
            color: var(--text) !important;
        }

        .stCaption, .stMarkdown p, .stMarkdown li, label, .stTextInput label, .stNumberInput label,
        .stSelectbox label, .stTextArea label, .stDateInput label {
            color: var(--text) !important;
        }

        div[data-testid="stMetric"] {
            background: var(--panel-strong);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 0.8rem 1rem;
            box-shadow: var(--shadow);
        }

        @keyframes riseIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulseDot {
            0% { box-shadow: 0 0 0 0 rgba(45,108,223,0.25); }
            70% { box-shadow: 0 0 0 10px rgba(45,108,223,0); }
            100% { box-shadow: 0 0 0 0 rgba(120,247,176,0); }
        }

        .hero-panel, .signal-panel, .tactical-panel, .form-shell {
            animation: riseIn 0.5s ease both;
        }

        .shell-hero {
            display: grid;
            grid-template-columns: 2.2fr 1fr;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .hero-panel, .signal-panel, .tactical-panel {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.90), rgba(248, 251, 255, 0.78));
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1.15rem 1.2rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(12px);
        }

        .eyebrow {
            font-size: 0.78rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--cyan);
            margin-bottom: 0.4rem;
            font-weight: 700;
        }

        .hero-title {
            font-size: 3rem;
            line-height: 0.92;
            margin: 0;
            text-transform: uppercase;
        }

        .hero-copy {
            font-size: 1.02rem;
            color: var(--muted);
            max-width: 42rem;
            margin-top: 0.8rem;
        }

        .section-title {
            font-size: 1.05rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--cyan);
            margin: 1.2rem 0 0.6rem;
        }

        .signal-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.85rem;
            margin-top: 0.9rem;
        }

        .signal-chip {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,251,255,0.80));
            border: 1px solid rgba(83,108,138,0.12);
            border-radius: 16px;
            padding: 0.95rem;
            box-shadow: 0 12px 24px rgba(41, 60, 84, 0.06);
        }

        .signal-label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em; }
        .signal-value { font-size: 2rem; font-weight: 700; margin-top: 0.15rem; color: var(--text); }

        .command-dock {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.75rem;
            margin: 0.95rem 0 0.2rem;
        }

        .command-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(246,249,254,0.84));
            border: 1px solid rgba(83,108,138,0.12);
            border-radius: 16px;
            padding: 0.85rem 0.9rem;
            box-shadow: 0 12px 24px rgba(41, 60, 84, 0.06);
        }

        .command-title {
            font-size: 0.88rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: var(--cyan);
            margin-bottom: 0.25rem;
            font-weight: 700;
        }

        .command-copy {
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.2;
        }

        .activity-row {
            display: grid;
            grid-template-columns: 135px 1fr auto;
            gap: 0.8rem;
            align-items: start;
            padding: 0.8rem 0.2rem;
            border-top: 1px solid rgba(83,108,138,0.10);
        }

        .activity-row:first-child { border-top: none; }

        .activity-tag {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 32px;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            border: 1px solid rgba(45, 108, 223, 0.16);
            background: rgba(45, 108, 223, 0.08);
            color: var(--cyan);
            font-size: 0.82rem;
            text-transform: uppercase;
            font-weight: 700;
        }

        .activity-main { font-size: 1rem; font-weight: 600; line-height: 1.1; }
        .activity-sub { color: var(--muted); font-size: 0.88rem; margin-top: 0.2rem; line-height: 1.25; }
        .activity-right { text-align: right; color: var(--muted); font-size: 0.8rem; white-space: nowrap; }

        .status-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-size: 0.76rem;
            text-transform: uppercase;
            border: 1px solid transparent;
            font-weight: 700;
        }

        .status-red { color: var(--red); background: rgba(210,79,107,0.10); border-color: rgba(210,79,107,0.18); }
        .status-green { color: var(--green); background: rgba(15,159,121,0.10); border-color: rgba(15,159,121,0.18); }
        .status-amber { color: var(--amber); background: rgba(209,139,23,0.11); border-color: rgba(209,139,23,0.20); }
        .status-cyan { color: var(--cyan); background: rgba(45,108,223,0.10); border-color: rgba(45,108,223,0.18); }

        .stack-note { color: var(--muted); font-size: 0.9rem; }

        .form-shell {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 251, 255, 0.80));
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1rem 1rem 0.6rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
        }

        .micro-title { font-size: 0.86rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--muted); margin-bottom: 0.35rem; }

        .nav-signal {
            margin-bottom: 0.8rem;
            padding: 0.8rem 0.85rem;
            border-radius: 14px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(246,249,253,0.85));
            box-shadow: 0 12px 26px rgba(41, 60, 84, 0.06);
        }

        .nav-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.45rem;
            background: var(--cyan);
            animation: pulseDot 1.8s infinite;
        }

        .quick-note { color: var(--muted); font-size: 0.84rem; margin-top: 0.25rem; }

        .timer-shell {
            border: 1px solid rgba(83,108,138,0.12);
            border-radius: 18px;
            padding: 0.95rem;
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,249,254,0.84));
            box-shadow: var(--shadow);
        }

        .hero-clock {
            background: linear-gradient(145deg, rgba(18, 40, 82, 0.98), rgba(37, 79, 165, 0.96));
            color: #f8fbff;
            border-radius: 28px;
            padding: 1.2rem;
            border: 1px solid rgba(255,255,255,0.14);
            box-shadow: 0 24px 48px rgba(25, 52, 102, 0.28);
        }

        .hero-clock .clock-label {
            font-size: 0.8rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.72);
        }

        .hero-clock .clock-copy {
            color: rgba(255,255,255,0.78);
            font-size: 0.96rem;
            margin-top: 0.35rem;
            margin-bottom: 0.8rem;
            max-width: 24rem;
        }

        .chart-shell {
            background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(247,250,254,0.82));
            border: 1px solid rgba(83,108,138,0.12);
            border-radius: 22px;
            padding: 0.9rem 1rem 0.6rem;
            box-shadow: var(--shadow);
        }

        .chart-copy {
            color: var(--muted);
            font-size: 0.9rem;
            margin-top: -0.15rem;
            margin-bottom: 0.55rem;
        }

        .lane-summary {
            color: var(--muted);
            font-size: 0.94rem;
            margin-top: 0.15rem;
            margin-bottom: 0.7rem;
        }

        .timeline-meta {
            color: var(--muted);
            font-size: 0.84rem;
            text-transform: uppercase;
            letter-spacing: 0.10em;
        }

        .focus-total {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            background: rgba(114,105,239,0.08);
            border: 1px solid rgba(114,105,239,0.16);
            color: var(--purple);
            font-size: 0.82rem;
            font-weight: 700;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
            margin-bottom: 0.7rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.72);
            border-radius: 12px;
            border: 1px solid rgba(83,108,138,0.10);
            padding: 0.45rem 0.8rem;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(45,108,223,0.12), rgba(114,105,239,0.08));
            border-color: rgba(45,108,223,0.22);
        }

        @media (max-width: 960px) {
            .shell-hero { grid-template-columns: 1fr; }
            .activity-row { grid-template-columns: 1fr; }
            .activity-right { text-align: left; }
            .command-dock { grid-template-columns: 1fr 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_navigation_signal() -> None:
    st.markdown(
        """
        <div class="nav-signal">
            <div><span class="nav-dot"></span><strong>Command Rail</strong></div>
            <div class="quick-note">Move between logging, review, and sprint control without leaving the current operating context.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_auto_capture_controls(work_date: str) -> None:
    status = get_auto_capture_status()
    st.markdown('<div class="micro-title" style="margin-top:.9rem;">Auto Capture</div>', unsafe_allow_html=True)
    if not status["supported"]:
        st.info("Auto capture is currently supported on Windows only.")
        return

    st.caption(f"Status: {'running' if status['running'] else 'stopped'} | Poll: {status['poll_seconds']}s")
    if status["current_title"]:
        st.caption(f"Active Window: {status['current_title'][:75]}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Start", key="auto_capture_start"):
            ok, msg = start_auto_capture()
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()
    with c2:
        if st.button("Stop", key="auto_capture_stop"):
            ok, msg = stop_auto_capture()
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()


def render_mini_timer() -> None:
    components.html(
        """
        <div class="timer-shell" style="margin-top:8px;font-family:'IBM Plex Mono',monospace;color:#17212e;">
            <div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">Global Focus Timer</div>
            <div id="miniClock" style="font-size:26px;font-weight:600;margin-top:5px;">25:00</div>
            <div style="display:flex;gap:6px;margin-top:8px;">
                <button onclick="miniToggle()" style="padding:5px 9px;border-radius:9px;border:1px solid rgba(45,108,223,.18);background:#2d6cdf;color:#fff;">Start</button>
                <button onclick="miniReset()" style="padding:5px 9px;border-radius:9px;border:1px solid rgba(83,108,138,.18);background:#eef3f8;color:#17212e;">Reset</button>
            </div>
        </div>
        <script>
            let miniTotal = 25 * 60;
            let miniCurrent = miniTotal;
            let miniRunning = false;
            let miniTimer = null;
            function miniRender(){
                const m = String(Math.floor(miniCurrent/60)).padStart(2,'0');
                const s = String(miniCurrent%60).padStart(2,'0');
                document.getElementById('miniClock').textContent = `${m}:${s}`;
            }
            function miniTick(){
                if(!miniRunning) return;
                miniCurrent -= 1;
                if(miniCurrent <= 0){
                    miniCurrent = 0;
                    miniRunning = false;
                    clearInterval(miniTimer);
                    miniTimer = null;
                }
                miniRender();
            }
            function miniToggle(){
                miniRunning = !miniRunning;
                if(miniRunning && !miniTimer){ miniTimer = setInterval(miniTick,1000); }
                if(!miniRunning && miniTimer){ clearInterval(miniTimer); miniTimer = null; }
            }
            function miniReset(){
                miniCurrent = miniTotal;
                miniRunning = false;
                if(miniTimer){ clearInterval(miniTimer); miniTimer = null; }
                miniRender();
            }
            miniRender();
            window.miniToggle = miniToggle;
            window.miniReset = miniReset;
        </script>
        """,
        height=132,
    )


def render_shell_header() -> None:
    st.markdown(
        """
        <div class="shell-hero">
            <div class="hero-panel">
                <div class="eyebrow">Operational Command</div>
                <h1 class="hero-title">SOC ACCOUNTABILITY<br/>COCKPIT</h1>
                <div class="hero-copy">
                    Run the day from one screen: start a focus block, log the work, ship evidence, and see immediately whether the day is getting stronger or slipping.
                </div>
            </div>
            <div class="signal-panel">
                <div class="eyebrow">Operating Rules</div>
                <div class="stack-note">1. Quality evidence matters more than busyness.</div>
                <div class="stack-note">2. No artifact means the streak dies.</div>
                <div class="stack-note">3. Urgent tasks should be louder than backlog noise.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def is_quality_artifact(item: dict) -> bool:
    return bool(
        item.get("evidence_path", "").strip()
        and item.get("objective", "").strip()
        and item.get("query_used", "").strip()
        and item.get("recommendation", "").strip()
    )


def quality_artifact_count(artifacts: list[dict]) -> int:
    return sum(1 for item in artifacts if is_quality_artifact(item))


def compute_streak(selected_date: date) -> int:
    start = selected_date - timedelta(days=120)
    historical = get_week_data(start.isoformat(), selected_date.isoformat())
    quality_by_date: dict[str, int] = {}
    for artifact in historical["artifacts"]:
        key = artifact["work_date"]
        if is_quality_artifact(artifact):
            quality_by_date[key] = quality_by_date.get(key, 0) + 1

    streak = 0
    cursor = selected_date
    while True:
        key = cursor.isoformat()
        if quality_by_date.get(key, 0) > 0:
            streak += 1
            cursor = cursor - timedelta(days=1)
            continue
        break
    return streak


def status_class(name: str) -> str:
    normalized = name.lower()
    if normalized in {"green", "done", "healthy", "success"}:
        return "status-green"
    if normalized in {"amber", "doing", "warning", "suspicious"}:
        return "status-amber"
    if normalized in {"red", "blocked", "failed", "critical"}:
        return "status-red"
    return "status-cyan"


def activity_row(tag: str, main: str, sub: str, right: str, *, right_is_html: bool = True) -> str:
    safe_tag = escape(tag)
    safe_main = escape(main)
    safe_sub = escape(sub)
    safe_right = right if right_is_html else escape(right)
    return f'''
        <div class="activity-row">
            <div><span class="activity-tag">{safe_tag}</span></div>
            <div>
                <div class="activity-main">{safe_main}</div>
                <div class="activity-sub">{safe_sub}</div>
            </div>
            <div class="activity-right">{safe_right}</div>
        </div>
    '''


def extract_time_label(timestamp: str | None) -> str:
    if not timestamp:
        return "--:--"
    if " " in timestamp:
        return timestamp.split(" ", maxsplit=1)[1][:5]
    if "T" in timestamp:
        return timestamp.split("T", maxsplit=1)[1][:5]
    return timestamp[:5]


def render_activity_panel(title: str, rows: list[str], empty_message: str) -> None:
    st.markdown(f'<div class="section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if not rows:
        st.markdown(f'<div class="tactical-panel"><div class="stack-note">{escape(empty_message)}</div></div>', unsafe_allow_html=True)
        return
    st.markdown('<div class="tactical-panel">', unsafe_allow_html=True)
    for row in rows:
        st.markdown(row, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def build_soc_artifact_report(artifact: dict) -> str:
    incident_ref = artifact.get("incident_ref") or "N/A"
    mitre_tactic = artifact.get("mitre_tactic") or "N/A"
    mitre_technique = artifact.get("mitre_technique") or "N/A"
    repo_link = artifact.get("repo_link") or "N/A"
    note = artifact.get("note") or "No additional analyst notes."

    return (
        f"# SOC Incident Artifact Report\n\n"
        f"## Metadata\n"
        f"- Date: {artifact.get('work_date', 'N/A')}\n"
        f"- Artifact ID: {artifact.get('id', 'Draft')}\n"
        f"- Incident Ref: {incident_ref}\n"
        f"- Severity: {artifact.get('severity', 'Medium')}\n"
        f"- Category: {artifact.get('category', 'N/A')}\n"
        f"- Verdict: {artifact.get('verdict', 'N/A')}\n\n"
        f"## Executive Summary\n"
        f"{artifact.get('title', 'Untitled artifact')}\n\n"
        f"## Investigation Objective\n"
        f"{artifact.get('objective', '').strip() or 'No objective provided.'}\n\n"
        f"## Detection Logic / Query\n"
        f"```\n{artifact.get('query_used', '').strip() or 'No query supplied.'}\n```\n\n"
        f"## Evidence\n"
        f"- Evidence Path: {artifact.get('evidence_path', '') or 'N/A'}\n"
        f"- Repository Link: {repo_link}\n\n"
        f"## ATT&CK Mapping\n"
        f"- Tactic: {mitre_tactic}\n"
        f"- Technique: {mitre_technique}\n\n"
        f"## Analyst Recommendation\n"
        f"{artifact.get('recommendation', '').strip() or 'No recommendation provided.'}\n\n"
        f"## Analyst Notes\n"
        f"{note}\n"
    )


def render_dashboard_capture_lane(work_date: str, summary: dict) -> None:
    st.markdown('<div class="section-title">Rapid Capture Lane</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="lane-summary">Inline logging modeled after a productivity cockpit: track focus, log work, ship an artifact, then close the day without leaving the dashboard.</div>',
        unsafe_allow_html=True,
    )
    focus_tab, work_tab, artifact_tab, progress_tab = st.tabs([
        'Focus Session',
        'Work Block',
        'Artifact',
        'Daily Review',
    ])

    with focus_tab:
        active_session = get_active_focus_session(work_date)
        st.markdown('<div class="form-shell">', unsafe_allow_html=True)
        if active_session:
            st.success(
                f"Active session: {active_session['title']} ({active_session['session_type']}) started {extract_time_label(active_session.get('started_at'))}."
            )
            with st.form('dashboard_focus_stop_form'):
                stop_outcome = st.text_area(
                    'Session Outcome',
                    placeholder='What did you complete, what remains, and what is the next action?',
                )
                submitted = st.form_submit_button('Stop And Save Session')
                if submitted:
                    stop_focus_session(int(active_session['id']), stop_outcome.strip())
                    st.success('Focus session stopped and saved with automatic duration.')
                    st.rerun()
        else:
            with st.form('dashboard_focus_form'):
                left, right = st.columns([1.3, 1.0])
                with left:
                    focus_title = st.text_input('Focus Objective', placeholder='Threat hunt for impossible travel anomalies')
                    focus_outcome = st.text_area('Manual Outcome (Optional)', placeholder='Use this if you are logging a completed session manually.')
                with right:
                    session_type = st.selectbox('Mode', ['Deep Work', 'Lab Drill', 'Review', 'Incident Simulation'])
                    duration_minutes = st.select_slider('Manual Duration', options=[15, 25, 30, 45, 60, 90], value=25)

                start_clicked = st.form_submit_button('Start Auto Session')
                manual_clicked = st.form_submit_button('Log Manual Session')
                if start_clicked:
                    if not focus_title.strip():
                        st.error('Auto session needs an objective.')
                    else:
                        start_focus_session(work_date, session_type, focus_title.strip())
                        st.success('Focus session started. Stop it when done to auto-calculate duration.')
                        st.rerun()
                if manual_clicked:
                    if not focus_title.strip():
                        st.error('Manual session needs an objective.')
                    else:
                        add_focus_session(work_date, session_type, focus_title.strip(), int(duration_minutes), focus_outcome.strip())
                        st.success('Manual focus session logged.')
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with work_tab:
        st.markdown('<div class="form-shell">', unsafe_allow_html=True)
        with st.form('dashboard_work_block_form'):
            top_left, top_right = st.columns(2)
            with top_left:
                category = st.selectbox('Track', ['SC-200', 'SOC Lab', 'Assignment', 'SIEM Project', 'Review'], key='dash_work_track')
                planned_minutes = st.number_input('Planned Minutes', min_value=15, max_value=480, value=60, step=15, key='dash_work_planned')
            with top_right:
                completed_minutes = st.number_input('Completed Minutes', min_value=0, max_value=480, value=60, step=15, key='dash_work_completed')
                st.caption(f'Planning delta: {completed_minutes - planned_minutes:+} minutes')
            note = st.text_area('Execution Note', placeholder='What did you actually do and what is next?', key='dash_work_note')
            submitted = st.form_submit_button('Save Work Block')
            if submitted:
                add_work_block(work_date, category, int(planned_minutes), int(completed_minutes), note.strip())
                st.success('Work block saved.')
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with artifact_tab:
        st.markdown('<div class="form-shell">', unsafe_allow_html=True)
        with st.form('dashboard_artifact_form'):
            title = st.text_input('Artifact Title', placeholder='Sentinel brute-force triage', key='dash_art_title')
            top_left, top_right = st.columns(2)
            with top_left:
                category = st.selectbox('Track', ['SC-200', 'Sentinel', 'Splunk', 'Wazuh', 'SOAR', 'SOC Simulation'], key='dash_art_track')
                severity = st.selectbox('Severity', ['Low', 'Medium', 'High', 'Critical'], index=1, key='dash_art_severity')
            with top_right:
                incident_ref = st.text_input('Incident Ref', placeholder='INC-2026-0314-01', key='dash_art_incident')
                verdict = st.selectbox('Verdict', ['True Positive', 'False Positive', 'Suspicious', 'N/A'], key='dash_art_verdict')
            objective = st.text_area('Objective', placeholder='What were you proving or investigating?', key='dash_art_objective')
            query_used = st.text_area('Query Or Detection Logic', placeholder='Paste KQL, SPL, or rule logic', key='dash_art_query')
            evidence_path = st.text_input('Evidence Path', placeholder='screenshots/day14/alert-01.png', key='dash_art_evidence')
            mitre_col1, mitre_col2 = st.columns(2)
            with mitre_col1:
                mitre_tactic = st.text_input('MITRE Tactic', placeholder='TA0006 Credential Access', key='dash_art_tactic')
            with mitre_col2:
                mitre_technique = st.text_input('MITRE Technique', placeholder='T1110 Brute Force', key='dash_art_technique')
            recommendation = st.text_area('Recommendation', placeholder='Containment or remediation recommendation', key='dash_art_reco')
            note = st.text_area('Summary', placeholder='What mattered and what happens next?', key='dash_art_note')
            submitted = st.form_submit_button('Log Artifact')
            if submitted:
                missing = []
                if not title.strip():
                    missing.append('title')
                if not objective.strip():
                    missing.append('objective')
                if not query_used.strip():
                    missing.append('query')
                if not recommendation.strip():
                    missing.append('recommendation')
                if not evidence_path.strip():
                    missing.append('evidence path')
                if missing:
                    st.error(f'Artifact rejected. Missing required fields: {", ".join(missing)}')
                else:
                    add_artifact(
                        work_date,
                        title.strip(),
                        category,
                        evidence_path.strip(),
                        '',
                        verdict,
                        severity,
                        incident_ref.strip(),
                        mitre_tactic.strip(),
                        mitre_technique.strip(),
                        objective.strip(),
                        query_used.strip(),
                        recommendation.strip(),
                        note.strip(),
                    )
                    st.success('Quality artifact logged.')
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with progress_tab:
        current = summary['progress'] or {
            'sc200_modules': 0,
            'labs_completed': 0,
            'commits_pushed': 0,
            'assignments_done': 0,
            'review_note': '',
        }
        st.markdown('<div class="form-shell">', unsafe_allow_html=True)
        with st.form('dashboard_progress_form'):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                sc200_modules = st.number_input('SC-200 Modules', min_value=0, max_value=20, value=int(current['sc200_modules']), step=1, key='dash_progress_sc200')
            with col2:
                labs_completed = st.number_input('Labs', min_value=0, max_value=20, value=int(current['labs_completed']), step=1, key='dash_progress_labs')
            with col3:
                commits_pushed = st.number_input('Commits', min_value=0, max_value=30, value=int(current['commits_pushed']), step=1, key='dash_progress_commits')
            with col4:
                assignments_done = st.number_input('Assignments', min_value=0, max_value=10, value=int(current['assignments_done']), step=1, key='dash_progress_assignments')
            review_note = st.text_area('Review Note', value=current.get('review_note', ''), placeholder='What shipped, what slipped, what gets hit first next.', key='dash_progress_note')
            submitted = st.form_submit_button('Save Daily Review')
            if submitted:
                upsert_daily_progress(work_date, int(sc200_modules), int(labs_completed), int(commits_pushed), int(assignments_done), review_note.strip())
                st.success('Daily progress saved.')
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_day_timeline(summary: dict) -> None:
    events: list[tuple[str, str]] = []
    for session in summary.get('focus_sessions', []):
        events.append(
            (
                session.get('created_at', ''),
                activity_row(
                    'Focus',
                    session['title'],
                    f"{session['duration_minutes']} min | {session['session_type']} | {session.get('outcome') or 'No outcome recorded.'}",
                    f"<span class='timeline-meta'>{extract_time_label(session.get('created_at'))}</span>",
                ),
            )
        )

    for block in summary['blocks']:
        events.append(
            (
                block.get('created_at', ''),
                activity_row(
                    block['category'],
                    f"{block['completed_minutes']} min completed against {block['planned_minutes']} min planned",
                    block.get('note') or 'No execution note logged.',
                    f"<span class='timeline-meta'>{extract_time_label(block.get('created_at'))}</span>",
                ),
            )
        )

    for item in summary['artifacts']:
        events.append(
            (
                item.get('created_at', ''),
                activity_row(
                    'Artifact',
                    item['title'],
                    item.get('recommendation') or item.get('note') or 'No analyst recommendation logged.',
                    f"<span class='timeline-meta'>{extract_time_label(item.get('created_at'))}</span>",
                ),
            )
        )

    for seg in summary.get('auto_activity', []):
        minutes = max(1, int(seg.get('duration_seconds', 0) // 60))
        events.append(
            (
                seg.get('started_at', ''),
                activity_row(
                    f"Auto:{seg.get('app_name', 'Unknown')}",
                    seg.get('window_title', 'Untitled window')[:90],
                    f"{minutes} min captured automatically",
                    f"<span class='timeline-meta'>{extract_time_label(seg.get('started_at'))}</span>",
                ),
            )
        )

    rows = [row for _, row in sorted(events, key=lambda pair: pair[0], reverse=True)[:14]]
    render_activity_panel('Live Activity Timeline', rows, 'No activity has been captured yet. Start a focus block or log work to build the timeline.')


def render_focus_command_center() -> None:
    st.markdown('<div class="section-title">Focus Command</div>', unsafe_allow_html=True)
    components.html(
        """
        <div class="hero-clock" style="font-family:'IBM Plex Mono',monospace;">
            <div class="clock-label">Primary Timer</div>
            <div id="heroClock" style="font-size:72px;font-weight:700;line-height:0.95;margin-top:6px;">25:00</div>
            <div class="clock-copy">Big, obvious, and impossible to ignore. Start one block and keep the whole screen oriented around the current effort.</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;">
                <button onclick="heroSetMode(25)" style="padding:8px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.12);color:#fff;">25m Focus</button>
                <button onclick="heroSetMode(50)" style="padding:8px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.12);color:#fff;">50m Deep</button>
                <button onclick="heroSetMode(5)" style="padding:8px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.12);color:#fff;">5m Break</button>
                <button onclick="heroToggle()" style="padding:8px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.18);background:#7be0ba;color:#0f2240;font-weight:700;">Start / Pause</button>
                <button onclick="heroReset()" style="padding:8px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.18);background:#ffffff;color:#17315f;font-weight:700;">Reset</button>
            </div>
        </div>
        <script>
            let heroTotal = 25 * 60;
            let heroCurrent = heroTotal;
            let heroTimer = null;
            let heroRunning = false;

            function heroRender(){
                const m = String(Math.floor(heroCurrent / 60)).padStart(2, '0');
                const s = String(heroCurrent % 60).padStart(2, '0');
                document.getElementById('heroClock').textContent = `${m}:${s}`;
            }

            function heroTick(){
                if(!heroRunning) return;
                heroCurrent -= 1;
                if(heroCurrent <= 0){
                    heroCurrent = 0;
                    heroRunning = false;
                    clearInterval(heroTimer);
                    heroTimer = null;
                }
                heroRender();
            }

            function heroSetMode(mins){
                heroTotal = mins * 60;
                heroCurrent = heroTotal;
                heroRunning = false;
                if(heroTimer){ clearInterval(heroTimer); heroTimer = null; }
                heroRender();
            }

            function heroToggle(){
                heroRunning = !heroRunning;
                if(heroRunning && !heroTimer){ heroTimer = setInterval(heroTick, 1000); }
                if(!heroRunning && heroTimer){ clearInterval(heroTimer); heroTimer = null; }
            }

            function heroReset(){
                heroCurrent = heroTotal;
                heroRunning = false;
                if(heroTimer){ clearInterval(heroTimer); heroTimer = null; }
                heroRender();
            }

            heroRender();
            window.heroSetMode = heroSetMode;
            window.heroToggle = heroToggle;
            window.heroReset = heroReset;
        </script>
        """,
        height=270,
    )


def render_trend_charts(selected_date: date) -> None:
    start = selected_date - timedelta(days=6)
    week = get_week_data(start.isoformat(), selected_date.isoformat())
    progress_by_day = {row['work_date']: row for row in week['progress']}
    blocks_by_day: dict[str, list[dict]] = {}
    artifacts_by_day: dict[str, list[dict]] = {}
    focus_by_day: dict[str, int] = {}

    for block in week['blocks']:
        blocks_by_day.setdefault(block['work_date'], []).append(block)

    for artifact in week['artifacts']:
        artifacts_by_day.setdefault(artifact['work_date'], []).append(artifact)

    historical = get_week_data((selected_date - timedelta(days=13)).isoformat(), selected_date.isoformat())
    for session in historical.get('focus_sessions', []):
        focus_by_day[session['work_date']] = focus_by_day.get(session['work_date'], 0) + session['duration_minutes']

    rows = []
    for offset in range(7):
        current_day = start + timedelta(days=offset)
        key = current_day.isoformat()
        progress = progress_by_day.get(key, {'sc200_modules': 0, 'labs_completed': 0, 'commits_pushed': 0})
        planned = sum(item['planned_minutes'] for item in blocks_by_day.get(key, []))
        completed = sum(item['completed_minutes'] for item in blocks_by_day.get(key, []))
        quality_count = quality_artifact_count(artifacts_by_day.get(key, []))
        score = daily_score(
            progress['sc200_modules'],
            progress['labs_completed'],
            progress['commits_pushed'],
            planned,
            completed,
            quality_count,
        )
        rows.append(
            {
                'Day': current_day.strftime('%a'),
                'Score': score,
                'Focus Minutes': focus_by_day.get(key, 0),
                'Labs': progress['labs_completed'],
                'Quality Artifacts': quality_count,
            }
        )

    chart_df = pd.DataFrame(rows).set_index('Day')
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section-title">7-Day Score Trend</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-shell"><div class="chart-copy">You were missing this: the dashboard needs to show whether execution is improving, not just what exists today.</div>', unsafe_allow_html=True)
        st.line_chart(chart_df[['Score', 'Focus Minutes']])
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-title">Output Mix</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-shell"><div class="chart-copy">Labs and quality artifacts should read like throughput, not buried form fields.</div>', unsafe_allow_html=True)
        st.bar_chart(chart_df[['Labs', 'Quality Artifacts']])
        st.markdown('</div>', unsafe_allow_html=True)


def render_pomodoro_widget() -> None:
    st.markdown('<div class="section-title">Focus Timer</div>', unsafe_allow_html=True)
    components.html(
        """
                <div class="timer-shell" style="font-family:'IBM Plex Mono',monospace;color:#17212e;">
                    <div style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#64748b;">Pomodoro</div>
                    <div id="clock" style="font-size:42px;font-weight:600;margin:8px 0 10px;">25:00</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <button onclick="setMode(25)" style="padding:6px 10px;border-radius:10px;border:1px solid rgba(45,108,223,.18);background:#f5f9ff;color:#1849b8;">25m Focus</button>
                        <button onclick="setMode(5)" style="padding:6px 10px;border-radius:10px;border:1px solid rgba(45,108,223,.18);background:#f5f9ff;color:#1849b8;">5m Break</button>
                        <button onclick="toggle()" style="padding:6px 10px;border-radius:10px;border:1px solid rgba(15,159,121,.18);background:#0f9f79;color:#fff;">Start / Pause</button>
                        <button onclick="resetClock()" style="padding:6px 10px;border-radius:10px;border:1px solid rgba(83,108,138,.18);background:#eef3f8;color:#17212e;">Reset</button>
          </div>
        </div>
        <script>
          let total = 25 * 60;
          let current = total;
          let timer = null;
          let running = false;

          function render(){
            const m = String(Math.floor(current/60)).padStart(2,'0');
            const s = String(current%60).padStart(2,'0');
            document.getElementById('clock').textContent = `${m}:${s}`;
          }

          function tick(){
            if(!running) return;
            current -= 1;
            if(current <= 0){
              current = 0;
              running = false;
              clearInterval(timer);
            }
            render();
          }

          function setMode(mins){
            total = mins * 60;
            current = total;
            running = false;
            if(timer){ clearInterval(timer); timer = null; }
            render();
          }

          function toggle(){
            if(running){
              running = false;
              return;
            }
            running = true;
            if(!timer){ timer = setInterval(tick, 1000); }
          }

          function resetClock(){
            current = total;
            running = false;
            if(timer){ clearInterval(timer); timer = null; }
            render();
          }

          render();
          window.setMode = setMode;
          window.toggle = toggle;
          window.resetClock = resetClock;
        </script>
        """,
        height=220,
    )


def render_today_dashboard(summary: dict, selected_date: date) -> None:
    progress = summary["progress"] or {
        "sc200_modules": 0,
        "labs_completed": 0,
        "commits_pushed": 0,
        "assignments_done": 0,
    }
    planned = sum(b["planned_minutes"] for b in summary["blocks"]) if summary["blocks"] else 0
    completed = sum(b["completed_minutes"] for b in summary["blocks"]) if summary["blocks"] else 0
    artifacts = summary["artifacts"]
    focus_sessions = summary.get("focus_sessions", [])
    focus_minutes = sum(item["duration_minutes"] for item in focus_sessions)
    quality_count = quality_artifact_count(artifacts)
    score = daily_score(
        sc200_modules=progress["sc200_modules"],
        labs_completed=progress["labs_completed"],
        commits_pushed=progress["commits_pushed"],
        planned_minutes=planned,
        completed_minutes=completed,
        quality_artifacts_count=quality_count,
    )
    fail_state = quality_count == 0
    streak = compute_streak(selected_date)
    status_name = "RED" if fail_state else "GREEN" if score >= 75 else "AMBER"
    status_text = "FAILED DAY RISK" if fail_state else "ON TRACK" if score >= 75 else "UNDER TARGET"
    status_html = f'<span class="status-pill {status_class(status_name)}">{status_text}</span>'
    work_date = selected_date.isoformat()
    sprint_tasks = get_sprint_tasks(work_date, (selected_date + timedelta(days=2)).isoformat())
    active_tasks = [t for t in sprint_tasks if t["status"] in {"todo", "doing"}]

    top_left, top_right = st.columns([1.15, 1.0])
    with top_left:
        render_focus_command_center()
    with top_right:
        st.markdown('<div class="section-title">Mission Signals</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="signal-grid">
                <div class="signal-chip"><div class="signal-label">Streak</div><div class="signal-value">{streak}d</div><div class="stack-note">One quality artifact keeps the chain alive</div></div>
                <div class="signal-chip"><div class="signal-label">Daily Score</div><div class="signal-value">{score}</div>{status_html}</div>
                <div class="signal-chip"><div class="signal-label">Labs Completed</div><div class="signal-value">{progress['labs_completed']}</div><div class="stack-note">Hands-on reps finished today</div></div>
                <div class="signal-chip"><div class="signal-label">Support</div><div class="signal-value">{quality_count} QA | {progress['commits_pushed']} C</div><div class="stack-note">Artifacts, commits, and <span class="focus-total">{focus_minutes} focus min</span></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    focus_rows = [
        activity_row(
            session["session_type"],
            session["title"],
            f"{session['duration_minutes']} min | {session.get('outcome') or 'No outcome recorded.'}",
            f"<span class='timeline-meta'>{extract_time_label(session.get('created_at'))}</span>",
        )
        for session in focus_sessions[:6]
    ]

    auto_segments = summary.get("auto_activity", [])
    auto_rows = [
        activity_row(
            segment.get("app_name", "Unknown"),
            segment.get("window_title", "Untitled window")[:90],
            f"{max(1, int(segment.get('duration_seconds', 0) // 60))} min auto-captured",
            f"<span class='timeline-meta'>{extract_time_label(segment.get('started_at'))}</span>",
        )
        for segment in auto_segments[:6]
    ]

    if active_tasks:
        next_rows = [
            activity_row(
                task["track"],
                task["task_title"],
                f"{task['task_date']} | Priority {task['priority']}",
                f'<span class="status-pill {status_class(task["status"])}">{task["status"]}</span>',
            )
            for task in active_tasks
        ][:6]
    else:
        next_rows = []

    timeline_left, timeline_right = st.columns([1.55, 1.0])
    with timeline_left:
        render_day_timeline(summary)
    with timeline_right:
        render_activity_panel('Urgent Queue (72h)', next_rows, 'No active sprint tasks in the next 72 hours.')
        render_activity_panel('Focus Session History', focus_rows, 'No focus sessions logged yet. Start with a 25-minute objective.')
        render_activity_panel('Auto Capture Feed', auto_rows, 'Auto capture is empty. Start capture from the sidebar to ingest active-window activity.')

    render_dashboard_capture_lane(work_date, summary)

    st.markdown(
        """
        <div class="command-dock">
            <div class="command-card"><div class="command-title">Sprint Board</div><div class="command-copy">View and manage the full 14-day execution queue.</div></div>
            <div class="command-card"><div class="command-title">Edit Records</div><div class="command-copy">Update or delete existing work blocks and artifacts.</div></div>
            <div class="command-card"><div class="command-title">Weekly Review</div><div class="command-copy">7-day pressure report with score trends.</div></div>
            <div class="command-card"><div class="command-title">Penalty Board</div><div class="command-copy">14-day compliance check for missed artifact days.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    jump1, jump2, jump3, jump4 = st.columns(4)
    with jump1:
        if st.button("Open Sprint Board", key="quick_sprint"):
            st.session_state.menu = "Sprint Plan"
            st.session_state.menu_radio = "Sprint Plan"
            st.rerun()
    with jump2:
        if st.button("Edit Records", key="quick_manage"):
            st.session_state.menu = "Manage Entries"
            st.session_state.menu_radio = "Manage Entries"
            st.rerun()
    with jump3:
        if st.button("Weekly Review", key="quick_weekly"):
            st.session_state.menu = "Weekly Review"
            st.session_state.menu_radio = "Weekly Review"
            st.rerun()
    with jump4:
        if st.button("Penalty Board", key="quick_penalty"):
            st.session_state.menu = "Penalty Board"
            st.session_state.menu_radio = "Penalty Board"
            st.rerun()

    render_trend_charts(selected_date)

    if active_tasks:
        focus_task = sorted(active_tasks, key=lambda x: (x["task_date"], x["priority"]))[0]
        render_activity_panel(
            "Current Focus Block",
            [
                activity_row(
                    focus_task["track"],
                    focus_task["task_title"],
                    f"Due {focus_task['task_date']} | Priority {focus_task['priority']}",
                    f'<span class="status-pill {status_class(focus_task["status"])}">{focus_task["status"]}</span>',
                )
            ],
            "",
        )

    work_rows = [
        activity_row(
            block["category"],
            f"{block['completed_minutes']} min completed against {block['planned_minutes']} min planned",
            block.get("note") or "No execution note logged.",
            f"Block #{block['id']}",
        )
        for block in summary["blocks"][:8]
    ]
    artifact_rows = [
        activity_row(
            item["category"],
            item["title"],
            item.get("recommendation") or item.get("note") or "No analyst recommendation logged.",
            f"{item['verdict']} | {'QUALITY' if is_quality_artifact(item) else 'WEAK'}",
        )
        for item in artifacts[:8]
    ]

    left, right = st.columns([1.2, 1.0])
    with left:
        render_activity_panel("Workstream Log", work_rows, "No work blocks recorded for this day.")
    with right:
        render_activity_panel("Artifact Feed", artifact_rows, "No artifacts logged for this day.")

    if fail_state:
        st.error("This day currently fails. You need at least one quality artifact with objective, detection/query, recommendation, and evidence path.")


def render_add_work_block(work_date: str) -> None:
    st.markdown('<div class="section-title">Log Work Block</div>', unsafe_allow_html=True)
    st.markdown('<div class="form-shell">', unsafe_allow_html=True)
    with st.form("work_block_form"):
        top_left, top_right = st.columns(2)
        with top_left:
            category = st.selectbox("Track", ["SC-200", "SOC Lab", "Assignment", "SIEM Project", "Review"])
            planned_minutes = st.number_input("Planned Minutes", min_value=15, max_value=480, value=60, step=15)
        with top_right:
            completed_minutes = st.number_input("Completed Minutes", min_value=0, max_value=480, value=60, step=15)
            st.caption(f"Planning delta: {completed_minutes - planned_minutes:+} minutes")
        note = st.text_area("Execution Note", placeholder="What did you actually do, and what still remains?")
        submitted = st.form_submit_button("Save Work Block")
        if submitted:
            add_work_block(work_date, category, int(planned_minutes), int(completed_minutes), note.strip())
            st.success("Work block saved.")
    st.markdown('</div>', unsafe_allow_html=True)


def render_log_artifact(work_date: str) -> None:
    st.markdown('<div class="section-title">Ship Quality Artifact</div>', unsafe_allow_html=True)
    st.markdown('<div class="form-shell">', unsafe_allow_html=True)
    generated_report = ""
    with st.form("artifact_form"):
        st.markdown('<div class="micro-title">Scenario</div>', unsafe_allow_html=True)
        top_left, top_right = st.columns(2)
        with top_left:
            title = st.text_input("Artifact Title", placeholder="Sentinel brute-force investigation")
            category = st.selectbox("Track", ["SC-200", "Sentinel", "Splunk", "Wazuh", "SOAR", "SOC Simulation"])
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=1)
        with top_right:
            incident_ref = st.text_input("Incident Ref", placeholder="INC-2026-0314-02")
            verdict = st.selectbox("Verdict", ["True Positive", "False Positive", "Suspicious", "N/A"])
        objective = st.text_area("Objective", placeholder="What were you trying to prove or investigate?")
        st.markdown('<div class="micro-title">Evidence</div>', unsafe_allow_html=True)
        query_used = st.text_area("Query Or Detection Logic", placeholder="Paste KQL, SPL, Wazuh rule, or detection logic")
        evidence_path = st.text_input("Evidence Path", placeholder="screenshots/day1/alert1.png")
        repo_link = st.text_input("Repo Link", placeholder="https://github.com/yourname/repo")
        mitre_left, mitre_right = st.columns(2)
        with mitre_left:
            mitre_tactic = st.text_input("MITRE Tactic", placeholder="TA0006 Credential Access")
        with mitre_right:
            mitre_technique = st.text_input("MITRE Technique", placeholder="T1110 Brute Force")
        st.markdown('<div class="micro-title">Analyst Judgment</div>', unsafe_allow_html=True)
        recommendation = st.text_area("Recommendation", placeholder="Containment or remediation recommendation")
        note = st.text_area("Summary", placeholder="What mattered, what you learned, what you would do next.")
        submitted = st.form_submit_button("Log Quality Artifact")
        if submitted:
            missing = []
            if not title.strip():
                missing.append("title")
            if not objective.strip():
                missing.append("objective")
            if not query_used.strip():
                missing.append("query")
            if not recommendation.strip():
                missing.append("recommendation")
            if not evidence_path.strip():
                missing.append("evidence path")
            if missing:
                st.error(f"Artifact rejected. Missing required fields: {', '.join(missing)}")
            else:
                add_artifact(
                    work_date,
                    title.strip(),
                    category,
                    evidence_path.strip(),
                    repo_link.strip(),
                    verdict,
                    severity,
                    incident_ref.strip(),
                    mitre_tactic.strip(),
                    mitre_technique.strip(),
                    objective.strip(),
                    query_used.strip(),
                    recommendation.strip(),
                    note.strip(),
                )
                st.success("Quality artifact logged.")
                generated_report = build_soc_artifact_report(
                    {
                        "work_date": work_date,
                        "title": title.strip(),
                        "category": category,
                        "evidence_path": evidence_path.strip(),
                        "repo_link": repo_link.strip(),
                        "verdict": verdict,
                        "severity": severity,
                        "incident_ref": incident_ref.strip(),
                        "mitre_tactic": mitre_tactic.strip(),
                        "mitre_technique": mitre_technique.strip(),
                        "objective": objective.strip(),
                        "query_used": query_used.strip(),
                        "recommendation": recommendation.strip(),
                        "note": note.strip(),
                    }
                )
    st.markdown('</div>', unsafe_allow_html=True)
    if generated_report:
        st.markdown('<div class="section-title">Generated SOC Report</div>', unsafe_allow_html=True)
        st.code(generated_report, language="markdown")
        st.download_button(
            "Download SOC Report (.md)",
            data=generated_report,
            file_name=f"soc-artifact-{work_date}.md",
            mime="text/markdown",
            key=f"download-soc-report-{work_date}",
        )


def render_daily_progress(work_date: str, summary: dict) -> None:
    st.markdown('<div class="section-title">Daily Progress Record</div>', unsafe_allow_html=True)
    current = summary["progress"] or {
        "sc200_modules": 0,
        "labs_completed": 0,
        "commits_pushed": 0,
        "assignments_done": 0,
        "review_note": "",
    }
    st.markdown('<div class="form-shell">', unsafe_allow_html=True)
    with st.form("daily_progress_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sc200_modules = st.number_input("SC-200 Modules", min_value=0, max_value=20, value=int(current["sc200_modules"]), step=1)
        with col2:
            labs_completed = st.number_input("Labs", min_value=0, max_value=20, value=int(current["labs_completed"]), step=1)
        with col3:
            commits_pushed = st.number_input("Commits", min_value=0, max_value=30, value=int(current["commits_pushed"]), step=1)
        with col4:
            assignments_done = st.number_input("Assignments", min_value=0, max_value=10, value=int(current["assignments_done"]), step=1)
        review_note = st.text_area("Review Note", value=current.get("review_note", ""), placeholder="What slowed you down, what shipped, and what gets hit first tomorrow?")
        submitted = st.form_submit_button("Save Daily Progress")
        if submitted:
            upsert_daily_progress(work_date, int(sc200_modules), int(labs_completed), int(commits_pushed), int(assignments_done), review_note.strip())
            st.success("Daily progress saved.")
    st.markdown('</div>', unsafe_allow_html=True)


def render_sprint_plan(selected_date: date) -> None:
    st.markdown('<div class="section-title">14-Day Sprint Command</div>', unsafe_allow_html=True)

    seed_col, add_col = st.columns(2)
    with seed_col:
        if st.button("Seed 14-Day Plan"):
            inserted = seed_14_day_plan(selected_date)
            if inserted > 0:
                st.success(f"Added {inserted} sprint tasks.")
            else:
                st.info("Plan already exists for this date window.")
    with add_col:
        if st.button("Seed Module 16 Lab Tasks"):
            inserted = seed_module_16_lab_tasks(selected_date)
            if inserted > 0:
                st.success(f"Added {inserted} Module 16 lab tasks.")
            else:
                st.info("Module 16 tasks already exist for this date window.")

    st.markdown('<div class="form-shell">', unsafe_allow_html=True)
    st.markdown('<div class="micro-title">Add Custom Task</div>', unsafe_allow_html=True)
    with st.form("add_sprint_task_form"):
        t_left, t_mid, t_right = st.columns(3)
        with t_left:
            task_title = st.text_input("Task Title", placeholder="Write KQL brute-force detection rule")
        with t_mid:
            track = st.selectbox("Track", ["SC-200", "Lab", "Assignment", "Project", "Artifact", "Review", "Personal"])
            task_date = st.date_input("Due Date", value=selected_date)
        with t_right:
            priority = st.number_input("Priority", min_value=1, max_value=10, value=2, step=1)
        submitted = st.form_submit_button("Add Task")
        if submitted:
            if not task_title.strip():
                st.error("Task needs a title.")
            else:
                add_sprint_task(task_date.isoformat(), track, task_title.strip(), int(priority))
                st.success("Task added.")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    end = selected_date + timedelta(days=13)
    tasks = get_sprint_tasks(selected_date.isoformat(), end.isoformat())
    if not tasks:
        render_activity_panel("Sprint Queue", [], "No sprint tasks yet. Seed the 14-day plan or add your own tasks above.")
        return

    grouped: dict[str, list[dict]] = {}
    for task in tasks:
        grouped.setdefault(task["task_date"], []).append(task)

    for task_date, day_tasks in grouped.items():
        rows = [
            activity_row(
                task["track"],
                task["task_title"],
                f"Priority {task['priority']}",
                f'<span class="status-pill {status_class(task["status"])}">{task["status"]}</span>',
            )
            for task in day_tasks
        ]
        render_activity_panel(f"Day {day_tasks[0]['day_number']} | {task_date}", rows, "")

    options = {f"{t['id']} | {t['task_date']} | {t['task_title']} ({t['status']})": t["id"] for t in tasks}
    st.markdown('<div class="form-shell">', unsafe_allow_html=True)
    st.markdown('<div class="micro-title">Manage Task</div>', unsafe_allow_html=True)
    selected_label = st.selectbox("Selected Task", list(options.keys()))
    new_status = st.selectbox("New Status", ["todo", "doing", "done", "blocked"])
    manage_left, manage_right = st.columns(2)
    with manage_left:
        if st.button("Update Status"):
            update_sprint_task_status(options[selected_label], new_status)
            st.success("Task status updated.")
            st.rerun()
    with manage_right:
        if st.button("Delete Task"):
            delete_sprint_task(options[selected_label])
            st.warning("Task deleted.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_manage_entries(summary: dict) -> None:
    st.markdown('<div class="section-title">Correct Records</div>', unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="form-shell">', unsafe_allow_html=True)
        st.markdown('<div class="micro-title">Work Blocks</div>', unsafe_allow_html=True)
        if summary["blocks"]:
            work_map = {f"#{b['id']} | {b['category']} | {b['planned_minutes']}m": b for b in summary["blocks"]}
            selected_work = st.selectbox("Choose Work Block", list(work_map.keys()))
            block = work_map[selected_work]
            new_category = st.selectbox(
                "Track",
                ["SC-200", "SOC Lab", "Assignment", "SIEM Project", "Review"],
                index=["SC-200", "SOC Lab", "Assignment", "SIEM Project", "Review"].index(block["category"]) if block["category"] in ["SC-200", "SOC Lab", "Assignment", "SIEM Project", "Review"] else 0,
                key="edit_work_category",
            )
            new_planned = st.number_input("Planned Minutes", min_value=15, max_value=480, value=int(block["planned_minutes"]), step=15, key="edit_work_planned")
            new_completed = st.number_input("Completed Minutes", min_value=0, max_value=480, value=int(block["completed_minutes"]), step=15, key="edit_work_completed")
            new_note = st.text_area("Execution Note", value=block.get("note", ""), key="edit_work_note")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Update Work Block"):
                    update_work_block(block["id"], new_category, int(new_planned), int(new_completed), new_note.strip())
                    st.success("Work block updated.")
            with c2:
                if st.button("Delete Work Block"):
                    delete_work_block(block["id"])
                    st.warning("Work block deleted.")
        else:
            st.info("No work blocks to manage for this day.")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="form-shell">', unsafe_allow_html=True)
        st.markdown('<div class="micro-title">Artifacts</div>', unsafe_allow_html=True)
        if summary["artifacts"]:
            art_map = {f"#{a['id']} | {a['title']}": a for a in summary["artifacts"]}
            selected_art = st.selectbox("Choose Artifact", list(art_map.keys()))
            art = art_map[selected_art]
            title = st.text_input("Artifact Title", value=art.get("title", ""), key="edit_art_title")
            category_choices = ["SC-200", "Sentinel", "Splunk", "Wazuh", "SOAR", "SOC Simulation"]
            category = st.selectbox("Track", category_choices, index=category_choices.index(art["category"]) if art.get("category") in category_choices else 0, key="edit_art_category")
            objective = st.text_area("Objective", value=art.get("objective", ""), key="edit_art_objective")
            query_used = st.text_area("Query", value=art.get("query_used", ""), key="edit_art_query")
            recommendation = st.text_area("Recommendation", value=art.get("recommendation", ""), key="edit_art_reco")
            evidence_path = st.text_input("Evidence Path", value=art.get("evidence_path", ""), key="edit_art_evidence")
            repo_link = st.text_input("Repo Link", value=art.get("repo_link", ""), key="edit_art_repo")
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=["Low", "Medium", "High", "Critical"].index(art.get("severity", "Medium")) if art.get("severity") in ["Low", "Medium", "High", "Critical"] else 1, key="edit_art_severity")
            incident_ref = st.text_input("Incident Ref", value=art.get("incident_ref", ""), key="edit_art_incident_ref")
            mitre_tactic = st.text_input("MITRE Tactic", value=art.get("mitre_tactic", ""), key="edit_art_tactic")
            mitre_technique = st.text_input("MITRE Technique", value=art.get("mitre_technique", ""), key="edit_art_technique")
            verdict = st.selectbox("Verdict", ["True Positive", "False Positive", "Suspicious", "N/A"], index=["True Positive", "False Positive", "Suspicious", "N/A"].index(art["verdict"]) if art.get("verdict") in ["True Positive", "False Positive", "Suspicious", "N/A"] else 3, key="edit_art_verdict")
            note = st.text_area("Summary", value=art.get("note", ""), key="edit_art_note")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Update Artifact"):
                    missing = []
                    if not title.strip():
                        missing.append("title")
                    if not objective.strip():
                        missing.append("objective")
                    if not query_used.strip():
                        missing.append("query")
                    if not recommendation.strip():
                        missing.append("recommendation")
                    if not evidence_path.strip():
                        missing.append("evidence path")
                    if missing:
                        st.error(f"Cannot save. Missing quality fields: {', '.join(missing)}")
                    else:
                        update_artifact(
                            art["id"],
                            title.strip(),
                            category,
                            evidence_path.strip(),
                            repo_link.strip(),
                            verdict,
                            severity,
                            incident_ref.strip(),
                            mitre_tactic.strip(),
                            mitre_technique.strip(),
                            objective.strip(),
                            query_used.strip(),
                            recommendation.strip(),
                            note.strip(),
                        )
                        st.success("Artifact updated.")
            with c2:
                if st.button("Delete Artifact"):
                    delete_artifact(art["id"])
                    st.warning("Artifact deleted.")

            report_md = build_soc_artifact_report(art)
            st.markdown('<div class="micro-title">SOC Report Export</div>', unsafe_allow_html=True)
            st.download_button(
                "Download SOC Report (.md)",
                data=report_md,
                file_name=f"artifact-{art['id']}-soc-report.md",
                mime="text/markdown",
                key=f"download-artifact-report-{art['id']}",
            )
        else:
            st.info("No artifacts to manage for this day.")
        st.markdown('</div>', unsafe_allow_html=True)


def render_weekly_review(selected_date: date) -> None:
    st.markdown('<div class="section-title">Weekly Pressure Review</div>', unsafe_allow_html=True)
    end = selected_date
    start = end - timedelta(days=6)
    week = get_week_data(start.isoformat(), end.isoformat())
    by_day = {row["work_date"]: row for row in week["progress"]}
    day_scores = []
    day_rows = []

    for i in range(7):
        day = (start + timedelta(days=i)).isoformat()
        label = (start + timedelta(days=i)).strftime("%a %b %d")
        progress = by_day.get(day, {"sc200_modules": 0, "labs_completed": 0, "commits_pushed": 0, "assignments_done": 0})
        day_blocks = [b for b in week["blocks"] if b["work_date"] == day]
        day_artifacts = [a for a in week["artifacts"] if a["work_date"] == day]
        planned = sum(b["planned_minutes"] for b in day_blocks)
        completed = sum(b["completed_minutes"] for b in day_blocks)
        quality_count = quality_artifact_count(day_artifacts)
        score = daily_score(progress["sc200_modules"], progress["labs_completed"], progress["commits_pushed"], planned, completed, quality_count)
        day_scores.append(score)
        state = "GREEN" if score >= 75 else "AMBER" if score >= 55 else "RED"
        day_rows.append({
            "label": label,
            "score": score,
            "state": state,
            "modules": int(progress["sc200_modules"]),
            "labs": int(progress["labs_completed"]),
            "commits": int(progress["commits_pushed"]),
            "quality_count": quality_count,
            "planned": planned,
            "completed": completed,
        })

    if not day_rows:
        st.info("No weekly data available.")
        return

    status = week_health(day_scores)
    avg_score = int(sum(day_scores) / max(len(day_scores), 1))
    total_labs = sum(r["labs"] for r in day_rows)
    total_quality = sum(r["quality_count"] for r in day_rows)
    total_focus = sum(s["duration_minutes"] for s in week.get("focus_sessions", []))
    status_color = "var(--green)" if status == "GREEN" else "var(--amber)" if status == "AMBER" else "var(--red)"

    st.markdown(
        f"""
        <div class="signal-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 1rem;">
            <div class="signal-chip">
                <div class="signal-label">Week Health</div>
                <div class="signal-value" style="color:{status_color};">{status}</div>
                <div class="stack-note">7-day rolling average</div>
            </div>
            <div class="signal-chip">
                <div class="signal-label">Avg Daily Score</div>
                <div class="signal-value">{avg_score}</div>
                <div class="stack-note">Target: 75+</div>
            </div>
            <div class="signal-chip">
                <div class="signal-label">Labs Done</div>
                <div class="signal-value">{total_labs}</div>
                <div class="stack-note">Hands-on reps this week</div>
            </div>
            <div class="signal-chip">
                <div class="signal-label">Quality Artifacts</div>
                <div class="signal-value">{total_quality}</div>
                <div class="stack-note">{total_focus} focus min total</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    activity_rows = [
        activity_row(
            r["label"],
            f"Score {r['score']} — {r['labs']} labs | {r['quality_count']} artifacts | {r['modules']} modules",
            f"{r['completed']}m done of {r['planned']}m planned | {r['commits']} commits",
            f'<span class="status-pill {status_class(r["state"])}">{r["state"]}</span>',
        )
        for r in day_rows
    ]
    render_activity_panel("Day-by-Day Breakdown", activity_rows, "No activity recorded this week.")

    chart_df = pd.DataFrame([
        {"Day": r["label"][:3], "Score": r["score"], "Labs": r["labs"], "Artifacts": r["quality_count"]}
        for r in day_rows
    ]).set_index("Day")
    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown('<div class="chart-shell"><div class="chart-copy">Score trend — aim for green on every day.</div>', unsafe_allow_html=True)
        st.line_chart(chart_df[["Score"]])
        st.markdown('</div>', unsafe_allow_html=True)
    with right_col:
        st.markdown('<div class="chart-shell"><div class="chart-copy">Labs and quality artifacts shipped per day.</div>', unsafe_allow_html=True)
        st.bar_chart(chart_df[["Labs", "Artifacts"]])
        st.markdown('</div>', unsafe_allow_html=True)


def render_penalty_board(selected_date: date) -> None:
    st.markdown('<div class="section-title">Penalty Board</div>', unsafe_allow_html=True)
    end = selected_date
    start = end - timedelta(days=13)
    data = get_week_data(start.isoformat(), end.isoformat())
    artifacts_by_date: dict[str, list[dict]] = {}
    for row in data["artifacts"]:
        artifacts_by_date.setdefault(row["work_date"], []).append(row)

    misses = []
    hits: list[tuple[str, int]] = []
    for i in range(14):
        day = (start + timedelta(days=i)).isoformat()
        q = quality_artifact_count(artifacts_by_date.get(day, []))
        if q == 0:
            misses.append(day)
        else:
            hits.append((day, q))

    total_days = 14
    missed_days = len(misses)
    compliance = int(((total_days - missed_days) / total_days) * 100)
    compliance_state = "GREEN" if compliance >= 85 else "AMBER" if compliance >= 60 else "RED"
    compliance_color = "var(--green)" if compliance_state == "GREEN" else "var(--amber)" if compliance_state == "AMBER" else "var(--red)"

    st.markdown(
        f"""
        <div class="signal-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 1rem;">
            <div class="signal-chip">
                <div class="signal-label">Days Evaluated</div>
                <div class="signal-value">{total_days}</div>
                <div class="stack-note">Rolling 14-day window</div>
            </div>
            <div class="signal-chip">
                <div class="signal-label">Missed Quality Days</div>
                <div class="signal-value" style="color:var(--red);">{missed_days}</div>
                <div class="stack-note">Each is an artifact debt</div>
            </div>
            <div class="signal-chip">
                <div class="signal-label">Compliance Rate</div>
                <div class="signal-value" style="color:{compliance_color};">{compliance}%</div>
                <div class="stack-note">Target: 85%+</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not misses:
        st.success("No missed quality artifact days in this 14-day window. Full compliance.")
    else:
        miss_rows = [
            activity_row(
                "MISSED",
                day,
                "No quality artifact shipped. This day counts as failed.",
                '<span class="status-pill status-red">DEBT</span>',
            )
            for day in misses
        ]
        render_activity_panel(f"Missed Days — {missed_days} Artifact Debt{'s' if missed_days != 1 else ''}", miss_rows, "")

    if hits:
        hit_rows = [
            activity_row(
                "CLEAR",
                day,
                f"{q} quality artifact{'s' if q > 1 else ''} shipped.",
                '<span class="status-pill status-green">COMPLIANT</span>',
            )
            for day, q in hits
        ]
        render_activity_panel("Compliant Days", hit_rows, "")

from datetime import date

import streamlit as st

from tracker.db import get_day_summary, init_db, seed_today_if_missing
from tracker.ui import (
    apply_glass_theme,
    render_auto_capture_controls,
    render_mini_timer,
    render_navigation_signal,
    render_shell_header,
    render_add_work_block,
    render_daily_progress,
    render_log_artifact,
    render_manage_entries,
    render_penalty_board,
    render_sprint_plan,
    render_today_dashboard,
    render_weekly_review,
)

st.set_page_config(page_title="SOC Accountability Tracker", layout="wide")
apply_glass_theme()

init_db()
seed_today_if_missing()

render_shell_header()

menu_options = [
    "Today Dashboard",
    "Add Work Block",
    "Log Artifact",
    "Daily Progress",
    "Sprint Plan",
    "Manage Entries",
    "Weekly Review",
    "Penalty Board",
]

if "menu" not in st.session_state or st.session_state.menu not in menu_options:
    st.session_state.menu = "Today Dashboard"

if "menu_radio" not in st.session_state or st.session_state.menu_radio not in menu_options:
    st.session_state.menu_radio = st.session_state.menu

with st.sidebar:
    render_navigation_signal()
    st.radio("Navigation", menu_options, key="menu_radio", label_visibility="collapsed")
    selected_date = st.date_input("Working Date", value=date.today())
    render_auto_capture_controls(selected_date.isoformat())
    render_mini_timer()

st.session_state.menu = st.session_state.menu_radio
work_date = selected_date.isoformat()
summary = get_day_summary(work_date)

if st.session_state.menu == "Today Dashboard":
    render_today_dashboard(summary, selected_date)

elif st.session_state.menu == "Add Work Block":
    render_add_work_block(work_date)

elif st.session_state.menu == "Log Artifact":
    render_log_artifact(work_date)

elif st.session_state.menu == "Daily Progress":
    render_daily_progress(work_date, summary)

elif st.session_state.menu == "Sprint Plan":
    render_sprint_plan(selected_date)

elif st.session_state.menu == "Manage Entries":
    render_manage_entries(summary)

elif st.session_state.menu == "Weekly Review":
    render_weekly_review(selected_date)

elif st.session_state.menu == "Penalty Board":
    render_penalty_board(selected_date)

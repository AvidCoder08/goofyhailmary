import streamlit as st
import datetime as dt
from datetime import date
from session_utils import restore_session_from_cookie
from calendar_utils import get_calendar_events
from role_utils import is_superadmin

restore_session_from_cookie()

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()

# Get profile data
profile = st.session_state.profile

# Handle both dict and object profiles
if isinstance(profile, dict):
    personal = profile.get('personal', {})
    name = personal.get('name', 'User') if isinstance(personal, dict) else personal.name
    program = personal.get('program', 'N/A') if isinstance(personal, dict) else personal.program
    branch = personal.get('branch', 'N/A') if isinstance(personal, dict) else personal.branch
    section = personal.get('section', 'N/A') if isinstance(personal, dict) else personal.section
    semester = personal.get('semester', 'N/A') if isinstance(personal, dict) else personal.semester
else:
    personal = profile.personal
    name = personal.name
    program = personal.program
    branch = personal.branch
    section = personal.section
    semester = personal.semester

st.title(f"Dashboard - Hi, {name.split()[0]}! 👋")

# Display user info cards
info_col1, info_col2, info_col3 = st.columns(3)
with info_col1:
    st.info(f"**Program:** {program}")
with info_col2:
    st.info(f"**Branch:** {branch}")
with info_col3:
    st.info(f"**Section:** {section} • Sem {semester}")
col1, col2 = st.columns(2)

# Initialize session state for tasks
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

#tasks class
class ToDoList:
    def __init__(self, tasks_list):
        self.tasks = tasks_list

    def add_task(self, task):
        self.tasks.append(task)

    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
    
    def finish_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            st.success(f"✅ Yessir! '{task}' is done fr fr 🔥")

    def get_tasks(self):
        return self.tasks

todo_list = ToDoList(st.session_state.tasks)

# Academic Calendar Section
st.divider()
st.header("📅 Academic Calendar")
st.caption("Managed by the GOAT (superadmin) 🐐")

if is_superadmin(profile):
    st.page_link("superadmin.py", label="Manage Calendar", icon="🛡️")

def _parse_date(value):
    try:
        return date.fromisoformat(value) if value else None
    except Exception:
        return None

events = []
try:
    raw_events = get_calendar_events()
    for event in raw_events:
        events.append({
            "id": event.get("id"),
            "title": event.get("title", "Untitled"),
            "type": event.get("type", "milestone"),
            "start_date": _parse_date(event.get("start_date")),
            "end_date": _parse_date(event.get("end_date")),
            "description": event.get("description", ""),
        })
except RuntimeError as exc:
    # GitHub credentials not configured
    if "GITHUB_TOKEN not set" in str(exc):
        st.info("📅 Calendar feature requires GitHub configuration")
    else:
        st.error(f"Calendar is down fr 💔 {exc}")
    events = []
except Exception as exc:
    st.error(f"Calendar is down fr 💔 {exc}")
    events = []

if not events:
    st.info("No events yet bestie! Dead asf 💀")
else:
    today = date.today()
    # Filter upcoming events - show if end_date is in future or start_date is in future
    upcoming = [e for e in events if (e.get("start_date") and e.get("start_date") >= today) or (e.get("end_date") and e.get("end_date") >= today) or (not e.get("start_date") and not e.get("end_date"))]
    upcoming = sorted(upcoming, key=lambda x: x.get("start_date") or today)

    st.subheader("🔔 Upcoming")
    
    # Display events in a 3x2 grid
    grid_events = upcoming[:6]
    rows = 2
    cols = 3
    
    def display_event_card(event, container):
        """Display a single event card"""
        start = event.get("start_date")
        end = event.get("end_date")
        title = event.get("title")
        event_type = event.get("type")

        if start and end:
            date_str = f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
            days_until = (start - today).days
        elif start:
            date_str = start.strftime("%B %d, %Y")
            days_until = (start - today).days
        else:
            date_str = "Date TBD"
            days_until = None

        icon = {
            "holiday": "🎉",
            "assessment": "📝",
            "meeting": "👥",
            "milestone": "📍",
        }.get(event_type, "📍")

        with container:
            card = st.container(border=True)
            with card:
                st.markdown(f"<div style='font-size: 2em; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
                st.markdown(f"**{title}**")
                if days_until is None:
                    st.caption(date_str)
                elif days_until == 0:
                    st.caption(f"{date_str} • **Today!**")
                elif days_until == 1:
                    st.caption(f"{date_str} • Tomorrow")
                elif days_until < 7:
                    st.caption(f"{date_str} • In {days_until} days")
                else:
                    st.caption(date_str)

                if event.get("description"):
                    st.caption(event.get("description"))
    
    # Create grid layout
    for row in range(rows):
        cols_layout = st.columns(cols)
        for col_idx in range(cols):
            event_idx = row * cols + col_idx
            if event_idx < len(grid_events):
                display_event_card(grid_events[event_idx], cols_layout[col_idx])

    with st.expander("📆 Full Calendar"):
        events_sorted = sorted(events, key=lambda x: x.get("start_date") or today)
        for event in events_sorted:
            start = event.get("start_date")
            end = event.get("end_date")
            title = event.get("title")
            event_type = event.get("type")

            if start and end:
                date_str = f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
            elif start:
                date_str = start.strftime("%B %d, %Y")
            else:
                date_str = "Date TBD"

            st.write(f"• **{title}** ({event_type}) — {date_str}")
import streamlit as st
from datetime import date
from session_utils import restore_session_from_cookie
from calendar_utils import (
    get_calendar_events, add_calendar_event, update_calendar_event, delete_calendar_event,
    get_semester_settings, save_semester_settings
)
from role_utils import is_superadmin

restore_session_from_cookie()

if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()

profile = st.session_state.profile
if not is_superadmin(profile):
    st.error("Nah you ain't got permission for this bestie 🚫")
    st.stop()

st.title("🛡️ Superadmin")
st.caption("U da GOAT - manage everything 🐐✨")

# Semester Settings Section
st.subheader("📚 Semester Settings")
try:
    settings = get_semester_settings()
    current_end_date = settings.get("semester_end_date")

    with st.form("semester_settings_form"):
        if current_end_date:
            try:
                default_date = date.fromisoformat(current_end_date)
            except:
                default_date = date.today()
        else:
            default_date = date.today()

        semester_end = st.date_input("Semester End Date", value=default_date)

        if st.form_submit_button("Save Semester Settings", type="primary"):
            try:
                save_semester_settings({"semester_end_date": semester_end.isoformat()})
                st.success("Semester settings saved! 🎓")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save settings: {e}")

    if current_end_date:
        st.info(f"Current semester ends: {current_end_date}")
except Exception as e:
    st.error(f"Failed to load semester settings: {e}")

st.divider()

st.subheader("Create Calendar Event")
with st.form("create_event_form", clear_on_submit=True):
    title = st.text_input("Title", placeholder="ISA 1 WEEK (Units I & II)")
    event_type = st.selectbox("Type", ["assessment", "meeting", "holiday", "milestone"], index=0)
    start_date = st.date_input("Start date", value=date.today())
    has_end_date = st.checkbox("Has end date", value=False, key="create_has_end_date")
    end_date = st.date_input("End date", value=date.today(), key="create_end_date")
    if not has_end_date:
        end_date = None
    description = st.text_area("Description (optional)", placeholder="Any additional notes")

    submitted = st.form_submit_button("Add Event", type="primary")
    if submitted:
        if not title.strip():
            st.error("Gotta give this event a name bestie! 📛")
        else:
            try:
                add_calendar_event(
                    title=title.strip(),
                    event_type=event_type,
                    start_date=start_date,
                    end_date=end_date,
                    description=description.strip() if description else ""
                )
                st.success("Event is live! Go off sis 🎉")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add event: {e}")

st.divider()
st.subheader("Existing Events")

try:
    events = get_calendar_events()

    def sort_key(item):
        return item.get("start_date", "") or ""

    events = sorted(events, key=sort_key)

    if not events:
        st.info("No events bestie! Add sum 📅")
    else:
        for event in events:
            title_val = event.get("title", "Untitled")
            start = event.get("start_date") or ""
            end = event.get("end_date") or ""
            event_type_val = event.get("type", "")
            description_val = event.get("description", "")

            with st.expander(f"{title_val} ({event_type_val})"):
                st.write(f"Start: {start}")
                if end:
                    st.write(f"End: {end}")
                if description_val:
                    st.caption(description_val)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Delete", key=f"delete_{event['id']}"):
                        try:
                            delete_calendar_event(event["id"])
                            st.success("Yeeted that event 🗑️")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
                with col2:
                    with st.form(f"edit_{event['id']}"):
                        new_title = st.text_input("Title", value=title_val)
                        new_type = st.selectbox(
                            "Type",
                            ["assessment", "meeting", "holiday", "milestone"],
                            index=["assessment", "meeting", "holiday", "milestone"].index(event_type_val) if event_type_val in ["assessment", "meeting", "holiday", "milestone"] else 0,
                        )
                        new_start = st.date_input("Start date", value=date.fromisoformat(start) if start else date.today())
                        has_end = st.checkbox("Has end date", value=bool(end), key=f"has_end_{event['id']}")
                        new_end = st.date_input("End date", value=date.fromisoformat(end) if end else date.today(), key=f"end_date_{event['id']}")
                        if not has_end:
                            new_end = None
                        new_desc = st.text_area("Description", value=description_val)
                        saved = st.form_submit_button("Save Changes")
                        if saved:
                            try:
                                update_calendar_event(
                                    event_id=event["id"],
                                    title=(new_title or "").strip(),
                                    event_type=new_type,
                                    start_date=new_start,
                                    end_date=new_end,
                                    description=(new_desc or "").strip()
                                )
                                st.success("Updated fr fr! 🔥")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to update: {e}")
except Exception as exc:
    st.error(f"Couldn't load events ngl 😪 {exc}")

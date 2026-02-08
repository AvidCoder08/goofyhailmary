import streamlit as st
import asyncio
from session_utils import restore_session_from_cookie
from pesuacademy.pages.seating_information import _SeatingInformationHandler

restore_session_from_cookie()

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()

st.title("📍 Exam Seating Arrangement")

@st.cache_data(ttl=3600)
def get_seating_arrangement():
    """Fetch seating arrangement from pesuacademy API."""
    try:
        # Get the PESU session from session state
        pesu_session = st.session_state.get('pesu_session')
        if not pesu_session:
            return None, "Session not available"
        
        # Run the async function to fetch seating
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        seating_data = loop.run_until_complete(_SeatingInformationHandler._get(pesu_session))
        
        return seating_data, None
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        st.error("**Error Details:**")
        st.code(error_details)
        return None, f"Error fetching seating: {str(e)}"

# Fetch and display seating arrangement
with st.spinner("Loading exam seating arrangements..."):
    seating_data, error = get_seating_arrangement()

if error:
    st.warning(f"⚠️ {error}")
elif seating_data and len(seating_data) > 0:
    st.success(f"✅ Found {len(seating_data)} exam seating arrangement(s)")
    
    # Display seating information in an expandable format
    for idx, seat in enumerate(seating_data, 1):
        with st.expander(f"📋 {seat.name} - {seat.course_code}", expanded=(idx == 1)):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📅 Date**")
                st.markdown(seat.date)
                st.markdown("")
                st.markdown("**🕒 Time**")
                st.markdown(seat.time)
            with col2:
                st.markdown("**🏢 Terminal/Hall**")
                st.markdown(seat.terminal)
                st.markdown("")
                st.markdown("**📍 Block/Section**")
                st.markdown(seat.block)
else:
    st.info("ℹ️ No exam seating arrangements available at the moment.")
    st.markdown("Check back closer to your exam dates!")

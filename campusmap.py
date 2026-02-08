import streamlit as st
from session_utils import restore_session_from_cookie

restore_session_from_cookie()

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()

st.title("🗺️ Campus Map")

# Create two columns - map on left, info on right
col1, col2 = st.columns([3, 1], gap="large")

with col1:
    # Embed Google My Maps
    # Replace the src URL with your actual Google My Maps embed URL
    # To get the embed code:
    # 1. Go to Google My Maps (mymaps.google.com)
    # 2. Create or open a map
    # 3. Click "Share" > "Embed on website"
    # 4. Copy the src URL from the iframe code
    
    google_maps_embed = """
    <iframe src="https://www.google.com/maps/d/u/0/embed?mid=1oiiRJpBkUlxS7jTQgC4TyjSkNkEgRtk&ehbc=2E312F" width="640" height="480"></iframe>    """
    
    st.markdown(google_maps_embed, unsafe_allow_html=True)
    
    st.info("💡 **Pro tip:** Click on the map markers to see building details and directions!")

with col2:
    st.subheader("📍 Quick Links")
    st.markdown("""
    - **Main Campus**
    - Academic Block
    - Admin Block
    - Library
    - Cafeteria
    - Sports Complex
    - Hostels
    - Medical Center
    """)
    
    st.subheader("ℹ️ Campus Info")
    st.caption("""
    Opens: 7:00 AM
    Closes: 10:00 PM
    
    Emergency: 9876543210
    """)
    
    if st.button("Get Directions", use_container_width=True):
        st.info("Open Google Maps for turn-by-turn directions 🧭")

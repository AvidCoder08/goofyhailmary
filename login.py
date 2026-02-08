import streamlit as st
import asyncio
import json
from pesuacademy import PESUAcademy
from session_utils import save_session_cookie, restore_session_from_cookie, clear_session_cookie

async def login_user(username, password):
    """Async function to login to PESU Academy"""
    try:
        pesu = await PESUAcademy.login(username, password)
        profile = await pesu.get_profile()
        await pesu.close()
        return profile, None
    except Exception as e:
        return None, str(e)

def main():
    st.set_page_config(page_title="Login - Hail Mary", layout="centered")
    
    restore_session_from_cookie()

    # Check if user is already logged in
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.success("Already in bestie! U good 🔐✨")
        
        # Display user info
        if isinstance(st.session_state.profile, dict):
            personal = st.session_state.profile.get('personal', {})
        else:
            personal = st.session_state.profile.personal
        
        st.markdown(f"### Hi, {personal.get('name', 'User') if isinstance(personal, dict) else personal.name}! 👋")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Program", personal.get('program', 'N/A') if isinstance(personal, dict) else personal.program)
        with col2:
            st.metric("Branch", personal.get('branch', 'N/A') if isinstance(personal, dict) else personal.branch)
        with col3:
            st.metric("Semester", personal.get('semester', 'N/A') if isinstance(personal, dict) else personal.semester)
        
        col4, col5 = st.columns(2)
        with col4:
            section = personal.get('section', 'N/A') if isinstance(personal, dict) else personal.section
            st.info(f"**Section:** {section}")
        with col5:
            srn = personal.get('srn', 'N/A') if isinstance(personal, dict) else personal.srn
            st.info(f"**SRN:** {srn}")
        
        # Logout button
        if st.button("Logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.profile = None
            st.session_state.pesu_username = None
            st.session_state.pesu_password = None
            st.session_state.restore_attempted = False
            clear_session_cookie()
            st.success("Logged out successfully!")
            st.rerun()
    else:
        # Clean, minimal login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("# Sign in")
            st.markdown("---")
            
            with st.form("login_form"):
                username = st.text_input("PRN / SRN", placeholder="Enter your PRN or SRN")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Gotta enter username AND password bestie 🔑")
                    else:
                        with st.spinner("Logging in..."):
                            # Run async login
                            profile, error = asyncio.run(login_user(username, password))
                            
                            if error:
                                st.error(f"Login said nope 🚫 {error}")
                            else:
                                st.session_state.logged_in = True
                                st.session_state.profile = profile
                                st.session_state.pesu_username = username
                                st.session_state.pesu_password = password
                                
                                # Save session to browser cookie
                                save_session_cookie(username, password, profile)
                                
                                st.success("U in now! Let's gooo 🔥")
                                st.rerun()
            
            st.markdown("---")
            st.markdown(
                "<div style='text-align: center; font-size: 0.85rem; color: #888;'>"
                "Session data stored securely in your browser only.</div>",
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()

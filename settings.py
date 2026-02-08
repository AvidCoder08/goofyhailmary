import streamlit as st
import base64
from io import BytesIO
from session_utils import restore_session_from_cookie, clear_session_cookie

# Safely import role utilities
try:
    from role_utils import get_class_id, get_class_id_variants, get_user_ids, is_cr
except (ImportError, KeyError, ModuleNotFoundError):
    # Fallback functions
    def get_class_id(profile):
        return ""
    
    def get_class_id_variants(profile):
        return []
    
    def get_user_ids(profile):
        return set()
    
    def is_cr(profile):
        return False

restore_session_from_cookie()

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()

st.header("Profile")

profile = st.session_state.profile

# Handle both dict and object profiles
if isinstance(profile, dict):
    personal = profile.get('personal', {})
else:
    personal = profile.personal

# Create layout with image on left and details on right
col_img, col_details = st.columns([1, 3])

with col_img:
    # Display profile image if available
    image_data = personal.get('image') if isinstance(personal, dict) else personal.image
    if image_data:
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            st.image(image_bytes, use_container_width=True)
        except:
            # If decoding fails, show placeholder
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 100px 20px; text-align: center; border-radius: 8px;">
                <p style="font-size: 48px; margin: 0;">👤</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Placeholder if no image
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 100px 20px; text-align: center; border-radius: 8px;">
            <p style="font-size: 48px; margin: 0;">👤</p>
        </div>
        """, unsafe_allow_html=True)

with col_details:
    # Create 3 columns for the details grid
    detail_col1, detail_col2, detail_col3 = st.columns(3)
    
    # Helper function to get value from dict or object
    def get_value(key):
        if isinstance(personal, dict):
            return personal.get(key, 'N/A')
        else:
            return getattr(personal, key, 'N/A')
    
    with detail_col1:
        st.markdown("**Name**")
        st.markdown(f"{get_value('name')}")
        st.markdown("")
        
        st.markdown("**PESU ID**")
        st.markdown(f"{get_value('pesu_id')}")
        st.markdown("")
        
        st.markdown("**SRN**")
        st.markdown(f"{get_value('srn')}")
        
        
        
    
    with detail_col2:
        st.markdown("**Branch**")
        st.markdown(f"{get_value('branch')}")
        st.markdown("")

        st.markdown("**Semester**")
        st.markdown(f"{get_value('semester')}")
        st.markdown("")
        
        st.markdown("**Section**")
        section = get_value('section')
        st.markdown(f"{section}")
        
        # Show cycle based on first letter of section
        if isinstance(personal, dict):
            sem = personal.get('semester', '1')
        else:
            sem = getattr(personal, 'semester', '1')
        
        # Parse semester
        try:
            if isinstance(sem, str):
                current_sem = int(sem.split('-')[-1]) if '-' in sem else int(sem)
            else:
                current_sem = int(sem)
        except:
            current_sem = 1
        
        # Show cycle for 1st and 2nd semester
        if current_sem in [1, 2] and section and len(str(section)) > 0:
            first_letter = str(section)[8].upper()
            if first_letter == 'C':
                st.markdown("**Cycle**")
                st.markdown("Chemistry")
            elif first_letter == 'P':
                st.markdown("**Cycle**")
                st.markdown("Physics")
    
    with detail_col3:
        st.markdown("**Program**")
        st.markdown(f"{get_value('program')}")
        st.markdown("")

        st.markdown("**Email ID**")
        st.markdown(f"{get_value('email_id')}")
        st.markdown("")
        
        st.markdown("**Contact No**")
        st.markdown(f"{get_value('contact_no')}")
        st.markdown("")
        
        
    
    

# Logout section
st.divider()
st.header("Account")

if st.button("Logout", use_container_width=True, type="secondary",icon=":material/logout:"):
    # Clear session
    clear_session_cookie()
    
    # Clear session state
    st.session_state.logged_in = False
    st.session_state.profile = None
    st.session_state.pesu_username = None
    st.session_state.pesu_password = None
    st.success("Peace out bestie! See u later 👋✨")
    st.rerun()

st.divider()

# with st.expander("Role debug", expanded=False):
#     st.caption("Use this to match your class_id key in role_config.py")
#     st.write("Class ID:", get_class_id(profile))
#     st.write("Class ID variants:", get_class_id_variants(profile))
#     st.write("User IDs:", sorted(get_user_ids(profile)))
#     st.write("CR access:", is_cr(profile))

st.markdown("""
## About
Hail Mary is an alternative to PESU Academy (which we know sucks), it is still in Beta stages. You may experience some bugs. You can raise issues on my [Github Page](https://github.com/AvidCoder08/better-pesu-acad/issues)
## Privacy
Your session is stored securely in your browser. Each device requires its own login. Your data never leaves your device except when communicating with PESU Academy servers. This project uses the PESU API created and maintained by seniors and alumni of PESU.
""")
st.markdown("""
<footer>Made with ❤️ by Shashank Munnangi. <br> If you like this, consider tipping: <a href="https://www.upi.me/pay?pa=soham.s.munnangi@axl">Tip me!</a>. This motivates me to work more on this project!</footer>
""",unsafe_allow_html=True)
import streamlit as st
import asyncio
from pesuacademy import PESUAcademy
import json
import os
from session_utils import restore_session_from_cookie
from role_utils import get_class_id, is_cr, get_section_from_class_id
from materials_utils import get_materials_by_section

restore_session_from_cookie()

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()

st.title("📚 Courses & Materials")

# Get profile early for role checks
profile = st.session_state.profile

material_source = st.radio(
    "Choose material source:",
    options=["PESU Academy", "Teacher Files"],
    horizontal=True,
)

if material_source == "Teacher Files":
    class_id = get_class_id(profile)
    section = get_section_from_class_id(class_id)
    st.subheader("Teacher Files")
    st.caption(f"Class: {class_id} • Section: {section} 📍")

    if is_cr(profile):
        st.page_link("admin.py", label="Go to Class Admin", icon="🛡️")

    course_filter = st.text_input("Filter by course code (optional)", placeholder="UE22CS202")
    
    # Get all materials for this section only
    materials = get_materials_by_section(class_id, section)
    
    # Filter by course code if provided
    if course_filter.strip():
        materials = [m for m in materials if m.get("course_code") == course_filter.strip()]

    if not materials:
        st.info("No teacher materials found bestie! CRs said JK 😭")
    else:
        materials = sorted(materials, key=lambda x: x.get("uploaded_at", ""), reverse=True)
        for item in materials:
            title = item.get("course_title") or item.get("course_code") or "Course"
            filename = item.get("filename", "file")
            with st.expander(f"{title} • {filename}"):
                st.write(f"Course: {item.get('course_code', '')}")
                st.write(f"Section: {item.get('section', 'N/A')} 📍")
                st.write(f"Uploaded at: {item.get('uploaded_at', '')}")
                file_url = item.get("file_url")
                if file_url:
                    st.link_button("Open File", file_url, type="primary")
                else:
                    st.error("Link is lowkey broken rn 🪦")

    st.stop()

# Get profile to determine current semester
if isinstance(profile, dict):
    personal = profile.get('personal', {})
    sem_str = personal.get('semester', '1') if isinstance(personal, dict) else personal.get('semester', '1')
else:
    sem_str = profile.personal.semester

# Parse semester
try:
    if isinstance(sem_str, str):
        current_sem = int(sem_str.split('-')[-1]) if '-' in sem_str else int(sem_str)
    else:
        current_sem = int(sem_str)
except:
    current_sem = 1

async def fetch_courses(semester):
    """Fetch courses from PESU Academy API"""
    try:
        pesu = await PESUAcademy.login(
            st.session_state.pesu_username,
            st.session_state.pesu_password
        )
        courses = await pesu.get_courses(semester)
        await pesu.close()
        return courses, None
    except Exception as e:
        return None, str(e)

async def fetch_units(course_id):
    """Fetch units for a course"""
    try:
        pesu = await PESUAcademy.login(
            st.session_state.pesu_username,
            st.session_state.pesu_password
        )
        units = await pesu.get_units_for_course(course_id)
        await pesu.close()
        return units, None
    except Exception as e:
        return None, str(e)

async def fetch_topics(unit_id):
    """Fetch topics for a unit"""
    try:
        pesu = await PESUAcademy.login(
            st.session_state.pesu_username,
            st.session_state.pesu_password
        )
        topics = await pesu.get_topics_for_unit(unit_id)
        await pesu.close()
        return topics, None
    except Exception as e:
        return None, str(e)

async def fetch_materials(topic, material_type_id):
    """Fetch material links for a topic"""
    try:
        pesu = await PESUAcademy.login(
            st.session_state.pesu_username,
            st.session_state.pesu_password
        )
        materials = await pesu.get_material_links(topic, material_type_id)
        await pesu.close()
        return materials, None
    except Exception as e:
        return None, str(e)

# Semester selector
selected_sem = st.selectbox(
    "Select Semester:",
    options=list(range(1, current_sem + 1)),
    index=current_sem - 1,
    key="course_semester_selector"
)

# Auto-fetch courses when semester changes
if st.session_state.get('last_selected_sem') != selected_sem or 'courses' not in st.session_state:
    st.session_state.last_selected_sem = selected_sem
    with st.spinner(f"Fetching semester {selected_sem} courses..."):
        courses_dict, error = asyncio.run(fetch_courses(selected_sem))
        
        if error:
            st.error(f"Couldn't get courses ngl 😪 {error}")
        elif courses_dict:
            # Store courses in session state
            st.session_state.courses = courses_dict.get(selected_sem, [])
        else:
            st.error("Courses said bye 👋 No data fr")

# Display courses if available
if 'courses' in st.session_state and st.session_state.courses:
    st.markdown("---")
    st.subheader(f"Semester {selected_sem} Courses")
    
    # Create course selection
    course_options = {f"{course.code} - {course.title}": course for course in st.session_state.courses}
    
    selected_course_name = st.selectbox(
        "Select Course:",
        options=list(course_options.keys()),
        key="selected_course",
        index=None
    )
    
    if selected_course_name:
        selected_course = course_options[selected_course_name]
        
        # Display course info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Course Code", selected_course.code)
        with col2:
            st.metric("Type", selected_course.type)
        with col3:
            st.metric("Status", selected_course.status)
        
        # Auto-fetch units for selected course
        if st.session_state.get('last_selected_course_id') != selected_course.id:
            st.session_state.last_selected_course_id = selected_course.id
            with st.spinner("Loading units..."):
                units, error = asyncio.run(fetch_units(selected_course.id))
                
                if error:
                    st.error(f"Units are being sus rn 😒 {error}")
                elif units:
                    st.session_state.current_units = units
                    st.session_state.current_course_id = selected_course.id
                else:
                    st.info("No units found bestie! This course is empty fr 💀")
        
        # Display units and materials
        if 'current_units' in st.session_state and st.session_state.current_units and st.session_state.get('current_course_id') == selected_course.id:
            st.markdown("---")
            st.subheader("📑 Course Materials")
            
            # Initialize expanded_units in session state if not present
            if 'expanded_units' not in st.session_state:
                st.session_state.expanded_units = {}
            
            for unit in st.session_state.current_units:
                # Auto-load topics if unit expander is marked as needing load
                if unit.id not in st.session_state.expanded_units:
                    st.session_state.expanded_units[unit.id] = False
                
                # Check if topics need to be loaded
                if st.session_state.expanded_units[unit.id] and f"topics_{unit.id}" not in st.session_state:
                    with st.spinner(f"Loading topics for {unit.title}..."):
                        topics, error = asyncio.run(fetch_topics(unit.id))
                        if error:
                            st.error(f"Topics are mid rn fr 😤 {error}")
                        else:
                            st.session_state[f"topics_{unit.id}"] = topics
                
                # Display unit with expander, keep open if topics are loaded
                is_open = f"topics_{unit.id}" in st.session_state
                with st.expander(f"📘 {unit.title}", expanded=is_open):
                    # Mark unit as expanded for auto-loading
                    st.session_state.expanded_units[unit.id] = True
                    
                    # Auto-load topics if not already loaded
                    if f"topics_{unit.id}" not in st.session_state:
                        with st.spinner(f"Loading topics for {unit.title}..."):
                            topics, error = asyncio.run(fetch_topics(unit.id))
                            
                            if error:
                                st.error(f"Topics are mid rn fr 😤 {error}")
                            else:
                                st.session_state[f"topics_{unit.id}"] = topics
                                st.rerun()
                    
                    # Display topics if loaded
                    if f"topics_{unit.id}" in st.session_state:
                        topics = st.session_state[f"topics_{unit.id}"]
                        
                        for topic in topics:
                            st.markdown(f"**📝 {topic.title}**")
                            
                            # Material type selector
                            material_types = {
                                "Lecture Notes": "1",
                                "Slides": "2",
                                "Notes": "3",
                                "Lab Materials": "4",
                                "Additional Resources": "5"
                            }
                            
                            cols = st.columns(len(material_types))
                            for idx, (mat_name, mat_id) in enumerate(material_types.items()):
                                with cols[idx]:
                                    if st.button(mat_name, key=f"mat_{topic.id}_{mat_id}", use_container_width=True):
                                        with st.spinner(f"Fetching {mat_name}..."):
                                            materials, error = asyncio.run(fetch_materials(topic, mat_id))
                                            
                                            if error:
                                                st.error(f"Nah that ain't it chief 💀 {error}")
                                            elif not materials:
                                                st.info(f"No {mat_name} available oof 😭")
                                            else:
                                                st.session_state[f"materials_{topic.id}_{mat_id}"] = materials
                                                st.rerun()
                            
                            # Display materials if loaded
                            for mat_name, mat_id in material_types.items():
                                mat_key = f"materials_{topic.id}_{mat_id}"
                                if mat_key in st.session_state:
                                    materials = st.session_state[mat_key]
                                    if materials:
                                        st.markdown(f"**{mat_name}:**")
                                        for material in materials:
                                            if material.is_pdf:
                                                st.markdown(f"📄 [{material.title}]({material.url})")
                                            else:
                                                st.markdown(f"🔗 [{material.title}]({material.url})")
                            
                            st.markdown("---")

else:
    st.info("👆 Click 'Fetch Courses' to load ur courses no cap 💯")

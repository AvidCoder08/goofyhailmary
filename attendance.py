import streamlit as st
import asyncio
import pandas as pd
from pesuacademy import PESUAcademy
from session_utils import restore_session_from_cookie
from attendance_calculator import calculate_bunkable_classes, get_bunk_calculator_data

restore_session_from_cookie()

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()

st.title("📋 Attendance")

# Get profile to determine current semester
profile = st.session_state.profile
if isinstance(profile, dict):
    personal = profile.get('personal', {})
    sem_str = personal.get('semester', '1') if isinstance(personal, dict) else personal.get('semester', '1')
else:
    sem_str = profile.personal.semester

# Parse semester - handle both "Sem-2" and "2" formats
try:
    if isinstance(sem_str, str):
        current_sem = int(sem_str.split('-')[-1]) if '-' in sem_str else int(sem_str)
    else:
        current_sem = int(sem_str)
except:
    current_sem = 1

# Semester selector
st.subheader("Select Semester")
sem_options = list(range(1, current_sem + 1))
selected_sem = st.selectbox(
    "Choose a semester to view attendance:",
    options=sem_options,
    index=len(sem_options) - 1 if sem_options else 0,
    key="attendance_semester_selector",
)

async def fetch_attendance(semester):
    """Fetch attendance from PESU Academy API"""
    try:
        # Check if credentials are available
        if not st.session_state.get('pesu_username') or not st.session_state.get('pesu_password'):
            return None, "Credentials not found. Please login again."
        
        # Create a new authenticated session
        pesu = await PESUAcademy.login(
            st.session_state.pesu_username,
            st.session_state.pesu_password
        )
        
        if not pesu:
            return None, "Login failed. Please try again."
        
        try:
            attendance_data = await pesu.get_attendance(semester)
        except Exception as e:
            await pesu.close()
            return None, f"Error fetching attendance: {str(e)}"
        
        await pesu.close()
        
        if not attendance_data or semester not in attendance_data:
            return None, f"No attendance data found for semester {semester}."
        
        return attendance_data[semester], None
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return None, f"Error fetching attendance: {error_msg}"

# Auto-load attendance on first visit or semester change
if 'attendance_initialized' not in st.session_state:
    st.session_state.attendance_initialized = True
    st.session_state.last_attendance_sem = selected_sem
    with st.spinner(f"Loading semester {selected_sem} attendance..."):
        courses, error = asyncio.run(fetch_attendance(selected_sem))
        if error:
            st.error(f"Yikes ngl 😬 {error}")
        else:
            st.session_state.attendance_data = courses
            st.success("Attendance loaded! Check it out fam 📊")
elif st.session_state.get('last_attendance_sem') != selected_sem:
    st.session_state.last_attendance_sem = selected_sem
    with st.spinner(f"Loading semester {selected_sem} attendance..."):
        courses, error = asyncio.run(fetch_attendance(selected_sem))
        if error:
            st.error(f"Yikes ngl 😬 {error}")
        else:
            st.session_state.attendance_data = courses
            st.success("Attendance loaded! Check it out fam 📊")

# Manual refresh button
if st.button("🔄 Refresh Attendance", use_container_width=True):
    with st.spinner(f"Refreshing semester {selected_sem} attendance..."):
        courses, error = asyncio.run(fetch_attendance(selected_sem))
        if error:
            st.error(f"Yikes ngl 😬 {error}")
        else:
            st.session_state.attendance_data = courses
            st.success("Attendance refreshed! 📊")

# Display attendance if available
if 'attendance_data' in st.session_state and st.session_state.attendance_data:
    courses = st.session_state.attendance_data
    
    # Create attendance data
    attendance_list = []
    total_classes_attended = 0
    total_classes = 0
    
    for course in courses:
        if course.attendance:
            attended = course.attendance.attended if course.attendance.attended is not None else 0
            total = course.attendance.total if course.attendance.total is not None else 0
            percentage = course.attendance.percentage if course.attendance.percentage is not None else 0
            
            total_classes_attended += attended
            total_classes += total
            
            # Color code the attendance percentage (75% is the cutoff)
            if percentage >= 75:
                status = "✅ Good"
            elif percentage >= 70:
                status = "⚠️ Danger"
            else:
                status = "🚨 Critical"
            
            attendance_list.append({
                "Course Code": course.code,
                "Course Title": course.title,
                "Attended": attended,
                "Total Classes": total,
                "Attendance %": f"{percentage:.1f}%",
                "Status": status
            })
        else:
            # No attendance data for this course
            attendance_list.append({
                "Course Code": course.code,
                "Course Title": course.title,
                "Attended": "N/A",
                "Total Classes": "N/A",
                "Attendance %": "N/A",
                "Status": "No data"
            })
    
    # Display overall summary
    st.markdown("---")
    st.subheader("📊 Overall Summary")
    
    if total_classes > 0:
        overall_percentage = (total_classes_attended / total_classes) * 100
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Classes Attended", total_classes_attended)
        with col2:
            st.metric("Total Classes", total_classes)
        with col3:
            st.metric("Overall Attendance %", f"{overall_percentage:.1f}%")
        with col4:
            if overall_percentage >= 85:
                st.metric("Status", "✅ Good")
            elif overall_percentage >= 75:
                st.metric("Status", "✅ Safe")
            elif overall_percentage >= 70:
                st.error("⚠️ Danger")
            else:
                st.error("🚨 Critical")
    else:
        st.info("No attendance data fr fr 💀")
    
    # Display detailed attendance table
    st.markdown("---")
    st.subheader("📑 Course-wise Attendance")
    
    attendance_df = pd.DataFrame(attendance_list)
    st.dataframe(
        attendance_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Attendance %": st.column_config.TextColumn(
                "Attendance %",
                width="medium"
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                width="medium"
            )
        }
    )
    
    # Get bunk calculator data for all courses
    bunk_data = get_bunk_calculator_data()
    working_days = bunk_data.get('working_days_remaining', 0)
    semester_end = bunk_data.get('semester_end_date')
    bunk_error = bunk_data.get('error')
    
    # Display course cards with attendance bars
    st.markdown("---")
    st.subheader("📈 Attendance Details")
    
    # Show bunk calculator status
    if bunk_error:
        st.warning(f"⚠️ Bunk calculator unavailable: {bunk_error}")
    elif semester_end and working_days > 0:
        st.info(f"📅 **{working_days}** working days left until {semester_end.strftime('%B %d, %Y')}")
    
    for course in courses:
        if course.attendance and course.attendance.total and course.attendance.total > 0:
            attended = course.attendance.attended if course.attendance.attended is not None else 0
            total = course.attendance.total if course.attendance.total is not None else 0
            percentage = course.attendance.percentage if course.attendance.percentage is not None else 0
            
            with st.expander(f"**{course.code}** - {course.title}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.progress(
                        min(percentage / 100, 1.0),
                        text=f"{percentage:.1f}% ({attended}/{total} classes)"
                    )
                
                with col2:
                    if percentage >= 85:
                        st.success("✅")
                    elif percentage >= 75:
                        st.info("✅")
                    elif percentage >= 70:
                        st.error("⚠️")
                    else:
                        st.error("🚨")
                
                # Additional details
                st.metric(f"Classes Attended", f"{attended} out of {total}")
                
                # Bunk calculator section
                if not bunk_error and working_days > 0:
                    st.markdown("---")
                    st.markdown("**🧮 Bunk Calculator**")
                    
                    # Calculate bunkable classes
                    bunk_calc = calculate_bunkable_classes(
                        attended=attended,
                        total=total,
                        working_days_remaining=working_days,
                        classes_per_week=5,  # Assuming 5 classes per week average
                        min_attendance=75.0
                    )
                    
                    # Display bunk calculator results in columns
                    bcol1, bcol2, bcol3 = st.columns(3)
                    
                    with bcol1:
                        st.metric(
                            "Classes Remaining",
                            f"~{bunk_calc['estimated_remaining']}",
                            help="Estimated classes left until semester end"
                        )
                    
                    with bcol2:
                        st.metric(
                            "Projected Total",
                            bunk_calc['projected_total'],
                            help="Total classes by semester end"
                        )
                    
                    with bcol3:
                        st.metric(
                            "Projected %",
                            f"{bunk_calc['projected_attendance']:.1f}%",
                            help="If you attend all remaining classes"
                        )
                    
                    # Bunk message
                    if bunk_calc['can_bunk'] and bunk_calc['bunkable_classes'] > 0:
                        st.success(f"🎉 **YO:** You can bunk **{bunk_calc['bunkable_classes']}** classes and still maintain 75% attendance! Living your best life fr 😎")
                    elif bunk_calc['classes_needed'] > 0:
                        st.warning(f"⚠️ **HEADS UP:** You need to attend **{bunk_calc['classes_needed']}** more classes to hit 75% by semester end!")
                    elif percentage >= 75:
                        st.info("✅ You're at 75%+ but need to attend all remaining classes to stay safe!")
                    else:
                        st.error(f"🚨 **CRITICAL:** Even attending all remaining classes, you'll only reach **{bunk_calc['projected_attendance']:.1f}%**. You might be cooked 💀")
                
                # Calculate classes needed to reach 75%
                classes_needed_for_cutoff = int((total * 0.75) - attended)
                if percentage < 75:
                    st.markdown("---")
                    if classes_needed_for_cutoff > 0:
                        if percentage >= 70:
                            st.error(f"🚨 **BRAH:** U gotta show up to like **{classes_needed_for_cutoff}** more classes or ur cooked 💀")
                        else:
                            st.error(f"🚨 **RIP:** Bro u need **{classes_needed_for_cutoff}** more to survive ngl 💀")
                    else:
                        st.error("🚨 **SHEESH:** Ur attendance is giving FAILED vibes 🚫")
        else:
            with st.expander(f"**{course.code}** - {course.title}"):
                st.info("No data yet bestie! Gotta attend sum classes first 🏫")

else:
    st.info(f"👆 Click that button to see ur attendance fr fr 📈")

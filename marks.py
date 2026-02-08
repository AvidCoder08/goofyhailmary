import streamlit as st
import asyncio
import pandas as pd
from pesuacademy import PESUAcademy
from session_utils import restore_session_from_cookie
from gpa_calculator import (
    marks_to_grade_point,
    grade_point_to_letter,
    calculate_sgpa,
    predict_sgpa,
    GRADE_LETTERS
)

restore_session_from_cookie()

# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("⚠️ Yo, gotta log in first no cap 🔐")
    st.page_link("login.py", label="Go to Login", icon="🔐")
    st.stop()
st.title("📊 Grades & Results")

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
    "Choose a semester to view results:",
    options=sem_options,
    index=len(sem_options) - 2 if sem_options else 0,
    key="semester_selector",
)

async def fetch_results(semester):
    """Fetch results from PESU Academy API"""
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
            results = await pesu.get_results(semester)
        except AttributeError as ae:
            await pesu.close()
            return None, f"Results page structure not found. This might mean:\n- No results available for semester {semester} yet\n- Results are still being processed\n- Please try again later or contact support"
        except IndexError as ie:
            await pesu.close()
            return None, f"Results not available yet for semester {semester}. This usually means:\n- Results haven't been published as **Final** yet (check PESU Academy)\n- Results are still provisional/in-progress\n- The semester doesn't have published results yet"
        except Exception as parse_error:
            await pesu.close()
            import traceback
            st.error("**Debug Info:**")
            st.code(traceback.format_exc())
            return None, f"Error parsing results: {str(parse_error)}"
        
        await pesu.close()
        
        if not results:
            return None, "No results found for this semester."
        
        return results, None
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return None, f"Error fetching results: {error_msg}"

# Auto-load results on first visit or semester change
if 'marks_initialized' not in st.session_state:
    st.session_state.marks_initialized = True
    st.session_state.last_marks_sem = selected_sem
    with st.spinner(f"Loading semester {selected_sem} results..."):
        results, error = asyncio.run(fetch_results(selected_sem))
        if error:
            st.error(f"Couldn't get ur grades ngl 😅 {error}")
            st.warning("Tips:\n- Make sure results are published as **Final** (not just provisional)\n- Try a different semester\n- Results might still be processing")
        else:
            st.session_state.results = results
            st.success("Results loaded! Let's see how u did 👀")
elif st.session_state.get('last_marks_sem') != selected_sem:
    st.session_state.last_marks_sem = selected_sem
    with st.spinner(f"Loading semester {selected_sem} results..."):
        results, error = asyncio.run(fetch_results(selected_sem))
        if error:
            st.error(f"Couldn't get ur grades ngl 😅 {error}")
            st.warning("Tips:\n- Make sure results are published as **Final** (not just provisional)\n- Try a different semester\n- Results might still be processing")
        else:
            st.session_state.results = results
            st.success("Results loaded! Let's see how u did 👀")

# Manual refresh button
if st.button("🔄 Refresh Results", use_container_width=True):
    with st.spinner(f"Refreshing semester {selected_sem} results..."):
        results, error = asyncio.run(fetch_results(selected_sem))
        if error:
            st.error(f"Couldn't get ur grades ngl 😅 {error}")
            st.warning("Tips:\n- Make sure results are published as **Final** (not just provisional)\n- Try a different semester\n- Results might still be processing")
        else:
            st.session_state.results = results
            st.success("Results refreshed! 👀")

st.caption("Note: The library currently supports final published results. If you see provisional results on PESU Academy, they may not be available through this API yet.")

# Tab interface for Results vs Predictor
results_tab, predictor_tab = st.tabs(["📈 Results", "🎯 SGPA Predictor"])

with results_tab:
    # Display results if available
    if 'results' in st.session_state and st.session_state.results:
        results = st.session_state.results
        
        # Prepare course data for SGPA calculation
        courses_data = []
        for course in results.courses:
            # Calculate total marks from assessments
            total_marks = 0
            total_possible = 0
            assessment_details = {}
            
            for assessment in course.assessments:
                marks = float(assessment.marks) if isinstance(assessment.marks, (int, float, str)) else 0
                total = float(assessment.total) if isinstance(assessment.total, (int, float, str)) else 0
                total_marks += marks
                total_possible += total
                
                # Extract assessment type
                assessment_name = assessment.name.lower()
                if 'assignment' in assessment_name or 'assgn' in assessment_name:
                    assessment_details['assignments'] = marks
                elif 'isa 1' in assessment_name or 'isa-1' in assessment_name:
                    assessment_details['isa_1'] = marks
                elif 'isa 2' in assessment_name or 'isa-2' in assessment_name:
                    assessment_details['isa_2'] = marks
                elif 'esa' in assessment_name:
                    assessment_details['esa'] = marks
                elif 'lab' in assessment_name:
                    assessment_details['lab'] = marks
            
            # Get credits (handle both string and numeric formats)
            try:
                if isinstance(course.credits.earned, str):
                    credits = float(course.credits.earned.split('/')[0])
                else:
                    credits = float(course.credits.earned)
            except:
                credits = 4  # Default to 4 credits
            
            percentage = (total_marks / total_possible * 100) if total_possible > 0 else 0
            grade_point = marks_to_grade_point(percentage)
            grade_letter = grade_point_to_letter(grade_point) if grade_point else "N/A"
            
            courses_data.append({
                "code": course.code,
                "title": course.title,
                "credits": credits,
                "marks": percentage,
                "grade_point": grade_point,
                "grade_letter": grade_letter,
                "total_marks": total_marks,
                "total_possible": total_possible,
                "assessments": course.assessments,
                "assessment_details": assessment_details
            })
        
        # Calculate SGPA
        sgpa = calculate_sgpa(courses_data)
        
        # Display SGPA prominently
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 SGPA (Calculated)", f"{sgpa:.2f}")
        with col2:
            total_credits = sum([c['credits'] for c in courses_data])
            st.metric("📚 Total Credits", int(total_credits))
        with col3:
            st.metric("📝 Courses", len(courses_data))
        
        # Display courses table with proper grading
        st.markdown("---")
        st.subheader(f"Semester {selected_sem} Courses")
        
        courses_display = []
        for course in courses_data:
            courses_display.append({
                "Course Code": course['code'],
                "Course Title": course['title'],
                "Credits": int(course['credits']),
                "Marks": f"{course['marks']:.1f}%",
                "Grade": course['grade_letter'],
                "Grade Point": course['grade_point'] if course['grade_point'] else "N/A"
            })
        
        courses_df = pd.DataFrame(courses_display)
        st.dataframe(
            courses_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Display detailed assessments
        st.markdown("---")
        st.subheader("Assessment Details")
        
        if courses_data:
            tabs = st.tabs([f"{course['code']}" for course in courses_data])
            
            for tab, course in zip(tabs, courses_data):
                with tab:
                    st.markdown(f"**{course['title']}** | Credits: {int(course['credits'])}")
                    
                    assessment_data = []
                    for assessment in course['assessments']:
                        marks = float(assessment.marks) if isinstance(assessment.marks, (int, float, str)) else 0
                        total = float(assessment.total) if isinstance(assessment.total, (int, float, str)) else 0
                        percentage = f"{(marks/total*100):.1f}%" if total > 0 else "N/A"
                        assessment_data.append({
                            "Assessment": assessment.name,
                            "Marks Obtained": f"{marks:.1f}m",
                            "Total Marks": f"{total:.1f}m",
                            "Percentage": percentage
                        })
                    
                    assessment_df = pd.DataFrame(assessment_data)
                    st.dataframe(
                        assessment_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.caption(f"**Course Percentage:** {course['marks']:.1f}% | **Grade:** {course['grade_letter']} ({course['grade_point']})")
        
        # Interactive SGPA Predictor for current semester
        st.markdown("---")
        st.subheader("🎯 What-If SGPA Predictor")
        st.caption("Adjust marks for courses below to see how it affects your SGPA")
        
        with st.expander("📊 Try different scores", expanded=False):
            st.info("Adjust marks for any course to see how it affects your SGPA")
            
            # Create editable copies of courses for prediction
            predicted_courses = []
            pred_cols = st.columns(2)
            
            for idx, course in enumerate(courses_data):
                col = pred_cols[idx % 2]
                with col:
                    st.write(f"**{course['code']}** ({int(course['credits'])} credits)")
                    
                    # Allow user to adjust marks
                    current_marks = course['marks']
                    new_marks = st.slider(
                        f"Adjust marks for {course['code']}",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(current_marks),
                        step=0.1,
                        label_visibility="collapsed",
                        key=f"pred_{course['code']}"
                    )
                    
                    new_gp = marks_to_grade_point(new_marks)
                    new_grade = grade_point_to_letter(new_gp) if new_gp else "N/A"
                    
                    st.metric(
                        f"New Grade",
                        new_grade,
                        delta=f"{new_marks - current_marks:+.1f}%"
                    )
                    
                    predicted_courses.append({
                        'credits': course['credits'],
                        'marks': new_marks,
                        'grade_point': new_gp
                    })
            
            # Calculate predicted SGPA
            predicted_sgpa = calculate_sgpa(predicted_courses)
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current SGPA", f"{sgpa:.2f}")
            with col2:
                st.metric("Predicted SGPA", f"{predicted_sgpa:.2f}")
            with col3:
                diff = predicted_sgpa - sgpa
                st.metric(
                    "Change",
                    f"{abs(diff):.2f}",
                    delta=f"{diff:+.2f}",
                    delta_color="normal" if diff >= 0 else "inverse"
                )
    else:
        st.info("👆 Click 'Fetch Results' or select a different semester to view ur grades 📄")

with predictor_tab:
    st.subheader("🎯 SGPA Predictor")
    st.caption("Predict what your SGPA could be with different scores")
    
    st.info("Enter your course information to calculate what SGPA you could achieve")
    
    # Number of courses
    num_courses = st.number_input("How many courses?", min_value=1, max_value=10, value=5)
    
    st.markdown("---")
    st.write("**Enter your course details:**")
    
    predictor_courses = []
    cols = st.columns(2)
    
    for i in range(num_courses):
        col = cols[i % 2]
        with col:
            st.markdown(f"**Course {i+1}**")
            
            course_code = st.text_input(
                "Course Code",
                placeholder="UE22CS202",
                key=f"pred_code_{i}",
                label_visibility="collapsed"
            )
            
            credits = st.number_input(
                "Credits",
                min_value=1,
                max_value=5,
                value=4,
                key=f"pred_credits_{i}",
                label_visibility="collapsed"
            )
            
            marks = st.slider(
                "Expected Marks (%)",
                min_value=0.0,
                max_value=100.0,
                value=75.0,
                step=0.5,
                key=f"pred_marks_{i}",
                label_visibility="collapsed"
            )
            
            gp = marks_to_grade_point(marks)
            grade = grade_point_to_letter(gp) if gp else "N/A"
            
            st.metric(f"Grade", f"{grade} ({gp})" if gp else "Invalid")
            
            if course_code:  # Only add if course code is provided
                predictor_courses.append({
                    'code': course_code,
                    'credits': credits,
                    'marks': marks,
                    'grade_point': gp
                })
            
            st.divider()
    
    # Calculate and display predicted SGPA
    if predictor_courses:
        st.markdown("---")
        st.subheader("📊 Your Predicted SGPA")
        
        predicted_sgpa = calculate_sgpa(predictor_courses)
        total_credits = sum([c['credits'] for c in predictor_courses])
        avg_marks = sum([c['marks'] for c in predictor_courses]) / len(predictor_courses)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Predicted SGPA", f"{predicted_sgpa:.2f}")
        with col2:
            st.metric("Total Credits", int(total_credits))
        with col3:
            st.metric("Avg Marks", f"{avg_marks:.1f}%")
        with col4:
            avg_gp = marks_to_grade_point(avg_marks)
            avg_grade = grade_point_to_letter(avg_gp) if avg_gp else "N/A"
            st.metric("Avg Grade", f"{avg_grade}")
        
        # Summary table
        st.markdown("---")
        st.write("**Course Summary:**")
        summary_data = []
        for course in predictor_courses:
            summary_data.append({
                "Code": course['code'],
                "Credits": course['credits'],
                "Marks": f"{course['marks']:.1f}%",
                "Grade": grade_point_to_letter(course['grade_point'])
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.warning("👆 Enter at least one course code above to calculate SGPA")



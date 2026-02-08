"""GPA and CGPA calculation utilities with grading system."""

# Grading scale: marks -> grade_point
GRADE_SCALE = {
    90: 10,    # S
    80: 9,     # A
    70: 8,     # B
    60: 7,     # C
    50: 6,     # D
    0: 5       # E
}

GRADE_LETTERS = {
    10: "S",
    9: "A",
    8: "B",
    7: "C",
    6: "D",
    5: "E"
}


def marks_to_grade_point(marks):
    """Convert marks percentage to grade point (0-10).
    
    Args:
        marks: Marks percentage (0-100)
    
    Returns:
        Grade point (0-10)
    """
    try:
        marks = float(marks)
    except (ValueError, TypeError):
        return None
    
    # Find the appropriate grade point
    for threshold in sorted(GRADE_SCALE.keys(), reverse=True):
        if marks >= threshold:
            return GRADE_SCALE[threshold]
    
    return 0


def grade_point_to_letter(gp):
    """Convert grade point to letter grade.
    
    Args:
        gp: Grade point (0-10)
    
    Returns:
        Letter grade (S, A, B, C, D, E, F)
    """
    gp = int(round(float(gp))) if gp else 0
    return GRADE_LETTERS.get(gp, "F")


def calculate_course_marks(assessment_marks):
    """Calculate final course marks from assessments.
    
    For 4-credit courses:
    - Assignments: 10m
    - ISA 1: 20m (out of 40)
    - ISA 2: 20m (out of 40)
    - ESA: 50m (out of 100)
    Total: 100m
    
    For 5-credit courses (with lab):
    - Same as above + Lab: 20m
    - Total: 120m, scaled to 100m
    
    Args:
        assessment_marks: Dict with keys like 'assignments', 'isa_1', 'isa_2', 'esa', 'lab' (optional)
    
    Returns:
        Total marks (out of 100)
    """
    total = 0
    has_lab = 'lab' in assessment_marks and assessment_marks['lab'] is not None
    
    # Extract and add marks
    if 'assignments' in assessment_marks and assessment_marks['assignments']:
        total += float(assessment_marks['assignments'])
    
    if 'isa_1' in assessment_marks and assessment_marks['isa_1']:
        total += float(assessment_marks['isa_1'])
    
    if 'isa_2' in assessment_marks and assessment_marks['isa_2']:
        total += float(assessment_marks['isa_2'])
    
    if 'esa' in assessment_marks and assessment_marks['esa']:
        total += float(assessment_marks['esa'])
    
    if has_lab:
        total += float(assessment_marks['lab'])
        # Scale from 120 to 100
        total = (total / 120) * 100
    
    return round(total, 2)


def calculate_sgpa(courses_data):
    """Calculate SGPA for a semester.
    
    SGPA = Σ(credits_course × grade_course) / Σ(credits_course)
    
    Args:
        courses_data: List of dicts with 'credits' and 'marks' or 'grade_point' keys
    
    Returns:
        SGPA (float)
    """
    weighted_sum = 0
    total_credits = 0
    
    for course in courses_data:
        credits = float(course.get('credits', 0))
        
        # Get grade point (either directly or from marks)
        if 'grade_point' in course:
            gp = course['grade_point']
        elif 'marks' in course:
            gp = marks_to_grade_point(course['marks'])
        else:
            continue
        
        if gp is None:
            continue
        
        weighted_sum += credits * gp
        total_credits += credits
    
    if total_credits == 0:
        return 0
    
    sgpa = weighted_sum / total_credits
    return round(sgpa, 2)


def calculate_cgpa(semesters_data):
    """Calculate CGPA across all semesters.
    
    CGPA = Σ(credits_sem × sgpa_sem) / Σ(credits_all_sems)
    
    Args:
        semesters_data: List of dicts with 'credits' and 'sgpa' keys
    
    Returns:
        CGPA (float)
    """
    weighted_sum = 0
    total_credits = 0
    
    for semester in semesters_data:
        credits = float(semester.get('credits', 0))
        sgpa = float(semester.get('sgpa', 0))
        
        weighted_sum += credits * sgpa
        total_credits += credits
    
    if total_credits == 0:
        return 0
    
    cgpa = weighted_sum / total_credits
    return round(cgpa, 2)


def predict_sgpa(current_courses, future_marks=None):
    """Predict SGPA with current results and optional future course marks.
    
    Args:
        current_courses: List of completed course data
        future_marks: Optional dict of future course marks
    
    Returns:
        Tuple of (current_sgpa, predicted_sgpa)
    """
    current_sgpa = calculate_sgpa(current_courses)
    
    if not future_marks:
        return current_sgpa, current_sgpa
    
    # Combine current and future courses
    all_courses = current_courses + future_marks
    predicted_sgpa = calculate_sgpa(all_courses)
    
    return current_sgpa, predicted_sgpa

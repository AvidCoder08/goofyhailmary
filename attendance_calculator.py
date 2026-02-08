from datetime import date, timedelta
from calendar_utils import get_calendar_events, get_semester_settings


def get_working_days_remaining(semester_end_date, exclude_holidays=True):
    """
    Calculate the number of working days (weekdays) remaining until semester end.
    Optionally excludes holidays from the calendar.

    Args:
        semester_end_date: date object representing end of semester
        exclude_holidays: bool, whether to exclude calendar holidays

    Returns:
        int: Number of working days remaining
    """
    if not semester_end_date:
        return 0

    today = date.today()
    if today >= semester_end_date:
        return 0

    # Get holidays from calendar
    holiday_dates = set()
    if exclude_holidays:
        try:
            events = get_calendar_events()
            for event in events:
                if event.get("type") == "holiday":
                    start = event.get("start_date")
                    end = event.get("end_date")

                    # Parse dates
                    try:
                        start_date = date.fromisoformat(start) if isinstance(start, str) else start
                        end_date = date.fromisoformat(end) if isinstance(end, str) and end else start_date
                    except:
                        continue

                    # Add all dates in the holiday range
                    if start_date and end_date:
                        current = start_date
                        while current <= end_date:
                            holiday_dates.add(current)
                            current += timedelta(days=1)
                    elif start_date:
                        holiday_dates.add(start_date)
        except:
            pass  # If we can't fetch holidays, proceed without them

    # Count working days (Monday-Friday) excluding holidays
    working_days = 0
    current = today

    while current <= semester_end_date:
        # Check if it's a weekday (0 = Monday, 6 = Sunday)
        if current.weekday() < 5:  # Monday to Friday
            # Check if it's not a holiday
            if current not in holiday_dates:
                working_days += 1
        current += timedelta(days=1)

    return working_days


def calculate_bunkable_classes(attended, total, working_days_remaining, classes_per_week=5, min_attendance=75.0):
    """
    Calculate how many classes a student can bunk while maintaining minimum attendance.

    Args:
        attended: int, number of classes attended so far
        total: int, total number of classes so far
        working_days_remaining: int, number of working days until semester end
        classes_per_week: int, average number of classes per week for this course
        min_attendance: float, minimum required attendance percentage (default 75%)

    Returns:
        dict with:
            - bunkable_classes: int, number of classes that can be bunked
            - projected_total: int, projected total classes by semester end
            - projected_attendance: float, projected attendance % if all remaining classes attended
            - can_bunk: bool, whether student can afford to bunk any classes
            - classes_needed: int, classes needed to attend to maintain min_attendance (if negative means you can bunk)
    """
    if total == 0:
        return {
            "bunkable_classes": 0,
            "projected_total": 0,
            "projected_attendance": 0,
            "can_bunk": False,
            "classes_needed": 0,
            "message": "No attendance data yet"
        }

    # Estimate remaining classes based on working days
    # Assume classes_per_week classes spread across 5 working days
    weeks_remaining = working_days_remaining / 5.0
    estimated_remaining_classes = int(weeks_remaining * classes_per_week)

    # Projected total by semester end
    projected_total = total + estimated_remaining_classes

    # Calculate minimum classes needed to attend to maintain min_attendance%
    min_classes_needed = (projected_total * min_attendance) / 100.0

    # How many more classes do we need to attend?
    classes_needed_to_attend = int(min_classes_needed - attended)

    # How many can we bunk?
    bunkable = max(0, estimated_remaining_classes - classes_needed_to_attend)

    # Projected attendance if all remaining classes are attended
    projected_attendance = ((attended + estimated_remaining_classes) / projected_total) * 100.0 if projected_total > 0 else 0

    # Current attendance percentage
    current_attendance = (attended / total) * 100.0

    can_bunk = bunkable > 0 and current_attendance >= min_attendance

    return {
        "bunkable_classes": bunkable,
        "projected_total": projected_total,
        "estimated_remaining": estimated_remaining_classes,
        "projected_attendance": projected_attendance,
        "can_bunk": can_bunk,
        "classes_needed": classes_needed_to_attend,
        "current_attendance": current_attendance
    }


def get_bunk_calculator_data():
    """
    Get all necessary data for the bunk calculator.

    Returns:
        dict with semester_end_date and working_days_remaining
    """
    try:
        settings = get_semester_settings()
        semester_end = settings.get("semester_end_date")

        if not semester_end:
            return {
                "semester_end_date": None,
                "working_days_remaining": 0,
                "error": "Semester end date not set by superadmin"
            }

        try:
            semester_end_date = date.fromisoformat(semester_end)
        except:
            return {
                "semester_end_date": None,
                "working_days_remaining": 0,
                "error": "Invalid semester end date"
            }

        working_days = get_working_days_remaining(semester_end_date, exclude_holidays=True)

        return {
            "semester_end_date": semester_end_date,
            "working_days_remaining": working_days,
            "error": None
        }
    except Exception as e:
        return {
            "semester_end_date": None,
            "working_days_remaining": 0,
            "error": str(e)
        }

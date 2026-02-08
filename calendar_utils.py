import json
import requests
from datetime import date, datetime

try:
    from github_utils import _get_github_config
except ImportError:
    def _get_github_config():
        raise RuntimeError("GitHub configuration not available")

CALENDAR_FILE_PATH = "data/calendar_events.json"
SETTINGS_FILE_PATH = "data/semester_settings.json"


def get_semester_settings():
    """
    Fetch semester settings from GitHub JSON file.
    Returns a dict with settings like semester_end_date.
    """
    try:
        from github_utils import get_file_from_github
        
        file_content = get_file_from_github(SETTINGS_FILE_PATH)
        if file_content is None:
            # File doesn't exist yet, return default
            return {"semester_end_date": None}
        
        settings = json.loads(file_content.decode('utf-8'))
        return settings if isinstance(settings, dict) else {"semester_end_date": None}
    except Exception as e:
        return {"semester_end_date": None}


def save_semester_settings(settings):
    """
    Save semester settings to GitHub JSON file.
    """
    try:
        from github_utils import upload_to_github

        # Convert settings to JSON
        json_bytes = json.dumps(settings, indent=2).encode('utf-8')

        # Upload to GitHub
        upload_to_github(
            file_bytes=json_bytes,
            file_path=SETTINGS_FILE_PATH,
            commit_message="Update semester settings"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to save semester settings: {e}")


def get_calendar_events():
    """
    Fetch calendar events from GitHub JSON file.
    Returns a list of event dictionaries.
    """
    try:
        from github_utils import get_file_from_github
        
        file_content = get_file_from_github(CALENDAR_FILE_PATH)
        if file_content is None:
            # File doesn't exist yet, return empty list
            return []
        
        events = json.loads(file_content.decode('utf-8'))
        return events if isinstance(events, list) else []
    except Exception as e:
        # Return empty list instead of raising error for better resilience
        return []


def save_calendar_events(events):
    """
    Save calendar events to GitHub JSON file.
    """
    try:
        from github_utils import upload_to_github

        # Convert events to JSON
        json_bytes = json.dumps(events, indent=2).encode('utf-8')

        # Upload to GitHub
        upload_to_github(
            file_bytes=json_bytes,
            file_path=CALENDAR_FILE_PATH,
            commit_message="Update calendar events"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to save calendar events: {e}")


def add_calendar_event(title, event_type, start_date, end_date=None, description=""):
    """
    Add a new calendar event.
    """
    events = get_calendar_events()

    # Generate a simple ID
    event_id = f"evt_{len(events) + 1}_{int(datetime.now().timestamp())}"

    new_event = {
        "id": event_id,
        "title": title,
        "type": event_type,
        "start_date": start_date.isoformat() if isinstance(start_date, date) else start_date,
        "end_date": end_date.isoformat() if isinstance(end_date, date) and end_date else None,
        "description": description
    }

    events.append(new_event)
    save_calendar_events(events)
    return event_id


def update_calendar_event(event_id, title, event_type, start_date, end_date=None, description=""):
    """
    Update an existing calendar event.
    """
    events = get_calendar_events()

    for event in events:
        if event.get("id") == event_id:
            event["title"] = title
            event["type"] = event_type
            event["start_date"] = start_date.isoformat() if isinstance(start_date, date) else start_date
            event["end_date"] = end_date.isoformat() if isinstance(end_date, date) and end_date else None
            event["description"] = description
            break

    save_calendar_events(events)


def delete_calendar_event(event_id):
    """
    Delete a calendar event by ID.
    """
    events = get_calendar_events()
    events = [e for e in events if e.get("id") != event_id]
    save_calendar_events(events)

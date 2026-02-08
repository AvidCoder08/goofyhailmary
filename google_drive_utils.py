import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_shared_drive_id():
    # Try Streamlit secrets first
    try:
        shared_drive_id = st.secrets.get("google_drive_shared_drive_id")
        if shared_drive_id:
            return shared_drive_id.strip()
    except (AttributeError, KeyError):
        pass

    # Fallback to environment variables
    shared_drive_id = os.getenv("GOOGLE_DRIVE_SHARED_DRIVE_ID")
    if shared_drive_id:
        return shared_drive_id.strip()

    return ""


def _load_credentials():
    # Try Streamlit secrets first
    try:
        service_account_path = st.secrets.get("google_drive_service_account")
        if service_account_path and os.path.exists(service_account_path):
            return Credentials.from_service_account_file(service_account_path, scopes=SCOPES)
        
        service_account_json = st.secrets.get("google_drive_service_account_json")
        if service_account_json:
            return Credentials.from_service_account_info(
                json.loads(service_account_json), scopes=SCOPES
            )
    except (AttributeError, KeyError):
        pass

    # Fallback to environment variables
    service_account_path = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT")
    if service_account_path and os.path.exists(service_account_path):
        return Credentials.from_service_account_file(service_account_path, scopes=SCOPES)

    service_account_json = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        return Credentials.from_service_account_info(
            json.loads(service_account_json), scopes=SCOPES
        )

    raise RuntimeError(
        "Google Drive credentials not found. Add them to .streamlit/secrets.toml or set env vars."
    )


def get_drive_service():
    try:
        creds = _load_credentials()
    except Exception:
        raise RuntimeError(
            "Google Drive authentication failed. Check your credentials setup."
        )
    return build("drive", "v3", credentials=creds)


def create_folder_if_not_exists(service, folder_name, parent_id=None):
    """Create a folder in Google Drive if it doesn't exist, return folder ID."""
    try:
        shared_drive_id = _get_shared_drive_id()
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        list_kwargs = {
            "q": query,
            "spaces": "drive",
            "fields": "files(id, name)",
            "pageSize": 1,
        }
        if shared_drive_id:
            list_kwargs.update(
                {
                    "corpora": "drive",
                    "driveId": shared_drive_id,
                    "includeItemsFromAllDrives": True,
                    "supportsAllDrives": True,
                }
            )

        results = service.files().list(**list_kwargs).execute()
        files = results.get("files", [])
        
        if files:
            return files[0]["id"]
        
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        create_kwargs = {"body": file_metadata, "fields": "id"}
        if shared_drive_id:
            create_kwargs["supportsAllDrives"] = True

        folder = service.files().create(**create_kwargs).execute()
        return folder.get("id")
    except HttpError as error:
        raise RuntimeError(f"Google Drive error: {error}")


def upload_file_correct(service, file_bytes, filename, parent_folder_id):
    """Upload file bytes to Google Drive."""
    try:
        shared_drive_id = _get_shared_drive_id()
        file_metadata = {
            "name": filename,
            "parents": [parent_folder_id],
        }
        
        stream = BytesIO(file_bytes)
        media = MediaIoBaseUpload(stream, mimetype="application/octet-stream", resumable=False)
        
        create_kwargs = {
            "body": file_metadata,
            "media_body": media,
            "fields": "id, webViewLink",
        }
        if shared_drive_id:
            create_kwargs["supportsAllDrives"] = True

        file_obj = service.files().create(**create_kwargs).execute()
        
        return file_obj.get("id"), file_obj.get("webViewLink")
    except HttpError as error:
        raise RuntimeError(f"Upload failed: {error}")


def delete_file(service, file_id):
    """Delete a file from Google Drive."""
    try:
        shared_drive_id = _get_shared_drive_id()
        delete_kwargs = {"fileId": file_id}
        if shared_drive_id:
            delete_kwargs["supportsAllDrives"] = True
        service.files().delete(**delete_kwargs).execute()
    except HttpError as error:
        raise RuntimeError(f"Delete failed: {error}")


def list_files_in_folder(service, folder_id):
    """List all files in a folder."""
    try:
        shared_drive_id = _get_shared_drive_id()
        list_kwargs = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "spaces": "drive",
            "fields": "files(id, name, mimeType, createdTime)",
            "pageSize": 100,
        }
        if shared_drive_id:
            list_kwargs.update(
                {
                    "corpora": "drive",
                    "driveId": shared_drive_id,
                    "includeItemsFromAllDrives": True,
                    "supportsAllDrives": True,
                }
            )

        results = service.files().list(**list_kwargs).execute()
        return results.get("files", [])
    except HttpError as error:
        raise RuntimeError(f"List failed: {error}")

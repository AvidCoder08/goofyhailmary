import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import timedelta
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def _load_credentials():
    # Try Streamlit secrets first (for production/deployed apps)
    try:
        # First try JSON string in secrets (preferred for Streamlit Cloud)
        service_account_json = st.secrets.get("firebase_service_account_json")
        if service_account_json:
            return credentials.Certificate(json.loads(service_account_json))

        # Fallback to file path in secrets (for local .streamlit/secrets.toml)
        service_account_path = st.secrets.get("firebase_service_account")
        if service_account_path and os.path.exists(service_account_path):
            return credentials.Certificate(service_account_path)
    except (AttributeError, KeyError):
        pass

    # Fallback to environment variables
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            return credentials.Certificate(json.loads(service_account_json))
        except (json.JSONDecodeError, ValueError) as e:
            raise RuntimeError(f"Invalid Firebase JSON credentials: {e}")

    # File path from environment
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if service_account_path and os.path.exists(service_account_path):
        return credentials.Certificate(service_account_path)

    raise RuntimeError(
        "Firebase credentials not found. Set firebase_service_account_json in Streamlit secrets or FIREBASE_SERVICE_ACCOUNT_JSON env var"
    )


def _get_bucket_name():
    # Try Streamlit secrets first
    try:
        bucket = st.secrets.get("firebase_storage_bucket")
        if bucket:
            return bucket
    except (AttributeError, KeyError):
        pass

    # Fallback to environment variable
    return os.getenv("FIREBASE_STORAGE_BUCKET")


def get_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred = _load_credentials()
    bucket_name = _get_bucket_name()
    if bucket_name:
        return firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
    return firebase_admin.initialize_app(cred)


def get_firestore_client():
    app = get_firebase_app()
    return firestore.client(app)


def get_storage_bucket():
    app = get_firebase_app()
    bucket_name = _get_bucket_name()
    if not bucket_name:
        raise RuntimeError("Firebase storage bucket not configured. Set firebase_storage_bucket or FIREBASE_STORAGE_BUCKET.")
    return storage.bucket(app)


def generate_signed_url(storage_path, expires_minutes=60):
    bucket = get_storage_bucket()
    blob = bucket.blob(storage_path)
    return blob.generate_signed_url(expiration=timedelta(minutes=expires_minutes))


def upload_to_storage(file_bytes, storage_path, content_type="application/octet-stream"):
    """Upload file bytes to Firebase Storage and return public URL."""
    bucket = get_storage_bucket()
    blob = bucket.blob(storage_path)
    blob.upload_from_string(file_bytes, content_type=content_type)
    blob.make_public()
    return blob.public_url


def delete_from_storage(storage_path):
    """Delete a file from Firebase Storage."""
    bucket = get_storage_bucket()
    blob = bucket.blob(storage_path)
    if blob.exists():
        blob.delete()

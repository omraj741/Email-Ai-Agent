"""Gmail API authentication and message retrieval."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from config import CREDENTIALS_PATH, GMAIL_SCOPES, GMAIL_SEARCH_QUERY, MAX_EMAILS, TOKEN_PATH
from logger import setup_logger

logger = setup_logger(__name__)


class MissingCredentialsError(FileNotFoundError):
    """Raised when credentials.json is missing."""


def get_gmail_service(credentials_path: Path = CREDENTIALS_PATH, token_path: Path = TOKEN_PATH):
    """Authenticate using Gmail OAuth 2.0 and return a Gmail API service."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError("Gmail API dependencies are not installed. Run: pip install -r requirements.txt") from exc
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise MissingCredentialsError(
                    "ERROR: credentials.json was not found.\n\nPlease download your OAuth Desktop Client credentials "
                    "from Google Cloud Console and place credentials.json in the project root."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    logger.info("Gmail authentication successful")
    return build("gmail", "v1", credentials=creds)


def _execute_with_retry(request, retries: int = 3) -> dict[str, Any]:
    for attempt in range(retries):
        try:
            return request.execute()
        except Exception as exc:
            status = getattr(getattr(exc, "resp", None), "status", None)
            if status in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            raise
    return {}


def search_messages(service, query: str = GMAIL_SEARCH_QUERY, max_results: int = MAX_EMAILS) -> list[dict[str, Any]]:
    """Search Gmail messages with pagination up to max_results."""
    messages: list[dict[str, Any]] = []
    page_token = None
    while len(messages) < max_results:
        request = service.users().messages().list(userId="me", q=query, maxResults=min(100, max_results - len(messages)), pageToken=page_token)
        response = _execute_with_retry(request)
        messages.extend(response.get("messages", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    logger.info("Messages found: %s", len(messages))
    return messages


def get_message(service, message_id: str) -> dict[str, Any] | None:
    """Fetch a full Gmail message, returning None if the individual message fails."""
    try:
        return _execute_with_retry(service.users().messages().get(userId="me", id=message_id, format="full"))
    except Exception as exc:
        logger.error("Failed to fetch Gmail message %s: %s", message_id, exc)
        return None


def get_message_details(service, message_id: str) -> dict[str, Any] | None:
    """Compatibility wrapper around get_message."""
    return get_message(service, message_id)

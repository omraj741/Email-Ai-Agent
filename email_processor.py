"""Email extraction, cleanup, keyword classification, and priority rules."""
from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from typing import Any

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - production dependency listed in requirements
    BeautifulSoup = None
from html.parser import HTMLParser

from config import EMAIL_CATEGORIES, HIGH_PRIORITY_KEYWORDS, MAX_EMAIL_BODY_LENGTH, MEDIUM_PRIORITY_KEYWORDS


@dataclass(slots=True)
class ProcessedEmail:
    gmail_id: str
    thread_id: str | None
    message_id: str | None
    sender: str
    recipient: str
    subject: str
    email_date: str
    body: str
    html_body: str
    plain_text_body: str
    labels: list[str]
    categories: list[str]
    priority: str
    gmail_link: str | None
    body_truncated: bool = False


def decode_data(data: str | None) -> str:
    """Decode Gmail URL-safe base64 content into UTF-8 text."""
    if not data:
        return ""
    try:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode((data + padding).encode("utf-8")).decode("utf-8", errors="replace")
    except Exception:
        return ""


class _HTMLTextExtractor(HTMLParser):
    """Small fallback HTML-to-text parser used when BeautifulSoup is unavailable."""

    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = True
        elif tag in {"p", "br", "div", "h1", "h2", "h3", "li"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = False
        elif tag in {"p", "div", "h1", "h2", "h3", "li"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def clean_html(html: str) -> str:
    """Convert HTML email content to readable plain text."""
    if not html:
        return ""
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
    else:
        parser = _HTMLTextExtractor()
        parser.feed(html)
        text = parser.text()
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", text)).strip()


def get_headers(message: dict[str, Any]) -> dict[str, str]:
    """Extract Gmail payload headers into a case-insensitive dictionary."""
    headers = message.get("payload", {}).get("headers", []) or []
    return {h.get("name", "").lower(): h.get("value", "") for h in headers if h.get("name")}


def _walk_parts(payload: dict[str, Any]) -> list[dict[str, Any]]:
    parts = [payload]
    for part in payload.get("parts", []) or []:
        parts.extend(_walk_parts(part))
    return parts


def get_email_body(message: dict[str, Any]) -> tuple[str, str, str, bool]:
    """Return preferred body, HTML body, plain text body, and truncation flag."""
    payload = message.get("payload", {}) or {}
    plain_chunks: list[str] = []
    html_chunks: list[str] = []
    for part in _walk_parts(payload):
        mime = part.get("mimeType", "")
        text = decode_data((part.get("body") or {}).get("data"))
        if not text:
            continue
        if mime == "text/plain":
            plain_chunks.append(text)
        elif mime == "text/html":
            html_chunks.append(text)
    plain = "\n".join(plain_chunks).strip()
    html = "\n".join(html_chunks).strip()
    body = plain or clean_html(html)
    truncated = len(body) > MAX_EMAIL_BODY_LENGTH
    if truncated:
        body = body[:MAX_EMAIL_BODY_LENGTH] + "\n\n[TRUNCATED: email body exceeded configured maximum length.]"
    return body, html, plain, truncated


def _phrase_found(keyword: str, text: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(keyword).replace(r"\ ", r"\s+") + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def find_categories(subject: str = "", body: str = "", sender: str = "") -> list[str]:
    """Find all configured categories using safe case-insensitive phrase matching."""
    haystack = f"{subject}\n{body}\n{sender}"
    return [category for category, keywords in EMAIL_CATEGORIES.items() if any(_phrase_found(k, haystack) for k in keywords)]


def calculate_priority(subject: str = "", body: str = "", sender: str = "") -> str:
    """Calculate HIGH, MEDIUM, or LOW priority from configured keyword signals."""
    haystack = f"{subject}\n{body}\n{sender}"
    if any(_phrase_found(k, haystack) for k in HIGH_PRIORITY_KEYWORDS):
        return "HIGH"
    if any(_phrase_found(k, haystack) for k in MEDIUM_PRIORITY_KEYWORDS):
        return "MEDIUM"
    return "LOW"


def process_email(message: dict[str, Any]) -> ProcessedEmail:
    """Normalize a Gmail message resource into a ProcessedEmail."""
    headers = get_headers(message)
    body, html, plain, truncated = get_email_body(message)
    subject = headers.get("subject", "(No subject)") or "(No subject)"
    sender = headers.get("from", "(Unknown sender)") or "(Unknown sender)"
    categories = find_categories(subject, body, sender)
    priority = calculate_priority(subject, body, sender)
    gmail_id = message.get("id", "")
    msg_id = headers.get("message-id") or gmail_id
    return ProcessedEmail(
        gmail_id=gmail_id,
        thread_id=message.get("threadId"),
        message_id=msg_id,
        sender=sender,
        recipient=headers.get("to", ""),
        subject=subject,
        email_date=headers.get("date", ""),
        body=body,
        html_body=html,
        plain_text_body=plain,
        labels=message.get("labelIds", []) or [],
        categories=categories,
        priority=priority,
        gmail_link=f"https://mail.google.com/mail/u/0/#all/{message.get('threadId') or gmail_id}" if gmail_id else None,
        body_truncated=truncated,
    )


def is_relevant_email(email: ProcessedEmail) -> bool:
    """Return True when keyword classification found at least one category."""
    return bool(email.categories)

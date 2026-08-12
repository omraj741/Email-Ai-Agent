"""Optional AI/LLM analysis layer with safe rule-based fallback."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - production dependency listed in requirements
    def load_dotenv() -> bool:
        return False

from email_processor import ProcessedEmail
from logger import setup_logger

ALLOWED_KEYS = {"category", "categories", "priority", "company", "role", "location", "action_required", "deadline", "interview_date", "summary"}
VALID_PRIORITIES = {"HIGH", "MEDIUM", "LOW"}
logger = setup_logger(__name__)


def _fallback(email: ProcessedEmail) -> dict[str, Any]:
    return {"categories": email.categories, "priority": email.priority, "company": None, "role": None, "location": None, "action_required": None, "deadline": None, "interview_date": None, "summary": None}


def _validate(data: dict[str, Any], email: ProcessedEmail) -> dict[str, Any]:
    cleaned = {key: data.get(key) for key in ALLOWED_KEYS}
    if cleaned.get("priority") not in VALID_PRIORITIES:
        cleaned["priority"] = email.priority
    if not cleaned.get("categories") and cleaned.get("category"):
        cleaned["categories"] = [cleaned["category"]]
    if not cleaned.get("categories"):
        cleaned["categories"] = email.categories
    return cleaned


def analyze_email(email: ProcessedEmail) -> dict[str, Any]:
    """Analyze an email if AI is configured; otherwise return rule-based data."""
    load_dotenv()
    if os.getenv("AI_ENABLED", "false").lower() != "true":
        return _fallback(email)
    provider = os.getenv("AI_PROVIDER", "").lower()
    api_key = os.getenv("AI_API_KEY")
    model = os.getenv("AI_MODEL")
    if provider != "openai" or not api_key or not model:
        logger.warning("AI enabled but provider/API key/model is missing or unsupported; using fallback")
        return _fallback(email)
    try:
        prompt = (
            "Extract only explicitly available job/interview email facts as strict JSON with keys: "
            "category, priority, company, role, location, action_required, deadline, interview_date, summary. "
            "Use null for unavailable fields. Do not invent information.\n\n"
            f"Subject: {email.subject}\nFrom: {email.sender}\nBody:\n{email.body[:8000]}"
        )
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "response_format": {"type": "json_object"}}).encode()
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as response:  # noqa: S310 - configured HTTPS API endpoint
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        return _validate(json.loads(content), email)
    except Exception as exc:
        logger.error("AI analysis failed; using rule-based fallback: %s", exc)
        return _fallback(email)

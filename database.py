"""SQLite persistence for processed Gmail messages."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATABASE_PATH
from email_processor import ProcessedEmail


def initialize_database(db_path: Path = DATABASE_PATH) -> None:
    """Create the emails table and unique gmail_id index if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gmail_id TEXT NOT NULL UNIQUE,
                thread_id TEXT,
                message_id TEXT,
                sender TEXT,
                recipient TEXT,
                subject TEXT,
                email_date TEXT,
                body TEXT,
                categories TEXT,
                priority TEXT,
                company TEXT,
                role TEXT,
                location TEXT,
                action_required INTEGER,
                deadline TEXT,
                interview_date TEXT,
                ai_summary TEXT,
                processed_at TEXT NOT NULL,
                gmail_link TEXT
            )
            """
        )


def email_already_processed(gmail_id: str, db_path: Path = DATABASE_PATH) -> bool:
    """Return True if gmail_id already exists."""
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT 1 FROM emails WHERE gmail_id = ?", (gmail_id,)).fetchone() is not None


def save_email(email: ProcessedEmail, ai_data: dict[str, Any] | None = None, db_path: Path = DATABASE_PATH) -> bool:
    """Insert one processed email. Return False on duplicate."""
    ai_data = ai_data or {}
    categories = ai_data.get("categories") or ai_data.get("category") or email.categories
    if isinstance(categories, str):
        categories = [categories]
    priority = ai_data.get("priority") or email.priority
    values = (
        email.gmail_id, email.thread_id, email.message_id, email.sender, email.recipient, email.subject,
        email.email_date, email.body, json.dumps(categories), priority, ai_data.get("company"),
        ai_data.get("role"), ai_data.get("location"), int(bool(ai_data.get("action_required"))) if ai_data.get("action_required") is not None else None,
        ai_data.get("deadline"), ai_data.get("interview_date"), ai_data.get("summary"), datetime.now().isoformat(timespec="seconds"), email.gmail_link,
    )
    with sqlite3.connect(db_path) as conn:
        try:
            conn.execute(
                """
                INSERT INTO emails (gmail_id, thread_id, message_id, sender, recipient, subject, email_date, body,
                categories, priority, company, role, location, action_required, deadline, interview_date, ai_summary,
                processed_at, gmail_link) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            return True
        except sqlite3.IntegrityError:
            return False


def get_report_emails(db_path: Path = DATABASE_PATH, limit: int = 500) -> list[dict[str, Any]]:
    """Fetch recent processed emails for PDF reporting."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM emails ORDER BY processed_at DESC LIMIT ?", (limit,)).fetchall()
    records = [dict(row) for row in rows]
    for record in records:
        try:
            record["categories"] = json.loads(record.get("categories") or "[]")
        except json.JSONDecodeError:
            record["categories"] = []
    return records

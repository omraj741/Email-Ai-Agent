"""Configuration for the Personal Email AI Agent."""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"
MAX_EMAILS = 100
GMAIL_SEARCH_QUERY = "newer_than:1d"
REPORT_FOLDER = BASE_DIR / "reports"
DATABASE_PATH = BASE_DIR / "data" / "emails.db"
LOG_FOLDER = BASE_DIR / "logs"
MAX_EMAIL_BODY_LENGTH = 20000

EMAIL_CATEGORIES = {
    "Interview": ["interview", "technical interview", "hr interview", "interview round", "interview schedule", "interview scheduled", "interview invitation", "interview invite", "interview process", "technical round", "hr round"],
    "Job": ["job", "job opportunity", "job opening", "hiring", "hiring opportunity", "vacancy", "career opportunity", "career opening", "software developer", "software engineer", "developer role", "full time", "full-time", "associate software engineer", "application", "job application"],
    "Internship": ["internship", "intern", "intern opportunity", "internship opportunity", "internship program", "summer internship", "software internship", "developer intern", "internship opening"],
    "GD": ["gd", "group discussion", "group discussion round", "gd round"],
    "Placement": ["placement", "placement drive", "campus placement", "campus hiring", "campus recruitment", "placement opportunity"],
    "Assessment": ["assessment", "online assessment", "coding assessment", "technical assessment", "aptitude test", "aptitude assessment", "coding test", "online test", "online coding test"],
}

HIGH_PRIORITY_KEYWORDS = ["urgent", "important", "shortlisted", "selected", "interview scheduled", "interview invitation", "assessment scheduled", "deadline", "action required", "respond by", "last date", "offer letter"]
MEDIUM_PRIORITY_KEYWORDS = ["interview", "assessment", "placement", "internship", "job opportunity"]
REPORT_CATEGORY_ORDER = ["HIGH PRIORITY", "Interview", "Job", "Internship", "GD", "Placement", "Assessment"]

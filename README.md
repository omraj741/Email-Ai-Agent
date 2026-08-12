# Personal Email AI Agent

A local Python 3.11+ application that connects to Gmail with the Gmail API and OAuth 2.0, scans recent email, detects job/interview/internship/GD/placement/assessment messages with configurable keywords, optionally analyzes relevant email with an AI provider, stores processed messages in SQLite, prevents duplicates, and creates timestamped PDF reports.

No n8n, Zapier, Make, Selenium, IMAP, browser scraping, or Gmail passwords are used.

## Features

- Gmail API integration with OAuth 2.0 readonly scope.
- Automatic token loading, refresh, and browser-based first authorization.
- Keyword filtering for Interview, Job, Internship, GD, Placement, and Assessment.
- Case-insensitive phrase matching across subject, sender, and email body.
- Rule-based HIGH/MEDIUM/LOW priority detection.
- Optional AI analysis controlled by environment variables.
- SQLite storage with `gmail_id` duplicate prevention.
- Complete relevant email content in professional PDF reports.
- Gmail web links in reports where possible.
- Windows `run_agent.bat` and `scheduler_setup.bat` for 8 AM, 2 PM, and 8 PM automation.
- Rotating logs under `logs/` without logging secrets or full private email bodies.

## Installation

```bash
git clone <repository>
cd Personal-Email-AI-Agent
python -m venv venv
```

Windows:

```powershell
.\venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Gmail Setup

1. Create a Google Cloud project.
2. Enable the Gmail API for that project.
3. Configure the OAuth consent screen.
4. Create an OAuth Client ID with application type **Desktop app**.
5. Download the OAuth client file as `credentials.json`.
6. Place `credentials.json` in the project root next to `main.py`.
7. Run the application with `python main.py`.
8. Your browser opens for Google authorization. Never enter your Gmail password into this app.
9. After successful authorization, `token.json` is created automatically and refreshed when needed.

Required scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

## Configuration

Edit `config.py` for:

- `MAX_EMAILS`
- `GMAIL_SEARCH_QUERY` such as `newer_than:1d`
- `DATABASE_PATH`
- `REPORT_FOLDER`
- `LOG_FOLDER`
- `MAX_EMAIL_BODY_LENGTH`
- keyword lists and priority keywords

Copy `.env.example` to `.env` only if you want AI analysis:

```env
AI_ENABLED=false
AI_PROVIDER=
AI_API_KEY=
AI_MODEL=
```

The current optional AI implementation supports `AI_PROVIDER=openai` through the HTTPS Chat Completions API. If AI is disabled or misconfigured, the app still works using rule-based classification.

## Run

```bash
python main.py
```

If `credentials.json` is unavailable, the app exits safely with setup instructions. It does not fabricate credentials or authenticate falsely.

## Scheduling on Windows

Option 1: run the helper from Command Prompt:

```bat
scheduler_setup.bat
```

It creates three daily Windows Task Scheduler entries:

- 08:00
- 14:00
- 20:00

Option 2: create tasks manually in Task Scheduler:

1. Open **Task Scheduler**.
2. Choose **Create Basic Task**.
3. Name it `Personal Email AI Agent 08 AM`.
4. Trigger: Daily at `08:00`.
5. Action: Start a program.
6. Program/script: full path to `run_agent.bat`.
7. Repeat for `14:00` and `20:00`.

`run_agent.bat` changes to the project directory, activates `venv` if present, and runs `python main.py`.

## Database and Duplicate Prevention

SQLite database path defaults to `data/emails.db`. The `emails` table uses `gmail_id` as a unique identifier, so a message found at 8 AM will be skipped rather than duplicated at 2 PM or 8 PM.

## Reports

Reports are generated under `reports/` with local timestamps, for example:

```text
reports/email_report_2026-08-12_08-00.pdf
```

Each relevant email includes sender, subject, date, categories, priority, AI summary, action fields, Gmail link, and complete email body up to the configured maximum length.

## Tests

```bash
pytest
python -m compileall .
```

## Security

`.gitignore` excludes:

- `credentials.json`
- `token.json`
- `.env`
- virtual environments
- Python caches
- SQLite database files
- generated reports
- logs

Never commit OAuth credentials, tokens, API keys, or private email data.

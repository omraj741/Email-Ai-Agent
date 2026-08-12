"""Command-line orchestrator for the Personal Email AI Agent."""
from __future__ import annotations

from ai_analyzer import analyze_email
from database import email_already_processed, get_report_emails, initialize_database, save_email
from email_processor import is_relevant_email, process_email
from gmail_service import MissingCredentialsError, get_gmail_service, get_message, search_messages
from logger import setup_logger
from pdf_generator import generate_pdf

logger = setup_logger(__name__)


def _print_header() -> None:
    print("=" * 50)
    print("       PERSONAL EMAIL AI AGENT")
    print("=" * 50)
    print()


def main() -> int:
    """Run one email scan and report generation cycle."""
    _print_header()
    logger.info("Application started")
    initialize_database()
    try:
        print("[1/6] Connecting to Gmail...")
        service = get_gmail_service()
        print("SUCCESS\n")
        print("[2/6] Searching emails...")
        messages = search_messages(service)
        print(f"Found: {len(messages)} emails\n")
        print("[3/6] Processing emails...")
        relevant = duplicates = ai_completed = saved = 0
        for message in messages:
            gmail_id = message.get("id")
            if not gmail_id:
                continue
            if email_already_processed(gmail_id):
                duplicates += 1
                continue
            full_message = get_message(service, gmail_id)
            if not full_message:
                continue
            try:
                email = process_email(full_message)
            except Exception as exc:
                logger.error("Malformed email skipped: %s", exc)
                continue
            if not is_relevant_email(email):
                continue
            relevant += 1
            ai_data = analyze_email(email)
            ai_completed += 1
            if save_email(email, ai_data):
                saved += 1
        logger.info("Relevant messages found: %s", relevant)
        logger.info("Duplicate messages skipped: %s", duplicates)
        print(f"Relevant emails: {relevant}")
        print(f"Duplicates skipped: {duplicates}\n")
        print("[4/6] AI analysis...")
        print(f"Completed: {ai_completed}\n")
        print("[5/6] Updating database...")
        logger.info("Database updated; saved %s emails", saved)
        print("SUCCESS\n")
        print("[6/6] Generating PDF...")
        report_path = generate_pdf(get_report_emails())
        logger.info("PDF generated: %s", report_path)
        print("SUCCESS\n")
        print("Report:")
        print(report_path)
        print("\n" + "=" * 50)
        print("       AGENT COMPLETED SUCCESSFULLY")
        print("=" * 50)
        logger.info("Application completed")
        return 0
    except MissingCredentialsError as exc:
        logger.error("Missing Gmail credentials")
        print(str(exc))
        return 2
    except Exception as exc:
        logger.exception("Application failed: %s", exc)
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from email_processor import ProcessedEmail
from database import email_already_processed, get_report_emails, initialize_database, save_email


def sample_email(gmail_id="g1"):
    return ProcessedEmail(gmail_id, "t1", "m1", "a@example.com", "b@example.com", "Interview", "today", "body", "", "body", [], ["Interview"], "HIGH", "https://mail.google.com/mail/u/0/#all/t1")


def test_duplicate_emails_are_prevented(tmp_path):
    db = tmp_path / "emails.db"
    initialize_database(db)
    assert save_email(sample_email(), {}, db) is True
    assert save_email(sample_email(), {}, db) is False
    assert email_already_processed("g1", db) is True
    assert len(get_report_emails(db)) == 1

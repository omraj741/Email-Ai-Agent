from pdf_generator import generate_pdf


def test_pdf_generation_creates_valid_pdf(tmp_path):
    path = generate_pdf([
        {"sender": "hr@example.com", "subject": "Campus Placement Interview", "email_date": "today", "body": "Complete relevant email content", "categories": ["Placement", "Interview"], "priority": "HIGH", "gmail_link": "https://mail.google.com/mail/u/0/#all/x"}
    ], tmp_path)
    assert path.exists()
    assert path.read_bytes().startswith(b"%PDF")

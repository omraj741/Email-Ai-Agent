import base64

from email_processor import clean_html, find_categories, get_email_body, process_email


def enc(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def test_keyword_detection_cases():
    assert "Interview" in find_categories("Interview", "", "")
    assert "Interview" in find_categories("INTERVIEW", "", "")
    assert "Interview" in find_categories("technical interview", "", "")
    assert "Internship" in find_categories("", "summer internship", "")
    assert "GD" in find_categories("", "group discussion round", "")
    assert "Placement" in find_categories("placement", "", "")
    assert "Assessment" in find_categories("assessment", "", "")


def test_multiple_categories():
    categories = find_categories("Campus Placement - Technical Interview and Assessment", "", "")
    assert {"Placement", "Interview", "Assessment"}.issubset(categories)


def test_html_processing_removes_noise():
    html = "<html><style>.x{}</style><script>alert(1)</script><body><h1>Interview</h1><p>Scheduled tomorrow</p></body></html>"
    assert clean_html(html) == "Interview\nScheduled tomorrow"


def test_empty_body_message_is_safe():
    body, html, plain, truncated = get_email_body({"payload": {"mimeType": "text/plain", "body": {}}})
    assert body == html == plain == ""
    assert truncated is False


def test_process_email_plain_text():
    msg = {"id": "abc", "threadId": "thr", "labelIds": ["INBOX"], "payload": {"headers": [{"name": "Subject", "value": "Assessment"}, {"name": "From", "value": "hr@example.com"}], "mimeType": "text/plain", "body": {"data": enc("Complete email body")}}}
    email = process_email(msg)
    assert email.gmail_id == "abc"
    assert email.body == "Complete email body"
    assert "Assessment" in email.categories

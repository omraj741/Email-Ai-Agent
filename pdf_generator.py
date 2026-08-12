"""ReportLab PDF generation for processed relevant emails."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
except ImportError:  # pragma: no cover - production dependency listed in requirements
    colors = letter = getSampleStyleSheet = ParagraphStyle = inch = PageBreak = Paragraph = SimpleDocTemplate = Spacer = None
from xml.sax.saxutils import escape

from config import REPORT_CATEGORY_ORDER, REPORT_FOLDER


def _para(text: Any, style) -> Any:
    return Paragraph(escape("" if text is None else str(text)).replace("\n", "<br/>"), style)


def _email_block(email: dict[str, Any], styles: dict[str, ParagraphStyle]) -> list[Any]:
    cats = email.get("categories") or []
    story: list[Any] = [
        _para(f"Company: {email.get('company') or 'Not available'}", styles["BodyText"]),
        _para(f"Role: {email.get('role') or 'Not available'}", styles["BodyText"]),
        _para(f"From: {email.get('sender') or ''}", styles["BodyText"]),
        _para(f"Subject: {email.get('subject') or ''}", styles["BodyText"]),
        _para(f"Date: {email.get('email_date') or ''}", styles["BodyText"]),
        _para(f"Category: {', '.join(cats)}", styles["BodyText"]),
        _para(f"Priority: {email.get('priority') or 'LOW'}", styles["BodyText"]),
        _para(f"AI Summary: {email.get('ai_summary') or 'Not available'}", styles["BodyText"]),
        _para(f"Action Required: {email.get('action_required')}", styles["BodyText"]),
        _para(f"Deadline: {email.get('deadline') or 'Not available'}", styles["BodyText"]),
    ]
    if email.get("gmail_link"):
        story.append(Paragraph(f'<link href="{escape(email["gmail_link"])}">Open Email in Gmail</link>: {escape(email["gmail_link"])}', styles["Link"]))
    story.extend([Spacer(1, 0.1 * inch), _para("Complete Email Content:", styles["Heading3"]), _para(email.get("body") or "(No body)", styles["BodyText"]), Spacer(1, 0.25 * inch)])
    return story


def generate_pdf(emails: list[dict[str, Any]], report_folder: Path = REPORT_FOLDER) -> Path:
    """Generate a timestamped PDF report and return its path."""
    report_folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    path = report_folder / f"email_report_{now:%Y-%m-%d_%H-%M}.pdf"
    if SimpleDocTemplate is None:
        lines = ["PERSONAL EMAIL AI REPORT", f"Date: {now:%Y-%m-%d}", f"Generated Time: {now:%H:%M:%S}"]
        for email in emails:
            lines.extend([email.get("subject", ""), email.get("sender", ""), email.get("body", "")])
        content = "\n".join(lines).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({content[:3000]}) Tj ET"
        pdf = f"%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >> endobj\n4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\ntrailer << /Root 1 0 R >>\n%%EOF"
        path.write_bytes(pdf.encode("latin-1", errors="replace"))
        return path
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Link", parent=styles["BodyText"], textColor=colors.blue))
    story: list[Any] = [Paragraph("PERSONAL EMAIL AI REPORT", styles["Title"]), _para(f"Date: {now:%Y-%m-%d}", styles["BodyText"]), _para(f"Generated Time: {now:%H:%M:%S}", styles["BodyText"]), Spacer(1, 0.25 * inch)]
    if not emails:
        story.append(_para("No relevant emails found for this report.", styles["BodyText"]))
    high = [e for e in emails if e.get("priority") == "HIGH"]
    sections: list[tuple[str, list[dict[str, Any]]]] = [("HIGH PRIORITY", high)]
    for category in REPORT_CATEGORY_ORDER[1:]:
        sections.append((category.upper(), [e for e in emails if category in (e.get("categories") or [])]))
    seen_sections = False
    for title, items in sections:
        if not items:
            continue
        if seen_sections:
            story.append(PageBreak())
        seen_sections = True
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(_para("-" * 40, styles["BodyText"]))
        for email in items:
            story.extend(_email_block(email, styles))
    doc.build(story)
    return path

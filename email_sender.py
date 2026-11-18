"""Sends the two emails for a new quote: a confirmation to the visitor and a notification to the team.

The email designs live in emails/ (built with React Email). The ready-to-send HTML is in emails/rendered/.
"""
import logging
import os
import re
from html import escape

import resend

log = logging.getLogger(__name__)
TEMPLATES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emails", "rendered")


def setting(name, default=""):
    """An empty value in .env counts as not set, so the default is used."""
    return (os.environ.get(name) or default).strip()


def fill_template(template_name, values):
    """Replaces each {{name}} marker in the email HTML with the real value.

    Every value is escaped first, because most of them were typed by a visitor.
    """
    frontend_url = setting("FRONTEND_URL", "https://portfolio.shakaaraahllc.com").rstrip("/")
    values = {
        "logo_url": setting("EMAIL_LOGO_URL") or f"{frontend_url}/assets/images/email-logo.png",
        "site_url": frontend_url,
        **values,
    }
    with open(os.path.join(TEMPLATES_FOLDER, f"{template_name}.html"), encoding="utf-8") as template_file:
        html = template_file.read()
    for marker, value in values.items():
        html = html.replace("{{" + marker + "}}", escape(str(value), quote=True))

    unfilled = re.findall(r"\{\{[a-z_]+\}\}", html)
    if unfilled:
        raise ValueError(f"{template_name} still has unfilled markers: {sorted(set(unfilled))}")
    return html


def send_email(to, subject, template_name, values, reply_to=None):
    """Returns True if the email service accepted it. It never raises, so an email problem cannot lose a quote."""
    api_key = setting("RESEND_API_KEY")
    if not api_key or not to:
        log.warning("Email '%s' skipped: RESEND_API_KEY or the recipient is missing", template_name)
        return False
    try:
        resend.api_key = api_key
        email = {
            "from": setting("MAIL_DEFAULT_SENDER", "Shakaaraah Communications <noreply@shakaaraahllc.com>"),
            "to": to,
            "subject": subject,
            "html": fill_template(template_name, values),
        }
        if reply_to:
            email["reply_to"] = reply_to
        resend.Emails.send(email)
        return True
    except Exception:
        log.exception("Email '%s' failed to send", template_name)
        return False


def send_quote_emails(quote):
    """Returns (visitor_email_sent, team_email_sent)."""
    team_addresses = [a.strip() for a in setting("TEAM_NOTIFICATION_EMAILS").split(",") if a.strip()]
    whatsapp_digits = quote["whatsapp_number"].lstrip("+").removeprefix("00")

    visitor_email_sent = send_email(
        to=[quote["email"]],
        subject=f"Welcome to Shakaaraah Communications, {quote['name']}. We have your quote request",
        template_name="quote-confirmation",
        values=quote,
        reply_to=setting("MAIL_REPLY_TO", "digital@shakaaraahllc.com"),
    )
    team_email_sent = send_email(
        to=team_addresses,
        subject=f"New quote request: {quote['service']} from {quote['name']}",
        template_name="quote-team-notification",
        values={**quote, "whatsapp_chat_url": f"https://wa.me/{whatsapp_digits}"},
        reply_to=quote["email"],
    )
    return visitor_email_sent, team_email_sent

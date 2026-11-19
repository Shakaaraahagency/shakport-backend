"""Run with:  python -m pytest"""
import io
import os
from datetime import datetime

import pytest
import resend
from openpyxl import load_workbook

os.environ.update(
    SECRET_KEY="test-secret-key",
    ADMIN_PASSWORD="a-long-test-password",
    DATABASE_URL="sqlite:///:memory:",
    FRONTEND_URL="https://portfolio.example.com",
    FRONTEND_ORIGINS="https://portfolio.example.com",
    RESEND_API_KEY="test-key",
    TEAM_NOTIFICATION_EMAILS="team@example.com",
    DEBUG="1",
)

from app import Quote, app, db, limiter  # noqa: E402

app.config.update(TESTING=True, SEND_EMAILS_IN_BACKGROUND=False)
limiter.enabled = False

GOOD_QUOTE = {
    "name": "Amaka Obi",
    "email": "Amaka@Example.com",
    "whatsapp": "+234 703 543 6057",
    "service": "Business website (US$350 offer)",
    "message": "We sell ginger drinks in bulk and need a site that takes orders.",
    "source": "/website-offer",
    "website": "",
}


@pytest.fixture(autouse=True)
def fresh_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield


@pytest.fixture
def client():
    return app.test_client()


@pytest.fixture
def sent_emails(monkeypatch):
    sent = []
    monkeypatch.setattr(resend.Emails, "send", lambda email: sent.append(email) or {"id": "x"})
    return sent


@pytest.fixture
def admin_client(client):
    client.post("/admin/login", data={"password": "a-long-test-password"})
    return client


def add_quote(reference, created_at, name="Amaka Obi"):
    db.session.add(Quote(reference=reference, name=name, email="a@example.com", whatsapp="+2347035436057",
                         service="Landing page", message="Need a landing page for my shop.",
                         source_page="/", created_at=created_at))
    db.session.commit()


def test_good_quote_is_saved_and_both_emails_go_out(client, sent_emails):
    reply = client.post("/api/v1/quotes", json=GOOD_QUOTE)

    assert reply.status_code == 201
    saved = Quote.query.one()
    assert saved.reference == reply.json["data"]["reference"]
    assert saved.email == "amaka@example.com"
    assert saved.whatsapp == "+2347035436057"
    assert saved.client_email_sent and saved.team_email_sent

    visitor_email, team_email = sent_emails
    assert visitor_email["to"] == ["amaka@example.com"]
    assert "Welcome to Shakaaraah Communications" in visitor_email["subject"]
    assert team_email["to"] == ["team@example.com"]
    assert "wa.me/2347035436057" in team_email["html"]
    for email in sent_emails:
        assert "https://portfolio.example.com/assets/images/email-logo.png" in email["html"]
        assert "{{" not in email["html"]


def test_html_typed_by_a_visitor_cannot_get_into_the_emails(client, sent_emails):
    client.post("/api/v1/quotes", json={**GOOD_QUOTE, "name": "<script>alert(1)</script>"})
    for email in sent_emails:
        assert "<script>alert(1)</script>" not in email["html"]
        assert "&lt;script&gt;" in email["html"]


def test_bad_fields_are_reported_one_by_one(client, sent_emails):
    reply = client.post("/api/v1/quotes", json={**GOOD_QUOTE, "email": "nope", "whatsapp": "0703"})
    assert reply.status_code == 422
    assert set(reply.json["errors"]) == {"email", "whatsapp"}
    assert Quote.query.count() == 0 and sent_emails == []


def test_spam_trap_pretends_to_work_but_saves_nothing(client, sent_emails):
    reply = client.post("/api/v1/quotes", json={**GOOD_QUOTE, "website": "http://spam.example"})
    assert reply.status_code == 201
    assert Quote.query.count() == 0 and sent_emails == []


def test_quote_is_kept_even_if_the_email_service_is_down(client, monkeypatch):
    def broken(email):
        raise RuntimeError("email service down")
    monkeypatch.setattr(resend.Emails, "send", broken)

    assert client.post("/api/v1/quotes", json=GOOD_QUOTE).status_code == 201
    saved = Quote.query.one()
    assert not saved.client_email_sent and not saved.team_email_sent


def test_only_our_website_may_call_the_api_from_a_browser(client):
    asking = {"Access-Control-Request-Method": "POST"}
    allowed = client.options("/api/v1/quotes", headers={**asking, "Origin": "https://portfolio.example.com"})
    blocked = client.options("/api/v1/quotes", headers={**asking, "Origin": "https://evil.example"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "https://portfolio.example.com"
    assert "Access-Control-Allow-Origin" not in blocked.headers


def test_health_check(client):
    assert client.get("/api/v1/health").json["success"] is True


def test_admin_pages_need_the_password(client):
    assert client.get("/admin").status_code == 302
    assert client.get("/admin/export?from=2026-11-01&to=2026-11-02").status_code == 302
    wrong = client.post("/admin/login", data={"password": "wrong"})
    assert wrong.status_code == 401 and b"Incorrect password." in wrong.data


def test_dashboard_shows_empty_state_then_escapes_visitor_text(admin_client):
    assert b"No quote requests yet" in admin_client.get("/admin").data
    add_quote("SQ-AAAAAA", datetime(2026, 11, 10, 9, 0), name="<b>Bold</b>")
    page = admin_client.get("/admin").data
    assert b"<b>Bold</b>" not in page and b"&lt;b&gt;Bold&lt;/b&gt;" in page


def test_export_only_includes_the_chosen_lagos_days(admin_client):
    add_quote("SQ-INSIDE", datetime(2026, 11, 10, 9, 0))
    add_quote("SQ-LATE", datetime(2026, 11, 12, 23, 30))   # 00:30 on the 13th in Lagos, so outside
    add_quote("SQ-EARLY", datetime(2026, 10, 1, 9, 0))

    reply = admin_client.get("/admin/export?from=2026-11-01&to=2026-11-12")

    assert reply.status_code == 200
    assert "shakaaraah-quotes_2026-11-01_to_2026-11-12.xlsx" in reply.headers["Content-Disposition"]
    rows = list(load_workbook(io.BytesIO(reply.data)).active.iter_rows(values_only=True))
    assert [row[0] for row in rows[1:]] == ["SQ-INSIDE"]
    assert rows[1][3] == "+2347035436057"


def test_export_turns_spreadsheet_formulas_into_plain_text(admin_client):
    add_quote("SQ-FORMULA", datetime(2026, 11, 10, 9, 0), name='=HYPERLINK("http://evil.example","x")')
    reply = admin_client.get("/admin/export?from=2026-11-01&to=2026-11-12")
    cell = load_workbook(io.BytesIO(reply.data)).active.cell(row=2, column=3)
    assert cell.data_type == "s" and cell.value.startswith("=HYPERLINK")


def test_export_explains_a_bad_date_range_instead_of_failing(admin_client):
    backwards = admin_client.get("/admin/export?from=2026-11-12&to=2026-11-01", follow_redirects=True)
    assert b"The end date comes before the start date." in backwards.data
    missing = admin_client.get("/admin/export?from=2026-11-01", follow_redirects=True)
    assert b"Choose a start date and an end date." in missing.data


def test_signing_out_locks_the_dashboard_again(admin_client):
    admin_client.post("/admin/logout")
    assert admin_client.get("/admin").status_code == 302

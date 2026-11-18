# Shakaaraah backend

Receives quote requests from the website, saves them, emails the visitor and your team, and gives you an admin page to download requests as an Excel file.

## What each file does

| File | Job |
| --- | --- |
| `app.py` | The whole backend: settings, database, the quote form endpoint, the admin page |
| `email_sender.py` | Sends the two emails |
| `excel_export.py` | Builds the Excel file |
| `templates/` | The two admin pages (sign in, dashboard) |
| `static/` | Admin page styles and the logo |
| `emails/` | The email designs (React Email). The ready-to-send HTML is in `emails/rendered/` |
| `test_app.py` | Automatic tests |
| `.env.example` | The settings you need to fill in |

## Run it on your computer

```
python -m venv venv
venv\Scripts\activate          (on Mac or Linux:  source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         (on Mac or Linux:  cp .env.example .env)
```

Open `.env` and fill in `SECRET_KEY` and `ADMIN_PASSWORD` (the comments in the file explain how). Then:

```
python app.py
```

Open http://localhost:5000 and sign in with your admin password.

## Put it on Render

1. Have your **MySQL** database ready (Render does not host MySQL, so this is the one from your hosting provider). It must accept connections from outside, so allow remote access in your provider's settings.
2. Create a **Web Service** from this project.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --preload app:app`
   - Health check path: `/api/v1/health`
3. Add these environment variables (the same names as in `.env.example`, but do not set `DEBUG`):
   `SECRET_KEY`, `ADMIN_PASSWORD`, `DATABASE_URL` (your MySQL address, written as `mysql://USERNAME:PASSWORD@HOST:3306/DATABASE_NAME`), `FRONTEND_URL`, `FRONTEND_ORIGINS`, `RESEND_API_KEY`, `MAIL_DEFAULT_SENDER`, `MAIL_REPLY_TO`, `TEAM_NOTIFICATION_EMAILS`
4. In the website project, open `scripts/config.js` and set `apiBaseUrl` to your Render address, for example `https://shakaaraah-api.onrender.com`.

`FRONTEND_ORIGINS` must be your website address exactly as it appears in the browser, or browsers will block the form.

The database tables are created automatically the first time the app starts. If your password has special characters such as `@` or `#`, write them as `%40` and `%23` in the address.

## Emails (Resend)

1. Create an account at resend.com and add your domain (`shakaaraahllc.com`). Add the DNS records it shows you and wait for it to verify.
2. Create an API key and put it in `RESEND_API_KEY`.
3. `MAIL_DEFAULT_SENDER` must use that verified domain.

Without a key, quotes are still saved. The log just says the email was skipped.

### Changing how the emails look

The designs are in `emails/`. You only need Node.js for this, and only when you edit a design:

```
cd emails
npm install
npm run dev       (live preview in your browser)
npm run render    (rebuilds the ready-to-send HTML in emails/rendered/)
```

Commit the rebuilt files in `emails/rendered/`. The logo in the emails is loaded from your website (`/assets/images/email-logo.png`), so publish the website first.

## Tests

```
pip install pytest
python -m pytest
```

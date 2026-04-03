"""
Email notification for access requests.

Configure via .env:
    SMTP_HOST      e.g. smtp.gmail.com
    SMTP_PORT      e.g. 587
    SMTP_USER      sender email address
    SMTP_PASSWORD  sender email password or app password
    ADMIN_EMAIL    recipient (default: wilson@srfcapital.studio — override via .env)

If SMTP credentials are not configured, the request is still saved to the
database and the error is printed to console — the flow does not break.
"""

import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "wilson@srfcapital.studio")


def send_access_request_email(username: str, email: str) -> tuple[bool, str]:
    """
    Send an access-request notification email to the admin.

    Returns (success: bool, message: str).
    Caller should handle the False case gracefully — request is already in DB.
    """
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    if not smtp_host or not smtp_user or not smtp_pass:
        msg = (
            "SMTP not configured — access request saved to database only. "
            "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env to enable email notifications."
        )
        print(f"[email_sender] {msg}")
        return False, msg

    subject = f"[SRF Capital Studio] Access Request — {username}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    body = f"""\
A new user has requested access to SRF Capital Studio.

  Username : {username}
  Email    : {email}
  Time     : {timestamp}

To approve, create their account:
  python scripts/create_user.py

Then notify them at: {email}

— SRF Capital Studio System
"""

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ADMIN_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, ADMIN_EMAIL, msg.as_string())
        return True, "Notification sent to admin."
    except Exception as exc:
        err = f"Email delivery failed: {exc}"
        print(f"[email_sender] {err}")
        return False, err

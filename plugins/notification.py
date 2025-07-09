# plugins/notification.py

import smtplib
from email.mime.text import MIMEText
from config import settings

def send_email(recipient, subject, body):
    """Sends an email notification."""
    if not settings.EMAIL_HOST:
        print("Email not configured. Skipping notification.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = settings.EMAIL_SENDER
    msg['To'] = recipient

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(settings.EMAIL_SENDER, [recipient], msg.as_string())
        print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")



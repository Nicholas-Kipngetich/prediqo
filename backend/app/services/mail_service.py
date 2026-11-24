"""Best-effort email delivery for development verification codes.

When SMTP is not configured the code is only logged; the API still returns it
in development mode so local testing does not depend on a mail server.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_code(recipient: str, code: str) -> bool:
    if not settings.smtp_host:
        logger.info("SMTP not configured; verification code for %s: %s", recipient, code)
        return False
    try:
        message = EmailMessage()
        message["Subject"] = "Your Prediqo verification code"
        message["From"] = settings.smtp_from
        message["To"] = recipient
        message.set_content(
            f"Your Prediqo verification code is {code}. "
            f"It expires in {settings.dev_verification_code_ttl_minutes} minutes."
        )
        if settings.smtp_use_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
        return True
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Failed to send verification email: %s", exc)
        return False

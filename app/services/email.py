import smtplib
from email.mime.text import MIMEText
from flask import current_app


def send_email(subject: str, body: str, recipients: list[str]):
    """Send an email using SMTP configuration from Flask app config."""
    smtp_server = current_app.config.get('SMTP_SERVER')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    username = current_app.config.get('SMTP_USERNAME')
    password = current_app.config.get('SMTP_PASSWORD')
    from_addr = current_app.config.get('SMTP_FROM', username)

    if not smtp_server or not username or not password:
        current_app.logger.warning('Email not sent. SMTP configuration missing.')
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(recipients)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_addr, recipients, msg.as_string())
        current_app.logger.info('Email sent to %s', recipients)
        return True
    except Exception as e:
        current_app.logger.error('Failed to send email: %s', e)
        return False


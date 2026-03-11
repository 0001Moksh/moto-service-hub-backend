import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)


def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP via email"""
    try:
        subject = "Moto Service Hub - OTP Verification"
        body = f"""
        <html>
            <body>
                <h2>OTP Verification</h2>
                <p>Your OTP for Moto Service Hub is:</p>
                <h1 style="color: #2563eb; font-size: 36px;">{otp}</h1>
                <p>This OTP is valid for 10 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <hr>
                <p><small>© 2026 Moto Service Hub. All rights reserved.</small></p>
            </body>
        </html>
        """
        
        return send_email(email, subject, body)
    except Exception as e:
        logger.error(f"Error sending OTP email: {e}")
        return False


def send_welcome_email(email: str, name: str) -> bool:
    """Send welcome email to new customer"""
    try:
        subject = "Welcome to Moto Service Hub!"
        body = f"""
        <html>
            <body>
                <h2>Welcome, {name}!</h2>
                <p>Your account has been successfully created.</p>
                <p>You can now sign in and start managing your vehicles.</p>
                <a href="https://your-app-url.com/signin" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Sign In</a>
                <p style="margin-top: 20px;">If you have any questions, feel free to contact us.</p>
                <hr>
                <p><small>© 2026 Moto Service Hub. All rights reserved.</small></p>
            </body>
        </html>
        """
        
        return send_email(email, subject, body)
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        return False


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email
        
        # Attach HTML body
        msg.attach(MIMEText(body, "html"))
        
        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


async def send_email_async(to_email: str, subject: str, body: str) -> bool:
    """Send email asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, send_email, to_email, subject, body)

"""
Email service for sending verification emails.
Uses FastAPI-Mail for async email sending.
"""

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

from src.helpers.config import settings
from src.helpers.logging_config import get_logger, mask_email

logger = get_logger("auth.email")


# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_verification_email(email: EmailStr, code: str, name: str) -> None:
    """
    Send email verification code to user.

    Args:
        email: User's email address
        code: 6-digit verification code
        name: User's name for personalization
    """
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Welcome to Our App, {name}!</h2>
            <p>Thank you for registering. Please use the following code to verify your email:</p>
            <div style="background-color: #f4f4f4; padding: 20px; text-align: center; margin: 20px 0;">
                <h1 style="letter-spacing: 10px; font-size: 32px; color: #333;">{code}</h1>
            </div>
            <p>This code will expire in 24 hours.</p>
            <br>
            <p style="color: #666;">If you didn't create an account, please ignore this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Your Verification Code",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )

    masked = mask_email(email)
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info("Verification email sent to %s", masked)
    except Exception:
        logger.exception("Failed to send verification email to %s", masked)
        raise


async def send_password_reset_email(email: EmailStr, code: str, name: str) -> None:
    """
    Send password reset code to user.

    Args:
        email: User's email address
        code: 6-digit reset code
        name: User's name for personalization
    """
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Reset Request</h2>
            <p>Hi {name},</p>
            <p>We received a request to reset your password. Use the following code to reset it:</p>
            <div style="background-color: #f4f4f4; padding: 20px; text-align: center; margin: 20px 0;">
                <h1 style="letter-spacing: 10px; font-size: 32px; color: #333;">{code}</h1>
            </div>
            <p>This code will expire in 24 hours.</p>
            <br>
            <p style="color: #666;">If you didn't request a password reset, please ignore this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Password Reset Code",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html,
    )

    masked = mask_email(email)
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info("Password reset email sent to %s", masked)
    except Exception:
        logger.exception("Failed to send password reset email to %s", masked)
        raise

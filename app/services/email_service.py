"""
Email service for sending verification and notification emails.
"""
import logging
from typing import Optional

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger("bookapi.email")


def _create_mail_config() -> Optional[ConnectionConfig]:
    """Create mail configuration if email settings are properly configured."""
    # Check if email is properly configured
    if not settings.MAIL_USERNAME or not settings.MAIL_SERVER:
        logger.warning("Email service not configured. Email functionality will be disabled.")
        return None

    mail_from = settings.MAIL_FROM or settings.MAIL_USERNAME
    if not mail_from or "@" not in mail_from:
        logger.warning("Invalid MAIL_FROM address. Email functionality will be disabled.")
        return None

    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=mail_from,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_TLS,
        MAIL_SSL_TLS=settings.MAIL_SSL,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


# Email configuration (may be None if not configured)
mail_config = _create_mail_config()


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.fastmail = FastMail(mail_config) if mail_config else None
        self._enabled = mail_config is not None

    @property
    def is_enabled(self) -> bool:
        """Check if email service is enabled and configured."""
        return self._enabled

    async def send_email(
            self,
            recipients: list[EmailStr],
            subject: str,
            body: str,
            subtype: MessageType = MessageType.html
    ) -> bool:
        """
        Send an email to recipients.

        Args:
            recipients: List of email addresses
            subject: Email subject
            body: Email body (HTML or plain text)
            subtype: Message type (html or plain)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._enabled:
            logger.warning(f"Email service not enabled. Skipping email to {recipients}")
            return False

        try:
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=body,
                subtype=subtype
            )
            await self.fastmail.send_message(message)
            logger.info(f"Email sent successfully to {recipients}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipients}: {str(e)}")
            return False

    async def send_verification_email(
            self,
            email: EmailStr,
            username: str,
            verification_token: str
    ) -> bool:
        """
        Send email verification link to user.

        Args:
            email: User's email address
            username: User's username
            verification_token: JWT verification token

        Returns:
            True if sent successfully
        """
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 30px; 
                    background-color: #4F46E5; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 BookAPI</h1>
                </div>
                <div class="content">
                    <h2>Welcome, {username}!</h2>
                    <p>Thank you for registering with BookAPI. Please verify your email address to activate your account.</p>
                    <p>Click the button below to verify your email:</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4F46E5;">{verification_url}</p>
                    <p><strong>This link will expire in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hours.</strong></p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2026 BookAPI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            recipients=[email],
            subject="Verify Your Email - BookAPI",
            body=html_body
        )

    async def send_password_reset_email(
            self,
            email: EmailStr,
            username: str,
            reset_token: str
    ) -> bool:
        """
        Send password reset link to user.

        Args:
            email: User's email address
            username: User's username
            reset_token: Password reset token

        Returns:
            True if sent successfully
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background-color: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 30px; 
                    background-color: #4F46E5; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 BookAPI</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>Hi {username},</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #4F46E5;">{reset_url}</p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2026 BookAPI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            recipients=[email],
            subject="Password Reset Request - BookAPI",
            body=html_body
        )


# Singleton instance
email_service = EmailService()

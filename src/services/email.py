from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from src.core.config import settings
from typing import Dict, Any

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME or "",
    MAIL_PASSWORD=settings.MAIL_PASSWORD or "",
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME)
)

class EmailService:
    @staticmethod
    async def _send_mail(subject: str, recipients: list[str], body: str):
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message)

    @staticmethod
    async def send_password_reset_otp(email: str, otp: str):
        body = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password. Use the OTP below to complete the process.</p>
                <h3>Your OTP: <strong>{otp}</strong></h3>
                <p>This OTP will expire in 10 minutes. If you did not request a password reset, please ignore this email.</p>
            </body>
        </html>
        """
        await EmailService._send_mail(subject="NEMSAS - Password Reset OTP", recipients=[email], body=body)

    @staticmethod
    async def send_account_activation(email: str, token: str):
        from src.core.config import settings
        activation_link = f"{settings.FRONTEND_URL}/activate?token={token}"
        body = f"""
        <html>
            <body>
                <h2>Welcome to NEMSAS</h2>
                <p>Your account has been created. Click the link below to activate your account and set your password:</p>
                <p><a href="{activation_link}">{activation_link}</a></p>
                <p>Alternatively, you can use this verification token: <strong>{token}</strong></p>
                <p>This link and token will expire in <strong>48 hours</strong>.</p>
            </body>
        </html>
        """
        await EmailService._send_mail(subject="NEMSAS - Account Activation", recipients=[email], body=body)

    @staticmethod
    async def send_partner_2fa(email: str, otp: str):
        body = f"""
        <html>
            <body>
                <h2>Partner Account Verification</h2>
                <p>As part of your registration as a NEMSAS partner, please use the OTP below to verify your account.</p>
                <h3>Your 2FA OTP: <strong>{otp}</strong></h3>
                <p>This OTP will expire in 10 minutes.</p>
            </body>
        </html>
        """
        await EmailService._send_mail(subject="NEMSAS - Partner Registration 2FA", recipients=[email], body=body)

email_service = EmailService()

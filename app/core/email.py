import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

# ------------------------------------------------------------------
# Base URL for static assets served by the backend
# ------------------------------------------------------------------
_STATIC_BASE = "https://nemsas-backend.onrender.com/static/images"

_DEFAULT_HERO_IMAGE = f"https://ik.imagekit.io/eqh0cjetc/amazon-image/hero-img.png"
_LOGO_RED = f"https://ik.imagekit.io/eqh0cjetc/amazon-image/Frame%202.svg"
_LOGO_WHITE = f"https://ik.imagekit.io/eqh0cjetc/amazon-image/logo-white.png"


# ------------------------------------------------------------------
# Transport layer – SMTP or Brevo
# ------------------------------------------------------------------
def _send_via_smtp(to_email: str, subject: str, html_content: str):
    """Send email using traditional SMTP relay."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAILS_FROM_EMAIL
        msg["To"] = to_email

        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
        if settings.EMAIL_USE_TLS:
            server.starttls()
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.EMAILS_FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"[Email Success – SMTP] Sent email to {to_email}")
    except Exception as e:
        print(f"[Email Error – SMTP] Failed to send email to {to_email}: {e}")


def _send_via_brevo(to_email: str, subject: str, html_content: str):
    """Send email using Brevo (Sendinblue) transactional API."""
    api_key = settings.BREVO_API_KEY
    sender_email = settings.BREVO_SENDER_EMAIL or settings.EMAILS_FROM_EMAIL

    if not api_key:
        print("[Email Error – Brevo] BREVO_API_KEY is not set. Falling back to SMTP.")
        _send_via_smtp(to_email, subject, html_content)
        return

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key,
    }
    payload = {
        "sender": {"email": sender_email, "name": "NEMSAS"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code in (200, 201):
            print(f"[Email Success – Brevo] Sent email to {to_email}")
        else:
            print(f"[Email Error – Brevo] {resp.status_code} – {resp.text}")
    except Exception as e:
        print(f"[Email Error – Brevo] Failed to send email to {to_email}: {e}")


def send_email(to_email: str, subject: str, html_content: str):
    """
    Unified send function.
    Routes through Brevo when EMAIL_PROVIDER == 'brevo', otherwise SMTP.
    """
    provider = (settings.EMAIL_PROVIDER or "default").strip().lower()
    if provider == "brevo":
        _send_via_brevo(to_email, subject, html_content)
    else:
        _send_via_smtp(to_email, subject, html_content)


# Keep the old name as an alias so existing callers still work
send_smtp_email = send_email


# ------------------------------------------------------------------
# HTML email template
# ------------------------------------------------------------------
def get_email_template(
    title: str,
    message_body: str,
    extra_content: str = "",
    hero_image_url: str | None = None,
) -> str:
    """
    Returns a styled HTML email.

    Parameters
    ----------
    title : str
        Heading shown inside the email body.
    message_body : str
        Paragraph text below the heading.
    extra_content : str
        Any additional HTML (verification code box, buttons, etc.).
    hero_image_url : str | None
        Optional URL for the hero banner image.
        Falls back to the default hero-img.png when not supplied.
    """
    hero_img = hero_image_url or _DEFAULT_HERO_IMAGE

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f4f0f0;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}
        .wrapper {{
            width: 100%;
            padding: 40px 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 30px rgba(96, 10, 10, 0.08);
        }}

        /* ---- Header ---- */
        .header {{
            padding: 20px 30px;
            border-bottom: 1px solid #f0e8e8;
            text-align: left;
        }}
        .header img {{
            height: 36px;
            width: auto;
        }}

        /* ---- Hero banner ---- */
        .hero {{
            width: 100%;
            background-color: #fcf6f5;
            text-align: center;
        }}
        .hero img {{
            width: 100%;
            max-width: 600px;
            height: auto;
            display: block;
        }}

        /* ---- Body content ---- */
        .content {{
            padding: 40px 30px 30px;
        }}
        h1 {{
            font-size: 22px;
            font-weight: 700;
            color: #2D1614;
            margin: 0 0 14px;
        }}
        p {{
            font-size: 15px;
            line-height: 1.7;
            color: #4A3E3D;
            margin: 0 0 22px;
        }}

        /* ---- Verification code box ---- */
        .code-box {{
            background-color: #fdf5f5;
            border: 1.5px dashed #600A0A;
            border-radius: 10px;
            padding: 18px;
            text-align: center;
            font-size: 34px;
            font-weight: 700;
            letter-spacing: 6px;
            color: #600A0A;
            margin: 28px 0;
        }}

        /* ---- CTA button ---- */
        .btn {{
            display: inline-block;
            background-color: #600A0A;
            color: #ffffff !important;
            text-decoration: none;
            padding: 14px 32px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 15px;
            text-align: center;
            box-shadow: 0px -4px 8px 0px rgba(0, 0, 0, 0.15) inset,
                         0px 4px 4px 0px rgba(255, 255, 255, 0.25) inset;
            transition: opacity 0.2s ease;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}

        /* ---- Footer ---- */
        .footer {{
            background-color: #600A0A;
            padding: 36px 30px;
            text-align: left;
            color: #ffffff;
        }}
        .footer-logo {{
            margin-bottom: 18px;
        }}
        .footer-logo img {{
            height: 30px;
            width: auto;
        }}
        .footer p {{
            font-size: 12px;
            color: #e5b9b9;
            line-height: 1.6;
            margin: 0 0 8px;
        }}
        .footer-divider {{
            border: none;
            border-top: 1px solid rgba(255,255,255,0.15);
            margin: 18px 0;
        }}
        .footer-bottom {{
            font-size: 11px;
            color: #d4a0a0;
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="container">
            <!-- Header with red logo -->
            <div class="header">
                <img src="{_LOGO_RED}" alt="NEMSAS" />
            </div>

            <!-- Hero image -->
            <div class="hero">
                <img src="{hero_img}" alt="NEMSAS" />
            </div>

            <!-- Main content -->
            <div class="content">
                <h1>{title}</h1>
                <p>{message_body}</p>
                {extra_content}
            </div>

            <!-- Footer with white logo -->
            <div class="footer">
                <div class="footer-logo">
                    <img src="{_LOGO_WHITE}" alt="NEMSAS" />
                </div>
                <p>If you'd rather not receive this kind of email, you can unsubscribe or manage your email preferences.</p>
                <hr class="footer-divider" />
                <p class="footer-bottom">NEMSAS, 123, Segun Ademelegun Av. Central Business District, Abuja, Nigeria, 900001</p>
            </div>
        </div>
    </div>
</body>
</html>
"""


# ------------------------------------------------------------------
# Pre-built email helpers
# ------------------------------------------------------------------
def send_verification_email(to_email: str, name: str, code: str):
    title = "Account Verification"
    message_body = (
        f"Hello {name}, thank you for registering a partner account with NEMSAS. "
        "Please use the verification code below to verify your email address. "
        "This code is valid for 90 seconds."
    )
    extra_content = f'<div class="code-box">{code}</div>'
    html_content = get_email_template(title, message_body, extra_content)
    send_email(to_email, "Verify Your NEMSAS Partner Account", html_content)


def send_password_reset_email(to_email: str, name: str, code: str):
    title = "Password Reset"
    message_body = (
        f"Hello {name}, seems like you forgot your password for NEMSAS. "
        "If this is true, please use the reset code below to reset your password. "
        "This code is valid for 90 seconds. If you did not forget your password, "
        "you can safely ignore this email."
    )
    extra_content = f'<div class="code-box">{code}</div>'
    html_content = get_email_template(title, message_body, extra_content)
    send_email(to_email, "Reset Your NEMSAS Partner Password", html_content)

"""
Email service using SMTP2GO.

Handles sending all email types with HTML templates.
"""
import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _sanitize_header(value: str) -> str:
    """Strip characters that could enable email header injection."""
    return value.replace('\r', '').replace('\n', '')


def send_email(to: str, subject: str, html_body: str, plain_body: Optional[str] = None) -> bool:
    """
    Send an email via SMTP2GO.

    Args:
        to: Recipient email address
        subject: Email subject line
        html_body: HTML content of email
        plain_body: Optional plain text fallback (auto-generated if not provided)

    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured — skipping email to %s: %s", to, subject)
        return False

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM
        msg["To"] = _sanitize_header(to)
        msg["Subject"] = _sanitize_header(subject)

        # Plain text fallback (strip HTML tags if not provided)
        if not plain_body:
            import re
            plain_body = re.sub(r'<[^>]+>', '', html_body)

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Connect to SMTP server
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Email sent to %s: %s", to, subject)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s (%s): %s", to, subject, e, exc_info=True)
        return False


# ============================================================================
# Email Templates
# ============================================================================

def send_welcome_email(to: str, name: str, temp_password: str, login_url: str) -> bool:
    """
    Send welcome email with temporary password to new user.

    Args:
        to: User's email address
        name: User's name
        temp_password: Generated temporary password
        login_url: URL to login page

    Returns:
        True if sent successfully
    """
    subject = "Welcome to SpoolSense"

    safe_to = _escape(to)
    safe_name = _escape(name)
    safe_temp_password = _escape(temp_password)
    safe_login_url = _escape(login_url)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; padding: 0; background: #F9FAFB; font-family: Arial, sans-serif; }}
            @media (max-width: 600px) {{
                .container {{ padding: 20px 16px !important; }}
                .button {{ display: block !important; width: 100% !important; }}
            }}
        </style>
    </head>
    <body>
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #F9FAFB;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table class="container" width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 32px; text-align: center; border-bottom: 1px solid #E5E7EB;">
                                <h1 style="margin: 0; color: #4F46E5; font-size: 24px;">SpoolSense</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding: 32px;">
                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;">Hi {safe_name},</p>
                                <p style="margin: 0 0 24px 0; color: #1F2937; font-size: 16px;">Your account has been created! You can now track your 3D printing inventory, costs, and orders.</p>

                                <!-- Credentials Box -->
                                <div style="background: #EEF2FF; border: 2px solid #4F46E5; padding: 32px 24px; margin: 24px 0; border-radius: 12px; text-align: center;">
                                    <p style="margin: 0 0 8px 0; color: #6B7280; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">Your Login Credentials</p>
                                    <div style="background: white; border-radius: 8px; padding: 20px; margin: 16px 0;">
                                        <p style="margin: 0 0 4px 0; color: #6B7280; font-size: 13px;">Email</p>
                                        <p style="margin: 0 0 20px 0; color: #1F2937; font-size: 16px; font-weight: 600; word-break: break-all;">{safe_to}</p>
                                        <p style="margin: 0 0 4px 0; color: #6B7280; font-size: 13px;">Temporary Password</p>
                                        <p style="margin: 0; font-size: 18px; font-weight: 700; color: #4F46E5; font-family: monospace; letter-spacing: 1px; word-break: break-all;">{safe_temp_password}</p>
                                    </div>
                                </div>

                                <!-- Button -->
                                <table cellpadding="0" cellspacing="0" style="margin: 24px auto;">
                                    <tr>
                                        <td align="center" style="border-radius: 6px; background: #4F46E5;">
                                            <a href="{safe_login_url}" class="button" style="display: inline-block; padding: 12px 32px; color: white; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Get Started
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin: 0 0 16px 0; color: #6B7280; font-size: 14px;"><em>You'll be prompted to change your password on first login.</em></p>
                                <p style="margin: 0; color: #1F2937; font-size: 16px;">Best,<br><strong>SpoolSense</strong></p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px; text-align: center; border-top: 1px solid #E5E7EB; background: #F9FAFB;">
                                <p style="margin: 0; color: #6B7280; font-size: 14px;">SpoolSense — 3D printing inventory & cost tracking</p>
                                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 12px;">This is an automated message. Please do not reply.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return send_email(to, subject, html_body)


def send_password_reset_email(to: str, name: str, reset_url: str) -> bool:
    """
    Send password reset email with reset link.

    Args:
        to: User's email address
        name: User's name
        reset_url: URL to reset password page with token

    Returns:
        True if sent successfully
    """
    subject = "Reset Your Password — SpoolSense"

    safe_name = _escape(name)
    safe_reset_url = _escape(reset_url)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; padding: 0; background: #F9FAFB; font-family: Arial, sans-serif; }}
            @media (max-width: 600px) {{
                .container {{ padding: 20px 16px !important; }}
                .button {{ display: block !important; width: 100% !important; }}
            }}
        </style>
    </head>
    <body>
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #F9FAFB;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table class="container" width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 32px; text-align: center; border-bottom: 1px solid #E5E7EB;">
                                <h1 style="margin: 0; color: #4F46E5; font-size: 24px;">SpoolSense</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding: 32px;">
                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;">Hi {safe_name},</p>
                                <p style="margin: 0 0 24px 0; color: #1F2937; font-size: 16px;">We received a request to reset your password. Click the button below to create a new password:</p>

                                <!-- Button -->
                                <table cellpadding="0" cellspacing="0" style="margin: 24px 0;">
                                    <tr>
                                        <td align="center" style="border-radius: 6px; background: #4F46E5;">
                                            <a href="{safe_reset_url}" class="button" style="display: inline-block; padding: 12px 32px; color: white; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Reset Password
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin: 0 0 24px 0; color: #DC2626; font-weight: 600;">This link expires in 1 hour.</p>

                                <!-- Security Alert -->
                                <div style="background: #FEF2F2; border-left: 4px solid #DC2626; padding: 16px; margin: 16px 0; border-radius: 4px;">
                                    <p style="margin: 0 0 8px 0; color: #991B1B; font-weight: 600;">⚠️ Security Notice</p>
                                    <p style="margin: 0; color: #7F1D1D; font-size: 14px;">If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
                                </div>

                                <p style="margin: 0; color: #1F2937; font-size: 16px;">Best,<br><strong>SpoolSense</strong></p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px; text-align: center; border-top: 1px solid #E5E7EB; background: #F9FAFB;">
                                <p style="margin: 0; color: #6B7280; font-size: 14px;">SpoolSense — 3D printing inventory & cost tracking</p>
                                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 12px;">This is an automated message. Please do not reply.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return send_email(to, subject, html_body)


def send_device_verification_email(
    to: str,
    name: str,
    code: str,
    ip_address: str,
    user_agent: str,
    timestamp: str
) -> bool:
    """
    Send device verification email when login from new device/location detected.

    Args:
        to: User's email address
        name: User's name
        code: 6-digit verification code
        ip_address: Login IP address
        user_agent: Browser/device user agent
        timestamp: Login timestamp (formatted string)

    Returns:
        True if sent successfully
    """
    subject = "New Login Detected - Verification Required"

    # Simplify user agent for display
    ua_display = user_agent[:80] + "..." if len(user_agent) > 80 else user_agent
    safe_name = _escape(name)
    safe_ip = _escape(ip_address)
    safe_ua = _escape(ua_display)
    safe_timestamp = _escape(timestamp)
    safe_code = _escape(code)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; padding: 0; background: #F9FAFB; font-family: Arial, sans-serif; }}
            @media (max-width: 600px) {{
                .container {{ padding: 20px 16px !important; }}
            }}
        </style>
    </head>
    <body>
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #F9FAFB;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table class="container" width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 32px; text-align: center; border-bottom: 1px solid #E5E7EB;">
                                <h1 style="margin: 0; color: #4F46E5; font-size: 24px;">SpoolSense</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding: 32px;">
                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;">Hi {safe_name},</p>
                                <p style="margin: 0 0 24px 0; color: #1F2937; font-size: 16px;">We detected a login from a new device or location:</p>

                                <!-- Security Details -->
                                <div style="background: #FEF2F2; border-left: 4px solid #DC2626; padding: 16px; margin: 16px 0; border-radius: 4px;">
                                    <p style="margin: 0 0 8px 0; color: #1F2937; font-size: 14px;"><strong>IP Address:</strong> {safe_ip}</p>
                                    <p style="margin: 0 0 8px 0; color: #1F2937; font-size: 14px;"><strong>Device:</strong> {safe_ua}</p>
                                    <p style="margin: 0; color: #1F2937; font-size: 14px;"><strong>Time:</strong> {safe_timestamp}</p>
                                </div>

                                <p style="margin: 0 0 8px 0; color: #1F2937; font-size: 16px;">Enter this verification code to complete your login:</p>

                                <!-- Verification Code -->
                                <div style="background: #F9FAFB; border: 2px dashed #4F46E5; padding: 24px; margin: 24px 0; border-radius: 8px; text-align: center;">
                                    <p style="margin: 0 0 8px 0; color: #6B7280; font-size: 14px;">Your verification code:</p>
                                    <p style="margin: 0; font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #4F46E5;">{safe_code}</p>
                                </div>

                                <p style="margin: 0 0 24px 0; color: #DC2626; font-weight: 600;">This code expires in 15 minutes.</p>

                                <!-- Security Alert -->
                                <div style="background: #FEF2F2; border-left: 4px solid #DC2626; padding: 16px; margin: 16px 0; border-radius: 4px;">
                                    <p style="margin: 0 0 8px 0; color: #991B1B; font-weight: 600;">⚠️ Security Alert</p>
                                    <p style="margin: 0; color: #7F1D1D; font-size: 14px;">If this wasn't you, someone may have your password. Change your password immediately and contact support.</p>
                                </div>

                                <p style="margin: 0; color: #1F2937; font-size: 16px;">Best,<br><strong>SpoolSense</strong></p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px; text-align: center; border-top: 1px solid #E5E7EB; background: #F9FAFB;">
                                <p style="margin: 0; color: #6B7280; font-size: 14px;">SpoolSense — 3D printing inventory & cost tracking</p>
                                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 12px;">This is an automated security message. Please do not reply.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return send_email(to, subject, html_body)


def send_account_suspended_email(to: str, name: str, support_email: str) -> bool:
    """
    Send account suspended notification email.

    Args:
        to: User's email address
        name: User's name
        support_email: Support contact email

    Returns:
        True if sent successfully
    """
    subject = "Account Suspended - Action Required"

    safe_name = _escape(name)
    safe_support_email = _escape(support_email)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; padding: 0; background: #F9FAFB; font-family: Arial, sans-serif; }}
            @media (max-width: 600px) {{
                .container {{ padding: 20px 16px !important; }}
            }}
        </style>
    </head>
    <body>
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #F9FAFB;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table class="container" width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 32px; text-align: center; border-bottom: 1px solid #E5E7EB;">
                                <h1 style="margin: 0; color: #4F46E5; font-size: 24px;">SpoolSense</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding: 32px;">
                                <p style="margin: 0 0 24px 0; color: #1F2937; font-size: 16px;">Hi {safe_name},</p>

                                <!-- Alert Box -->
                                <div style="background: #FEF2F2; border-left: 4px solid #DC2626; padding: 16px; margin: 16px 0; border-radius: 4px;">
                                    <p style="margin: 0; color: #991B1B; font-weight: 600;">⚠️ Your account has been suspended due to non-payment.</p>
                                </div>

                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;">To restore access, please send payment and contact us at:</p>
                                <p style="margin: 0 0 24px 0; color: #4F46E5; font-size: 18px; font-weight: 600;">{safe_support_email}</p>

                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;">We'll reactivate your account as soon as payment is confirmed.</p>
                                <p style="margin: 0; color: #1F2937; font-size: 16px;">Best,<br><strong>SpoolSense</strong></p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px; text-align: center; border-top: 1px solid #E5E7EB; background: #F9FAFB;">
                                <p style="margin: 0; color: #6B7280; font-size: 14px;">SpoolSense — 3D printing inventory & cost tracking</p>
                                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 12px;">This is an automated message. Please contact support for assistance.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return send_email(to, subject, html_body)


def send_payment_reminder_email(to: str, name: str, amount: float, currency: str = "USD") -> bool:
    """
    Send monthly subscription payment reminder email.

    Args:
        to: User's email address
        name: User's name
        amount: Subscription amount
        currency: Currency code (default: USD)

    Returns:
        True if sent successfully
    """
    subject = "Monthly Subscription Due — SpoolSense"

    safe_name = _escape(name)
    safe_currency = _escape(currency)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; padding: 0; background: #F9FAFB; font-family: Arial, sans-serif; }}
            @media (max-width: 600px) {{
                .container {{ padding: 20px 16px !important; }}
            }}
        </style>
    </head>
    <body>
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #F9FAFB;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table class="container" width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 32px; text-align: center; border-bottom: 1px solid #E5E7EB;">
                                <h1 style="margin: 0; color: #4F46E5; font-size: 24px;">SpoolSense</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding: 32px;">
                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;">Hi {safe_name},</p>
                                <p style="margin: 0 0 24px 0; color: #1F2937; font-size: 16px;">Your monthly subscription to SpoolSense is due:</p>

                                <!-- Amount Display -->
                                <div style="background: #F9FAFB; border: 2px dashed #4F46E5; padding: 24px; margin: 24px 0; border-radius: 8px; text-align: center;">
                                    <p style="margin: 0; font-size: 36px; font-weight: 700; color: #4F46E5;">${amount:.2f} {safe_currency}</p>
                                </div>

                                <!-- Payment Info -->
                                <div style="background: #F9FAFB; border-left: 4px solid #4F46E5; padding: 16px; margin: 16px 0; border-radius: 4px;">
                                    <p style="margin: 0 0 8px 0; color: #1F2937; font-weight: 600;">Payment Methods:</p>
                                    <p style="margin: 0 0 4px 0; color: #1F2937; font-size: 14px;">• Venmo: @yourhandle</p>
                                    <p style="margin: 0; color: #1F2937; font-size: 14px;">• CashApp: $yourhandle</p>
                                </div>

                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;"><strong>Please reply to this email once payment is sent to confirm.</strong></p>
                                <p style="margin: 0 0 16px 0; color: #6B7280; font-size: 14px;">Thanks for using SpoolSense! Your support keeps this service running.</p>
                                <p style="margin: 0; color: #1F2937; font-size: 16px;">Best,<br><strong>SpoolSense</strong></p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px; text-align: center; border-top: 1px solid #E5E7EB; background: #F9FAFB;">
                                <p style="margin: 0; color: #6B7280; font-size: 14px;">SpoolSense — 3D printing inventory & cost tracking</p>
                                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 12px;">Questions about billing? Reply to this email.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return send_email(to, subject, html_body)


def send_email_change_verification_email(to: str, name: str, confirm_url: str) -> bool:
    """
    Send email address change verification email to the new address.

    Args:
        to: New email address to verify
        name: User's display name
        confirm_url: URL with token to confirm the change

    Returns:
        True if sent successfully
    """
    subject = "Confirm Your New Email Address — SpoolSense"

    safe_name = _escape(name)
    safe_confirm_url = _escape(confirm_url)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin: 0; padding: 0; background: #F9FAFB; font-family: Arial, sans-serif; }}
            @media (max-width: 600px) {{
                .container {{ padding: 20px 16px !important; }}
                .button {{ display: block !important; width: 100% !important; }}
            }}
        </style>
    </head>
    <body>
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #F9FAFB;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table class="container" width="600" cellpadding="0" cellspacing="0" style="background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 32px; text-align: center; border-bottom: 1px solid #E5E7EB;">
                                <h1 style="margin: 0; color: #4F46E5; font-size: 24px;">SpoolSense</h1>
                            </td>
                        </tr>
                        <!-- Body -->
                        <tr>
                            <td style="padding: 32px;">
                                <p style="margin: 0 0 16px 0; color: #1F2937; font-size: 16px;">Hi {safe_name},</p>
                                <p style="margin: 0 0 24px 0; color: #1F2937; font-size: 16px;">
                                    A request was made to change your SpoolSense account email to this address.
                                    Click the button below to confirm the change.
                                </p>

                                <!-- Button -->
                                <table cellpadding="0" cellspacing="0" style="margin: 24px 0;">
                                    <tr>
                                        <td align="center" style="border-radius: 6px; background: #4F46E5;">
                                            <a href="{safe_confirm_url}" class="button" style="display: inline-block; padding: 12px 32px; color: white; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Confirm New Email
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin: 0 0 24px 0; color: #DC2626; font-weight: 600;">This link expires in 1 hour.</p>

                                <!-- Security Alert -->
                                <div style="background: #FEF2F2; border-left: 4px solid #DC2626; padding: 16px; margin: 16px 0; border-radius: 4px;">
                                    <p style="margin: 0 0 8px 0; color: #991B1B; font-weight: 600;">&#x26A0;&#xFE0F; Security Notice</p>
                                    <p style="margin: 0; color: #7F1D1D; font-size: 14px;">
                                        If you did not request an email change, please ignore this email.
                                        Your account email will remain unchanged.
                                    </p>
                                </div>

                                <p style="margin: 0; color: #1F2937; font-size: 16px;">Best,<br><strong>SpoolSense</strong></p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px; text-align: center; border-top: 1px solid #E5E7EB; background: #F9FAFB;">
                                <p style="margin: 0; color: #6B7280; font-size: 14px;">SpoolSense — 3D printing inventory & cost tracking</p>
                                <p style="margin: 8px 0 0 0; color: #9CA3AF; font-size: 12px;">This is an automated message. Please do not reply.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return send_email(to, subject, html_body)

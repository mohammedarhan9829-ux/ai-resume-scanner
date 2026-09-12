import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("EmailService")

SENDER_EMAIL = os.environ.get("SENDER_GMAIL", "mohammedarhan9829@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")


def send_otp_email(recipient_gmail: str, otp_code: str, candidate_name: str = "Candidate") -> bool:
    """
    Send a 6-digit password reset verification OTP code to candidate's Gmail address via SMTP.
    Sender: mohammedarhan9829@gmail.com
    """
    sender = SENDER_EMAIL
    app_password = GMAIL_APP_PASSWORD

    subject = f"🔐 ResuMatch AI - Password Reset OTP Verification Code: {otp_code}"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 550px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #334155;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #38bdf8; margin: 0;">ResuMatch <span style="background: #6366f1; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 14px;">AI 2.0</span></h2>
            <p style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Multi-Stream Resume Parser & Placement Suite</p>
        </div>

        <div style="background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #475569;">
            <h3 style="color: #f1f5f9; margin-top: 0;">Hello {candidate_name},</h3>
            <p style="color: #cbd5e1; font-size: 15px; line-height: 1.5;">
                We received a request to reset your password. Your 6-digit OTP verification code is:
            </p>

            <div style="text-align: center; margin: 25px 0;">
                <span style="font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #fbbf24; background: #0f172a; padding: 12px 24px; border-radius: 8px; border: 2px dashed #f59e0b; display: inline-block;">
                    {otp_code}
                </span>
            </div>

            <p style="color: #94a3b8; font-size: 13px;">
                ⚠️ This OTP code is valid for <strong>10 minutes</strong>. If you did not request a password reset, please ignore this message.
            </p>
        </div>

        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #64748b;">
            <p>Official Technical Support: <a href="mailto:mohammedarhan9829@gmail.com" style="color: #38bdf8; text-decoration: none;">mohammedarhan9829@gmail.com</a></p>
            <p>&copy; 2026 ResuMatch AI Career Engine. All rights reserved.</p>
        </div>
    </div>
    """

    if not app_password:
        logger.warning(f"GMAIL_APP_PASSWORD env var not configured. OTP delivery logged for {recipient_gmail} with code {otp_code}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ResuMatch AI Support <{sender}>"
        msg["To"] = recipient_gmail

        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(sender, app_password)
            server.sendmail(sender, recipient_gmail, msg.as_string())

        logger.info(f"Successfully sent OTP email to {recipient_gmail} from {sender}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email via SMTP to {recipient_gmail}: {e}", exc_info=True)
        return False

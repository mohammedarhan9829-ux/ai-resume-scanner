import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("EmailService")

SENDER_EMAIL = os.environ.get("SENDER_GMAIL", "mohammedarhan9829@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "jqyghbiepedmlhad").replace(" ", "")


def get_smtp_connection():
    """Establish authenticated connection to Gmail SMTP server (Port 587 TLS with Port 465 SSL fallback)."""
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        return server
    except Exception as e:
        logger.warning(f"SMTP Port 587 TLS connection failed ({e}). Attempting Port 465 SSL fallback...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        return server


def send_welcome_email(recipient_gmail: str, candidate_name: str = "Candidate") -> bool:
    """
    Send an automated HTML Welcome Email to new candidates joining ResuMatch AI 2.0.
    Sent FROM: mohammedarhan9829@gmail.com TO: candidate's registered Gmail (with admin copy).
    """
    sender = SENDER_EMAIL
    subject = f"🎉 Welcome to ResuMatch AI 2.0, {candidate_name}!"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 28px; border-radius: 14px; border: 1px solid #334155;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #38bdf8; margin: 0; font-size: 26px;">ResuMatch <span style="background: linear-gradient(135deg, #6366f1, #a855f7); color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 16px;">AI 2.0</span></h1>
            <p style="color: #94a3b8; font-size: 14px; margin-top: 6px;">Universal Resume Parser & Multi-Stream Placement Suite</p>
        </div>

        <div style="background: #1e293b; padding: 24px; border-radius: 10px; border: 1px solid #475569;">
            <h2 style="color: #f1f5f9; margin-top: 0; font-size: 20px;">Welcome to the Platform, {candidate_name}! 👋</h2>
            <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6;">
                Thank you for creating your account with <strong>{recipient_gmail}</strong>. You now have <strong>100% Free & Unlimited Access</strong> to our entire AI placement career intelligence suite across all academic streams (Tech, Engineering, Business, Commerce, Design & Healthcare).
            </p>

            <div style="margin: 20px 0; background: #0f172a; padding: 16px; border-radius: 8px; border-left: 4px solid #10b981;">
                <h4 style="color: #34d399; margin: 0 0 10px 0; font-size: 15px;">🚀 What You Can Do Now:</h4>
                <ul style="color: #e2e8f0; font-size: 14px; margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li>📄 <strong>Upload Resume</strong> in PDF, JPG, or PNG format for instant NLP skill gap analysis.</li>
                    <li>📚 <strong>Download OpenAI PDF Study Notes</strong> for high-priority missing skills.</li>
                    <li>⏱️ <strong>Take Timed 10-Q Placement Mock Interview Tests</strong> tailored to your specific field.</li>
                    <li>✍️ <strong>AI Bullet Point ATS Rewriter</strong> to optimize your resume bullet points for ATS scanners.</li>
                </ul>
            </div>

            <div style="text-align: center; margin-top: 24px;">
                <a href="https://ai-resume-scanner-439j.onrender.com" style="background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #ffffff; padding: 12px 28px; border-radius: 50px; font-weight: 700; text-decoration: none; display: inline-block; font-size: 15px;">
                    ⚡ Start Scanning Your Resume Now
                </a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 24px; font-size: 12px; color: #64748b; border-top: 1px solid #334155; padding-top: 16px;">
            <p>Need help or have questions? Contact Official Support: <a href="mailto:mohammedarhan9829@gmail.com" style="color: #38bdf8; text-decoration: none;">mohammedarhan9829@gmail.com</a></p>
            <p>&copy; 2026 ResuMatch AI Career Engine. All rights reserved.</p>
        </div>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ResuMatch AI Support <{sender}>"
        msg["To"] = recipient_gmail
        msg.attach(MIMEText(html_content, "html"))

        recipients = list(set([recipient_gmail, sender]))

        server = get_smtp_connection()
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()

        logger.info(f"Welcome email sent from {sender} to candidate {recipient_gmail} (and admin copy)")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {recipient_gmail}: {e}", exc_info=True)
        return False


def send_login_notification_email(recipient_gmail: str, candidate_name: str = "Candidate") -> bool:
    """
    Send an automated Login Notification Email FROM mohammedarhan9829@gmail.com TO candidate's registered Gmail.
    """
    sender = SENDER_EMAIL
    subject = f"🔔 ResuMatch AI - Account Login Alert for {candidate_name}"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 550px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #334155;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #38bdf8; margin: 0;">ResuMatch <span style="background: #6366f1; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 14px;">AI 2.0</span></h2>
        </div>

        <div style="background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #475569;">
            <h3 style="color: #f1f5f9; margin-top: 0;">Hello {candidate_name},</h3>
            <p style="color: #cbd5e1; font-size: 15px; line-height: 1.5;">
                A new login was recorded for your registered account: <strong>{recipient_gmail}</strong>.
            </p>
            <div style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); padding: 12px; border-radius: 6px; color: #7dd3fc; margin: 15px 0; font-size: 14px;">
                🔑 Login Activity: Successfully authenticated on ResuMatch AI Platform.
            </div>
            <p style="color: #94a3b8; font-size: 13px;">
                If you did not perform this login, please change your password immediately or contact support at <a href="mailto:mohammedarhan9829@gmail.com" style="color: #38bdf8;">mohammedarhan9829@gmail.com</a>.
            </p>
        </div>

        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #64748b;">
            <p>Support: mohammedarhan9829@gmail.com &copy; 2026 ResuMatch AI</p>
        </div>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ResuMatch AI Support <{sender}>"
        msg["To"] = recipient_gmail
        msg.attach(MIMEText(html_content, "html"))

        recipients = list(set([recipient_gmail, sender]))

        server = get_smtp_connection()
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()

        logger.info(f"Login notification email sent from {sender} to {recipient_gmail}")
        return True
    except Exception as e:
        logger.error(f"Failed to send login notification to {recipient_gmail}: {e}", exc_info=True)
        return False


def send_password_reset_confirmation_email(recipient_gmail: str, candidate_name: str = "Candidate") -> bool:
    """
    Send an HTML confirmation email when password reset is completed.
    Sent FROM: mohammedarhan9829@gmail.com TO: candidate's registered Gmail.
    """
    sender = SENDER_EMAIL
    subject = "🔐 ResuMatch AI - Password Reset Successful"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 550px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #334155;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #38bdf8; margin: 0;">ResuMatch <span style="background: #6366f1; color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 14px;">AI 2.0</span></h2>
        </div>

        <div style="background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #475569;">
            <h3 style="color: #f1f5f9; margin-top: 0;">Hello {candidate_name},</h3>
            <p style="color: #cbd5e1; font-size: 15px; line-height: 1.5;">
                Your password for <strong>{recipient_gmail}</strong> has been <strong>successfully updated</strong>.
            </p>
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 12px; border-radius: 6px; color: #a7f3d0; margin: 15px 0; font-size: 14px;">
                ✅ Security Alert: You can now log into your account using your new password.
            </div>
            <p style="color: #94a3b8; font-size: 13px;">
                If you did not perform this password change, please contact technical support immediately at <a href="mailto:mohammedarhan9829@gmail.com" style="color: #38bdf8;">mohammedarhan9829@gmail.com</a>.
            </p>
        </div>

        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #64748b;">
            <p>&copy; 2026 ResuMatch AI Career Engine. Sender & Support: mohammedarhan9829@gmail.com</p>
        </div>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ResuMatch AI Support <{sender}>"
        msg["To"] = recipient_gmail
        msg.attach(MIMEText(html_content, "html"))

        recipients = list(set([recipient_gmail, sender]))

        server = get_smtp_connection()
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()

        logger.info(f"Password reset confirmation email sent from {sender} to {recipient_gmail}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset confirmation to {recipient_gmail}: {e}", exc_info=True)
        return False


def send_otp_email(recipient_gmail: str, otp_code: str, candidate_name: str = "Candidate") -> bool:
    """
    Send a 6-digit password reset verification OTP code to candidate's Gmail via SMTP.
    Sent FROM: mohammedarhan9829@gmail.com TO: candidate's registered Gmail.
    """
    sender = SENDER_EMAIL
    subject = "🔐 ResuMatch AI - Your 6-Digit Password Reset OTP Code"

    plain_text = f"Hello {candidate_name},\n\nYour 6-digit OTP verification code for ResuMatch AI is: {otp_code}\n\nThis code is valid for 10 minutes.\nIf you did not request this, please ignore this email.\n\nSupport: mohammedarhan9829@gmail.com"

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
            <p>Official Support & Sender: <a href="mailto:mohammedarhan9829@gmail.com" style="color: #38bdf8; text-decoration: none;">mohammedarhan9829@gmail.com</a></p>
            <p>&copy; 2026 ResuMatch AI Career Engine. All rights reserved.</p>
        </div>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ResuMatch AI Support <{sender}>"
        msg["To"] = recipient_gmail
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        recipients = list(set([recipient_gmail, sender]))

        server = get_smtp_connection()
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()

        logger.info(f"Successfully sent OTP email from {sender} to candidate {recipient_gmail}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email via SMTP to {recipient_gmail}: {e}", exc_info=True)
        return False

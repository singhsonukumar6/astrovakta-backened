import os
import logging

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "AstroVakta <noreply@astrovakta.com>")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://astrovakta.com")

_resend_client = None


def _get_resend():
    global _resend_client
    if _resend_client is None:
        if not RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not set — emails will not be sent")
            return None
        import resend
        resend.api_key = RESEND_API_KEY
        _resend_client = resend
    return _resend_client


def _send_html(to: str, subject: str, html: str) -> bool:
    r = _get_resend()
    if not r:
        logger.warning(f"Email not sent (no Resend client): {subject} -> {to}")
        return False
    try:
        params: r.Emails.SendParams = {
            "from": RESEND_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        result = r.Emails.send(params)
        logger.info(f"Email sent: {subject} -> {to} (id={result.get('id', '?')})")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


def send_verification_email(email: str, token: str, name: str = "") -> bool:
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    display_name = name or email.split("@")[0]
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; padding: 40px 24px; background: #0a0a1a; color: #e2e8f0;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 28px; font-weight: 800; margin: 0; background: linear-gradient(135deg, #7c3aed, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          AstroVakta
        </h1>
      </div>
      <div style="background: #1a1a3e; border-radius: 16px; padding: 32px; border: 1px solid rgba(124,58,237,0.2);">
        <h2 style="font-size: 22px; font-weight: 700; margin: 0 0 16px;">Verify your email</h2>
        <p style="color: #94a3b8; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
          Hi {display_name},<br><br>
          Welcome to AstroVakta! Please verify your email address to activate your account and start exploring the cosmos.
        </p>
        <a href="{verify_url}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #6d28d9); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-weight: 600; font-size: 15px;">
          Verify Email Address
        </a>
        <p style="color: #64748b; font-size: 13px; line-height: 1.6; margin: 24px 0 0;">
          This link expires in 24 hours. If you didn't create an account, you can safely ignore this email.
        </p>
      </div>
      <p style="color: #475569; font-size: 12px; text-align: center; margin-top: 24px;">
        AstroVakta — Vedic Astrology API
      </p>
    </div>
    """
    return _send_html(email, "Verify your AstroVakta account", html)


def send_password_reset_email(email: str, token: str, name: str = "") -> bool:
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    display_name = name or email.split("@")[0]
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; padding: 40px 24px; background: #0a0a1a; color: #e2e8f0;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 28px; font-weight: 800; margin: 0; background: linear-gradient(135deg, #7c3aed, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          AstroVakta
        </h1>
      </div>
      <div style="background: #1a1a3e; border-radius: 16px; padding: 32px; border: 1px solid rgba(124,58,237,0.2);">
        <h2 style="font-size: 22px; font-weight: 700; margin: 0 0 16px;">Reset your password</h2>
        <p style="color: #94a3b8; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
          Hi {display_name},<br><br>
          We received a request to reset your password. Click the button below to set a new one.
        </p>
        <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #dc2626, #b91c1c); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 10px; font-weight: 600; font-size: 15px;">
          Reset Password
        </a>
        <p style="color: #64748b; font-size: 13px; line-height: 1.6; margin: 24px 0 0;">
          This link expires in 1 hour. If you didn't request a password reset, you can safely ignore this email.
        </p>
      </div>
      <p style="color: #475569; font-size: 12px; text-align: center; margin-top: 24px;">
        AstroVakta — Vedic Astrology API
      </p>
    </div>
    """
    return _send_html(email, "Reset your AstroVakta password", html)

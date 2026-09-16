import html
import os
import logging
from datetime import datetime
from email.utils import parseaddr

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


def _send_html(to: str, subject: str, html_body: str, from_display: str = "", reply_to: str = "") -> bool:
    r = _get_resend()
    if not r:
        logger.warning(f"Email not sent (no Resend client): {subject} -> {to}")
        return False
    try:
        params: r.Emails.SendParams = {
            "from": from_display or RESEND_FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html_body,
        }
        if reply_to:
            params["reply_to"] = reply_to
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


# ═══════════════════════════════════════════════
#  White-label booking notifications (tenant websites)
#
#  Every email is branded as the astrologer's site — their name, colors, logo,
#  contact details. AstroVakta is never mentioned: the sending address only
#  borrows the platform's verified domain, with the site's name as the display
#  name and replies routed to the astrologer.
# ═══════════════════════════════════════════════

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _verified_from_address() -> str:
    return parseaddr(RESEND_FROM_EMAIL)[1] or RESEND_FROM_EMAIL


def _fmt_booking_date(iso: str) -> str:
    try:
        d = datetime.strptime(str(iso)[:10], "%Y-%m-%d")
        return f"{_WEEKDAYS[d.weekday()]}, {d.day} {_MONTHS[d.month - 1]} {d.year}"
    except Exception:
        return str(iso or "")


def _fmt_booking_time(t: str) -> str:
    try:
        h, m = str(t)[:5].split(":")
        h, m = int(h), int(m)
        return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"
    except Exception:
        return str(t or "")


def _site_url(site: dict) -> str:
    if site.get("custom_domain"):
        return f"https://{site['custom_domain']}"
    return f"https://{site.get('slug', '')}.astrovakta.com"


def _payment_note(site: dict) -> str:
    mode = (site.get("settings") or {}).get("paymentsMode") or "later"
    if mode == "upi" and (site.get("settings") or {}).get("upiId"):
        return f"Pay via UPI: {(site['settings']).get('upiId')}"
    if mode == "razorpay":
        return "You will receive a secure online payment link."
    return "No advance payment — pay at your appointment."


def _duration_minutes(booking: dict, service: dict | None) -> int:
    try:
        fmt = "%H:%M"
        start = datetime.strptime(str(booking.get("start_time"))[:5], fmt)
        end = datetime.strptime(str(booking.get("end_time"))[:5], fmt)
        return max(0, int((end - start).total_seconds() // 60))
    except Exception:
        return (service or {}).get("duration_minutes") or 30


def _booking_shell(site: dict, accent: str, heading: str, body: str, footer_hint: str = "") -> str:
    """White-label email frame: the astrologer's brand only — no platform mention."""
    raw_name = (site.get("name") or "Astrologer").strip()
    name = html.escape(raw_name)
    initial = html.escape(raw_name[:1].upper())
    logo = site.get("logo_url")
    if logo:
        logo_html = (f'<img src="{html.escape(logo)}" alt="{name}" width="52" height="52" '
                     f'style="border-radius: 12px; object-fit: cover; display: inline-block;" />')
    else:
        logo_html = ""
    avatar_html = (f'<div style="width:52px;height:52px;border-radius:12px;background:{accent};'
                   f'color:#ffffff;font-size:22px;font-weight:800;line-height:52px;text-align:center;'
                   f'display:inline-block;">{initial}</div>')
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8" /></head><body style="margin:0;padding:0;background:#f4f4f7;">
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:#f4f4f7;padding:32px 16px;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e6e6ef;">
    <div style="text-align:center;padding:28px 24px 8px;">
      {logo_html if logo else avatar_html}
      <div style="font-size:18px;font-weight:800;color:#18181b;margin-top:10px;">{name}</div>
      {f'<div style="font-size:12.5px;color:#71717a;margin-top:2px;">{html.escape(site.get("tagline") or "")}</div>' if site.get("tagline") else ''}
    </div>
    <div style="padding:20px 32px 8px;">
      <div style="font-size:20px;font-weight:800;color:{accent};text-align:center;margin:8px 0 18px;">{heading}</div>
      {body}
    </div>
    <div style="padding:18px 32px 28px;text-align:center;">
      <p style="font-size:12.5px;color:#a1a1aa;margin:0;line-height:1.7;">
        {footer_hint or f"Questions? Just reply to this email — {name} will get back to you."}
      </p>
    </div>
  </div>
  <div style="max-width:560px;margin:14px auto 0;text-align:center;">
    <a href="{html.escape(_site_url(site))}" style="font-size:12px;color:#a1a1aa;text-decoration:none;">{_site_url(site).replace('https://', '')}</a>
  </div>
</div>
</body></html>"""


def _detail_table(rows: list[tuple[str, str]], accent: str) -> str:
    trs = "".join(
        f'<tr>'
        f'<td style="padding:9px 0;font-size:13.5px;color:#71717a;vertical-align:top;white-space:nowrap;padding-right:18px;">{label}</td>'
        f'<td style="padding:9px 0;font-size:13.5px;color:#18181b;font-weight:600;line-height:1.55;">{value}</td>'
        f'</tr>'
        for label, value in rows
    )
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="background:#fafafc;border:1px solid #ececf3;border-radius:12px;padding:6px 18px;">{trs}</table>')


def send_booking_confirmation_to_client(site: dict, booking: dict, service: dict | None = None) -> bool:
    """White-label confirmation to the client: full booking details in the
    astrologer's branding, replies routed to the astrologer."""
    to = booking.get("client_email")
    if not to:
        return False
    accent = (site.get("theme") or {}).get("primaryColor") or "#4f46e5"
    site_name = site.get("name") or "the astrologer"
    reply_to = (site.get("settings") or {}).get("email") or ""
    esc = html.escape
    service_name = esc((service or {}).get("name") or "Consultation")
    amount = booking.get("amount") or 0
    duration = _duration_minutes(booking, service)
    rows = _detail_table([
        ("Service", service_name),
        ("Date", esc(_fmt_booking_date(booking.get("date")))),
        ("Time", f"{esc(_fmt_booking_time(booking.get('start_time')))} &ndash; {esc(_fmt_booking_time(booking.get('end_time')))} ({duration} min)"),
        ("Reference", f"#{booking.get('id', '')}"),
        ("Amount", f"&#8377;{amount}" if amount else "Free"),
        ("Payment", esc(_payment_note(site))),
    ], accent)
    contact_bits = []
    settings = site.get("settings") or {}
    if settings.get("phone"):
        contact_bits.append(f"Phone / WhatsApp: <b>{esc(settings['phone'])}</b>")
    if settings.get("email"):
        contact_bits.append(f"Email: <b>{esc(settings['email'])}</b>")
    if settings.get("city"):
        contact_bits.append(esc(settings["city"]))
    contact_html = (f'<p style="font-size:13.5px;color:#52525b;line-height:2;margin:18px 0 0;">'
                    f'{" &nbsp;·&nbsp; ".join(contact_bits)}</p>') if contact_bits else ""
    client_name = esc((booking.get("client_name") or "").split(" ")[0] or "there")
    body = f"""
      <p style="font-size:14.5px;color:#3f3f46;line-height:1.7;margin:0 0 16px;">
        Namaste {client_name}, your appointment is confirmed. Here are your booking details:
      </p>
      {rows}
      {contact_html}
      <p style="font-size:13px;color:#71717a;line-height:1.7;margin:18px 0 0;">
        Need to reschedule or cancel? Manage your bookings anytime in your account on our website.
      </p>
    """
    subject = f"Your consultation with {site_name} is confirmed — {_fmt_booking_date(booking.get('date'))}"
    return _send_html(to, subject, _booking_shell(site, accent, "Consultation Confirmed", body),
                      from_display=f"{site_name} <{_verified_from_address()}>", reply_to=reply_to)


def send_booking_alert_to_owner(site: dict, booking: dict, service: dict | None = None,
                                owner_email: str = "") -> bool:
    """New-booking alert to the astrologer with the client's details."""
    if not owner_email:
        return False
    accent = (site.get("theme") or {}).get("primaryColor") or "#4f46e5"
    esc = html.escape
    service_name = esc((service or {}).get("name") or "Consultation")
    notes = booking.get("notes")
    amount = booking.get("amount") or 0
    rows = _detail_table([
        ("Client", esc(booking.get("client_name") or "—")),
        ("Email", esc(booking.get("client_email") or "—")),
        ("Phone", esc(booking.get("client_phone") or "—")),
        ("Service", service_name),
        ("Date", esc(_fmt_booking_date(booking.get("date")))),
        ("Time", f"{esc(_fmt_booking_time(booking.get('start_time')))} &ndash; {esc(_fmt_booking_time(booking.get('end_time')))}"),
        ("Amount", f"&#8377;{amount}" if amount else "Free"),
    ], accent)
    notes_html = ""
    if notes:
        notes_html = (f'<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;'
                      f'padding:12px 16px;margin-top:14px;font-size:13px;color:#7c2d12;line-height:1.6;">'
                      f'<b>Client notes:</b><br>{esc(notes)}</div>')
    body = f"""
      <p style="font-size:14.5px;color:#3f3f46;line-height:1.7;margin:0 0 16px;">
        You have a new booking on your website:
      </p>
      {rows}
      {notes_html}
    """
    site_name = site.get("name") or "your site"
    subject = f"New booking: {booking.get('client_name', 'Client')} — {_fmt_booking_date(booking.get('date'))} at {_fmt_booking_time(booking.get('start_time'))}"
    # Reply goes straight to the client so the astrologer can confirm in one tap.
    return _send_html(owner_email, subject, _booking_shell(
        site, accent, "New Booking Received", body,
        footer_hint=f"Reply directly to this email to reach {html.escape((booking.get('client_name') or 'the client').split(' ')[0])}."),
                      from_display=f"{site_name} <{_verified_from_address()}>",
                      reply_to=booking.get("client_email") or "")


def send_booking_emails(site: dict, booking: dict, service: dict | None = None,
                        notify_owner: bool = True) -> dict:
    """Send the white-label booking notifications: confirmation to the client
    and a new-booking alert to the astrologer. Best-effort — failures never
    break the booking. Returns which emails were sent."""
    from .database import get_db

    results = {"client": None, "owner": None}
    try:
        results["client"] = send_booking_confirmation_to_client(site, booking, service)
    except Exception as e:
        logger.error(f"Client booking email failed: {e}")

    if not notify_owner:
        return results
    settings = site.get("settings") or {}
    if settings.get("bookingAlerts") is False:
        return results

    try:
        recipients = []
        from .tenants import _convert
        owner_row = get_db().execute(
            _convert("SELECT email FROM users WHERE id = ?"), (site.get("user_id"),)
        ).fetchone()
        owner_email = (owner_row[0] if not isinstance(owner_row, dict) else owner_row.get("email")) if owner_row else None
        client_email = booking.get("client_email")
        for candidate in (settings.get("email"), owner_email):
            if candidate and candidate not in recipients and candidate != client_email:
                recipients.append(candidate)
        sent = [send_booking_alert_to_owner(site, booking, service, email) for email in recipients]
        results["owner"] = any(sent)
    except Exception as e:
        logger.error(f"Owner booking email failed: {e}")
    return results


# ═══════════════════════════════════════════════
#  White-label invoice email (tenant → their client)
# ═══════════════════════════════════════════════

def invoice_url(invoice: dict) -> str:
    """Public shareable link for an invoice — served by the frontend."""
    base = os.getenv("TENANT_APP_URL") or FRONTEND_URL
    return f"{base.rstrip('/')}/invoice/{invoice.get('token', '')}"


def send_invoice_email(site: dict, invoice: dict, client: dict) -> bool:
    """White-label 'invoice from your astrologer' email with a link to the
    online invoice. Replies route to the astrologer."""
    to = client.get("email") or invoice.get("client_email")
    if not to:
        return False
    accent = (site.get("theme") or {}).get("primaryColor") or "#4f46e5"
    site_name = site.get("name") or "your astrologer"
    esc = html.escape
    total = invoice.get("total") or 0
    currency = invoice.get("currency") or "INR"
    symbol = "&#8377;" if currency == "INR" else ""
    url = invoice_url(invoice)
    client_name = esc((client.get("name") or "there").split(" ")[0])
    due = esc(_fmt_booking_date(invoice.get("due_date"))) if invoice.get("due_date") else "at your convenience"
    items_summary = "".join(
        f'<li style="margin: 4px 0;">{esc(it.get("name", ""))} &times; {it.get("qty", 1)}</li>'
        for it in (invoice.get("items") or [])[:5]
    )
    extra = ""
    if len(invoice.get("items") or []) > 5:
        extra = f'<li style="color:#71717a;">+ {len(invoice["items"]) - 5} more</li>'
    body = f"""
      <p style="font-size:14.5px;color:#3f3f46;line-height:1.7;margin:0 0 16px;">
        Hi {client_name}, {esc(site_name)} has sent you an invoice.
      </p>
      <div style="background:#fafafc;border:1px solid #ececf3;border-radius:12px;padding:16px 18px;margin-bottom:18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
          <div>
            <div style="font-size:12.5px;color:#71717a;font-weight:600;">Invoice {esc(invoice.get("number", ""))}</div>
            <div style="font-size:20px;font-weight:800;color:#18181b;margin-top:2px;">{symbol}{total}</div>
          </div>
          <div style="font-size:12.5px;color:#71717a;">Due {due}</div>
        </div>
        <ul style="margin:12px 0 0;padding-left:18px;font-size:13px;color:#52525b;">{items_summary}{extra}</ul>
      </div>
      <div style="text-align:center;">
        <a href="{esc(url)}" style="display:inline-block;background:{accent};color:#ffffff;text-decoration:none;padding:13px 30px;border-radius:10px;font-weight:700;font-size:14.5px;">View Invoice</a>
      </div>
      <p style="font-size:13px;color:#71717a;line-height:1.7;margin:18px 0 0;">
        The link opens the full invoice with payment details. Questions? Just reply to this email.
      </p>
    """
    subject = f"Invoice {invoice.get('number', '')} from {site_name} — {symbol}{total}"
    return _send_html(to, subject, _booking_shell(site, accent, "Invoice", body),
                      from_display=f"{site_name} <{_verified_from_address()}>",
                      reply_to=(site.get("settings") or {}).get("email") or "")

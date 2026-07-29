import os
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "deckstation-fallback-secret-key")

# ─── EMAIL CONFIG ───────────────────────────────────────
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVERS = [
    os.getenv("EMAIL_RECEIVER_1"),
    os.getenv("EMAIL_RECEIVER_2"),
]

# ─── GOOGLE CALENDAR ────────────────────────────────────
CALENDAR_ENABLED = False
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    SERVICE_ACCOUNT_FILE = "credentials.json"

    if os.path.exists(SERVICE_ACCOUNT_FILE):
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        calendar_service = build("calendar", "v3", credentials=credentials)
        CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        CALENDAR_ENABLED = True
        print("[✓] Google Calendar API active")
    else:
        print("[!] credentials.json not found. Google Calendar disabled.")
except ImportError:
    print("[!] google-api-python-client not installed. Google Calendar disabled.")
except Exception as e:
    print(f"[!] Failed to init Google Calendar: {e}")


# ─── HELPERS ─────────────────────────────────────────────

def send_email_booking(data: dict) -> bool:
    """Send booking email to all receivers via SMTP Gmail."""
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("[!] EMAIL_SENDER or EMAIL_PASSWORD not configured")
        return False

    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    subject = f"[New Booking] {data.get('layanan', 'N/A')} — {data.get('nama', 'N/A')}"

    html = f"""
    <html>
    <body style="font-family:Inter,sans-serif;background:#f4f4f4;padding:30px;">
        <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;padding:30px;border:1px solid #ddd;">
            <h2 style="color:#000;margin:0 0 20px 0;">🎧 New Booking — DeckStation.id</h2>
            <table style="width:100%;border-collapse:collapse;">
                <tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:700;">Name</td>
                    <td style="padding:10px;border-bottom:1px solid #eee;">{data.get('nama', '—')}</td></tr>
                <tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:700;">WhatsApp</td>
                    <td style="padding:10px;border-bottom:1px solid #eee;">{data.get('wa', '—')}</td></tr>
                <tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:700;">Service</td>
                    <td style="padding:10px;border-bottom:1px solid #eee;">{data.get('layanan', '—')}</td></tr>
                <tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:700;">Issue</td>
                    <td style="padding:10px;border-bottom:1px solid #eee;">{data.get('keluhan', '—')}</td></tr>
                <tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:700;">Pickup Address</td>
                    <td style="padding:10px;border-bottom:1px solid #eee;">{data.get('alamat', '—')}</td></tr>
                <tr><td style="padding:10px;border-bottom:1px solid #eee;font-weight:700;">Date</td>
                    <td style="padding:10px;border-bottom:1px solid #eee;">{data.get('tanggal', '—')}</td></tr>
                <tr><td style="padding:10px;font-weight:700;">Booking Time</td>
                    <td style="padding:10px;">{now}</td></tr>
            </table>
            <p style="margin-top:25px;font-size:13px;color:#888;">
                This email was sent automatically from the DeckStation.id booking system
            </p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(r for r in EMAIL_RECEIVERS if r)
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            for receiver in EMAIL_RECEIVERS:
                if receiver:
                    server.sendmail(EMAIL_SENDER, receiver, msg.as_string())
        print(f"[✓] Email sent to {', '.join(r for r in EMAIL_RECEIVERS if r)}")
        return True
    except Exception as e:
        print(f"[!] Failed to send email: {e}")
        return False


def create_calendar_event(data: dict) -> bool:
    """Create Google Calendar event from booking data."""
    if not CALENDAR_ENABLED:
        return False

    try:
        summary = f"[Booking] {data.get('layanan', 'Service')} — {data.get('nama', 'Customer')}"
        description = (
            f"Name: {data.get('nama', '—')}\n"
            f"WA: {data.get('wa', '—')}\n"
            f"Service: {data.get('layanan', '—')}\n"
            f"Issue: {data.get('keluhan', '—')}\n"
            f"Address: {data.get('alamat', '—')}"
        )

        tgl = data.get("tanggal", "")
        if tgl:
            start_dt = tgl.replace("T", " ") + ":00"
            end_dt = tgl.replace("T", " ") + ":00"
        else:
            start_dt = datetime.now().strftime("%Y-%m-%dT09:00:00")
            end_dt = datetime.now().strftime("%Y-%m-%dT10:00:00")

        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_dt, "timeZone": "Asia/Makassar"},
            "end": {"dateTime": end_dt, "timeZone": "Asia/Makassar"},
        }

        result = calendar_service.events().insert(
            calendarId=CALENDAR_ID, body=event
        ).execute()
        print(f"[✓] Google Calendar event created: {result.get('htmlLink')}")
        return True
    except Exception as e:
        print(f"[!] Failed to create Google Calendar event: {e}")
        return False


# ─── ROUTES ──────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/tentang")
def tentang():
    return render_template("tentang.html")


@app.route("/layanan")
def layanan():
    return render_template("layanan.html")


@app.route("/booking", methods=["GET", "POST"])
def booking():
    if request.method == "POST":
        data = {
            "nama": request.form.get("nama", "").strip(),
            "wa": request.form.get("wa", "").strip(),
            "layanan": request.form.get("layanan", "").strip(),
            "keluhan": request.form.get("keluhan", "").strip(),
            "alamat": request.form.get("alamat", "").strip(),
            "tanggal": request.form.get("tanggal", "").strip(),
        }

        email_ok = send_email_booking(data)
        cal_ok = create_calendar_event(data)

        if email_ok:
            return render_template("sukses.html", **data)
        else:
            return render_template(
                "booking.html",
                error="Sorry, something went wrong. Please try again or contact us directly via WhatsApp.",
            )

    return render_template("booking.html")


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/kontak")
def kontak():
    return render_template("kontak.html")


# ─── RUN ─────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    print(f"[✓] DeckStation.id running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)

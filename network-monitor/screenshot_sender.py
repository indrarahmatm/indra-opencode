import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def get_latest_screenshot(folder="/home/indra/Pictures/Screenshots"):
    try:
        files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
        ]
        if not files:
            return None
        latest = max(files, key=os.path.getmtime)
        return latest
    except Exception as e:
        print(f"Error getting screenshot: {e}")
        return None


def send_email_with_attachment(
    sender_email,
    sender_password,
    receiver_email,
    subject,
    body,
    attachment_path=None,
    smtp_host="smtp.gmail.com",
    smtp_port=587,
):
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_screenshot_email():
    screenshot = get_latest_screenshot()
    sender = "pspindrarahmat@gmail.com"
    password = "Lupabnaget120374"
    receiver = "pspindrarahmat@gmail.com"

    subject = f"Screenshot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    body = f"Lampiran screenshot terbaru.\n\nWaktu: {datetime.now()}"

    success = send_email_with_attachment(
        sender, password, receiver, subject, body, screenshot
    )
    return success


if __name__ == "__main__":
    if send_screenshot_email():
        print("Email sent successfully!")
    else:
        print("Failed to send email")

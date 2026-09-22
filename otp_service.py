import os
import random
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twilio.rest import Client

OTP_EXPIRY = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))


def generate_otp():
    return f"{random.SystemRandom().randint(100000, 999999)}"


def send_email_otp(email: str, otp: str):
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    if not sender or not password:
        raise RuntimeError("EMAIL_ADDRESS / EMAIL_APP_PASSWORD is not configured.")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = email
    msg["Subject"] = "PragyanAI Student Account - Email Verification OTP"
    body = f"""Hello,\n\nYour PragyanAI student account verification OTP is: {otp}\n\nThis OTP is valid for 5 minutes.\nDo not share this OTP with anyone.\n\nRegards,\nPragyanAI"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, email, msg.as_string())


def send_phone_otp(phone: str):
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
    if not all([os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), service_sid]):
        raise RuntimeError("Twilio credentials are not configured.")
    verification = client.verify.v2.services(service_sid).verifications.create(
        to=phone, channel="sms"
    )
    return verification.status


def verify_phone_otp(phone: str, otp: str):
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID")
    result = client.verify.v2.services(service_sid).verification_checks.create(
        to=phone, code=otp
    )
    return result.status == "approved"


def otp_is_valid(created_at: float):
    return (time.time() - created_at) <= OTP_EXPIRY

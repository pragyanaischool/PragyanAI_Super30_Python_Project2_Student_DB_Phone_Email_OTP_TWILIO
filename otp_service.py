# ============================================================
# otp_service.py
# ============================================================
# PragyanAI Student Verification System
#
# Services:
#   1. Email OTP using Gmail SMTP
#   2. Phone OTP using Twilio Verify
#
# Configuration:
#   Streamlit Secrets
#
# Expected .streamlit/secrets.toml:
#
# [email]
# address = "your-email@gmail.com"
# app_password = "your-gmail-app-password"
#
# [twilio]
# account_sid = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# auth_token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# verify_service_sid = "VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#
# ============================================================

import smtplib
import re

import streamlit as st

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


# ============================================================
# 1. LOAD SECRETS
# ============================================================

try:

    EMAIL_ADDRESS = st.secrets["email"]["address"]

    EMAIL_APP_PASSWORD = st.secrets["email"]["app_password"]

except Exception as e:

    raise RuntimeError(
        "Email configuration is missing from Streamlit Secrets. "
        "Please configure [email] in .streamlit/secrets.toml."
    ) from e


try:

    TWILIO_ACCOUNT_SID = st.secrets["twilio"]["account_sid"]

    TWILIO_AUTH_TOKEN = st.secrets["twilio"]["auth_token"]

    TWILIO_VERIFY_SERVICE_SID = (
        st.secrets["twilio"]["verify_service_sid"]
    )

except Exception as e:

    raise RuntimeError(
        "Twilio configuration is missing from Streamlit Secrets. "
        "Please configure [twilio] in .streamlit/secrets.toml."
    ) from e


# ============================================================
# 2. CREATE TWILIO CLIENT
# ============================================================

twilio_client = Client(
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)


# ============================================================
# 3. CONSTANTS
# ============================================================

OTP_LENGTH = 6

OTP_EXPIRY_SECONDS = 300

SMTP_SERVER = "smtp.gmail.com"

SMTP_PORT = 587


# ============================================================
# 4. EMAIL VALIDATION
# ============================================================

def validate_email(email: str) -> bool:
    """
    Validate email format.
    """

    if not email:

        return False

    email = email.strip()

    pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    return bool(
        re.match(
            pattern,
            email
        )
    )


# ============================================================
# 5. PHONE VALIDATION
# ============================================================

def validate_phone(phone: str) -> bool:
    """
    Validate international phone number.

    Example:

        +919876543210
    """

    if not phone:

        return False

    phone = phone.strip()

    pattern = r"^\+[1-9]\d{7,14}$"

    return bool(
        re.match(
            pattern,
            phone
        )
    )


# ============================================================
# 6. GENERATE OTP
# ============================================================

def generate_otp() -> str:
    """
    Generate a 6-digit OTP.

    Example:

        483921
    """

    import secrets

    return "".join(
        str(
            secrets.randbelow(10)
        )
        for _ in range(OTP_LENGTH)
    )


# ============================================================
# 7. SEND EMAIL OTP
# ============================================================

def send_email_otp(
    email: str,
    otp: str
) -> tuple[bool, str]:
    """
    Send OTP through Gmail SMTP.

    Returns:

        (True, success message)

    or

        (False, error message)
    """

    # -----------------------------------------
    # Validate email
    # -----------------------------------------

    if not validate_email(email):

        return (
            False,
            "Invalid email address."
        )

    # -----------------------------------------
    # Validate OTP
    # -----------------------------------------

    if not otp:

        return (
            False,
            "OTP cannot be empty."
        )

    try:

        # -------------------------------------
        # Email Subject
        # -------------------------------------

        subject = (
            "PragyanAI Student Registration "
            "Verification OTP"
        )

        # -------------------------------------
        # Email Body
        # -------------------------------------

        body = f"""
Hello,

Welcome to PragyanAI.

Your Email Verification OTP is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this OTP with anyone.

If you did not request this verification,
please ignore this email.

Regards,

PragyanAI
AI Engineering & Career Programs
Bangalore
"""

        # -------------------------------------
        # Create Email
        # -------------------------------------

        message = MIMEMultipart()

        message["From"] = EMAIL_ADDRESS

        message["To"] = email

        message["Subject"] = subject

        message.attach(
            MIMEText(
                body,
                "plain"
            )
        )

        # -------------------------------------
        # Connect to Gmail SMTP
        # -------------------------------------

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30
        ) as server:

            # Start TLS encryption
            server.starttls()

            # Login using Gmail App Password
            server.login(
                EMAIL_ADDRESS,
                EMAIL_APP_PASSWORD
            )

            # Send email
            server.sendmail(
                EMAIL_ADDRESS,
                email,
                message.as_string()
            )

        return (
            True,
            "Email OTP sent successfully."
        )

    except smtplib.SMTPAuthenticationError:

        return (
            False,
            "Gmail authentication failed. "
            "Check EMAIL_ADDRESS and Gmail App Password."
        )

    except smtplib.SMTPException as e:

        return (
            False,
            f"SMTP error: {str(e)}"
        )

    except Exception as e:

        return (
            False,
            f"Email OTP error: {str(e)}"
        )


# ============================================================
# 8. SEND PHONE OTP
# ============================================================

def send_phone_otp(
    phone: str
) -> tuple[bool, str]:
    """
    Send SMS OTP using Twilio Verify.

    Phone must be in international format.

    Example:

        +919876543210
    """

    # -----------------------------------------
    # Validate phone
    # -----------------------------------------

    if not validate_phone(phone):

        return (
            False,
            "Invalid phone number. "
            "Use international format, "
            "for example +919876543210."
        )

    try:

        # -------------------------------------
        # Send Verification
        # -------------------------------------

        verification = (
            twilio_client
            .verify
            .v2
            .services(
                TWILIO_VERIFY_SERVICE_SID
            )
            .verifications
            .create(
                to=phone,
                channel="sms"
            )
        )

        # -------------------------------------
        # Check status
        # -------------------------------------

        if verification.status == "pending":

            return (
                True,
                "Phone OTP sent successfully."
            )

        return (
            True,
            f"OTP request status: "
            f"{verification.status}"
        )

    except TwilioRestException as e:

        return (
            False,
            f"Twilio error: {e.msg}"
        )

    except Exception as e:

        return (
            False,
            f"Phone OTP error: {str(e)}"
        )


# ============================================================
# 9. VERIFY PHONE OTP
# ============================================================

def verify_phone_otp(
    phone: str,
    otp: str
) -> tuple[bool, str]:
    """
    Verify SMS OTP using Twilio Verify.
    """

    # -----------------------------------------
    # Validate phone
    # -----------------------------------------

    if not validate_phone(phone):

        return (
            False,
            "Invalid phone number."
        )

    # -----------------------------------------
    # Validate OTP
    # -----------------------------------------

    if not otp:

        return (
            False,
            "Please enter the OTP."
        )

    otp = otp.strip()

    if not otp.isdigit() or len(otp) != OTP_LENGTH:

        return (
            False,
            "OTP must be a 6-digit number."
        )

    try:

        # -------------------------------------
        # Verify OTP
        # -------------------------------------

        verification_check = (
            twilio_client
            .verify
            .v2
            .services(
                TWILIO_VERIFY_SERVICE_SID
            )
            .verification_checks
            .create(
                to=phone,
                code=otp
            )
        )

        # -------------------------------------
        # Approved
        # -------------------------------------

        if verification_check.status == "approved":

            return (
                True,
                "Phone number verified successfully."
            )

        # -------------------------------------
        # Not approved
        # -------------------------------------

        return (
            False,
            "Invalid or expired phone OTP."
        )

    except TwilioRestException as e:

        return (
            False,
            f"Twilio verification error: {e.msg}"
        )

    except Exception as e:

        return (
            False,
            f"Phone verification error: {str(e)}"
        )


# ============================================================
# 10. TEST CONFIGURATION
# ============================================================

def check_configuration() -> dict:
    """
    Check whether Email and Twilio configuration
    has been loaded.

    Does NOT expose secrets.
    """

    return {

        "email_configured": bool(
            EMAIL_ADDRESS
            and EMAIL_APP_PASSWORD
        ),

        "twilio_configured": bool(
            TWILIO_ACCOUNT_SID
            and TWILIO_AUTH_TOKEN
            and TWILIO_VERIFY_SERVICE_SID
        )

    }

# ============================================================
# END OF otp_service.py
# ============================================================

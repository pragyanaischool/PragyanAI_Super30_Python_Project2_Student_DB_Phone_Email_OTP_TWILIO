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
# Expected Streamlit Secrets:
#
# EMAIL_ADDRESS = "your-email@gmail.com"
# EMAIL_APP_PASSWORD = "your-gmail-app-password"
#
# TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# TWILIO_VERIFY_SERVICE_SID = "VAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import smtplib
import re
import secrets
import time

import streamlit as st

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


# ============================================================
# 1. LOAD SECRETS
# ============================================================
#
# Your Streamlit Cloud Secrets are configured as:
#
# EMAIL_ADDRESS = "..."
# EMAIL_APP_PASSWORD = "..."
# TWILIO_ACCOUNT_SID = "..."
# TWILIO_AUTH_TOKEN = "..."
# TWILIO_VERIFY_SERVICE_SID = "..."
#
# ============================================================


try:

    EMAIL_ADDRESS = st.secrets["EMAIL_ADDRESS"]

    EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]

except KeyError as e:

    raise RuntimeError(
        "Email configuration is missing from Streamlit Secrets. "
        "Please configure EMAIL_ADDRESS and "
        "EMAIL_APP_PASSWORD."
    ) from e


try:

    TWILIO_ACCOUNT_SID = (
        st.secrets["TWILIO_ACCOUNT_SID"]
    )

    TWILIO_AUTH_TOKEN = (
        st.secrets["TWILIO_AUTH_TOKEN"]
    )

    TWILIO_VERIFY_SERVICE_SID = (
        st.secrets["TWILIO_VERIFY_SERVICE_SID"]
    )

except KeyError as e:

    raise RuntimeError(
        "Twilio configuration is missing from "
        "Streamlit Secrets. "
        "Please configure TWILIO_ACCOUNT_SID, "
        "TWILIO_AUTH_TOKEN and "
        "TWILIO_VERIFY_SERVICE_SID."
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

# Email OTP validity:
# 300 seconds = 5 minutes

OTP_EXPIRY_SECONDS = 300

SMTP_SERVER = "smtp.gmail.com"

SMTP_PORT = 587


# ============================================================
# 4. EMAIL VALIDATION
# ============================================================

def validate_email(email: str) -> bool:
    """
    Validate email format.

    Example:

        student@gmail.com

    Returns:

        True  -> valid email
        False -> invalid email
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

    Returns:

        True  -> valid phone format
        False -> invalid phone format
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
    Generate a secure 6-digit OTP.

    Example:

        483921
    """

    return "".join(
        str(
            secrets.randbelow(10)
        )
        for _ in range(OTP_LENGTH)
    )


# ============================================================
# 7. CHECK OTP VALIDITY / EXPIRY
# ============================================================

def otp_is_valid(otp_time) -> bool:
    """
    Check whether an OTP is still valid.

    Parameters:
        otp_time:
            The timestamp at which the OTP was generated.

            Example:

                time.time()

    Returns:
        True:
            OTP is still valid.

        False:
            OTP is expired or timestamp is invalid.

    OTP validity:
        5 minutes / 300 seconds
    """

    if otp_time is None:

        return False

    try:

        elapsed_time = (
            time.time()
            - float(otp_time)
        )

        return (
            elapsed_time
            <= OTP_EXPIRY_SECONDS
        )

    except (
        TypeError,
        ValueError
    ):

        return False


# ============================================================
# 8. GET OTP REMAINING TIME
# ============================================================

def otp_remaining_seconds(
    otp_time
) -> int:
    """
    Return remaining OTP validity time.

    Example:

        275

    means 275 seconds remaining.

    Returns:

        0 when expired.
    """

    if otp_time is None:

        return 0

    try:

        elapsed_time = (
            time.time()
            - float(otp_time)
        )

        remaining = (
            OTP_EXPIRY_SECONDS
            - elapsed_time
        )

        return max(
            0,
            int(remaining)
        )

    except (
        TypeError,
        ValueError
    ):

        return 0


# ============================================================
# 9. SEND EMAIL OTP
# ============================================================

def send_email_otp(
    email: str,
    otp: str
) -> tuple[bool, str]:
    """
    Send OTP through Gmail SMTP.

    Parameters:

        email:
            Student email address.

        otp:
            Generated 6-digit OTP.

    Returns:

        (True, success message)

    OR

        (False, error message)
    """

    # --------------------------------------------------------
    # Validate Email
    # --------------------------------------------------------

    if not validate_email(email):

        return (
            False,
            "Invalid email address."
        )

    # --------------------------------------------------------
    # Validate OTP
    # --------------------------------------------------------

    if not otp:

        return (
            False,
            "OTP cannot be empty."
        )

    try:

        # ----------------------------------------------------
        # Email Subject
        # ----------------------------------------------------

        subject = (
            "PragyanAI Student Registration "
            "Verification OTP"
        )

        # ----------------------------------------------------
        # Email Body
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Create Email
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Connect to Gmail SMTP
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        return (
            True,
            "Email OTP sent successfully."
        )

    # --------------------------------------------------------
    # Gmail Authentication Error
    # --------------------------------------------------------

    except smtplib.SMTPAuthenticationError:

        return (
            False,
            "Gmail authentication failed. "
            "Check EMAIL_ADDRESS and Gmail App Password."
        )

    # --------------------------------------------------------
    # SMTP Error
    # --------------------------------------------------------

    except smtplib.SMTPException as e:

        return (
            False,
            f"SMTP error: {str(e)}"
        )

    # --------------------------------------------------------
    # General Error
    # --------------------------------------------------------

    except Exception as e:

        return (
            False,
            f"Email OTP error: {str(e)}"
        )


# ============================================================
# 10. SEND PHONE OTP
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

    # --------------------------------------------------------
    # Validate Phone
    # --------------------------------------------------------

    if not validate_phone(phone):

        return (
            False,
            "Invalid phone number. "
            "Use international format, "
            "for example +919876543210."
        )

    try:

        # ----------------------------------------------------
        # Send Verification
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Check Status
        # ----------------------------------------------------

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

    # --------------------------------------------------------
    # Twilio Error
    # --------------------------------------------------------

    except TwilioRestException as e:

        return (
            False,
            f"Twilio error: {e.msg}"
        )

    # --------------------------------------------------------
    # General Error
    # --------------------------------------------------------

    except Exception as e:

        return (
            False,
            f"Phone OTP error: {str(e)}"
        )


# ============================================================
# 11. VERIFY PHONE OTP
# ============================================================

def verify_phone_otp(
    phone: str,
    otp: str
) -> tuple[bool, str]:
    """
    Verify SMS OTP using Twilio Verify.

    Returns:

        (True, success message)

    OR

        (False, error message)
    """

    # --------------------------------------------------------
    # Validate Phone
    # --------------------------------------------------------

    if not validate_phone(phone):

        return (
            False,
            "Invalid phone number."
        )

    # --------------------------------------------------------
    # Validate OTP
    # --------------------------------------------------------

    if not otp:

        return (
            False,
            "Please enter the OTP."
        )

    otp = otp.strip()

    # --------------------------------------------------------
    # OTP Must Be 6 Digits
    # --------------------------------------------------------

    if (
        not otp.isdigit()
        or len(otp) != OTP_LENGTH
    ):

        return (
            False,
            "OTP must be a 6-digit number."
        )

    try:

        # ----------------------------------------------------
        # Verify OTP
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Approved
        # ----------------------------------------------------

        if verification_check.status == "approved":

            return (
                True,
                "Phone number verified successfully."
            )

        # ----------------------------------------------------
        # Not Approved
        # ----------------------------------------------------

        return (
            False,
            "Invalid or expired phone OTP."
        )

    # --------------------------------------------------------
    # Twilio Error
    # --------------------------------------------------------

    except TwilioRestException as e:

        return (
            False,
            f"Twilio verification error: {e.msg}"
        )

    # --------------------------------------------------------
    # General Error
    # --------------------------------------------------------

    except Exception as e:

        return (
            False,
            f"Phone verification error: {str(e)}"
        )


# ============================================================
# 12. TEST CONFIGURATION
# ============================================================

def check_configuration() -> dict:
    """
    Check whether Email and Twilio configuration
    has been loaded.

    Does NOT expose secret values.
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
# 13. GET CONFIGURATION STATUS MESSAGE
# ============================================================

def configuration_status() -> str:
    """
    Return a safe configuration status.

    Secret values are never displayed.
    """

    config = check_configuration()

    email_status = (
        "Configured"
        if config["email_configured"]
        else "Not Configured"
    )

    twilio_status = (
        "Configured"
        if config["twilio_configured"]
        else "Not Configured"
    )

    return (
        f"Email: {email_status} | "
        f"Twilio: {twilio_status}"
    )


# ============================================================
# END OF otp_service.py
# ============================================================

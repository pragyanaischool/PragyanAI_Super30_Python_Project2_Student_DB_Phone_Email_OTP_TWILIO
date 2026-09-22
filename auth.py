# ============================================================
# auth.py
# ============================================================
# PragyanAI Student Verification System
#
# Authentication Services:
#
#   1. Student Password Hashing
#   2. Student Password Verification
#   3. Student Login
#   4. Admin Login
#   5. Streamlit Session Management
#   6. Logout
#
# Admin credentials are loaded from:
#
# .streamlit/secrets.toml
#
# Example:
#
# [admin]
# email = "admin@pragyanai.com"
# password = "ChangeThisPassword123!"
#
# ============================================================

import hashlib
import hmac
import secrets

import streamlit as st

# ============================================================
# CONSTANTS
# ============================================================

HASH_ITERATIONS = 310_000
SALT_LENGTH = 32
KEY_LENGTH = 32

# ============================================================
# 1. PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Securely hash a password using PBKDF2-HMAC-SHA256.

    The returned value contains:

        salt + hash

    Example:

        salt$hash
    """

    if not password:

        raise ValueError(
            "Password cannot be empty."
        )

    password_bytes = password.encode(
        "utf-8"
    )

    salt = secrets.token_bytes(
        SALT_LENGTH
    )

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        HASH_ITERATIONS,
        dklen=KEY_LENGTH
    )

    return (
        salt.hex()
        + "$"
        + password_hash.hex()
    )
# ============================================================
# 2. VERIFY PASSWORD
# ============================================================

def verify_password(
    password: str,
    stored_password: str
) -> bool:
    """
    Verify a password against a stored PBKDF2 hash.

    Expected stored format:

        salt$hash
    """

    if not password:

        return False

    if not stored_password:

        return False

    try:

        parts = stored_password.split(
            "$"
        )

        if len(parts) != 2:

            return False

        salt_hex = parts[0]

        stored_hash_hex = parts[1]

        salt = bytes.fromhex(
            salt_hex
        )

        stored_hash = bytes.fromhex(
            stored_hash_hex
        )

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            HASH_ITERATIONS,
            dklen=KEY_LENGTH
        )

        return hmac.compare_digest(
            password_hash,
            stored_hash
        )

    except (
        ValueError,
        TypeError,
        UnicodeError
    ):

        return False

# ============================================================
# 3. PASSWORD VALIDATION
# ============================================================

def validate_password(
    password: str
) -> tuple[bool, str]:
    """
    Validate password strength.

    Requirements:

        Minimum 8 characters
        At least one uppercase letter
        At least one lowercase letter
        At least one number
    """

    if not password:

        return (
            False,
            "Password is required."
        )

    if len(password) < 8:

        return (
            False,
            "Password must contain at least 8 characters."
        )

    if not any(
        character.isupper()
        for character in password
    ):

        return (
            False,
            "Password must contain at least one uppercase letter."
        )

    if not any(
        character.islower()
        for character in password
    ):

        return (
            False,
            "Password must contain at least one lowercase letter."
        )

    if not any(
        character.isdigit()
        for character in password
    ):

        return (
            False,
            "Password must contain at least one number."
        )

    return (
        True,
        "Password is valid."
    )

# ============================================================
# 4. STUDENT LOGIN
# ============================================================

def student_login(
    email: str,
    password: str,
    db_connection
) -> tuple[bool, str, dict | None]:
    """
    Authenticate a student using email and password.

    Expected database columns:

        id
        full_name
        email
        password_hash
        email_verified
        phone_verified
        approval_status

    Returns:

        (
            success,
            message,
            student_data
        )
    """

    if not email:

        return (
            False,
            "Please enter your email.",
            None
        )

    if not password:

        return (
            False,
            "Please enter your password.",
            None
        )

    email = email.strip().lower()

    try:

        cursor = db_connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM students
            WHERE LOWER(email) = ?
            LIMIT 1
            """,
            (email,)
        )

        row = cursor.fetchone()

        if row is None:

            return (
                False,
                "Invalid email or password.",
                None
            )

        # ----------------------------------------------------
        # Convert SQLite Row to Dictionary
        # ----------------------------------------------------

        if hasattr(
            row,
            "keys"
        ):

            student = dict(row)

        else:

            columns = [
                description[0]
                for description
                in cursor.description
            ]

            student = dict(
                zip(
                    columns,
                    row
                )
            )

        # ----------------------------------------------------
        # Get Stored Password
        # ----------------------------------------------------

        stored_password = student.get(
            "password_hash"
        )

        if not stored_password:

            return (
                False,
                "Account password is not configured correctly.",
                None
            )

        # ----------------------------------------------------
        # Verify Password
        # ----------------------------------------------------

        if not verify_password(
            password,
            stored_password
        ):

            return (
                False,
                "Invalid email or password.",
                None
            )

        # ----------------------------------------------------
        # Email Verification
        # ----------------------------------------------------

        email_verified = student.get(
            "email_verified",
            0
        )

        if not bool(email_verified):

            return (
                False,
                "Please verify your email before login.",
                None
            )

        # ----------------------------------------------------
        # Phone Verification
        # ----------------------------------------------------

        phone_verified = student.get(
            "phone_verified",
            0
        )

        if not bool(phone_verified):

            return (
                False,
                "Please verify your phone before login.",
                None
            )

        # ----------------------------------------------------
        # Login Successful
        # ----------------------------------------------------

        return (
            True,
            "Student login successful.",
            student
        )

    except Exception as e:

        return (
            False,
            f"Login error: {str(e)}",
            None
        )

# ============================================================
# 5. ADMIN LOGIN
# ============================================================

def admin_login(
    email: str,
    password: str
) -> tuple[bool, str]:
    """
    Authenticate Admin using Streamlit Secrets.

    Expected:

        [admin]

        email = "admin@pragyanai.com"
        password = "ChangeThisPassword123!"
    """

    if not email:

        return (
            False,
            "Please enter admin email."
        )

    if not password:

        return (
            False,
            "Please enter admin password."
        )

    try:

        admin_email = st.secrets[
            "admin"
        ][
            "email"
        ]

        admin_password = st.secrets[
            "admin"
        ][
            "password"
        ]

    except Exception:

        return (
            False,
            "Admin credentials are not configured in Streamlit Secrets."
        )

    # --------------------------------------------------------
    # Constant-Time Comparison
    # --------------------------------------------------------

    email_match = hmac.compare_digest(
        email.strip().lower(),
        admin_email.strip().lower()
    )

    password_match = hmac.compare_digest(
        password,
        admin_password
    )

    if email_match and password_match:

        return (
            True,
            "Admin login successful."
        )

    return (
        False,
        "Invalid admin credentials."
    )

# ============================================================
# 6. INITIALIZE SESSION STATE
# ============================================================

def initialize_session_state():
    """
    Initialize authentication-related
    Streamlit session variables.
    """

    defaults = {

        "logged_in": False,

        "user_type": None,

        "student_id": None,

        "student_email": None,

        "student_name": None,

        "admin_logged_in": False,

        "email_verified": False,

        "phone_verified": False,

        "email_otp": None,

        "email_otp_time": None,

        "registration_data": {},

    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value

# ============================================================
# 7. SET STUDENT LOGIN SESSION
# ============================================================

def set_student_session(
    student: dict
):
    """
    Store authenticated student information
    in Streamlit session state.
    """

    st.session_state[
        "logged_in"
    ] = True

    st.session_state[
        "user_type"
    ] = "student"

    st.session_state[
        "student_id"
    ] = student.get("id")

    st.session_state[
        "student_email"
    ] = student.get("email")

    st.session_state[
        "student_name"
    ] = student.get("full_name")

    st.session_state[
        "email_verified"
    ] = bool(
        student.get(
            "email_verified",
            0
        )
    )

    st.session_state[
        "phone_verified"
    ] = bool(
        student.get(
            "phone_verified",
            0
        )
    )

# ============================================================
# 8. SET ADMIN SESSION
# ============================================================

def set_admin_session():
    """
    Set Admin login session.
    """

    st.session_state[
        "logged_in"
    ] = True

    st.session_state[
        "user_type"
    ] = "admin"

    st.session_state[
        "admin_logged_in"
    ] = True

# ============================================================
# 9. CHECK LOGIN
# ============================================================

def is_logged_in() -> bool:
    """
    Check whether any user is logged in.
    """

    return bool(
        st.session_state.get(
            "logged_in",
            False
        )
    )

# ============================================================
# 10. CHECK STUDENT LOGIN
# ============================================================

def is_student_logged_in() -> bool:
    """
    Check whether a student is logged in.
    """

    return (
        st.session_state.get(
            "logged_in",
            False
        )
        and
        st.session_state.get(
            "user_type"
        ) == "student"
    )

# ============================================================
# 11. CHECK ADMIN LOGIN
# ============================================================

def is_admin_logged_in() -> bool:
    """
    Check whether admin is logged in.
    """

    return (
        st.session_state.get(
            "logged_in",
            False
        )
        and
        st.session_state.get(
            "user_type"
        ) == "admin"
    )

# ============================================================
# 12. LOGOUT
# ============================================================

def logout():
    """
    Clear authentication-related
    Streamlit session state.
    """

    keys_to_clear = [

        "logged_in",

        "user_type",

        "student_id",

        "student_email",

        "student_name",

        "admin_logged_in",

        "email_verified",

        "phone_verified",

        "email_otp",

        "email_otp_time",

        "registration_data",

    ]

    for key in keys_to_clear:

        if key in st.session_state:

            del st.session_state[key]

    # Reinitialize the state
    initialize_session_state()

# ============================================================
# 13. LOGOUT BUTTON
# ============================================================

def logout_button():
    """
    Display a Streamlit logout button.
    """

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()

        st.rerun()

# ============================================================
# 14. GET CURRENT USER
# ============================================================

def get_current_user() -> dict:
    """
    Return current authenticated user information.
    """

    return {

        "logged_in": st.session_state.get(
            "logged_in",
            False
        ),

        "user_type": st.session_state.get(
            "user_type"
        ),

        "student_id": st.session_state.get(
            "student_id"
        ),

        "student_email": st.session_state.get(
            "student_email"
        ),

        "student_name": st.session_state.get(
            "student_name"
        ),

        "admin_logged_in": st.session_state.get(
            "admin_logged_in",
            False
        ),

    }

# ============================================================
# 15. CHANGE PASSWORD
# ============================================================

def change_student_password(
    student_id: int,
    current_password: str,
    new_password: str,
    db_connection
) -> tuple[bool, str]:
    """
    Change the student's password.

    This function expects:

        students.password_hash

    """

    if not student_id:

        return (
            False,
            "Invalid student ID."
        )

    if not current_password:

        return (
            False,
            "Please enter current password."
        )

    if not new_password:

        return (
            False,
            "Please enter new password."
        )

    # --------------------------------------------------------
    # Validate New Password
    # --------------------------------------------------------

    valid, message = validate_password(
        new_password
    )

    if not valid:

        return (
            False,
            message
        )

    try:

        cursor = db_connection.cursor()

        # ----------------------------------------------------
        # Get Current Password
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT password_hash
            FROM students
            WHERE id = ?
            LIMIT 1
            """,
            (student_id,)
        )

        row = cursor.fetchone()

        if row is None:

            return (
                False,
                "Student account not found."
            )

        if hasattr(
            row,
            "keys"
        ):

            stored_password = row[
                "password_hash"
            ]

        else:

            stored_password = row[0]

        # ----------------------------------------------------
        # Verify Current Password
        # ----------------------------------------------------

        if not verify_password(
            current_password,
            stored_password
        ):

            return (
                False,
                "Current password is incorrect."
            )

        # ----------------------------------------------------
        # Hash New Password
        # ----------------------------------------------------

        new_password_hash = hash_password(
            new_password
        )

        # ----------------------------------------------------
        # Update Database
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE students
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                new_password_hash,
                student_id
            )
        )

        db_connection.commit()

        return (
            True,
            "Password changed successfully."
        )

    except Exception as e:

        db_connection.rollback()

        return (
            False,
            f"Password change failed: {str(e)}"
        )

# ============================================================
# END OF auth.py
# ============================================================

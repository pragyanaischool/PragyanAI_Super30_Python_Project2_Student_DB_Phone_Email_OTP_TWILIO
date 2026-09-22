import os
import re
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from auth import hash_password, verify_password
from db import init_db, create_student, get_student_by_email, email_or_phone_exists, list_students, set_approval
from otp_service import generate_otp, send_email_otp, send_phone_otp, verify_phone_otp, otp_is_valid

st.set_page_config(page_title="PragyanAI Student Verification", page_icon="🎓", layout="wide")
init_db()

# -------------------------------
# Configuration
# -------------------------------
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pragyanai.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe@123")

if "role" not in st.session_state:
    st.session_state.role = None
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "email_otp" not in st.session_state:
    st.session_state.email_otp = None
if "email_otp_time" not in st.session_state:
    st.session_state.email_otp_time = None
if "email_verified" not in st.session_state:
    st.session_state.email_verified = False
if "phone_verified" not in st.session_state:
    st.session_state.phone_verified = False
if "pending_student" not in st.session_state:
    st.session_state.pending_student = None


def normalize_phone(phone):
    return phone.strip().replace(" ", "")


def valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def logout():
    for key in ["role", "student_id", "email_otp", "email_otp_time", "email_verified", "phone_verified", "pending_student"]:
        st.session_state[key] = None if key in ["role", "student_id", "email_otp", "email_otp_time", "pending_student"] else False
    st.rerun()

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.title(" PragyanAI")
    st.image("PragyanAI_Transperent.png")
    st.caption("Student Registration & Verification")
    if st.session_state.role:
        st.success(f"Logged in as {st.session_state.role.title()}")
        if st.button("Logout", use_container_width=True):
            logout()

# -------------------------------
# Admin Dashboard
# -------------------------------
def admin_dashboard():
    st.title(" Admin Dashboard")
    st.image("PragyanAI_Transperent.png")
    st.write("Review verified student accounts and update approval status.")

    rows = list_students()
    if not rows:
        st.info("No student accounts found.")
        return

    data = [dict(r) for r in rows]
    df = pd.DataFrame(data)
    cols = ["id", "full_name", "college_name", "degree", "branch", "tenth_cgpa", "twelfth_cgpa", "be_cgpa", "phone", "email", "email_verified", "phone_verified", "approval_status", "created_at", "approved_by", "approved_at"]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    st.subheader("Update Approval")
    options = {f"#{r['id']} - {r['full_name']} - {r['email']} [{r['approval_status']}]": r for r in rows}
    selected = st.selectbox("Select Student", list(options.keys()))
    row = options[selected]

    st.write({
        "Email Verified": bool(row["email_verified"]),
        "Phone Verified": bool(row["phone_verified"]),
        "Current Status": row["approval_status"],
    })

    new_status = st.selectbox("Approval Status", ["Pending", "Approved", "Rejected"], index=["Pending", "Approved", "Rejected"].index(row["approval_status"]))
    if st.button(" Update Approval Status", type="primary"):
        if new_status == "Approved" and not (row["email_verified"] and row["phone_verified"]):
            st.error("Student must have both Email and Phone verified before approval.")
        else:
            set_approval(row["id"], new_status, ADMIN_EMAIL)
            st.success(f"Student status updated to {new_status}.")
            st.rerun()

# -------------------------------
# Student Portal
# -------------------------------
def student_portal():
    row = get_student_by_email(st.session_state.student_email)
    st.title(" Student Portal")
    st.image("PragyanAI_Transperent.png")
    if not row:
        st.error("Student account not found.")
        return
    st.success(f"Welcome, {row['full_name']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Email", "Verified" if row["email_verified"] else "Not Verified")
    c2.metric("Phone", "Verified" if row["phone_verified"] else "Not Verified")
    c3.metric("Approval", row["approval_status"])
    st.subheader("Profile")
    st.dataframe(pd.DataFrame([dict(row)]), use_container_width=True, hide_index=True)

# -------------------------------
# Main Login / Registration
# -------------------------------
if st.session_state.role == "admin":
    admin_dashboard()
    st.stop()

if st.session_state.role == "student":
    student_portal()
    st.stop()

st.title("🎓 PragyanAI Student Account & Verification")
st.markdown("Create a student account, verify **Email + Phone**, then wait for **Admin Approval**.")

login_tab, register_tab, admin_tab = st.tabs(["🔐 Student Login", "📝 Create Student Account", "🛡️ Admin Login"])

with login_tab:
    st.subheader("Student Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login", type="primary", key="student_login"):
        row = get_student_by_email(email)
        if not row or not verify_password(password, row["password_hash"]):
            st.error("Invalid email or password.")
        elif not (row["email_verified"] and row["phone_verified"]):
            st.warning("Please complete both Email and Phone verification.")
        else:
            st.session_state.role = "student"
            st.session_state.student_id = row["id"]
            st.session_state.student_email = row["email"]
            st.rerun()

with register_tab:
    st.subheader("Create Student Account")
    with st.form("student_registration"):
        full_name = st.text_input("Full Name *")
        college_name = st.text_input("College Name *")
        degree = st.selectbox("Degree *", ["BE", "BTech", "ME", "MTech", "BCA", "MCA", "Other"])
        branch = st.text_input("Branch *", placeholder="CSE / AI&ML / ISE / ECE")
        c1, c2, c3 = st.columns(3)
        tenth = c1.number_input("10th CGPA *", min_value=0.0, max_value=10.0, step=0.01)
        twelfth = c2.number_input("12th CGPA *", min_value=0.0, max_value=10.0, step=0.01)
        be = c3.number_input("BE CGPA *", min_value=0.0, max_value=10.0, step=0.01)
        phone = st.text_input("Phone *", placeholder="+919876543210")
        email = st.text_input("Email *", placeholder="student@gmail.com")
        password = st.text_input("Create Password *", type="password")
        confirm = st.text_input("Confirm Password *", type="password")
        submitted = st.form_submit_button("Create Account & Continue to Verification", type="primary")

    if submitted:
        phone = normalize_phone(phone)
        email = email.strip()
        errors = []
        if not all([full_name.strip(), college_name.strip(), branch.strip(), phone, email, password, confirm]):
            errors.append("Please fill all required fields.")
        if not valid_email(email):
            errors.append("Enter a valid email address.")
        if len(phone) < 10:
            errors.append("Enter a valid phone number with country code, e.g. +919876543210.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        existing = email_or_phone_exists(email, phone)
        if existing:
            errors.append("An account already exists with this email or phone.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state.pending_student = {
                "full_name": full_name.strip(), "college_name": college_name.strip(),
                "degree": degree, "branch": branch.strip(), "tenth_cgpa": tenth,
                "twelfth_cgpa": twelfth, "be_cgpa": be, "phone": phone, "email": email,
                "password_hash": hash_password(password), "email_verified": 0, "phone_verified": 0
            }
            st.session_state.email_verified = False
            st.session_state.phone_verified = False
            st.success("Details captured. Complete Email and Phone verification below.")

    if st.session_state.pending_student:
        p = st.session_state.pending_student
        st.divider()
        st.subheader("Step 2 — Verify Email")
        st.caption(f"Verification email will be sent to: {p['email']}")
        if st.button("📧 Send Email OTP", key="send_email"):
            try:
                otp = generate_otp()
                send_email_otp(p["email"], otp)
                st.session_state.email_otp = otp
                st.session_state.email_otp_time = time.time()
                st.success("Email OTP sent.")
            except Exception as e:
                st.error(f"Could not send email OTP: {e}")

        email_otp_input = st.text_input("Enter Email OTP", key="email_otp_input")
        if st.button("✅ Verify Email", key="verify_email"):
            if not st.session_state.email_otp:
                st.error("Send an Email OTP first.")
            elif not otp_is_valid(st.session_state.email_otp_time):
                st.session_state.email_otp = None
                st.error("OTP expired. Send a new OTP.")
            elif email_otp_input == st.session_state.email_otp:
                st.session_state.email_verified = True
                st.session_state.email_otp = None
                st.success("Email verified successfully.")
            else:
                st.error("Invalid Email OTP.")

        st.subheader("Step 3 — Verify Phone")
        st.caption(f"SMS OTP will be sent to: {p['phone']}")
        if st.button(" Send Phone OTP", key="send_phone"):
            try:
                status = send_phone_otp(p["phone"])
                st.success(f"Phone OTP sent. Twilio status: {status}")
            except Exception as e:
                st.error(f"Could not send SMS OTP: {e}")

        phone_otp_input = st.text_input("Enter Phone OTP", key="phone_otp_input")
        if st.button("✅ Verify Phone", key="verify_phone"):
            try:
                if verify_phone_otp(p["phone"], phone_otp_input):
                    st.session_state.phone_verified = True
                    st.success("Phone verified successfully.")
                else:
                    st.error("Invalid Phone OTP.")
            except Exception as e:
                st.error(f"Phone verification failed: {e}")

        st.write("### Verification Status")
        v1, v2 = st.columns(2)
        v1.success("Email Verified ✅" if st.session_state.email_verified else "Email Not Verified ❌")
        v2.success("Phone Verified ✅" if st.session_state.phone_verified else "Phone Not Verified ❌")

        if st.session_state.email_verified and st.session_state.phone_verified:
            if st.button(" Save Student Account", type="primary", key="save_student"):
                try:
                    create_student({**p, "email_verified": 1, "phone_verified": 1})
                    st.session_state.pending_student = None
                    st.session_state.email_verified = False
                    st.session_state.phone_verified = False
                    st.session_state.email_otp = None
                    st.success("Account created successfully. Your application is now Pending Admin Approval.")
                except Exception as e:
                    st.error(f"Could not save account: {e}")

with admin_tab:
    st.subheader("Admin Login")
    admin_email = st.text_input("Admin Email", key="admin_email")
    admin_password = st.text_input("Admin Password", type="password", key="admin_password")
    if st.button("Admin Login", type="primary", key="admin_login"):
        if admin_email.strip().lower() == ADMIN_EMAIL.lower() and admin_password == ADMIN_PASSWORD:
            st.session_state.role = "admin"
            st.rerun()
        else:
            st.error("Invalid admin credentials.")

st.divider()
st.caption("PragyanAI • Student Account Verification System • Streamlit + SQLite + SMTP + Twilio Verify")

# PragyanAI Student Account & Verification System

A Streamlit application for:

- Student account creation
- Student details stored in SQLite
- Email OTP verification using Gmail SMTP
- Phone OTP verification using Twilio Verify
- Student login
- Admin login
- Admin review and approval/rejection
- Approval status stored in SQL database

## Student fields

- Full Name
- College Name
- Degree
- Branch
- 10th CGPA
- 12th CGPA
- BE CGPA
- Phone
- Email
- Password
- Email verification status
- Phone verification status
- Admin approval status

## Project flow

```text
Student
   |
   v
Create Account
   |
   +--> Email OTP --> Verify Email
   |
   +--> SMS OTP --> Verify Phone
   |
   v
Save to SQLite
   |
   v
Pending Admin Approval
   |
   v
Admin Login
   |
   v
Review Student
   |
   +--> Approve
   +--> Reject
   |
   v
Student Login / Student Portal
```

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Configure secrets

For local development, create `.env` and export variables, or use your deployment platform's secrets/environment variables.

Required:

```text
EMAIL_ADDRESS
EMAIL_APP_PASSWORD
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_VERIFY_SERVICE_SID
ADMIN_EMAIL
ADMIN_PASSWORD
```

For Gmail, use a Google App Password rather than your normal Gmail password.

## 3. Run

```bash
streamlit run app.py
```

The SQLite file `students.db` is created automatically.

## 4. Google Colab

You can also run the Streamlit application from Colab using a tunnel such as Cloudflare Tunnel or another approved tunneling method. Configure secrets through environment variables rather than hard-coding credentials.

## Security notes

- OTPs are never written to the database in this demo.
- Passwords are stored as PBKDF2-SHA256 hashes.
- Admin credentials should be changed from the example values before deployment.
- Use HTTPS for deployed applications.
- For production, add rate limiting, audit logging, CSRF/session hardening, account lockout, and a persistent OTP/rate-limit store such as Redis.
- SQLite is appropriate for a learning/small deployment. For multi-user production deployments, PostgreSQL is recommended.

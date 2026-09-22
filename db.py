import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent / "students.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            college_name TEXT NOT NULL,
            degree TEXT NOT NULL,
            branch TEXT NOT NULL,
            tenth_cgpa REAL NOT NULL,
            twelfth_cgpa REAL NOT NULL,
            be_cgpa REAL NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email_verified INTEGER NOT NULL DEFAULT 0,
            phone_verified INTEGER NOT NULL DEFAULT 0,
            approval_status TEXT NOT NULL DEFAULT 'Pending',
            approved_by TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """)

def create_student(data):
    with get_db() as conn:
        cur = conn.execute("""
        INSERT INTO students
        (full_name, college_name, degree, branch, tenth_cgpa, twelfth_cgpa,
         be_cgpa, phone, email, password_hash, email_verified, phone_verified,
         approval_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        """, (
            data['full_name'], data['college_name'], data['degree'], data['branch'],
            data['tenth_cgpa'], data['twelfth_cgpa'], data['be_cgpa'],
            data['phone'], data['email'], data['password_hash'],
            int(data.get('email_verified', 0)), int(data.get('phone_verified', 0))
        ))
        return cur.lastrowid

def get_student_by_email(email):
    with get_db() as conn:
        return conn.execute("SELECT * FROM students WHERE lower(email)=lower(?)", (email.strip(),)).fetchone()

def get_student_by_id(student_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()

def email_or_phone_exists(email, phone):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, email, phone FROM students WHERE lower(email)=lower(?) OR phone=?",
            (email.strip(), phone.strip())
        ).fetchone()
        return row

def list_students(status=None):
    with get_db() as conn:
        if status and status != "All":
            return conn.execute(
                "SELECT * FROM students WHERE approval_status=? ORDER BY created_at DESC", (status,)
            ).fetchall()
        return conn.execute("SELECT * FROM students ORDER BY created_at DESC").fetchall()

def set_approval(student_id, status, approved_by):
    with get_db() as conn:
        conn.execute("""
            UPDATE students
            SET approval_status=?, approved_by=?, approved_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (status, approved_by, student_id))

def set_verification(student_id, email_verified=None, phone_verified=None):
    fields, values = [], []
    if email_verified is not None:
        fields.append("email_verified=?"); values.append(int(email_verified))
    if phone_verified is not None:
        fields.append("phone_verified=?"); values.append(int(phone_verified))
    if not fields:
        return
    fields.append("updated_at=CURRENT_TIMESTAMP")
    values.append(student_id)
    with get_db() as conn:
        conn.execute(f"UPDATE students SET {', '.join(fields)} WHERE id=?", values)

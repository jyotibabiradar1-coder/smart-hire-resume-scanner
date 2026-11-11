"""
Database Diagnostics and Auto-Repair Utility
Ensures SQLite tables and schemas match the Resume Screening Application requirements.
"""
import sqlite3
import os
import sys
import bcrypt
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.db")

print("="*60)
print("🔍 Checking and repairing database: users.db")
print("="*60)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# ----------------------------------------------------
# 1. TABLE: users
# ----------------------------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password BLOB NOT NULL,
    role TEXT NOT NULL,
    email TEXT,
    created_at TEXT
)
""")
c.execute("PRAGMA table_info(users)")
user_cols = [col[1] for col in c.fetchall()]

if "email" not in user_cols:
    c.execute("ALTER TABLE users ADD COLUMN email TEXT")
    print("➕ Added 'email' column to users table.")

if "created_at" not in user_cols:
    c.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
    print("➕ Added 'created_at' column to users table.")

# ----------------------------------------------------
# 2. TABLE: resumes_blob
# ----------------------------------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS resumes_blob (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate TEXT,
    filename TEXT,
    file_blob BLOB,
    file_text TEXT,
    uploaded_at TEXT
)
""")
c.execute("PRAGMA table_info(resumes_blob)")
blob_cols = [col[1] for col in c.fetchall()]

if "file_text" not in blob_cols:
    c.execute("ALTER TABLE resumes_blob ADD COLUMN file_text TEXT")
    print("➕ Added 'file_text' column to resumes_blob table.")

# ----------------------------------------------------
# 3. TABLE: screening_results
# ----------------------------------------------------
c.execute("""
SELECT name FROM sqlite_master WHERE type='table' AND name='screening_results';
""")
if not c.fetchone():
    c.execute("""
    CREATE TABLE screening_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate TEXT,
        filename TEXT,
        similarity REAL,
        probability REAL,
        status TEXT,
        jd_checksum TEXT,
        timestamp TEXT
    )
    """)
    print("✅ Created 'screening_results' table with standard schema.")
else:
    c.execute("PRAGMA table_info(screening_results)")
    res_cols = [col[1] for col in c.fetchall()]

    # Migrate legacy columns if detected
    if "candidate" not in res_cols and "username" in res_cols:
        c.execute("ALTER TABLE screening_results ADD COLUMN candidate TEXT")
        c.execute("UPDATE screening_results SET candidate = username WHERE candidate IS NULL")
        print("🔄 Migrated legacy column 'username' to 'candidate'.")

    if "filename" not in res_cols and "resume_name" in res_cols:
        c.execute("ALTER TABLE screening_results ADD COLUMN filename TEXT")
        c.execute("UPDATE screening_results SET filename = resume_name WHERE filename IS NULL")
        print("🔄 Migrated legacy column 'resume_name' to 'filename'.")

    if "similarity" not in res_cols and "similarity_score" in res_cols:
        c.execute("ALTER TABLE screening_results ADD COLUMN similarity REAL")
        c.execute("UPDATE screening_results SET similarity = similarity_score WHERE similarity IS NULL")
        print("🔄 Migrated legacy column 'similarity_score' to 'similarity'.")

    if "probability" not in res_cols and "shortlist_probability" in res_cols:
        c.execute("ALTER TABLE screening_results ADD COLUMN probability REAL")
        c.execute("UPDATE screening_results SET probability = shortlist_probability WHERE probability IS NULL")
        print("🔄 Migrated legacy column 'shortlist_probability' to 'probability'.")

    # Add any missing standard columns
    c.execute("PRAGMA table_info(screening_results)")
    res_cols_updated = [col[1] for col in c.fetchall()]
    for col_name, col_type in [
        ("candidate", "TEXT"),
        ("filename", "TEXT"),
        ("similarity", "REAL"),
        ("probability", "REAL"),
        ("status", "TEXT"),
        ("jd_checksum", "TEXT"),
        ("timestamp", "TEXT")
    ]:
        if col_name not in res_cols_updated:
            c.execute(f"ALTER TABLE screening_results ADD COLUMN {col_name} {col_type}")
            print(f"➕ Added missing column '{col_name}' ({col_type}) to screening_results.")

# ----------------------------------------------------
# 4. SEED DEFAULT ADMIN IF EMPTY
# ----------------------------------------------------
c.execute("SELECT COUNT(*) FROM users WHERE role='HR'")
hr_count = c.fetchone()[0]

if hr_count == 0:
    admin_pw_hash = bcrypt.hashpw("Admin@12345".encode("utf-8"), bcrypt.gensalt())
    now_ts = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO users (username, password, role, email, created_at) VALUES (?, ?, ?, ?, ?)",
        ("admin", admin_pw_hash, "HR", "admin@company.com", now_ts)
    )
    print("🔑 Seeded default HR Admin account: (admin / Admin@12345)")

c.execute("SELECT COUNT(*) FROM users WHERE role='Candidate'")
cand_count = c.fetchone()[0]

if cand_count == 0:
    cand_pw_hash = bcrypt.hashpw("Candidate@12345".encode("utf-8"), bcrypt.gensalt())
    now_ts = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO users (username, password, role, email, created_at) VALUES (?, ?, ?, ?, ?)",
        ("candidate1", cand_pw_hash, "Candidate", "candidate1@example.com", now_ts)
    )
    print("👤 Seeded demo Candidate account: (candidate1 / Candidate@12345)")

conn.commit()
conn.close()

print("="*60)
print("✅ Database verification and repair completed successfully!")
print("="*60)

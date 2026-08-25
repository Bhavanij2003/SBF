

import sqlite3
import os
import datetime
import uuid
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "sbf_digitisation.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor(commit=False):
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the database file and all tables if they do not already exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    _migrate_add_missing_columns(conn)
    conn.close()


def _migrate_add_missing_columns(conn):

    wanted_columns = {
        "documents": [
            ("perspective_cropped", "INTEGER"),
            ("aligned_to_reference", "INTEGER"),
        ],
    }
    cur = conn.cursor()
    for table, columns in wanted_columns.items():
        cur.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cur.fetchall()}  # row[1] = column name
        for col_name, col_type in columns:
            if col_name not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
    conn.commit()


def new_document_number():
    """Generate a short, unique, human readable document number."""
    today = datetime.date.today().strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"SBF-{today}-{suffix}"


# ---------------------------------------------------------------------------
# documents
# ---------------------------------------------------------------------------

def create_document(form_type, original_file_path, uploaded_by, file_hash=None):
    doc_number = new_document_number()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO documents
               (document_number, form_type, original_file_path, upload_date,
                uploaded_by, processing_status, ocr_status, file_hash)
               VALUES (?, ?, ?, ?, ?, 'Uploaded', 'Pending', ?)""",
            (doc_number, form_type, original_file_path, now, uploaded_by, file_hash),
        )
        return cur.lastrowid, doc_number


def update_document_status(document_id, processing_status=None, ocr_status=None,
                            processed_file_path=None, verified_by=None,
                            perspective_cropped=None, aligned_to_reference=None):
    fields, values = [], []
    if processing_status is not None:
        fields.append("processing_status = ?")
        values.append(processing_status)
    if ocr_status is not None:
        fields.append("ocr_status = ?")
        values.append(ocr_status)
    if processed_file_path is not None:
        fields.append("processed_file_path = ?")
        values.append(processed_file_path)
    if perspective_cropped is not None:
        fields.append("perspective_cropped = ?")
        values.append(1 if perspective_cropped else 0)
    if aligned_to_reference is not None:
        fields.append("aligned_to_reference = ?")
        values.append(1 if aligned_to_reference else 0)
    if verified_by is not None:
        fields.append("verified_by = ?")
        values.append(verified_by)
        fields.append("verified_date = ?")
        values.append(datetime.datetime.now().isoformat(timespec="seconds"))
    if not fields:
        return
    values.append(document_id)
    with db_cursor(commit=True) as cur:
        cur.execute(f"UPDATE documents SET {', '.join(fields)} WHERE document_id = ?", values)


def get_document(document_id):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def find_duplicate_by_hash(file_hash):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_documents(status=None, form_type=None, limit=200):
    query = "SELECT * FROM documents WHERE 1=1"
    params = []
    if status:
        query += " AND processing_status = ?"
        params.append(status)
    if form_type:
        query += " AND form_type = ?"
        params.append(form_type)
    query += " ORDER BY document_id DESC LIMIT ?"
    params.append(limit)
    with db_cursor() as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# extracted_fields
# ---------------------------------------------------------------------------

def save_extracted_fields(document_id, fields):
    with db_cursor(commit=True) as cur:
        cur.execute("DELETE FROM extracted_fields WHERE document_id = ?", (document_id,))
        for f in fields:
            cur.execute(
                """INSERT INTO extracted_fields
                   (document_id, field_name, field_type, ocr_value, corrected_value,
                    confidence_score, verified_status, region_x, region_y, region_w, region_h)
                   VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?, ?, ?)""",
                (document_id, f["field_name"], f.get("field_type", "text"),
                 f.get("ocr_value"), f.get("ocr_value"), f.get("confidence_score"),
                 f.get("region_x"), f.get("region_y"), f.get("region_w"), f.get("region_h")),
            )


def get_extracted_fields(document_id):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM extracted_fields WHERE document_id = ? ORDER BY field_id",
                     (document_id,))
        return [dict(r) for r in cur.fetchall()]


def update_corrected_fields(document_id, corrections):
    """corrections: dict field_name -> corrected_value"""
    with db_cursor(commit=True) as cur:
        for field_name, value in corrections.items():
            cur.execute(
                """UPDATE extracted_fields
                   SET corrected_value = ?,
                       verified_status = CASE WHEN ocr_value IS NOT ? THEN 'Corrected' ELSE 'Confirmed' END
                   WHERE document_id = ? AND field_name = ?""",
                (value, value, document_id, field_name),
            )


# ---------------------------------------------------------------------------
# deposit_applications / share_applications
# ---------------------------------------------------------------------------

def upsert_deposit_application(document_id, data: dict):
    columns = [c for c in data.keys()]
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT application_id FROM deposit_applications WHERE document_id = ?",
                     (document_id,))
        row = cur.fetchone()
        if row:
            set_clause = ", ".join(f"{c} = ?" for c in columns)
            cur.execute(
                f"UPDATE deposit_applications SET {set_clause} WHERE document_id = ?",
                [data[c] for c in columns] + [document_id],
            )
            return row["application_id"]
        else:
            cols = ["document_id"] + columns
            placeholders = ", ".join(["?"] * len(cols))
            cur.execute(
                f"INSERT INTO deposit_applications ({', '.join(cols)}) VALUES ({placeholders})",
                [document_id] + [data[c] for c in columns],
            )
            return cur.lastrowid


def upsert_share_application(document_id, data: dict):
    columns = [c for c in data.keys()]
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT application_id FROM share_applications WHERE document_id = ?",
                     (document_id,))
        row = cur.fetchone()
        if row:
            set_clause = ", ".join(f"{c} = ?" for c in columns)
            cur.execute(
                f"UPDATE share_applications SET {set_clause} WHERE document_id = ?",
                [data[c] for c in columns] + [document_id],
            )
            return row["application_id"]
        else:
            cols = ["document_id"] + columns
            placeholders = ", ".join(["?"] * len(cols))
            cur.execute(
                f"INSERT INTO share_applications ({', '.join(cols)}) VALUES ({placeholders})",
                [document_id] + [data[c] for c in columns],
            )
            return cur.lastrowid


def search_applications(filters: dict):

    results = []
    with db_cursor() as cur:
        # Deposit applications
        q = """SELECT d.document_id, d.document_number, d.form_type, d.processing_status,
                      da.first_depositor_name AS customer_name, da.phone_number,
                      da.deposit_type, da.amount, da.nominee_name, da.application_date,
                      da.account_number, NULL as share_number
               FROM documents d JOIN deposit_applications da ON d.document_id = da.document_id
               WHERE 1=1"""
        params = []
        if filters.get("customer_name"):
            q += " AND da.first_depositor_name LIKE ?"
            params.append(f"%{filters['customer_name']}%")
        if filters.get("phone_number"):
            q += " AND da.phone_number LIKE ?"
            params.append(f"%{filters['phone_number']}%")
        if filters.get("deposit_account_number"):
            q += " AND da.account_number LIKE ?"
            params.append(f"%{filters['deposit_account_number']}%")
        if filters.get("application_date"):
            q += " AND da.application_date = ?"
            params.append(filters["application_date"])
        if filters.get("deposit_type"):
            q += " AND da.deposit_type = ?"
            params.append(filters["deposit_type"])
        if filters.get("nominee_name"):
            q += " AND da.nominee_name LIKE ?"
            params.append(f"%{filters['nominee_name']}%")
        if filters.get("processing_status"):
            q += " AND d.processing_status = ?"
            params.append(filters["processing_status"])
        cur.execute(q, params)
        results.extend(dict(r) for r in cur.fetchall())

        # Share applications
        q = """SELECT d.document_id, d.document_number, d.form_type, d.processing_status,
                      sa.applicant_name AS customer_name, NULL as phone_number,
                      NULL as deposit_type, sa.amount_received AS amount,
                      sa.nominee_name, sa.application_date, NULL as account_number,
                      sa.share_number
               FROM documents d JOIN share_applications sa ON d.document_id = sa.document_id
               WHERE 1=1"""
        params = []
        if filters.get("customer_name"):
            q += " AND sa.applicant_name LIKE ?"
            params.append(f"%{filters['customer_name']}%")
        if filters.get("share_number"):
            q += " AND sa.share_number LIKE ?"
            params.append(f"%{filters['share_number']}%")
        if filters.get("application_date"):
            q += " AND sa.application_date = ?"
            params.append(filters["application_date"])
        if filters.get("nominee_name"):
            q += " AND sa.nominee_name LIKE ?"
            params.append(f"%{filters['nominee_name']}%")
        if filters.get("processing_status"):
            q += " AND d.processing_status = ?"
            params.append(filters["processing_status"])
        cur.execute(q, params)
        results.extend(dict(r) for r in cur.fetchall())

    return results


def share_number_exists(share_number, exclude_document_id=None):
    with db_cursor() as cur:
        if exclude_document_id:
            cur.execute(
                "SELECT 1 FROM share_applications WHERE share_number = ? AND document_id != ?",
                (share_number, exclude_document_id))
        else:
            cur.execute("SELECT 1 FROM share_applications WHERE share_number = ?", (share_number,))
        return cur.fetchone() is not None


def log_action(document_id, action, performed_by, details=""):
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO audit_log (document_id, action, performed_by, performed_at, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (document_id, action, performed_by, now, details),
        )

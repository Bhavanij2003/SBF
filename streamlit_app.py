"""
SBF Form Digitisation — Streamlit UI
=====================================

Single-file Streamlit replacement for the FastAPI + HTML/JS frontend.

It reuses the existing pipeline modules in backend/ UNCHANGED:
    preprocessing.py, ocr_engine.py, validation.py, database.py,
    export_utils.py, templates_config.py

so OCR results, validation rules, and the database schema/output are
identical to the FastAPI version — only the UI layer changed.

Run locally:
    pip install -r requirements_streamlit.txt
    streamlit run streamlit_app.py

Deploy on Hugging Face Spaces:
    Space SDK = "streamlit", app file = "streamlit_app.py"
"""

import os
import sys
import hashlib
import shutil
import datetime

import cv2
import numpy as np
import streamlit as st

# ---------------------------------------------------------------------------
# Make backend/ importable exactly like main.py does, then import the
# existing pipeline modules unchanged.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.append(BACKEND_DIR)

import database as db
import preprocessing as prep
import ocr_engine as ocr
import validation as val
import export_utils as exp
from templates_config import FORM_TEMPLATES, KEY_FIELDS

UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".pdf"}

BAND_EMOJI = {"green": "🟢", "orange": "🟠", "red": "🔴"}

STATUS_COLORS = {
    "Uploaded": "gray",
    "Processing": "orange",
    "Pending Verification": "blue",
    "Verified": "green",
    "Rejected": "red",
    "Duplicate": "violet",
}

# ---------------------------------------------------------------------------
# App-wide setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SBF Form Digitisation", page_icon="🗂️", layout="wide")
db.init_db()

if "staff_name" not in st.session_state:
    st.session_state.staff_name = "staff"


# ---------------------------------------------------------------------------
# Shared pipeline helpers
# ---------------------------------------------------------------------------
def _file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def process_upload(uploaded_file, uploaded_by, form_type_hint=None):
    """Mirrors POST /api/upload. Returns a result dict, same shape as the API."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXT:
        return {"error": f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXT)}"}

    tmp_name = f"tmp_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
    tmp_path = os.path.join(UPLOAD_DIR, tmp_name)
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    file_hash = _file_hash(tmp_path)
    dup = db.find_duplicate_by_hash(file_hash)
    if dup:
        os.remove(tmp_path)
        return {
            "error": "duplicate",
            "message": "This exact form appears to already be uploaded.",
            "existing_document_id": dup["document_id"],
            "existing_document_number": dup["document_number"],
        }

    document_id, doc_number = db.create_document("unknown", tmp_path, uploaded_by, file_hash)

    final_original_name = f"{doc_number}_original{ext}"
    final_original_path = os.path.join(UPLOAD_DIR, final_original_name)
    shutil.move(tmp_path, final_original_path)

    with db.db_cursor(commit=True) as cur:
        cur.execute("UPDATE documents SET original_file_path = ? WHERE document_id = ?",
                    (final_original_path, document_id))

    db.update_document_status(document_id, processing_status="Processing")

    try:
        image, prep_warnings = prep.preprocess_pipeline_verbose(final_original_path)

        if form_type_hint in FORM_TEMPLATES:
            form_type, type_conf = form_type_hint, 100.0
        else:
            form_type, type_conf = ocr.identify_form_type(image)

        if form_type in FORM_TEMPLATES:
            ref_path = os.path.join(BASE_DIR, FORM_TEMPLATES[form_type]["reference_image"])
            before_align = image.copy()
            image = prep.align_to_reference(image, ref_path)
            prep_warnings["aligned_to_reference"] = not np.array_equal(image, before_align)

        processed_path = os.path.join(PROCESSED_DIR, f"{doc_number}_processed.png")
        cv2.imwrite(processed_path, image)

        db.update_document_status(
            document_id,
            processing_status="Uploaded" if form_type == "unknown" else "Processing",
            processed_file_path=processed_path,
            perspective_cropped=prep_warnings.get("perspective_cropped"),
            aligned_to_reference=prep_warnings.get("aligned_to_reference"),
        )

        if form_type == "unknown":
            db.update_document_status(document_id, processing_status="Uploaded", ocr_status="Failed")
            return {
                "document_id": document_id,
                "document_number": doc_number,
                "form_type": "unknown",
                "form_type_confidence": type_conf,
                "preprocessing_warnings": prep_warnings,
                "message": "Could not automatically identify the form type. "
                           "Please re-upload and choose the form type manually.",
            }

        fields = ocr.extract_fields(image, form_type)
        db.save_extracted_fields(document_id, fields)

        with db.db_cursor(commit=True) as cur:
            cur.execute("UPDATE documents SET form_type = ? WHERE document_id = ?",
                        (form_type, document_id))

        db.update_document_status(document_id, processing_status="Pending Verification", ocr_status="Completed")
        db.log_action(document_id, "OCR_COMPLETE", uploaded_by, f"form_type={form_type}")

        return {
            "document_id": document_id,
            "document_number": doc_number,
            "form_type": form_type,
            "form_type_confidence": type_conf,
            "processing_status": "Pending Verification",
            "fields": fields,
            "key_fields": KEY_FIELDS.get(form_type, []),
            "preprocessing_warnings": prep_warnings,
        }

    except Exception as e:
        db.update_document_status(document_id, processing_status="Uploaded", ocr_status="Failed")
        db.log_action(document_id, "OCR_ERROR", uploaded_by, str(e))
        return {"error": f"Processing failed: {e}"}


def verify_document(document_id, corrected_fields, verified_by, action="approve"):
    """Mirrors POST /api/document/{id}/verify. Returns a result dict."""
    doc = db.get_document(document_id)
    if not doc:
        return {"error": "Document not found"}

    if action == "reject":
        db.update_document_status(document_id, processing_status="Rejected", verified_by=verified_by)
        db.log_action(document_id, "REJECTED", verified_by)
        return {"status": "Rejected"}

    if action == "duplicate":
        db.update_document_status(document_id, processing_status="Duplicate", verified_by=verified_by)
        db.log_action(document_id, "MARKED_DUPLICATE", verified_by)
        return {"status": "Duplicate"}

    db.update_corrected_fields(document_id, corrected_fields)

    if action == "draft":
        db.update_document_status(document_id, processing_status="Pending Verification")
        db.log_action(document_id, "DRAFT_SAVED", verified_by)
        return {"status": "Draft saved"}

    data = corrected_fields
    form_type = doc["form_type"]

    if form_type == "deposit":
        errors = val.validate_deposit(data)
    elif form_type == "share":
        errors = val.validate_share(data)
        if data.get("share_number") and db.share_number_exists(data["share_number"], exclude_document_id=document_id):
            errors.append("Share number should not be duplicated - this share number already exists.")
    else:
        return {"error": "Unknown form type; cannot approve."}

    if errors:
        return {"status": "Validation failed", "errors": errors}

    if form_type == "deposit":
        allowed_cols = [
            "application_date", "deposit_type", "amount", "amount_in_words", "deposit_term", "term_unit",
            "payment_mode", "cheque_or_draft_number", "bank_name", "remittance_date", "remittance_place",
            "renewal_indicator", "existing_fd_rd_number", "maturity_date", "maturity_amount",
            "first_depositor_name", "first_depositor_age", "first_depositor_guardian",
            "second_depositor_name", "second_depositor_age", "second_depositor_guardian",
            "nominee_name", "nominee_relationship", "nominee_age", "address", "pincode",
            "phone_number", "occupation", "share_number", "folio_number", "account_type",
            "interest_option", "tax_deducted", "payment_of_interest", "account_number",
            "introducer_name", "introducer_address",
            "first_depositor_signature_present", "second_depositor_signature_present",
        ]
        mapped = dict(data)
        if "deposit_amount_figures" in mapped:
            mapped["amount"] = mapped.pop("deposit_amount_figures")
        if "deposit_amount_words" in mapped:
            mapped["amount_in_words"] = mapped.pop("deposit_amount_words")
        if "first_depositor_signature" in mapped:
            mapped["first_depositor_signature_present"] = mapped.pop("first_depositor_signature")
        if "second_depositor_signature" in mapped:
            mapped["second_depositor_signature_present"] = mapped.pop("second_depositor_signature")
        row = {k: mapped.get(k) for k in allowed_cols if k in mapped}
        db.upsert_deposit_application(document_id, row)
    else:
        allowed_cols = [
            "application_date", "share_number", "applicant_name", "age", "nationality",
            "father_or_husband_name", "door_number", "street_name", "postal_address",
            "nominee_name", "nominee_age", "nominee_relationship", "witness_1", "witness_2",
            "applicant_signature_present", "application_received_date", "amount_received",
            "payment_mode", "clerk_approval", "cashier_approval", "secretary_md_approval",
        ]
        mapped = dict(data)
        if "applicant_signature" in mapped:
            mapped["applicant_signature_present"] = mapped.pop("applicant_signature")
        row = {k: mapped.get(k) for k in allowed_cols if k in mapped}
        db.upsert_share_application(document_id, row)

    db.update_document_status(document_id, processing_status="Verified", verified_by=verified_by)
    db.log_action(document_id, "APPROVED", verified_by)
    return {"status": "Verified"}


def field_widget(field, key_prefix):
    """Render the right input widget for a field, based on its type."""
    name = field["field_name"]
    ftype = field["field_type"]
    current = field.get("corrected_value") if field.get("corrected_value") is not None else field.get("ocr_value") or ""
    label = name.replace("_", " ").title()
    key = f"{key_prefix}_{name}"

    if ftype == "checkbox_group":
        cfg = FORM_TEMPLATES[st.session_state.verify_form_type]["fields"][name]
        options = [""] + list(cfg["options"].keys())
        idx = options.index(current) if current in options else 0
        return st.selectbox(label, options, index=idx, key=key)

    if ftype == "signature":
        options = ["Signature present", "Signature not present", "Unable to determine"]
        idx = options.index(current) if current in options else 2
        return st.selectbox(label, options, index=idx, key=key)

    return st.text_input(label, value=current, key=key)


# ---------------------------------------------------------------------------
# Sidebar — navigation + staff identity
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🗂️ SBF Digitisation")
    st.session_state.staff_name = st.text_input("Staff name", value=st.session_state.staff_name)
    page = st.radio("Go to", ["📊 Dashboard", "📤 Upload", "✅ Verify", "🔍 Search & Export"])
    st.caption("Prototype — OCR with mandatory human verification.")

# ---------------------------------------------------------------------------
# 📊 Dashboard
# ---------------------------------------------------------------------------
if page == "📊 Dashboard":
    st.header("Processing queue")

    docs = db.list_documents(limit=500)
    counts = {}
    for d in docs:
        counts[d["processing_status"]] = counts.get(d["processing_status"], 0) + 1

    cols = st.columns(max(len(counts), 1) or 1)
    for i, (status, n) in enumerate(sorted(counts.items())):
        cols[i % len(cols)].metric(status, n)

    st.divider()

    status_filter = st.selectbox(
        "Filter by status", ["All"] + sorted({d["processing_status"] for d in docs})
    )
    filtered = docs if status_filter == "All" else [d for d in docs if d["processing_status"] == status_filter]

    if not filtered:
        st.info("No documents yet. Upload a form to get started.")
    else:
        table = [
            {
                "Doc #": d["document_number"],
                "Form type": d["form_type"],
                "Status": d["processing_status"],
                "OCR status": d["ocr_status"],
                "Uploaded by": d["uploaded_by"],
                "Uploaded": d["upload_date"],
                "Verified by": d.get("verified_by") or "",
            }
            for d in filtered
        ]
        st.dataframe(table, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# 📤 Upload
# ---------------------------------------------------------------------------
elif page == "📤 Upload":
    st.header("Upload a form")

    uploaded_file = st.file_uploader("Deposit or Share application (JPG/PNG/PDF)",
                                      type=["jpg", "jpeg", "png", "pdf"])
    hint_label = st.selectbox("Form type", ["Auto-detect", "Deposit application", "Share application"])
    form_type_hint = {"Auto-detect": None, "Deposit application": "deposit", "Share application": "share"}[hint_label]

    if uploaded_file and st.button("Process form", type="primary"):
        with st.spinner("Preprocessing image, identifying form type and running OCR "
                         "(first run also loads the OCR models — can take a while)..."):
            result = process_upload(uploaded_file, st.session_state.staff_name, form_type_hint)

        if "error" in result:
            if result["error"] == "duplicate":
                st.warning(f"{result['message']} (existing doc: {result['existing_document_number']})")
            else:
                st.error(result["error"])
        elif result.get("form_type") == "unknown":
            st.warning(result["message"])
        else:
            st.success(f"Processed as **{result['form_type']}** application — "
                       f"document **{result['document_number']}** "
                       f"(type confidence: {result['form_type_confidence']:.0f}%)")

            warn = result.get("preprocessing_warnings", {})
            if warn.get("perspective_cropped"):
                st.caption("📐 Perspective correction was applied to this scan.")
            if warn.get("aligned_to_reference"):
                st.caption("🎯 Aligned to the reference template.")

            st.subheader("Extracted fields")
            rows = []
            for f in result["fields"]:
                band = ocr.confidence_band(f["confidence_score"])
                rows.append({
                    "Field": f["field_name"].replace("_", " ").title(),
                    "Value": f["ocr_value"],
                    "Confidence": f"{BAND_EMOJI[band]} {f['confidence_score']:.0f}%"
                    if f["confidence_score"] is not None else "—",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.info("Go to **✅ Verify** to review, correct, and approve this document.")

# ---------------------------------------------------------------------------
# ✅ Verify
# ---------------------------------------------------------------------------
elif page == "✅ Verify":
    st.header("Verify extracted data")

    pending = db.list_documents(status="Pending Verification")
    if not pending:
        st.info("Nothing waiting for verification right now.")
    else:
        options = {f"{d['document_number']} ({d['form_type']})": d["document_id"] for d in pending}
        choice = st.selectbox("Document", list(options.keys()))
        document_id = options[choice]

        doc = db.get_document(document_id)
        fields = db.get_extracted_fields(document_id)
        st.session_state.verify_form_type = doc["form_type"]

        left, right = st.columns([1, 1])
        with left:
            st.subheader("Scanned form")
            img_path = doc.get("processed_file_path")
            if img_path and os.path.exists(img_path):
                img = cv2.imread(img_path)
                if img is None:
                    st.warning("Processed image file exists but could not be read (it may be corrupted). Try re-uploading this document.")
                else:
                    try:
                        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
                    except TypeError:
                        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            else:
                st.warning("Processed image not found on disk.")

        with right:
            st.subheader("Fields")
            key_fields = set(KEY_FIELDS.get(doc["form_type"], []))
            corrected = {}

            with st.form("verify_form"):
                for f in fields:
                    band = ocr.confidence_band(f["confidence_score"])
                    conf_txt = f"{f['confidence_score']:.0f}%" if f["confidence_score"] is not None else "—"
                    star = "⭐ " if f["field_name"] in key_fields else ""
                    st.caption(f"{star}{BAND_EMOJI[band]} confidence: {conf_txt}")
                    corrected[f["field_name"]] = field_widget(f, key_prefix=f"v{document_id}")

                c1, c2, c3, c4 = st.columns(4)
                save_draft = c1.form_submit_button("💾 Save draft")
                approve = c2.form_submit_button("✅ Approve", type="primary")
                reject = c3.form_submit_button("🚫 Reject")
                duplicate = c4.form_submit_button("🔁 Mark duplicate")

            action = None
            if save_draft:
                action = "draft"
            elif approve:
                action = "approve"
            elif reject:
                action = "reject"
            elif duplicate:
                action = "duplicate"

            if action:
                result = verify_document(document_id, corrected, st.session_state.staff_name, action)
                if result.get("errors"):
                    st.error("Validation failed:")
                    for e in result["errors"]:
                        st.write(f"- {e}")
                elif result.get("error"):
                    st.error(result["error"])
                else:
                    st.success(result["status"])
                    st.rerun()

# ---------------------------------------------------------------------------
# 🔍 Search & Export
# ---------------------------------------------------------------------------
elif page == "🔍 Search & Export":
    st.header("Search applications")

    with st.form("search_form"):
        c1, c2, c3 = st.columns(3)
        customer_name = c1.text_input("Customer / applicant name")
        phone_number = c1.text_input("Phone number")
        nominee_name = c1.text_input("Nominee name")
        share_number = c2.text_input("Share number")
        deposit_account_number = c2.text_input("Deposit account number")
        deposit_type = c2.selectbox("Deposit type", ["", "Fixed Deposit", "Savings Deposit", "Recurring Deposit"])
        application_date = c3.text_input("Application date (as stored, e.g. 12/05/2025)")
        processing_status = c3.selectbox(
            "Status", ["", "Uploaded", "Processing", "Pending Verification", "Verified", "Rejected", "Duplicate"]
        )
        search_clicked = st.form_submit_button("Search", type="primary")

    if search_clicked:
        filters = {
            "customer_name": customer_name,
            "phone_number": phone_number,
            "share_number": share_number,
            "deposit_account_number": deposit_account_number,
            "application_date": application_date,
            "deposit_type": deposit_type,
            "nominee_name": nominee_name,
            "processing_status": processing_status,
        }
        filters = {k: v for k, v in filters.items() if v}
        st.session_state.search_results = db.search_applications(filters)

    results = st.session_state.get("search_results", [])
    if results:
        st.write(f"**{len(results)}** matching record(s)")
        st.dataframe(results, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        csv_path = exp.export_to_csv(results)
        with open(csv_path, "rb") as f:
            col1.download_button("⬇️ Download CSV", f, file_name=os.path.basename(csv_path), mime="text/csv")

        xlsx_path = exp.export_to_excel(results)
        with open(xlsx_path, "rb") as f:
            col2.download_button(
                "⬇️ Download Excel", f, file_name=os.path.basename(xlsx_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    elif "search_results" in st.session_state:
        st.info("No matching records.")

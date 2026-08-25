

import os
import sys
import hashlib
import shutil
import base64
import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database as db
import preprocessing as prep
import ocr_engine as ocr
import validation as val
import export_utils as exp
from templates_config import FORM_TEMPLATES, KEY_FIELDS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".pdf"}

app = FastAPI(title="SBF Form Digitisation API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prototype only - restrict in production (see section 18)
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    db.init_db()


# Serve uploaded/processed images so the verification screen can display them.
# In production this should sit behind authentication (section 18: "No public
# document URLs") - see README "Security notes".
app.mount("/files/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/files/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class VerifyPayload(BaseModel):
    corrected_fields: dict            # field_name -> corrected value
    verified_by: str
    action: str = "approve"           # approve | reject | draft | duplicate


class SearchPayload(BaseModel):
    customer_name: Optional[str] = None
    phone_number: Optional[str] = None
    share_number: Optional[str] = None
    deposit_account_number: Optional[str] = None
    application_date: Optional[str] = None
    deposit_type: Optional[str] = None
    nominee_name: Optional[str] = None
    processing_status: Optional[str] = None


# ---------------------------------------------------------------------------
# Upload + processing pipeline
# ---------------------------------------------------------------------------

def _file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    uploaded_by: str = Form("staff"),
    form_type_hint: Optional[str] = Form(None),  # optional manual override
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXT)}")

    tmp_name = f"tmp_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
    tmp_path = os.path.join(UPLOAD_DIR, tmp_name)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_hash = _file_hash(tmp_path)
    dup = db.find_duplicate_by_hash(file_hash)
    if dup:
        os.remove(tmp_path)
        return JSONResponse(
            status_code=409,
            content={"error": "duplicate", "message": "This exact form appears to already be uploaded.",
                     "existing_document_id": dup["document_id"], "existing_document_number": dup["document_number"]},
        )

    # Create the DB row first so we have a stable document_number for filenames
    document_id, doc_number = db.create_document("unknown", tmp_path, uploaded_by, file_hash)

    final_original_name = f"{doc_number}_original{ext}"
    final_original_path = os.path.join(UPLOAD_DIR, final_original_name)
    shutil.move(tmp_path, final_original_path)

    with db.db_cursor(commit=True) as cur:
        cur.execute("UPDATE documents SET original_file_path = ? WHERE document_id = ?",
                     (final_original_path, document_id))

    db.update_document_status(document_id, processing_status="Processing")

    try:
        # --- Step 1-2: preprocessing (rotation, perspective, denoise, resize) ---
        image, prep_warnings = prep.preprocess_pipeline_verbose(final_original_path)

        # --- Step 3: identify form type ---
        if form_type_hint in FORM_TEMPLATES:
            form_type, type_conf = form_type_hint, 100.0
        else:
            form_type, type_conf = ocr.identify_form_type(image)

        # try alignment against the blank reference template, if calibrated
        if form_type in FORM_TEMPLATES:
            ref_path = os.path.join(BASE_DIR, FORM_TEMPLATES[form_type]["reference_image"])
            before_align = image.copy()
            image = prep.align_to_reference(image, ref_path)
            import numpy as _np
            prep_warnings["aligned_to_reference"] = not _np.array_equal(image, before_align)

        processed_path = os.path.join(PROCESSED_DIR, f"{doc_number}_processed.png")
        import cv2
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
                           "Please re-submit with form_type_hint='deposit' or 'share'.",
            }

        # --- Step 4-5: field-level OCR + checkbox/signature detection ---
        fields = ocr.extract_fields(image, form_type)
        db.save_extracted_fields(document_id, fields)

        # update form_type on the document now that we know it
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
        raise HTTPException(500, f"Processing failed: {e}")


@app.post("/api/document/{document_id}/reprocess")
def reprocess_document(document_id: int, form_type_hint: Optional[str] = Form(None)):
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    image = prep.preprocess_pipeline(doc["original_file_path"])
    form_type = form_type_hint if form_type_hint in FORM_TEMPLATES else doc["form_type"]
    if form_type not in FORM_TEMPLATES:
        form_type, _ = ocr.identify_form_type(image)
    if form_type not in FORM_TEMPLATES:
        raise HTTPException(400, "Could not identify form type; pass form_type_hint explicitly.")

    ref_path = os.path.join(BASE_DIR, FORM_TEMPLATES[form_type]["reference_image"])
    image = prep.align_to_reference(image, ref_path)

    fields = ocr.extract_fields(image, form_type)
    db.save_extracted_fields(document_id, fields)
    with db.db_cursor(commit=True) as cur:
        cur.execute("UPDATE documents SET form_type = ? WHERE document_id = ?", (form_type, document_id))
    db.update_document_status(document_id, processing_status="Pending Verification", ocr_status="Completed")
    db.log_action(document_id, "REPROCESSED", "staff")

    return {"document_id": document_id, "form_type": form_type, "fields": fields}


# ---------------------------------------------------------------------------
# Document / field retrieval
# ---------------------------------------------------------------------------

@app.get("/api/document/{document_id}")
def get_document(document_id: int):
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    fields = db.get_extracted_fields(document_id)
    for f in fields:
        f["confidence_band"] = ocr.confidence_band(f["confidence_score"])
    return {"document": doc, "fields": fields}


@app.get("/api/documents")
def list_documents(status: Optional[str] = None, form_type: Optional[str] = None):
    return db.list_documents(status=status, form_type=form_type)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

@app.post("/api/document/{document_id}/verify")
def verify_document(document_id: int, payload: VerifyPayload):
    doc = db.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    if payload.action == "reject":
        db.update_document_status(document_id, processing_status="Rejected", verified_by=payload.verified_by)
        db.log_action(document_id, "REJECTED", payload.verified_by)
        return {"status": "Rejected"}

    if payload.action == "duplicate":
        db.update_document_status(document_id, processing_status="Duplicate", verified_by=payload.verified_by)
        db.log_action(document_id, "MARKED_DUPLICATE", payload.verified_by)
        return {"status": "Duplicate"}

    # save corrections against extracted_fields regardless of draft/approve
    db.update_corrected_fields(document_id, payload.corrected_fields)

    if payload.action == "draft":
        db.update_document_status(document_id, processing_status="Pending Verification")
        db.log_action(document_id, "DRAFT_SAVED", payload.verified_by)
        return {"status": "Draft saved"}

    # action == approve -> validate, then write to the typed table
    data = payload.corrected_fields
    form_type = doc["form_type"]

    if form_type == "deposit":
        errors = val.validate_deposit(data)
    elif form_type == "share":
        errors = val.validate_share(data)
        if data.get("share_number") and db.share_number_exists(data["share_number"], exclude_document_id=document_id):
            errors.append("Share number should not be duplicated - this share number already exists.")
    else:
        raise HTTPException(400, "Unknown form type; cannot approve.")

    if errors:
        return JSONResponse(status_code=422, content={"status": "Validation failed", "errors": errors})

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
        # map the OCR field names used in templates_config to DB columns where they differ
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

    else:  # share
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
        if "postal_address" not in mapped and "postal_address" in allowed_cols:
            pass
        row = {k: mapped.get(k) for k in allowed_cols if k in mapped}
        db.upsert_share_application(document_id, row)

    db.update_document_status(document_id, processing_status="Verified", verified_by=payload.verified_by)
    db.log_action(document_id, "APPROVED", payload.verified_by)
    return {"status": "Verified"}


# ---------------------------------------------------------------------------
# Search + export
# ---------------------------------------------------------------------------

@app.post("/api/search")
def search(payload: SearchPayload):
    filters = {k: v for k, v in payload.dict().items() if v}
    return db.search_applications(filters)


@app.post("/api/export/csv")
def export_csv(payload: SearchPayload):
    filters = {k: v for k, v in payload.dict().items() if v}
    rows = db.search_applications(filters)
    if not rows:
        raise HTTPException(404, "No matching records to export.")
    path = exp.export_to_csv(rows)
    return FileResponse(path, filename=os.path.basename(path), media_type="text/csv")


@app.post("/api/export/excel")
def export_excel(payload: SearchPayload):
    filters = {k: v for k, v in payload.dict().items() if v}
    rows = db.search_applications(filters)
    if not rows:
        raise HTTPException(404, "No matching records to export.")
    path = exp.export_to_excel(rows)
    return FileResponse(
        path, filename=os.path.basename(path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.datetime.now().isoformat()}

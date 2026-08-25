-- Suryan Benefit Fund - Form Digitisation Prototype
-- SQLite schema

CREATE TABLE IF NOT EXISTS documents (
    document_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    document_number     TEXT UNIQUE NOT NULL,
    form_type           TEXT NOT NULL,               -- 'deposit' | 'share' | 'unknown'
    original_file_path  TEXT NOT NULL,
    processed_file_path TEXT,
    upload_date          TEXT NOT NULL,
    uploaded_by          TEXT,
    processing_status    TEXT NOT NULL DEFAULT 'Uploaded',
                          -- Uploaded, Processing, Pending Verification, Verified, Rejected, Duplicate
    ocr_status            TEXT DEFAULT 'Pending',
    verified_by           TEXT,
    verified_date         TEXT,
    file_hash             TEXT,
    perspective_cropped   INTEGER,   -- 1/0/NULL: did preprocessing confidently
                                      -- crop the photo to the paper's edges?
                                      -- 0 means background may still be in
                                      -- frame and field-crop coordinates may
                                      -- be unreliable (see Section 3 step 2).
    aligned_to_reference   INTEGER   -- 1/0/NULL: did ORB alignment against the
                                      -- blank template succeed for this scan?
);

CREATE TABLE IF NOT EXISTS deposit_applications (
    application_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id            INTEGER NOT NULL REFERENCES documents(document_id),
    application_date       TEXT,
    deposit_type            TEXT,
    amount                   TEXT,
    amount_in_words          TEXT,
    deposit_term              TEXT,
    term_unit                 TEXT,
    payment_mode               TEXT,
    cheque_or_draft_number     TEXT,
    bank_name                   TEXT,
    remittance_date              TEXT,
    remittance_place              TEXT,
    renewal_indicator              TEXT,
    existing_fd_rd_number           TEXT,
    maturity_date                    TEXT,
    maturity_amount                   TEXT,
    first_depositor_name               TEXT,
    first_depositor_age                 TEXT,
    first_depositor_guardian             TEXT,
    second_depositor_name                 TEXT,
    second_depositor_age                   TEXT,
    second_depositor_guardian               TEXT,
    nominee_name                             TEXT,
    nominee_relationship                      TEXT,
    nominee_age                                TEXT,
    address                                     TEXT,
    pincode                                      TEXT,
    phone_number                                  TEXT,
    occupation                                     TEXT,
    share_number                                    TEXT,
    folio_number                                     TEXT,
    account_type                                      TEXT,
    interest_option                                    TEXT,
    tax_deducted                                        TEXT,
    payment_of_interest                                  TEXT,
    account_number                                        TEXT,
    introducer_name                                        TEXT,
    introducer_address                                      TEXT,
    first_depositor_signature_present                       TEXT,
    second_depositor_signature_present                       TEXT
);

CREATE TABLE IF NOT EXISTS share_applications (
    application_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id           INTEGER NOT NULL REFERENCES documents(document_id),
    application_date        TEXT,
    share_number              TEXT,
    applicant_name             TEXT,
    age                          TEXT,
    nationality                   TEXT,
    father_or_husband_name         TEXT,
    door_number                     TEXT,
    street_name                      TEXT,
    postal_address                    TEXT,
    nominee_name                       TEXT,
    nominee_age                         TEXT,
    nominee_relationship                 TEXT,
    witness_1                             TEXT,
    witness_2                              TEXT,
    applicant_signature_present             TEXT,
    application_received_date                TEXT,
    amount_received                           TEXT,
    payment_mode                               TEXT,
    clerk_approval                              TEXT,
    cashier_approval                             TEXT,
    secretary_md_approval                         TEXT
);

CREATE TABLE IF NOT EXISTS extracted_fields (
    field_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id           INTEGER NOT NULL REFERENCES documents(document_id),
    field_name             TEXT NOT NULL,
    field_type              TEXT DEFAULT 'text',   -- text | checkbox | signature | date
    ocr_value                 TEXT,
    corrected_value            TEXT,
    confidence_score             REAL,
    verified_status               TEXT DEFAULT 'Pending',  -- Pending, Confirmed, Corrected
    region_x                       REAL, region_y REAL, region_w REAL, region_h REAL
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER,
    action          TEXT,
    performed_by     TEXT,
    performed_at      TEXT,
    details            TEXT
);

CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_deposit_doc ON deposit_applications(document_id);
CREATE INDEX IF NOT EXISTS idx_share_doc ON share_applications(document_id);
CREATE INDEX IF NOT EXISTS idx_fields_doc ON extracted_fields(document_id);

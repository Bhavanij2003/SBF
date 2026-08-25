# ---------------------------------------------------------------------------
# Coordinates below were re-calibrated by hand against the actual blank
# forms supplied by the fund (deposit_blank.jpg / share_blank.jpg, 1240x1755
# portrait JPEGs). All x/y/w/h are fractions of page width/height, top-left
# origin, matching the convention used by tools/calibrate_template.py.
# ---------------------------------------------------------------------------

DEPOSIT_FIELDS = {
    "application_date": {"x": 0.80,   "y": 0.058,  "w": 0.145,  "h": 0.022, "type": "date"},

    "deposit_type": {
        "type": "checkbox_group",
        "options": {
            "Fixed Deposit":     {"x": 0.043, "y": 0.113, "w": 0.018, "h": 0.016},
            "Savings Deposit":   {"x": 0.043, "y": 0.146, "w": 0.018, "h": 0.016},
            "Recurring Deposit": {"x": 0.043, "y": 0.179, "w": 0.018, "h": 0.016},
        },
    },
    "deposit_amount_figures": {"x": 0.395, "y": 0.116, "w": 0.40,  "h": 0.014, "type": "text"},
    "deposit_amount_words":   {"x": 0.395, "y": 0.136, "w": 0.35,  "h": 0.014, "type": "text"},
    "deposit_term":           {"x": 0.805, "y": 0.116, "w": 0.16,  "h": 0.014, "type": "text"},
    "term_unit":              {"x": 0.805, "y": 0.176, "w": 0.16,  "h": 0.014, "type": "text"},  # "MONTHS" is pre-printed; field kept for parity

    # These are the "From" checkboxes under REMITTANCE DETAILS (Bank Transfer/UPI, NEFT/RTGS, Cheque) —
    # the previous "Cheque/Draft/Cash" option set/positions belonged to a different form.
    "payment_mode": {
        "type": "checkbox_group",
        "options": {
            "Bank Transfer/UPI": {"x": 0.043, "y": 0.204, "w": 0.018, "h": 0.016},
            "NEFT/RTGS":         {"x": 0.043, "y": 0.224, "w": 0.018, "h": 0.016},
            "Cheque":            {"x": 0.043, "y": 0.244, "w": 0.018, "h": 0.016},
        },
    },
    "cheque_or_draft_number": {"x": 0.155, "y": 0.208, "w": 0.145, "h": 0.014, "type": "text"},  # "Number" column
    "bank_name":              {"x": 0.30,  "y": 0.208, "w": 0.185, "h": 0.014, "type": "text"},  # "Bank" column
    "remittance_date":        {"x": 0.155, "y": 0.253, "w": 0.145, "h": 0.014, "type": "date"},  # "Dated" column
    "remittance_place":       {"x": 0.30,  "y": 0.253, "w": 0.185, "h": 0.014, "type": "text"},  # "Place" column

    "renewal_indicator":      {"x": 0.02,  "y": 0.298, "w": 0.13,  "h": 0.013, "type": "text"},
    "existing_fd_rd_number":  {"x": 0.16,  "y": 0.298, "w": 0.14,  "h": 0.013, "type": "text"},
    "maturity_date":          {"x": 0.31,  "y": 0.298, "w": 0.175, "h": 0.013, "type": "date"},
    "maturity_amount":        {"x": 0.16,  "y": 0.318, "w": 0.56,  "h": 0.013, "type": "text"},  # "Amount Rs." row

    "first_depositor_name":      {"x": 0.02,  "y": 0.348, "w": 0.375, "h": 0.013, "type": "text"},
    "first_depositor_age":       {"x": 0.415, "y": 0.348, "w": 0.07,  "h": 0.013, "type": "text"},
    "first_depositor_guardian":  {"x": 0.02,  "y": 0.370, "w": 0.46,  "h": 0.013, "type": "text"},
    "first_depositor_signature": {"x": 0.02,  "y": 0.618, "w": 0.46,  "h": 0.028, "type": "signature"},

    "second_depositor_name":      {"x": 0.02,  "y": 0.398, "w": 0.375, "h": 0.013, "type": "text"},
    "second_depositor_age":       {"x": 0.415, "y": 0.398, "w": 0.07,  "h": 0.013, "type": "text"},
    "second_depositor_guardian":  {"x": 0.02,  "y": 0.436, "w": 0.46,  "h": 0.013, "type": "text"},
    "second_depositor_signature": {"x": 0.02,  "y": 0.661, "w": 0.46,  "h": 0.028, "type": "signature"},

    "nominee_name":         {"x": 0.09,  "y": 0.468, "w": 0.395, "h": 0.013, "type": "text"},
    "nominee_relationship": {"x": 0.09,  "y": 0.488, "w": 0.30,  "h": 0.013, "type": "text"},
    "nominee_age":          {"x": 0.415, "y": 0.488, "w": 0.07,  "h": 0.013, "type": "text"},

    "address":       {"x": 0.545, "y": 0.183, "w": 0.42,  "h": 0.013, "type": "text"},
    "pincode":       {"x": 0.605, "y": 0.208, "w": 0.36,  "h": 0.013, "type": "text"},
    "phone_number":  {"x": 0.605, "y": 0.228, "w": 0.36,  "h": 0.013, "type": "text"},
    "occupation":    {"x": 0.605, "y": 0.256, "w": 0.36,  "h": 0.013, "type": "text"},

    "share_number":  {"x": 0.02,  "y": 0.500, "w": 0.465, "h": 0.013, "type": "text"},
    "folio_number":  {"x": 0.02,  "y": 0.517, "w": 0.465, "h": 0.013, "type": "text"},

    # Real form only has THREE account-type checkboxes; "Jointly" is part of the first
    # option's label, not a separate box.
    "account_type": {
        "type": "checkbox_group",
        "options": {
            "Sole/First Depositor/Jointly": {"x": 0.487, "y": 0.502, "w": 0.016, "h": 0.016},
            "Either or Survivor":           {"x": 0.487, "y": 0.532, "w": 0.016, "h": 0.016},
            "Any one or Survivor":          {"x": 0.487, "y": 0.562, "w": 0.016, "h": 0.016},
        },
    },

    "interest_option": {
        "type": "checkbox_group",
        "options": {
            "Monthly":     {"x": 0.535, "y": 0.278, "w": 0.017, "h": 0.017},
            "Quarterly":   {"x": 0.732, "y": 0.278, "w": 0.017, "h": 0.017},
            "Half-Yearly": {"x": 0.535, "y": 0.312, "w": 0.017, "h": 0.017},
            "Yearly":      {"x": 0.732, "y": 0.312, "w": 0.017, "h": 0.017},
        },
    },
    "tax_deducted": {
        "type": "checkbox_group",
        "options": {
            "Yes":            {"x": 0.535, "y": 0.362, "w": 0.017, "h": 0.017},
            "No":              {"x": 0.732, "y": 0.362, "w": 0.017, "h": 0.017},
            "Not Applicable":   {"x": 0.535, "y": 0.396, "w": 0.017, "h": 0.017},
        },
    },
    "payment_of_interest": {
        "type": "checkbox_group",
        "options": {
            "Collect Cash":               {"x": 0.535, "y": 0.429, "w": 0.017, "h": 0.017},
            "Collect Post-Dated Cheque":   {"x": 0.535, "y": 0.463, "w": 0.017, "h": 0.017},
            "Credit to SBF/Other Account": {"x": 0.535, "y": 0.418, "w": 0.017, "h": 0.017},  # "To credit SB A/c No." box
        },
    },
    "credit_sb_account_number": {"x": 0.655, "y": 0.428, "w": 0.31, "h": 0.013, "type": "text"},  # blank after "A/c No."

    # "F.D / RD / S.B / OTHER / NO," line in the FOR OFFICE USE ONLY box (closest real
    # equivalent to a stored account/reference number on this form).
    "account_number":     {"x": 0.02,  "y": 0.718, "w": 0.375, "h": 0.014, "type": "text"},

    "introducer_name":    {"x": 0.535, "y": 0.463, "w": 0.42,  "h": 0.013, "type": "text"},
    "introducer_address": {"x": 0.535, "y": 0.483, "w": 0.42,  "h": 0.013, "type": "text"},
}

SHARE_FIELDS = {
    "application_date": {"x": 0.77,   "y": 0.058,  "w": 0.185, "h": 0.013, "type": "date"},
    "share_number":     {"x": 0.52,   "y": 0.083,  "w": 0.435, "h": 0.013, "type": "text"},
    "applicant_name":   {"x": 0.10,   "y": 0.211,  "w": 0.865, "h": 0.013, "type": "text"},
    "age":              {"x": 0.06,   "y": 0.241,  "w": 0.24,  "h": 0.013, "type": "text"},
    "nationality":      {"x": 0.375,  "y": 0.241,  "w": 0.125, "h": 0.013, "type": "text"},
    "father_or_husband_name": {"x": 0.345, "y": 0.271, "w": 0.62,  "h": 0.013, "type": "text"},
    # The form has a single combined "Residence with door No. and Street." line —
    # both fields point at that same blank.
    "door_number":      {"x": 0.245,  "y": 0.30,   "w": 0.72,  "h": 0.013, "type": "text"},
    "street_name":      {"x": 0.245,  "y": 0.30,   "w": 0.72,  "h": 0.013, "type": "text"},
    "postal_address":   {"x": 0.145,  "y": 0.335,  "w": 0.82,  "h": 0.013, "type": "text"},
    "nominee_name":     {"x": 0.245,  "y": 0.395,  "w": 0.72,  "h": 0.013, "type": "text"},
    # Form combines these into one "Age and relationship of nominee" line; split in half.
    "nominee_age":      {"x": 0.26,   "y": 0.425,  "w": 0.14,  "h": 0.013, "type": "text"},
    "nominee_relationship": {"x": 0.40, "y": 0.425, "w": 0.565, "h": 0.013, "type": "text"},
    "witness_1":        {"x": 0.065,  "y": 0.492,  "w": 0.435, "h": 0.013, "type": "text"},
    "witness_2":        {"x": 0.065,  "y": 0.512,  "w": 0.435, "h": 0.013, "type": "text"},
    "applicant_signature": {"x": 0.68, "y": 0.508, "w": 0.285, "h": 0.038, "type": "signature"},
    "application_received_date": {"x": 0.16, "y": 0.558, "w": 0.12,  "h": 0.013, "type": "date"},
    "amount_received":  {"x": 0.20,   "y": 0.578,  "w": 0.22,  "h": 0.013, "type": "text"},

    # NOTE: the real form only prints "Amount by Cash/Cheque Rs." as a single label —
    # there are no separate tick-boxes for Cash vs Cheque on this form. Coordinates
    # below sit just before that label as a best-effort placeholder.
    "payment_mode": {
        "type": "checkbox_group",
        "options": {
            "Cash":   {"x": 0.14, "y": 0.577, "w": 0.02, "h": 0.013},
            "Cheque": {"x": 0.16, "y": 0.577, "w": 0.02, "h": 0.013},
        },
    },

    "clerk_approval":        {"x": 0.02, "y": 0.61, "w": 0.30, "h": 0.065, "type": "signature"},
    "cashier_approval":      {"x": 0.35, "y": 0.61, "w": 0.30, "h": 0.065, "type": "signature"},
    "secretary_md_approval": {"x": 0.68, "y": 0.61, "w": 0.29, "h": 0.065, "type": "signature"},
}

FORM_TEMPLATES = {
    "deposit": {
        "heading_keywords": ["DEPOSIT APPLICATION FORM", "DEPOSIT APPLICATION"],
        "reference_image": "data/templates/deposit_blank.png",
        "fields": DEPOSIT_FIELDS,
        "db_table": "deposit_applications",
    },
    "share": {
        "heading_keywords": ["APPLICATION FOR SHARE", "SHARE APPLICATION"],
        "reference_image": "data/templates/share_blank.png",
        "fields": SHARE_FIELDS,
        "db_table": "share_applications",
    },
}

KEY_FIELDS = {
    "deposit": [
        "application_date", "deposit_type", "deposit_amount_figures",
        "first_depositor_name", "phone_number", "address", "pincode",
        "nominee_name", "account_number", "maturity_date",
    ],
    "share": [
        "application_date", "share_number", "applicant_name", "age",
        "father_or_husband_name", "postal_address", "nominee_name",
        "amount_received", "payment_mode",
    ],
}

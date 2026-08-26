# ---------------------------------------------------------------------------
# Coordinates below were re-calibrated by hand against the actual blank
# forms supplied by the fund (deposit_blank.jpg / share_blank.jpg, 1240x1755
# portrait JPEGs). All x/y/w/h are fractions of page width/height, top-left
# origin, matching the convention used by tools/calibrate_template.py.
# ---------------------------------------------------------------------------
DEPOSIT_FIELDS = {
    "application_date": {"x": 0.8641, "y": 0.0423, "w": 0.0888, "h": 0.0136, "type": "date"},

    "deposit_type": {
        "type": "checkbox_group",
        "options": {
            "Fixed Deposit":     {"x": 0.0341, "y": 0.1086, "w": 0.0182, "h": 0.015},
            "Savings Deposit":   {"x": 0.0353, "y": 0.1286, "w": 0.0182, "h": 0.0118},
            "Recurring Deposit": {"x": 0.0353, "y": 0.1468, "w": 0.0171, "h": 0.0114},
        },
    },

    "deposit_amount_figures": {"x": 0.4518, "y": 0.1109, "w": 0.3447, "h": 0.0114, "type": "text"},
    "deposit_amount_words":   {"x": 0.4465, "y": 0.1223, "w": 0.3488, "h": 0.0232, "type": "text"},
    "deposit_term":           {"x": 0.8535, "y": 0.1441, "w": 0.0706, "h": 0.0191, "type": "text"},
    "term_unit":              {"x": 0.8588, "y": 0.1109, "w": 0.0694, "h": 0.0295, "type": "text"},

    "payment_mode": {
        "type": "checkbox_group",
        "options": {
            "Bank Transfer/UPI": {"x": 0.0341, "y": 0.2068, "w": 0.0194, "h": 0.0114},
            "NEFT/RTGS":         {"x": 0.0365, "y": 0.2282, "w": 0.0171, "h": 0.0118},
            "Cheque":            {"x": 0.0353, "y": 0.2423, "w": 0.0171, "h": 0.0114},
        },
    },

    "cheque_or_draft_number": {"x": 0.1541, "y": 0.2041, "w": 0.1694, "h": 0.0495, "type": "text"},  # "Number" col
    "bank_name":              {"x": 0.3265, "y": 0.2068, "w": 0.1682, "h": 0.0495, "type": "text"},  # "Bank" col

    "remittance_date":  {"x": 0.1541, "y": 0.2655, "w": 0.1629, "h": 0.0191, "type": "date"},
    "remittance_place":  {"x": 0.3212, "y": 0.2655, "w": 0.1724, "h": 0.0205, "type": "text"},

    "existing_fd_rd_number": {"x": 0.1276, "y": 0.2945, "w": 0.1806, "h": 0.0168, "type": "text"},  # "FD/RD No."

    "maturity_date":   {"x": 0.3147, "y": 0.2959, "w": 0.18,   "h": 0.0168, "type": "date"},
    "maturity_amount": {"x": 0.1071, "y": 0.3127, "w": 0.1029, "h": 0.0164, "type": "text"},   # "Amount Rs." row

    "first_depositor_name":      {"x": 0.03,   "y": 0.3391, "w": 0.3488, "h": 0.0205, "type": "text"},
    "first_depositor_age":       {"x": 0.4165, "y": 0.3318, "w": 0.0794, "h": 0.0227, "type": "text"},
    "first_depositor_guardian":  {"x": 0.03,   "y": 0.3673, "w": 0.3471, "h": 0.0191, "type": "text"},
    "first_depositor_signature": {"x": 0.2653, "y": 0.6123, "w": 0.2294, "h": 0.0241, "type": "signature"},

    "second_depositor_name":      {"x": 0.0312, "y": 0.3968, "w": 0.3424, "h": 0.0205, "type": "text"},
    "second_depositor_age":       {"x": 0.4188, "y": 0.3877, "w": 0.0771, "h": 0.0241, "type": "text"},
    "second_depositor_guardian":  {"x": 0.0324, "y": 0.4273, "w": 0.38,   "h": 0.0177, "type": "text"},
    "second_depositor_signature": {"x": 0.2818, "y": 0.6377, "w": 0.2171, "h": 0.0241, "type": "signature"},

    "nominee_name":         {"x": 0.1371, "y": 0.4577, "w": 0.3576, "h": 0.0155, "type": "text"},
    "nominee_relationship": {"x": 0.1176, "y": 0.4718, "w": 0.2453, "h": 0.0191, "type": "text"},
    "nominee_age":          {"x": 0.4124, "y": 0.4718, "w": 0.0835, "h": 0.0168, "type": "text"},

    "address":     {"x": 0.5041, "y": 0.1873, "w": 0.4647, "h": 0.0218, "type": "text"},
    "pincode":     {"x": 0.56,   "y": 0.2091, "w": 0.2153, "h": 0.0155, "type": "text"},
    "phone_number":{"x": 0.5729, "y": 0.2232, "w": 0.3488, "h": 0.0141, "type": "text"},
    "occupation":  {"x": 0.5771, "y": 0.2514, "w": 0.3929, "h": 0.0177, "type": "text"},

    # Not in schema, kept as a bonus field (won't map into deposit_applications
    # table, but will still show up during verification/extraction).
    "email": {"x": 0.5559, "y": 0.2359, "w": 0.2718, "h": 0.0141, "type": "text"},

    "share_number": {"x": 0.0394, "y": 0.4973, "w": 0.2241, "h": 0.0168, "type": "text"},
    "folio_number": {"x": 0.0441, "y": 0.5255, "w": 0.2171, "h": 0.0191, "type": "text"},

    "account_type": {
        "type": "checkbox_group",
        "options": {
            "Sole/First Depositor": {"x": 0.2688, "y": 0.5036, "w": 0.0159, "h": 0.0155},
            "Either or Survivor":   {"x": 0.2688, "y": 0.5232, "w": 0.0194, "h": 0.0127},
            "Anyone or Survivor":   {"x": 0.27,   "y": 0.5395, "w": 0.0159, "h": 0.01},
        },
    },

    "interest_option": {
        "type": "checkbox_group",
        "options": {
            "Monthly":     {"x": 0.5065, "y": 0.2832, "w": 0.0182, "h": 0.0155},
            "Quarterly":   {"x": 0.7376, "y": 0.2845, "w": 0.0171, "h": 0.0127},
            "Half-Yearly": {"x": 0.5076, "y": 0.3009, "w": 0.0171, "h": 0.0141},
            "Yearly":      {"x": 0.7388, "y": 0.305,  "w": 0.0147, "h": 0.0114},
        },
    },
    "tax_deducted": {
        "type": "checkbox_group",
        "options": {
            "Yes":           {"x": 0.5065, "y": 0.3305, "w": 0.0182, "h": 0.015},
            "No":             {"x": 0.7376, "y": 0.3341, "w": 0.0171, "h": 0.0114},
            "Not Applicable": {"x": 0.5094, "y": 0.3509, "w": 0.0153, "h": 0.0114},
        },
    },
    "payment_of_interest": {
        "type": "checkbox_group",
        "options": {
            "Collect Cash":               {"x": 0.5094, "y": 0.3814, "w": 0.0153, "h": 0.0114},
            "Collect Post-Dated Cheque":  {"x": 0.5094, "y": 0.3968, "w": 0.0153, "h": 0.0114},
            "Credit to SBF/Other Account":{"x": 0.5076, "y": 0.4182, "w": 0.0171, "h": 0.0118},
        },
    },

    "account_number": {"x": 0.6135, "y": 0.4095, "w": 0.3512, "h": 0.0227, "type": "text"},  # "F.D/RD/S.B/OTHER/NO,"

    "introducer_name":    {"x": 0.6212, "y": 0.4527, "w": 0.1124, "h": 0.0241, "type": "text"},
    "introducer_address": {"x": 0.7347, "y": 0.4527, "w": 0.2312, "h": 0.0255, "type": "text"},
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

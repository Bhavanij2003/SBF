

import re
import datetime


def _parse_date(value):
    if not value:
        return None
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def is_valid_phone(value):
    if not value:
        return False
    digits = re.sub(r"\D", "", value)
    return 10 <= len(digits) <= 13


def is_valid_pincode(value):
    if not value:
        return False
    digits = re.sub(r"\D", "", value)
    return len(digits) == 6


def is_reasonable_age(value):
    try:
        age = int(re.sub(r"\D", "", str(value)))
        return 0 < age <= 120
    except (ValueError, TypeError):
        return False


def is_numeric_amount(value):
    if not value:
        return False
    cleaned = re.sub(r"[,\s]", "", str(value))
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def is_valid_date(value):
    return _parse_date(value) is not None


def maturity_after_deposit(deposit_date, maturity_date):
    d1, d2 = _parse_date(deposit_date), _parse_date(maturity_date)
    if d1 and d2:
        return d2 > d1
    return True  # can't verify -> don't block, just skip


NUMBER_WORDS_HINT = re.compile(r"\d")


def amounts_roughly_match(figures, words):

    if not figures or not words:
        return True
    digits = re.sub(r"[^\d]", "", figures)
    return bool(digits)  # placeholder heuristic; flagged for manual check either way


def validate_deposit(data: dict):
    errors = []
    if data.get("phone_number") and not is_valid_phone(data["phone_number"]):
        errors.append("Phone number should contain 10-13 valid digits.")
    if data.get("pincode") and not is_valid_pincode(data["pincode"]):
        errors.append("Pincode should normally contain six digits.")
    if data.get("first_depositor_age") and not is_reasonable_age(data["first_depositor_age"]):
        errors.append("First depositor age should be a reasonable numeric value.")
    if data.get("nominee_age") and not is_reasonable_age(data["nominee_age"]):
        errors.append("Nominee age should be numeric and reasonable.")
    if data.get("deposit_amount_figures") and not is_numeric_amount(data["deposit_amount_figures"]):
        errors.append("Deposit amount (figures) should be numeric.")
    if data.get("application_date") and not is_valid_date(data["application_date"]):
        errors.append("Application date should be a valid date.")
    if data.get("remittance_date") and data.get("maturity_date"):
        if not maturity_after_deposit(data["remittance_date"], data["maturity_date"]):
            errors.append("Maturity date should normally be after the deposit date.")
    if not data.get("deposit_type"):
        errors.append("At least one deposit type must be selected.")
    if not (data.get("first_depositor_signature") == "Signature present"):
        errors.append("First depositor signature should be present.")
    return errors


def validate_share(data: dict):
    errors = []
    if data.get("age") and not is_reasonable_age(data["age"]):
        errors.append("Applicant age should be a reasonable numeric value.")
    if data.get("nominee_age") and not is_reasonable_age(data["nominee_age"]):
        errors.append("Nominee age should be numeric.")
    if data.get("amount_received") and not is_numeric_amount(data["amount_received"]):
        errors.append("Amount received should be numeric.")
    if data.get("application_date") and not is_valid_date(data["application_date"]):
        errors.append("Application date should be a valid date.")
    if not (data.get("applicant_signature") == "Signature present"):
        errors.append("Applicant signature should be present.")
    return errors

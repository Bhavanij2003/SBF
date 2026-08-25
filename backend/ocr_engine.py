

import os

import cv2
import numpy as np

from templates_config import FORM_TEMPLATES
from preprocessing import crop_region

# ---------------------------------------------------------------------------
# PaddleOCR singletons
# ---------------------------------------------------------------------------
# Override with environment variables if needed, e.g. (PowerShell):
#   $env:PADDLEOCR_DEVICE = "gpu:0"
#
# Default to the "mobile" model family rather than "server": on a 1 GB
# Streamlit Community Cloud instance the server detection+recognition
# models (~200MB+ combined, plus PaddlePaddle's own overhead) reliably
# push the app past the memory limit and get OOM-killed. The mobile
# models are a fraction of the size with a modest accuracy trade-off.
# Override PADDLEOCR_REC_MODEL / PADDLEOCR_DET_MODEL back to the
# *_server_* variants if you deploy somewhere with more RAM.
_PADDLEOCR_DEVICE = os.environ.get("PADDLEOCR_DEVICE", "cpu")
_PADDLEOCR_REC_MODEL = os.environ.get("PADDLEOCR_REC_MODEL", "PP-OCRv5_mobile_rec")
_PADDLEOCR_DET_MODEL = os.environ.get("PADDLEOCR_DET_MODEL", "PP-OCRv5_mobile_det")

_text_recognizer = None
_ocr_pipeline = None


def _get_text_recognizer():
    """Recognition-only model, used on pre-cropped single-field images."""
    global _text_recognizer
    if _text_recognizer is None:
        from paddleocr import TextRecognition
        _text_recognizer = TextRecognition(
            model_name=_PADDLEOCR_REC_MODEL,

            enable_mkldnn=False,
        )
    return _text_recognizer


def _get_ocr_pipeline():
 
    global _ocr_pipeline
    if _ocr_pipeline is None:
        from paddleocr import PaddleOCR
        _ocr_pipeline = PaddleOCR(
            text_detection_model_name=_PADDLEOCR_DET_MODEL,
            text_recognition_model_name=_PADDLEOCR_REC_MODEL,
            device=_PADDLEOCR_DEVICE,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            # See note in _get_text_recognizer() above.
            enable_mkldnn=False,
        )
    return _ocr_pipeline


# ---------------------------------------------------------------------------
# Form type identification
# ---------------------------------------------------------------------------

def _match_heading(text):
    for form_type, cfg in FORM_TEMPLATES.items():
        for kw in cfg["heading_keywords"]:
            if kw in text:
                return form_type, 95.0
    if "DEPOSIT" in text and "APPLICATION" in text:
        return "deposit", 60.0
    if "SHARE" in text:
        return "share", 60.0
    return None


def _ocr_region_text(image_bgr):

    if image_bgr is None or image_bgr.size == 0:
        return ""
    pipeline = _get_ocr_pipeline()
    results = pipeline.predict(image_bgr)
    lines = []
    for res in results:
        lines.extend(res.get("rec_texts", []) or [])
    return " ".join(lines).upper()


def identify_form_type(image):

    h, w = image.shape[:2]

    for frac in (0.15, 0.30, 0.45):
        header_crop = image[0:int(h * frac), 0:w]
        text = _ocr_region_text(header_crop)
        match = _match_heading(text)
        if match:
            form_type, conf = match
            # Lower confidence slightly for the larger, less-targeted windows
            # so callers can tell an easy top-15% match from a rescued one.
            if frac > 0.15:
                conf = min(conf, 70.0)
            return form_type, conf

    # Last resort: OCR the whole page (slow but catches badly-cropped photos
    # where the heading ended up anywhere on the page).
    text_full = _ocr_region_text(image)
    match = _match_heading(text_full)
    if match:
        form_type, _ = match
        return form_type, 40.0  # low confidence: rescued from a full-page scan

    return "unknown", 0.0


# ---------------------------------------------------------------------------
# Text field OCR
# ---------------------------------------------------------------------------

_MIN_REC_HEIGHT = 48  # PP-OCR recognition models are trained around this line
                       # height; upscale shorter crops rather than feed tiny text in.


def _prep_for_ocr(crop_bgr):

    if crop_bgr.size == 0:
        return crop_bgr
    h = crop_bgr.shape[0]
    if h < _MIN_REC_HEIGHT:
        scale = _MIN_REC_HEIGHT / max(h, 1)
        crop_bgr = cv2.resize(crop_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return crop_bgr


def ocr_text_with_confidence(crop_bgr, psm=7):

    if crop_bgr is None or crop_bgr.size == 0:
        return "", 0.0

    processed = _prep_for_ocr(crop_bgr)
    if processed.size == 0:
        return "", 0.0

    recognizer = _get_text_recognizer()
    results = recognizer.predict(processed)
    if not results:
        return "", 0.0

    res = results[0]
    text = (res.get("rec_text") or "").strip()
    score = res.get("rec_score") or 0.0
    return text, float(score) * 100.0


# ---------------------------------------------------------------------------
# Checkbox detection
# ---------------------------------------------------------------------------

def detect_checkbox(crop_bgr, selected_threshold=0.18, unclear_band=0.05):

    if crop_bgr is None or crop_bgr.size == 0:
        return "Unclear", 0.0

    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    dark_ratio = np.count_nonzero(thresh) / thresh.size

    if dark_ratio >= selected_threshold + unclear_band:
        return "Selected", min(99.0, 60 + dark_ratio * 100)
    elif dark_ratio <= selected_threshold - unclear_band:
        return "Not selected", min(99.0, 60 + (1 - dark_ratio) * 40)
    else:
        return "Unclear", 40.0


def detect_checkbox_group(image, options: dict):

    results = {}
    for label, region in options.items():
        crop = crop_region(image, region)
        status, conf = detect_checkbox(crop)
        results[label] = {"status": status, "confidence": conf}

    selected = [lbl for lbl, r in results.items() if r["status"] == "Selected"]
    if len(selected) == 1:
        return selected[0], results, results[selected[0]]["confidence"]
    elif len(selected) > 1:
        # ambiguous - multiple boxes look ticked; pick highest confidence, lower score
        best = max(selected, key=lambda l: results[l]["confidence"])
        return best, results, max(20.0, results[best]["confidence"] - 40)
    else:
        return None, results, 30.0


# ---------------------------------------------------------------------------
# Signature detection
# ---------------------------------------------------------------------------

def detect_signature(crop_bgr, ink_threshold=0.02, unclear_band=0.01):

    if crop_bgr is None or crop_bgr.size == 0:
        return "Unable to determine", 0.0

    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    ink_ratio = np.count_nonzero(thresh) / thresh.size

    ys, xs = np.nonzero(thresh)
    spread = 0.0
    if len(xs) > 5:
        spread = (np.std(xs) + np.std(ys)) / (thresh.shape[1] + thresh.shape[0])

    if ink_ratio >= ink_threshold + unclear_band and spread > 0.05:
        return "Signature present", min(95.0, 55 + ink_ratio * 500)
    elif ink_ratio <= ink_threshold - unclear_band:
        return "Signature not present", min(95.0, 70 + (1 - ink_ratio) * 20)
    else:
        return "Unable to determine", 35.0


# ---------------------------------------------------------------------------
# Full field-level extraction for a form
# ---------------------------------------------------------------------------

def extract_fields(image, form_type):

    cfg = FORM_TEMPLATES.get(form_type)
    if not cfg:
        return []

    results = []
    for field_name, region in cfg["fields"].items():
        ftype = region.get("type")

        if ftype == "checkbox_group":
            selected, per_option, conf = detect_checkbox_group(image, region["options"])
            results.append({
                "field_name": field_name,
                "field_type": "checkbox_group",
                "ocr_value": selected or "",
                "confidence_score": conf,
                "region_x": None, "region_y": None, "region_w": None, "region_h": None,
            })

        elif ftype == "signature":
            crop = crop_region(image, region)
            status, conf = detect_signature(crop)
            results.append({
                "field_name": field_name,
                "field_type": "signature",
                "ocr_value": status,
                "confidence_score": conf,
                "region_x": region["x"], "region_y": region["y"],
                "region_w": region["w"], "region_h": region["h"],
            })

        else:  # text or date
            crop = crop_region(image, region)
            text, conf = ocr_text_with_confidence(crop)
            results.append({
                "field_name": field_name,
                "field_type": ftype or "text",
                "ocr_value": text,
                "confidence_score": conf,
                "region_x": region["x"], "region_y": region["y"],
                "region_w": region["w"], "region_h": region["h"],
            })

    return results


def confidence_band(score):
    """Section 7: colour band for a confidence score."""
    if score is None:
        return "red"
    if score >= 90:
        return "green"
    if score >= 70:
        return "orange"
    return "red"

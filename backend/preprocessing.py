import cv2
import numpy as np
import os

STANDARD_WIDTH = 1700
STANDARD_HEIGHT = 2200

def load_image(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        import fitz
        doc = fitz.open(path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(200 / 72, 200 / 72))
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        doc.close()
        return img
    else:
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Could not read image at {path}")
        return img

def auto_rotate(image):
    try:
        import pytesseract
        osd = pytesseract.image_to_osd(image)
        angle = 0
        for line in osd.split("\n"):
            if "Rotate:" in line:
                angle = int(line.split(":")[1].strip())
                break
        if angle != 0:
            image = _rotate_bound(image, -angle)
    except Exception:
        pass
    return image

def _rotate_bound(image, angle):
    (h, w) = image.shape[:2]
    (cx, cy) = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    M[0, 2] += (nW / 2) - cx
    M[1, 2] += (nH / 2) - cy
    return cv2.warpAffine(image, M, (nW, nH), borderValue=(255, 255, 255))

def perspective_correct(image):
    orig = image.copy()
    h_orig, w_orig = image.shape[:2]
    
    # Downscale for fast contour detection
    ratio = h_orig / 1000.0
    small = cv2.resize(image, (int(w_orig / ratio), 1000))
    
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Morphological closing to seal form border gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)
    
    edged = cv2.Canny(closed, 30, 120)
    
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    doc_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # Relax minimum area threshold from 0.40 down to 0.20
        if len(approx) == 4 and cv2.contourArea(approx) > (0.20 * small.shape[0] * small.shape[1]):
            doc_contour = approx
            break
            
    if doc_contour is None:
        return orig

    pts = doc_contour.reshape(4, 2).astype("float32") * ratio
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect

    # Calculate real geometric side lengths
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    if maxWidth < 200 or maxHeight < 200:
        return orig

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")
    
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight), borderValue=(255, 255, 255))
    return warped

def _order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]       # top-left
    rect[2] = pts[np.argmax(s)]       # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]    # top-right
    rect[3] = pts[np.argmax(diff)]    # bottom-left
    return rect

def deskew(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if coords.shape[0] < 20:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) > 15:
        return image
    return _rotate_bound(image, angle)

def correct_brightness_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def denoise(image):
    return cv2.fastNlMeansDenoisingColored(image, None, 5, 5, 7, 21)

def resize_to_standard(image):
    return cv2.resize(image, (STANDARD_WIDTH, STANDARD_HEIGHT), interpolation=cv2.INTER_AREA)

def align_to_reference(image, reference_path):
    if not reference_path or not os.path.exists(reference_path):
        return image

    reference = cv2.imread(reference_path)
    if reference is None:
        return image

    gray1 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)

    # Increased keypoints for higher feature resolution on skewed inputs
    orb = cv2.ORB_create(5000)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)
    if des1 is None or des2 is None:
        return image

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(des1, des2)
    matches = sorted(matches, key=lambda m: m.distance)
    good = matches[: max(30, int(len(matches) * 0.20))]

    if len(good) < 10:
        return image

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    if H is None:
        return image

    h, w = reference.shape[:2]
    aligned = cv2.warpPerspective(image, H, (w, h), borderValue=(255, 255, 255))
    return aligned

# ---------------------------------------------------------------------------
# Inside backend/preprocessing.py
# ---------------------------------------------------------------------------
def preprocess_pipeline_verbose(input_path, reference_template_path=None, save_path=None):
    warnings = {"perspective_cropped": False, "aligned_to_reference": False}

    # Load original image directly without perspective warping
    image = load_image(input_path)
    image = auto_rotate(image)
    
    # Simple brightness and contrast cleanup only
    image = correct_brightness_contrast(image)
    image = resize_to_standard(image)

    if save_path:
        cv2.imwrite(save_path, image)
        
    return image, warnings

def crop_region(image, region):
    h, w = image.shape[:2]
    x1 = int(region["x"] * w)
    y1 = int(region["y"] * h)
    x2 = int((region["x"] + region["w"]) * w)
    y2 = int((region["y"] + region["h"]) * h)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return image[y1:y2, x1:x2]

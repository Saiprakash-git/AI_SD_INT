import cv2
import numpy as np


def preprocess_image(image_path):

    img = cv2.imread(image_path)

    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    # -------------------------
    # STEP 4: Increase Resolution
    # -------------------------
    img = cv2.resize(
        img,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Improve contrast (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Remove noise
    denoised = cv2.fastNlMeansDenoising(
        enhanced,
        None,
        30,
        7,
        21
    )

    # -------------------------
    # STEP 3: Crop Margins
    # -------------------------
    h, w = denoised.shape

    cropped = denoised[
        int(h * 0.1): int(h * 0.95),
        int(w * 0.05): int(w * 0.95)
    ]

    return cropped
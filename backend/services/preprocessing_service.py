"""Preprocessing service: image quality assessment and enhancement using OpenCV."""

from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image


def load_image(image_path: str) -> np.ndarray:
    """Load an image from disk as a BGR numpy array."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to load image: {image_path}")
    return image


def resize_image(image: np.ndarray, max_dimension: int = 1600) -> np.ndarray:
    """Resize image so its longest side is at most max_dimension, preserving aspect ratio."""
    height, width = image.shape[:2]
    if max(height, width) <= max_dimension:
        return image
    scale = max_dimension / max(height, width)
    new_size = (int(width * scale), int(height * scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def correct_rotation(image: np.ndarray) -> np.ndarray:
    """Attempt to correct image rotation based on dominant text lines (best effort)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
    if lines is None:
        return image
    angles = []
    for line in lines[:, 0, :]:
        x1, y1, x2, y2 = line
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        angles.append(angle)
    if not angles:
        return image
    median_angle = float(np.median(angles))
    # Only correct small rotations
    if abs(median_angle) > 0.5 and abs(median_angle) < 45:
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return image


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """Enhance contrast using CLAHE on the L channel of LAB color space."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def reduce_noise(image: np.ndarray) -> np.ndarray:
    """Reduce noise using fast non-local means denoising."""
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)


def sharpen(image: np.ndarray) -> np.ndarray:
    """Apply an unsharp masking sharpening filter."""
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)


def adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """Produce a binary adaptive-threshold version of the grayscale image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )


def assess_quality(image: np.ndarray) -> Dict[str, float]:
    """Assess image quality: blur (Laplacian variance), brightness, contrast."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())
    return {
        "blur_score": blur_score,
        "brightness": brightness,
        "contrast": contrast,
        "is_blurry": blur_score < 100.0,
    }


def preprocess(image_path: str, max_dimension: int = 1600) -> Tuple[np.ndarray, Dict[str, float]]:
    """Run the full preprocessing pipeline and return the processed image plus quality metrics."""
    image = load_image(image_path)
    quality = assess_quality(image)
    image = resize_image(image, max_dimension=max_dimension)
    image = correct_rotation(image)
    image = reduce_noise(image)
    image = enhance_contrast(image)
    image = sharpen(image)
    return image, quality

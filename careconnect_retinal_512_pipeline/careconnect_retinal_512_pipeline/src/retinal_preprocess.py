"""512x512 retinal preprocessing with green-channel CLAHE."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def load_rgb(image):
    if isinstance(image, (str, Path)):
        with Image.open(image) as im:
            return np.asarray(im.convert("RGB"), dtype=np.uint8)
    if isinstance(image, Image.Image):
        return np.asarray(image.convert("RGB"), dtype=np.uint8)
    arr = np.asarray(image)
    if arr.ndim != 3 or arr.shape[2] not in (3, 4):
        raise ValueError("Image array must have shape HxWx3 or HxWx4.")
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr[:, :, :3]

def preprocess_green_clahe(image, size=512, clip_limit=2.0, tile_grid=(8, 8)):
    """Return (resized RGB image, green-channel CLAHE grayscale image)."""
    if size < 1:
        raise ValueError("size must be positive.")
    rgb = load_rgb(image)
    interp = cv2.INTER_AREA if max(rgb.shape[:2]) > size else cv2.INTER_CUBIC
    rgb = cv2.resize(rgb, (size, size), interpolation=interp)
    green = rgb[:, :, 1]
    clahe = cv2.createCLAHE(clipLimit=float(clip_limit), tileGridSize=tuple(tile_grid))
    return rgb, clahe.apply(green)

def retinal_fov_mask(rgb):
    """Approximate non-black retinal field-of-view mask; validate for your dataset."""
    return rgb.max(axis=2) > 8

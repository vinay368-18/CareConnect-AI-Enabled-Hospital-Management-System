import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

from vessel_segmentation import VesselSegmenter, THRESHOLD

def main():
    if len(sys.argv) < 2:
        print('Usage: python test_vessel_segmentation.py "path\to\retinal_image.jpg"')
        raise SystemExit(2)

    image_path = Path(sys.argv[1])
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    output_dir = PROJECT / "segmentation_test_output"
    output_dir.mkdir(exist_ok=True)

    # Keep the image's aspect ratio; cap its longest side at 512 pixels.
    segmenter = VesselSegmenter(device="cpu", max_side=512)

    with Image.open(image_path) as im:
        rgb = segmenter._prepare(im)

    probability = segmenter._probability_map(rgb)
    fov = segmenter._fov_mask(rgb)
    mask = ((probability >= THRESHOLD) & fov).astype(np.uint8) * 255

    overlay_bytes = segmenter._overlay_png(rgb, mask > 0)
    overlay_path = output_dir / "vessel_overlay.png"
    overlay_path.write_bytes(overlay_bytes)

    mask_path = output_dir / "vessel_mask.png"
    if not cv2.imwrite(str(mask_path), mask):
        raise RuntimeError("Could not save vessel mask")

    # Save the green-channel CLAHE image used by the model, for inspection.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    green = clahe.apply(np.ascontiguousarray(rgb[:, :, 1]))
    preprocessed_path = output_dir / "green_clahe.png"
    if not cv2.imwrite(str(preprocessed_path), green):
        raise RuntimeError("Could not save preprocessed image")

    density = 100.0 * mask.astype(bool).sum() / max(1, fov.sum())

    print("Segmentation test: PASSED")
    print("Input:", image_path)
    print("Working image size (width, height):", (rgb.shape[1], rgb.shape[0]))
    print("Model patch size:", 256, "x", 256)
    print("Patch stride:", 128)
    print(f"Estimated vessel pixel percentage: {density:.2f}%")
    print("Saved overlay:", overlay_path)
    print("Saved binary mask:", mask_path)
    print("Saved green + CLAHE image:", preprocessed_path)
    print("Device: CPU")

if __name__ == "__main__":
    main()

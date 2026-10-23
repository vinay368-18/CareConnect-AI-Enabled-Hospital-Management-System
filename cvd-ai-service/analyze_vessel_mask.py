from pathlib import Path
import json
import cv2
import numpy as np

root = Path(__file__).resolve().parent / "segmentation_test_output"
mask_path = root / "vessel_mask.png"
report_path = root / "mask_quality_report.txt"

if not mask_path.is_file():
    raise FileNotFoundError(f"Mask not found: {mask_path}")

gray = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
if gray is None:
    raise RuntimeError("Could not read vessel mask")

mask = (gray >= 128).astype(np.uint8)
height, width = mask.shape
vessel_pixels = int(mask.sum())
total_pixels = int(mask.size)
coverage = 100.0 * vessel_pixels / max(1, total_pixels)

count, labels, stats, centroids = cv2.connectedComponentsWithStats(
    mask, connectivity=8
)
areas = stats[1:, cv2.CC_STAT_AREA] if count > 1 else np.array([], dtype=int)
large = areas[areas >= 10]

distance = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
inside = distance[mask > 0]
estimated_width = float(np.median(inside * 2)) if inside.size else 0.0

lines = [
    "RETINAL VESSEL MASK QUALITY REPORT",
    "=================================",
    f"Image dimensions: {width} x {height}",
    f"White vessel pixels: {vessel_pixels}",
    f"Total image pixels: {total_pixels}",
    f"White-pixel coverage of full image: {coverage:.2f}%",
    f"Connected components, excluding background: {max(0, count - 1)}",
    f"Components with at least 10 pixels: {len(large)}",
    f"Largest component area: {int(areas.max()) if areas.size else 0} pixels",
    f"Median local mask width estimate: {estimated_width:.2f} pixels",
    "",
    "Interpretation:",
    "- Coverage is calculated over the full rectangular image, not just the retinal field.",
    "- Components may include true vessels, false positives, or disconnected vessel fragments.",
    "- Width is an approximate mask-thickness measure, not anatomical vessel diameter.",
    "- These metrics alone do not measure segmentation accuracy; a reference mask is needed.",
]

report_path.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print(f"\nReport saved to: {report_path}")

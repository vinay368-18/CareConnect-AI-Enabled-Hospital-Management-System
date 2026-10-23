"""CLI scaffold. Connect build_model() to your existing ResUNet/checkpoint."""
import argparse
from pathlib import Path
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vessel_segmentation import segment_vessels, SegmentationConfig

def build_model(checkpoint):
    # Replace with your exact model class and checkpoint-loading logic.
    # Do not guess the architecture or state-dict keys.
    raise NotImplementedError("Connect your project's exact Residual U-Net and checkpoint here.")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out", default="retinal_512_output")
    p.add_argument("--patch-size", type=int, default=256)
    p.add_argument("--stride", type=int, default=128)
    a = p.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    model = build_model(a.checkpoint)
    r = segment_vessels(a.image, model, SegmentationConfig(patch_size=a.patch_size, stride=a.stride))
    Image.fromarray(r["rgb_512"]).save(out / "resized_rgb_512.png")
    Image.fromarray(r["green_clahe_512"]).save(out / "green_clahe_512.png")
    Image.fromarray(r["vessel_mask_512"]).save(out / "vessel_mask_512.png")
    Image.fromarray(r["overlay_rgba_512"], mode="RGBA").save(out / "vessel_overlay_512.png")
    np.save(out / "probability_map_512.npy", r["probability_map_512"])
    (out / "vessel_density.txt").write_text(f"Approximate vessel density: {r['vessel_density_percent']:.4f}%\nDevice: {r['device']}\n", encoding="utf-8")
    print("Saved outputs to", out.resolve())

if __name__ == "__main__":
    main()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import numpy as np
from retinal_preprocess import preprocess_green_clahe
from vessel_segmentation import patch_starts

def test_preprocessing_returns_512():
    img = np.zeros((300, 700, 3), dtype=np.uint8)
    img[:, :, 1] = np.arange(700, dtype=np.uint8)[None, :]
    rgb, clahe = preprocess_green_clahe(img)
    assert rgb.shape == (512, 512, 3)
    assert clahe.shape == (512, 512)
    assert clahe.dtype == np.uint8

def test_patch_starts_covers_last_edge():
    starts = patch_starts(512, 256, 128)
    assert starts[0] == 0
    assert starts[-1] == 256

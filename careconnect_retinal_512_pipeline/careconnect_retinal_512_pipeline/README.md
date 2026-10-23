# CareConnect retinal 512x512 + green CLAHE + vessel segmentation

## Included
- Resize a retinal image to a 512x512 working image.
- Extract its green channel and apply OpenCV CLAHE.
- Run overlapping 256x256 patches (stride 128) and stitch outputs into a 512x512 mask.
- Return a transparent cyan overlay and approximate vessel-density percentage.
- Keep the existing classifier's 224x224 preprocessing separate.

## Important compatibility note
Your project documentation describes a Residual U-Net with 256x256 patches, but the actual source code and trained checkpoint are not included in this package. You must connect `build_model()` in `src/run_segmentation.py` to the exact existing model class and checkpoint. Confirm input channels, normalization, output activation, and state-dict keys. The wrapper currently assumes a one-channel grayscale input scaled to [0,1]. Adapt it if your model was trained differently. Do not claim valid segmentation until you inspect outputs on retinal images.

## Install on Windows
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
```

## Run after connecting the model
```powershell
python src\run_segmentation.py --image "C:\path\to\fundus.jpg" --checkpoint "C:\path\to\residual_unet_best.pt" --out output
```

Outputs: resized RGB, green CLAHE, binary mask, transparent overlay, probability map, and density text file.

## Google Colab
`colab/Retinal_512_CLAHE_Segmentation_Setup.ipynb` checks GPU and mounts Drive. Upload your exact source/checkpoint and connect the model loader before running inference or training. GPU is optional for preprocessing and can accelerate inference. A GPU cannot fix checkpoint/model incompatibility.

## Integration
The current Java/Python integration can expose base64 PNG fields for the CLAHE image, mask, and overlay, plus `vessel_density_percent` and working dimensions. Do not change the classifier input size unless you retrain and evaluate that classifier separately.

The density uses a simple dark-background field-of-view heuristic and is an image-derived metric, not a diagnosis.

# ODIR-5K to mBRSET - Vascular Disease Classification

## Training
- Architecture: EfficientNet-B0
- Input image size: 512
- Batch size: 4
- Optimizer: AdamW
- Loss: BCEWithLogitsLoss with positive class weighting
- Training completed: 100 epochs
- Best checkpoint: Epoch 96

## Best validation result
- Validation PR-AUC: 0.23924

## Test evaluation
- Test images: 609
- Accuracy: 0.7734
- Precision: 0.1321
- Recall: 0.0707
- Specificity: 0.9098
- F1-score: 0.0921
- ROC-AUC: 0.4774
- PR-AUC: 0.1520

## Important limitation
The current test performance is poor. This model is experimental
and is not suitable for clinical use.

## Included files
- Training notebook
- Training manifest
- Best model checkpoint
- Latest model checkpoint
- Training history

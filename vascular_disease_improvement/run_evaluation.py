import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)

# 1. Load Extracted Features
csv_path = Path("results/full_mbrset_vessel_features/mbrset_all_3933_vessel_features.csv")
if not csv_path.exists():
    raise FileNotFoundError(f"Feature dataset not found at {csv_path.resolve()}")

df = pd.read_csv(csv_path)

# 2. Select Pruned Morphological Features
pruned_cols = [
    "skel_per_100k",
    "skeleton_length",
    "branch_clusters",
    "branch_per_100k",
    "endpt_to_branch_ratio",
    "endpoints",
    "endpts_per_100k"
]

train_df = df[df["split"] == "train"]
val_df   = df[df["split"] == "val"]
test_df  = df[df["split"] == "test"]

X_tr = train_df[pruned_cols].values
y_tr = train_df["vascular_disease"].values

X_te = test_df[pruned_cols].values
y_te = test_df["vascular_disease"].values

print(f"Data Loaded: Train Samples = {len(train_df)}, Test Samples = {len(test_df)}")

# 3. Train Model
clf = HistGradientBoostingClassifier(
    class_weight="balanced",
    max_iter=120,
    learning_rate=0.025,
    max_leaf_nodes=12,
    min_samples_leaf=15,
    l2_regularization=1.0,
    random_state=42
)
clf.fit(X_tr, y_tr)

# 4. Predict on Test Split
y_prob = clf.predict_proba(X_te)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)

tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
spec = tn / (tn + fp)

print("\n" + "="*50)
print("=== OPTIMIZED VESSEL CLASSIFIER TEST RESULTS ===")
print("="*50)
print(f"Accuracy:             {accuracy_score(y_te, y_pred)*100:.2f}%")
print(f"Precision:            {precision_score(y_te, y_pred, zero_division=0)*100:.2f}%")
print(f"Recall (Sensitivity): {recall_score(y_te, y_pred)*100:.2f}%")
print(f"Specificity:          {spec*100:.2f}%")
print(f"F1-Score:             {f1_score(y_te, y_pred)*100:.2f}%")
print(f"ROC-AUC:              {roc_auc_score(y_te, y_prob):.4f}")
print(f"PR-AUC:               {average_precision_score(y_te, y_prob):.4f}")
print("="*50)

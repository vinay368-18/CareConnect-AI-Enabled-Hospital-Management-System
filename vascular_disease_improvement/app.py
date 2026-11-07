from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingClassifier

app = Flask(__name__)

# 1. Load Data and Fit Model
csv_path = Path("results/full_mbrset_vessel_features/mbrset_all_3933_vessel_features.csv")
df = pd.read_csv(csv_path)

feature_cols = [
    "skel_per_100k",
    "skeleton_length",
    "branch_clusters",
    "branch_per_100k",
    "endpt_to_branch_ratio",
    "endpoints",
    "endpts_per_100k"
]

train_df = df[df["split"] == "train"]
X_train = train_df[feature_cols].values
y_train = train_df["vascular_disease"].values

clf = HistGradientBoostingClassifier(
    class_weight="balanced",
    max_iter=120,
    learning_rate=0.025,
    max_leaf_nodes=12,
    min_samples_leaf=15,
    l2_regularization=1.0,
    random_state=42
)
clf.fit(X_train, y_train)

# Calculate medians for default form placeholders
medians = train_df[feature_cols].median().to_dict()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Retinal CVD Screening Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f6f9; margin: 0; padding: 30px; }
        .container { max-width: 750px; background: white; margin: 0 auto; padding: 28px; border-radius: 12px; box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
        h2 { color: #1a365d; margin-top: 0; }
        p.subtitle { color: #4a5568; margin-bottom: 24px; font-size: 14px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .field { display: flex; flex-direction: column; }
        label { font-size: 13px; font-weight: 600; color: #2d3748; margin-bottom: 6px; }
        input { padding: 9px 12px; border: 1px solid #cbd5e0; border-radius: 6px; font-size: 14px; }
        button { grid-column: span 2; padding: 12px; background: #2b6cb0; color: white; border: none; border-radius: 6px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 10px; }
        button:hover { background: #2c5282; }
        .result-box { margin-top: 24px; padding: 18px; border-radius: 8px; display: none; }
        .low-risk { background: #e6fffa; border: 1px solid #81e6d9; color: #234e52; }
        .high-risk { background: #fff5f5; border: 1px solid #feb2b2; color: #742a2a; }
        .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 6px; }
    </style>
</head>
<body>
<div class="container">
    <h2>CareConnect: Retinal CVD Screening</h2>
    <p class="subtitle">Microvascular Morphometry Predictive Engine (Optimized HistGBM)</p>
    
    <form id="predictionForm" class="grid">
        <div class="field">
            <label>Skeleton Density (skel_per_100k):</label>
            <input type="number" step="any" id="skel_per_100k" value="{{ medians['skel_per_100k']|round(2) }}" required>
        </div>
        <div class="field">
            <label>Skeleton Length (pixels):</label>
            <input type="number" step="any" id="skeleton_length" value="{{ medians['skeleton_length']|round(2) }}" required>
        </div>
        <div class="field">
            <label>Branch Clusters:</label>
            <input type="number" step="any" id="branch_clusters" value="{{ medians['branch_clusters']|round(2) }}" required>
        </div>
        <div class="field">
            <label>Branching Density (branch_per_100k):</label>
            <input type="number" step="any" id="branch_per_100k" value="{{ medians['branch_per_100k']|round(2) }}" required>
        </div>
        <div class="field">
            <label>Endpoint to Branch Ratio:</label>
            <input type="number" step="any" id="endpt_to_branch_ratio" value="{{ medians['endpt_to_branch_ratio']|round(3) }}" required>
        </div>
        <div class="field">
            <label>Total Endpoints:</label>
            <input type="number" step="any" id="endpoints" value="{{ medians['endpoints']|round(2) }}" required>
        </div>
        <div class="field">
            <label>Endpoints Density (endpts_per_100k):</label>
            <input type="number" step="any" id="endpts_per_100k" value="{{ medians['endpts_per_100k']|round(2) }}" required>
        </div>
        
        <button type="submit">Analyze Retinal Risk</button>
    </form>

    <div id="result" class="result-box">
        <div class="metric-title" id="riskLabel"></div>
        <div id="riskScore"></div>
    </div>
</div>

<script>
document.getElementById('predictionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const payload = {
        skel_per_100k: parseFloat(document.getElementById('skel_per_100k').value),
        skeleton_length: parseFloat(document.getElementById('skeleton_length').value),
        branch_clusters: parseFloat(document.getElementById('branch_clusters').value),
        branch_per_100k: parseFloat(document.getElementById('branch_per_100k').value),
        endpt_to_branch_ratio: parseFloat(document.getElementById('endpt_to_branch_ratio').value),
        endpoints: parseFloat(document.getElementById('endpoints').value),
        endpts_per_100k: parseFloat(document.getElementById('endpts_per_100k').value)
    };

    const res = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    
    const resBox = document.getElementById('result');
    const riskLabel = document.getElementById('riskLabel');
    const riskScore = document.getElementById('riskScore');

    resBox.style.display = 'block';
    if(data.prediction === 1) {
        resBox.className = 'result-box high-risk';
        riskLabel.innerText = 'High Risk of Cardiovascular Vascular Disease';
    } else {
        resBox.className = 'result-box low-risk';
        riskLabel.innerText = 'Low Risk (Normal Vascular Pattern)';
    }
    riskScore.innerText = Estimated Risk Probability: %;
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE, medians=medians)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    row = np.array([[
        data["skel_per_100k"],
        data["skeleton_length"],
        data["branch_clusters"],
        data["branch_per_100k"],
        data["endpt_to_branch_ratio"],
        data["endpoints"],
        data["endpts_per_100k"]
    ]])
    prob = clf.predict_proba(row)[0, 1]
    pred = int(prob >= 0.5)
    return jsonify({"prediction": pred, "probability": float(prob)})

if __name__ == "__main__":
    print("CareConnect CVD Dashboard running at http://127.0.0.1:5000/")
    app.run(host="127.0.0.1", port=5000, debug=False)

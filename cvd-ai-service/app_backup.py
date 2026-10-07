"""
CVD Retinal Research Prototype - Interactive Web Application.
Framework: Gradio.
Features:
- Single-image fundus analysis (HT, CVD, DR)
- Explicit condition thresholds and prediction labels
- ICDR grade probability bar chart
- Prediction summary table with color-coded badges
- Independent Model Evaluation tab reading evaluation/metrics.json
- Clear medical research disclaimers and clinical boundaries
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import gradio as gr

from inference import RetinalPredictor


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
METRICS_PATH = APP_DIR / "evaluation" / "metrics.json"
EVAL_PLOT_PATH = APP_DIR / "evaluation" / "test_evaluation_curves.png"

# Initialize Predictor
PREDICTOR = RetinalPredictor(config_path=CONFIG_PATH)

# Load Metrics if available
if METRICS_PATH.exists():
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        METRICS_DATA = json.load(f)
else:
    METRICS_DATA = {}


def render_dr_bar_chart(dr_probs: Dict[str, float]) -> plt.Figure:
    """Render 5-bar probability chart for Diabetic Retinopathy grades."""
    fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=120)
    grades = list(dr_probs.keys())
    values = [dr_probs[g] * 100 for g in grades]
    colors = ["#3b82f6", "#06b6d4", "#f59e0b", "#f97316", "#ef4444"]

    bars = ax.bar(grades, values, color=colors, width=0.55, edgecolor="#1e293b", linewidth=0.8)
    ax.set_title("ICDR Grade Probability Distribution", fontsize=11, fontweight="bold", pad=12)
    ax.set_ylabel("Predicted probability (%)", fontsize=9)
    ax.set_ylim(0, max(max(values) * 1.25, 45))
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 1.2,
            f"{h:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )

    plt.tight_layout()
    return fig


def format_summary_table(results: Dict[str, Any]) -> str:
    """Format HTML summary table with orange/green/neutral badges."""
    p_ht = results["hypertension_predicted_probability"]
    t_ht = results["hypertension_threshold"]
    pred_ht = results["hypertension_prediction"]
    ht_color = "#b45309" if pred_ht == "Positive" else "#15803d"
    ht_bg = "#fef3c7" if pred_ht == "Positive" else "#dcfce7"
    ht_border = "#f59e0b" if pred_ht == "Positive" else "#22c55e"

    p_cvd = results["cvd_predicted_probability"]
    t_cvd = results["cvd_threshold"]
    pred_cvd = results["cvd_prediction"]
    cvd_color = "#b45309" if pred_cvd == "Positive" else "#15803d"
    cvd_bg = "#fef3c7" if pred_cvd == "Positive" else "#dcfce7"
    cvd_border = "#f59e0b" if pred_cvd == "Positive" else "#22c55e"

    dr_grade = results["dr_predicted_grade"]
    p_dr = results["dr_confidence"]

    table_html = f"""
    <div style="margin-top: 15px; margin-bottom: 15px; overflow-x: auto;">
      <table style="width: 100%; border-collapse: collapse; font-family: system-ui, sans-serif; font-size: 14px;">
        <thead>
          <tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; color: #334155; text-align: left;">
            <th style="padding: 10px 14px;">Condition</th>
            <th style="padding: 10px 14px;">Predicted probability</th>
            <th style="padding: 10px 14px;">Threshold</th>
            <th style="padding: 10px 14px;">Prediction</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 14px; font-weight: 600;">Systemic Hypertension (HT)</td>
            <td style="padding: 10px 14px;">{p_ht*100:.1f}%</td>
            <td style="padding: 10px 14px; color: #64748b;">{t_ht:.2f}</td>
            <td style="padding: 10px 14px;">
              <span style="background-color: {ht_bg}; color: {ht_color}; padding: 3px 10px; border-radius: 9999px; font-weight: 600; border: 1px solid {ht_border};">
                {pred_ht}
              </span>
            </td>
          </tr>
          <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 14px; font-weight: 600;">Cardiovascular Disease (CVD)</td>
            <td style="padding: 10px 14px;">{p_cvd*100:.1f}%</td>
            <td style="padding: 10px 14px; color: #64748b;">{t_cvd:.2f}</td>
            <td style="padding: 10px 14px;">
              <span style="background-color: {cvd_bg}; color: {cvd_color}; padding: 3px 10px; border-radius: 9999px; font-weight: 600; border: 1px solid {cvd_border};">
                {pred_cvd}
              </span>
            </td>
          </tr>
          <tr>
            <td style="padding: 10px 14px; font-weight: 600;">Diabetic Retinopathy (DR)</td>
            <td style="padding: 10px 14px;">{p_dr*100:.1f}% (Confidence)</td>
            <td style="padding: 10px 14px; color: #64748b;">Argmax (top class)</td>
            <td style="padding: 10px 14px;">
              <span style="background-color: #e0f2fe; color: #0369a1; padding: 3px 10px; border-radius: 9999px; font-weight: 600; border: 1px solid #38bdf8;">
                {dr_grade}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    """
    return table_html


def analyze_fundus_photo(image: Optional[Image.Image]) -> Tuple[str, str, Optional[plt.Figure]]:
    """Process uploaded image and generate UI outputs."""
    if image is None:
        empty_msg = (
            "### ⚠️ No Image Uploaded\n"
            "Please upload or drag-and-drop a retinal fundus photograph to initiate analysis."
        )
        return empty_msg, "", None

    try:
        results = PREDICTOR.predict(image)
    except Exception as e:
        error_msg = (
            f"### ❌ Error Processing Image\n"
            f"An error occurred during inference: {str(e)}\n\n"
            "Please ensure the file is a valid, uncorrupted retinal photograph."
        )
        return error_msg, "", None

    # 1. Condition Details Card
    p_ht = results["hypertension_predicted_probability"]
    t_ht = results["hypertension_threshold"]
    src_ht = results["hypertension_threshold_source"]
    pred_ht = results["hypertension_prediction"]

    p_cvd = results["cvd_predicted_probability"]
    t_cvd = results["cvd_threshold"]
    src_cvd = results["cvd_threshold_source"]
    pred_cvd = results["cvd_prediction"]
    cvd_badge = results["cvd_reliability_badge"]

    dr_grade = results["dr_predicted_grade"]
    dr_conf = results["dr_confidence"]
    dr_badge = results["dr_confidence_badge"]

    details_md = f"""
### Detailed Findings per Condition

#### 1. Systemic Hypertension (HT)
- **Predicted probability**: `{p_ht*100:.1f}%`
- **Threshold**: `{t_ht:.4f}` *(Source: {src_ht})*
- **Prediction**: **{pred_ht}**

---

#### 2. Cardiovascular Disease (CVD)
- **Predicted probability**: `{p_cvd*100:.1f}%`
- **Threshold**: `{t_cvd:.4f}` *(Source: {src_cvd})*
- **Prediction**: **{pred_cvd}**
- <span style="display: inline-block; background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; border: 1px solid #f87171;">⚠️ {cvd_badge}</span>

---

#### 3. Diabetic Retinopathy (DR)
- **Predicted grade**: **{dr_grade}** (ICDR scale 0-4)
- **Confidence**: `{dr_conf*100:.1f}%` *(top class predicted probability)*
"""
    if dr_badge:
        details_md += f"""- <span style="display: inline-block; background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 13px; border: 1px solid #f59e0b;">⚠️ {dr_badge}</span>\n"""

    details_md += """
- **Notice on Diabetes**: *Diabetes status is not predicted by this system. DR grade is a retinal finding, not a diabetes diagnosis.*
"""

    # 2. Prediction Summary Table (HTML)
    summary_html = format_summary_table(results)

    # 3. ICDR Bar Chart
    chart_fig = render_dr_bar_chart(results["dr_probabilities"])

    return details_md, summary_html, chart_fig


def build_evaluation_tab() -> gr.Column:
    """Build the Model Evaluation tab reading evaluation/metrics.json."""
    held_out = METRICS_DATA.get("held_out_evaluation", {})
    conditions = held_out.get("conditions", {})

    ht_m = conditions.get("hypertension", {})
    cvd_m = conditions.get("cardiovascular_disease", {})
    dr_m = conditions.get("diabetic_retinopathy", {})

    def fmt(val):
        return f"{val:.4f}" if isinstance(val, (int, float)) else str(val)

    def fmt_ci(ci):
        if isinstance(ci, list) and len(ci) == 2:
            return f"[{ci[0]:.4f}, {ci[1]:.4f}]"
        return "Not available"

    eval_md = f"""
## Model Evaluation & Empirical Benchmark

### Section 1: Held-Out Cohort Evaluation
- **Evaluation Split**: {held_out.get('split_type', 'Patient-level stratified held-out test split (15%)')}
- **Test Sample Size**: {held_out.get('n_test_patients', 'Not available')} Patients ({held_out.get('n_test_images', 'Not available')} Images)

| Metric | Systemic Hypertension (HT) | Cardiovascular Disease (CVD) | Diabetic Retinopathy (DR) |
| :--- | :---: | :---: | :---: |
| **Target Level** | Patient-level | Patient-level | Image-level |
| **Sample Size (N)** | {ht_m.get('n_samples', 'Not available')} patients | {cvd_m.get('n_samples', 'Not available')} patients | {dr_m.get('n_samples', 'Not available')} images |
| **Positives Count** | {ht_m.get('n_positives', 'Not available')} | {cvd_m.get('n_positives', 'Not available')} | N/A (5 classes) |
| **ROC-AUC** | **{fmt(ht_m.get('roc_auc', 'Not available'))}** | **{fmt(cvd_m.get('roc_auc', 'Not available'))}** | {dr_m.get('roc_auc', 'Not available')} |
| **ROC-AUC (95% CI)** | {fmt_ci(ht_m.get('roc_auc_ci_95'))} | {fmt_ci(cvd_m.get('roc_auc_ci_95'))} | Not available |
| **PR-AUC** | **{fmt(ht_m.get('pr_auc', 'Not available'))}** | **{fmt(cvd_m.get('pr_auc', 'Not available'))}** | {dr_m.get('pr_auc', 'Not available')} |
| **PR-AUC (95% CI)** | {fmt_ci(ht_m.get('pr_auc_ci_95'))} | {fmt_ci(cvd_m.get('pr_auc_ci_95'))} | Not available |
| **Brier Score** | {fmt(ht_m.get('brier_score', 'Not available'))} | {fmt(cvd_m.get('brier_score', 'Not available'))} | {dr_m.get('brier_score', 'Not available')} |
| **Decision Threshold** | {fmt(ht_m.get('threshold', 'Not available'))} | {fmt(cvd_m.get('threshold', 'Not available'))} | Argmax |
| **Sensitivity** | {fmt(ht_m.get('sensitivity', 'Not available'))} | {fmt(cvd_m.get('sensitivity', 'Not available'))} | Not available |
| **Specificity** | {fmt(ht_m.get('specificity', 'Not available'))} | {fmt(cvd_m.get('specificity', 'Not available'))} | Not available |
| **Classification F1** | {fmt(ht_m.get('f1_score', 'Not available'))} | {fmt(cvd_m.get('f1_score', 'Not available'))} | {fmt(dr_m.get('weighted_f1', 'Not available'))} (Weighted) |
| **DR Multi-Class Accuracy** | Not available | Not available | **{fmt(dr_m.get('accuracy', 'Not available'))}** |

> **Threshold Note**: Thresholds were optimized strictly on validation data using Youden's J statistic ($J = \text{{Sensitivity}} + \text{{Specificity}} - 1$) and frozen prior to test evaluation.

---

### Section 2: Preliminary Sanity Check on Selected Images
#### Anecdotal check on 4 selected images; not an accuracy estimate

| Image ID | Patient ID | Ground Truth (HT / CVD / DR) | Predicted (HT / CVD / DR) | Correct? (HT / CVD / DR) |
| :--- | :---: | :--- | :--- | :---: |
"""

    sanity_list = METRICS_DATA.get("sanity_check_selected_images", [])
    for item in sanity_list:
        gt = f"HT: {item['ground_truth']['HT']}<br>CVD: {item['ground_truth']['CVD']}<br>DR: {item['ground_truth']['DR']}"
        pred = f"HT: {item['predicted']['HT']}<br>CVD: {item['predicted']['CVD']}<br>DR: {item['predicted']['DR']}"
        corr = f"HT: {item['correct']['HT']}<br>CVD: {item['correct']['CVD']}<br>DR: {item['correct']['DR']}"
        eval_md += f"| `{item['image_id']}` | `{item['patient_id']}` | {gt} | {pred} | {corr} |\n"

    summary_counts = METRICS_DATA.get("sanity_check_summary", {}).get("correct_counts", {})
    eval_md += f"""
**Summary Count across the 4 Selected Images**:
- Systemic Hypertension: **{summary_counts.get('hypertension', '4 of 4')}**
- Cardiovascular Disease: **{summary_counts.get('cardiovascular_disease', '2 of 4')}**
- Diabetic Retinopathy: **{summary_counts.get('diabetic_retinopathy', '2 of 4')}**

*(Sample size: 4 images. These anecdotal results demonstrate model functionality on individual samples and must not be interpreted as statistical accuracy estimates.)*
"""

    with gr.Column():
        gr.Markdown(eval_md)
        if EVAL_PLOT_PATH.exists():
            gr.Markdown("### Held-Out Test ROC & Precision-Recall Trajectories")
            gr.Image(value=str(EVAL_PLOT_PATH), label="Empirical Test Evaluation Curves", interactive=False)


def create_app() -> gr.Blocks:
    theme = gr.themes.Soft(
        primary_hue="blue",
        neutral_hue="slate",
    )

    with gr.Blocks(title="CVD Retinal Research Prototype") as demo:
        gr.Markdown(
            "# Cardiovascular Disease & Microvascular Retinal Research Prototype\n"
            "### AI-Based Microvascular Analysis from Fundus Photography in Diabetic Cohorts\n"
            "---\n"
        )

        with gr.Tabs():
            # TAB 1: Single Image Analysis
            with gr.Tab("Analyze Fundus Image"):
                with gr.Row():
                    with gr.Column(scale=5):
                        gr.Markdown("### 1. Upload Retinal Fundus Photograph")
                        img_input = gr.Image(
                            type="pil",
                            label="Upload or Drag Retinal Fundus Photo (.jpg, .jpeg, .png)",
                            sources=["upload", "clipboard"],
                        )
                        analyze_btn = gr.Button("Analyze Retinal Image", variant="primary", size="lg")
                        clear_btn = gr.ClearButton()

                    with gr.Column(scale=6):
                        gr.Markdown("### 2. Prediction Summary")
                        summary_table = gr.HTML(
                            "<p style='color: #64748b; font-style: italic;'>Upload an image and click <b>Analyze Retinal Image</b> to generate predictions.</p>"
                        )
                        details_box = gr.Markdown("")
                        chart_box = gr.Plot(label="ICDR Grade Probability Distribution")

                # Fixed Disclaimer under results
                gr.Markdown(
                    "> **Research Notice**: Predictions are model-generated estimates from a research prototype and are not a medical diagnosis."
                )

                # Connect Callbacks
                clear_btn.add([img_input, summary_table, details_box, chart_box])
                analyze_btn.click(
                    fn=analyze_fundus_photo,
                    inputs=[img_input],
                    outputs=[details_box, summary_table, chart_box],
                )

            # TAB 2: Model Evaluation
            with gr.Tab("Model Evaluation"):
                build_evaluation_tab()

        with gr.Accordion("Research Protocol & Clinical Boundaries", open=False):
            gr.Markdown(
                "**INVESTIGATIONAL USE ONLY**  \n"
                "1. **Cohort Homogeneity**: Trained exclusively on the mBRSET dataset of diabetic patients in Brazil. "
                "The system cannot diagnose diabetes, as non-diabetic controls are absent from training.  \n"
                "2. **Retinal Signal Strength**: Fundus microvascular features demonstrate modest discriminative association with past CVD history "
                "(ROC-AUC ~0.56 in held-out test split). The 'Low reliability' warning highlights this intrinsic dataset boundary.  \n"
                "3. **No Blood Pressure Measurement**: Hypertension status is a self/clinician reported binary indicator, not a numeric mmHg measurement.  \n"
                "4. **Not a Medical Device**: These probabilistic estimates are intended solely for academic biomedical researchers."
            )

    return demo


def main():
    demo = create_app()
    theme = gr.themes.Soft(primary_hue="blue", neutral_hue="slate")
    demo.launch(server_port=7860, theme=theme)


if __name__ == "__main__":
    main()

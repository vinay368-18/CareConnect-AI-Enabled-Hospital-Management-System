<%@ page language="java"
    contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="com.hms.model.CVDScreening" %>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CareConnect | AI Diagnostic Report</title>

    <link rel="stylesheet" href="${pageContext.request.contextPath}/css/style.css">

    <style>
        body {
            background: #f1f5f9;
            color: #1e293b;
            font-family: "Segoe UI", Arial, sans-serif;
            margin: 0;
            padding: 30px 15px;
        }

        .report-container {
            max-width: 950px;
            margin: auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
            overflow: hidden;
        }

        /* Top Action Bar (hidden on print) */
        .action-bar {
            background: #0f172a;
            color: white;
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .action-bar a, .action-bar button {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: white;
            text-decoration: none;
            font-size: 13.5px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            background: transparent;
        }

        .action-bar .btn-print {
            background: #0f766e;
            padding: 8px 16px;
            border-radius: 6px;
            transition: background 0.2s;
        }

        .action-bar .btn-print:hover {
            background: #115e59;
        }

        /* Report Header */
        .report-header {
            padding: 30px 36px 20px 36px;
            border-bottom: 2px solid #f1f5f9;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }

        .hospital-brand h1 {
            font-size: 24px;
            color: #0f172a;
            margin: 0 0 4px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .hospital-brand p {
            color: #64748b;
            font-size: 13px;
            margin: 0;
        }

        .report-meta {
            text-align: right;
            font-size: 13px;
            color: #64748b;
        }

        .report-meta strong {
            color: #0f172a;
            font-size: 14px;
        }

        /* Section Styling */
        .report-body {
            padding: 28px 36px;
        }

        /* Patient Info Grid */
        .info-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px 22px;
            margin-bottom: 28px;
        }

        .info-item .lbl {
            font-size: 11.5px;
            font-weight: 700;
            text-transform: uppercase;
            color: #64748b;
            letter-spacing: 0.5px;
            margin-bottom: 3px;
        }

        .info-item .val {
            font-size: 14.5px;
            font-weight: 600;
            color: #0f172a;
        }

        /* Scan + Results Layout */
        .diagnostic-section {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 28px;
            margin-bottom: 28px;
        }

        .scan-preview-box {
            text-align: center;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
        }

        .scan-preview-box img {
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        }

        .scan-preview-box .caption {
            font-size: 12px;
            color: #64748b;
            margin-top: 8px;
            font-weight: 500;
        }

        /* Disease Risk Cards */
        .risk-cards-col {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .finding-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 16px 20px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        }

        .finding-card .head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .finding-card .title {
            font-size: 14px;
            font-weight: 700;
            color: #1e293b;
        }

        .progress-bar-bg {
            background: #e2e8f0;
            border-radius: 20px;
            height: 10px;
            overflow: hidden;
            margin-top: 6px;
        }

        .progress-bar-fill {
            height: 100%;
            border-radius: 20px;
            transition: width 0.6s ease;
        }

        .bar-cvd { background: linear-gradient(90deg, #f59e0b, #ef4444); }
        .bar-ht { background: linear-gradient(90deg, #06b6d4, #3b82f6); }
        .bar-dr { background: linear-gradient(90deg, #10b981, #0f766e); }

        /* Overall Assessment Banner */
        .assessment-banner {
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            display: flex;
            gap: 18px;
            align-items: flex-start;
        }

        .banner-high {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b;
        }

        .banner-mod {
            background: #fffbeb;
            border: 1px solid #fde68a;
            color: #92400e;
        }

        .banner-low {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
        }

        .assessment-banner .icon {
            font-size: 32px;
            line-height: 1;
        }

        .assessment-banner h3 {
            margin: 0 0 6px 0;
            font-size: 17px;
        }

        .assessment-banner p {
            margin: 0;
            font-size: 13.5px;
            line-height: 1.5;
        }

        /* Disclaimer */
        .disclaimer-box {
            background: #f8fafc;
            border-left: 4px solid #94a3b8;
            padding: 12px 18px;
            font-size: 12px;
            color: #64748b;
            line-height: 1.5;
            margin-top: 24px;
            border-radius: 0 8px 8px 0;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 700;
        }

        .badge-positive { background: #fee2e2; color: #b91c1c; }
        .badge-negative { background: #dcfce7; color: #15803d; }

        @media print {
            body { padding: 0; background: white; }
            .action-bar { display: none; }
            .report-container { box-shadow: none; border: none; }
        }
    </style>
</head>

<body>

<%
    CVDScreening s = (CVDScreening) request.getAttribute("screening");
    if (s != null) {
        String bannerClass = "banner-low";
        String bannerIcon = "✅";
        if ("High Risk".equalsIgnoreCase(s.getRiskLevel())) {
            bannerClass = "banner-high";
            bannerIcon = "⚠️";
        } else if ("Moderate Risk".equalsIgnoreCase(s.getRiskLevel())) {
            bannerClass = "banner-mod";
            bannerIcon = "⚡";
        }
%>

<div class="report-container">

    <!-- Action Bar -->
    <div class="action-bar">
        <div>
            <a href="${pageContext.request.contextPath}/CVDServlet?action=list">
                ← Back to All Screenings
            </a>
        </div>
        <div style="display: flex; gap: 12px;">
            <button class="btn-print" onclick="window.print();">
                🖨️ Print / Save Report
            </button>
        </div>
    </div>

    <!-- Header -->
    <div class="report-header">
        <div class="hospital-brand">
            <h1><span>🏥</span> CareConnect Hospital</h1>
            <p>Department of Preventive Cardiology & AI Diagnostics</p>
        </div>
        <div class="report-meta">
            <div>Report ID: <strong>#CVD-<%= s.getScreeningId() %></strong></div>
            <div>Date: <%= s.getScreeningDate() != null ? s.getScreeningDate().toString().substring(0, 16) : "Recent" %></div>
            <div style="color: #0f766e; font-weight: 600; margin-top: 4px;">PyTorch Multi-Task Model v1.0</div>
        </div>
    </div>

    <!-- Report Body -->
    <div class="report-body">

        <!-- Patient Demographics -->
        <div class="info-grid">
            <div class="info-item">
                <div class="lbl">Patient Name</div>
                <div class="val"><%= s.getPatientName() %></div>
            </div>
            <div class="info-item">
                <div class="lbl">Patient ID & Age</div>
                <div class="val">#<%= s.getPatientId() %> | <%= s.getPatientAge() %> yrs, <%= s.getPatientGender() %></div>
            </div>
            <div class="info-item">
                <div class="lbl">Phone / Contact</div>
                <div class="val"><%= s.getPatientPhone() != null ? s.getPatientPhone() : "N/A" %></div>
            </div>
            <div class="info-item">
                <div class="lbl">Assigned Doctor</div>
                <div class="val"><%= s.getDoctorName() != null ? s.getDoctorName() : "Cardiology Team" %></div>
            </div>
        </div>

        <!-- Overall Assessment Banner -->
        <div class="assessment-banner <%= bannerClass %>">
            <div class="icon"><%= bannerIcon %></div>
            <div>
                <h3>Overall Assessment: <%= s.getRiskLevel() %></h3>
                <p><strong>Clinical Recommendation:</strong> <%= s.getRecommendation() %></p>
                <% if (s.getNotes() != null && !s.getNotes().trim().isEmpty()) { %>
                    <p style="margin-top: 6px; font-style: italic;">Patient Notes: <%= s.getNotes() %></p>
                <% } %>
            </div>
        </div>

        <!-- Diagnostic Grid -->
        <div class="diagnostic-section">

            <!-- Fundus Photograph (+ Residual U-Net vessel segmentation) -->
            <div style="display: flex; flex-direction: column; gap: 16px;">
                <div class="scan-preview-box">
                    <img src="${pageContext.request.contextPath}/<%= s.getImagePath() != null ? s.getImagePath() : "uploads/fundus/samples/img00330.jpg" %>"
                         alt="Retinal Fundus Scan"
                         onerror="this.src='${pageContext.request.contextPath}/uploads/fundus/samples/img00330.jpg';">
                    <div class="caption">Retinal Fundus Photography (Input Tensor: 224x224)</div>
                </div>

                <% if (s.getVesselOverlayPath() != null && !s.getVesselOverlayPath().isEmpty()) { %>
                <div class="scan-preview-box">
                    <img src="${pageContext.request.contextPath}/<%= s.getVesselOverlayPath() %>"
                         alt="Segmented retinal vessels"
                         onerror="this.parentNode.style.display='none';">
                    <div class="caption">
                        Vessel segmentation (Residual U-Net)<%= s.getVesselDensity() != null ? " &middot; vessel density " + String.format("%.1f", s.getVesselDensity()) + "% of retinal area" : "" %><br>
                        Research output &ndash; not clinically validated
                    </div>
                </div>
                <% } %>
            </div>

            <!-- Deep Learning Prediction Scores -->
            <div class="risk-cards-col">

                <!-- 1. CVD Risk -->
                <div class="finding-card">
                    <div class="head">
                        <span class="title">Cardiovascular Disease (CVD) Risk</span>
                        <span class="badge <%= "Positive".equalsIgnoreCase(s.getCvdPrediction()) ? "badge-positive" : "badge-negative" %>">
                            <%= s.getCvdPrediction() %>
                        </span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:12.5px; color:#64748b;">
                        <span>Estimated Risk Probability</span>
                        <strong><%= s.getCvdPercent() %>%</strong>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill bar-cvd" style="width: <%= s.getCvdPercent() %>%;"></div>
                    </div>
                </div>

                <!-- 2. Systemic Hypertension -->
                <div class="finding-card">
                    <div class="head">
                        <span class="title">Systemic Hypertension (HT)</span>
                        <span class="badge <%= "Positive".equalsIgnoreCase(s.getHypertensionPrediction()) ? "badge-positive" : "badge-negative" %>">
                            <%= s.getHypertensionPrediction() %>
                        </span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:12.5px; color:#64748b;">
                        <span>Hypertensive Retinopathy Probability</span>
                        <strong><%= s.getHypertensionPercent() %>%</strong>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill bar-ht" style="width: <%= s.getHypertensionPercent() %>%;"></div>
                    </div>
                </div>

                <!-- 3. Diabetic Retinopathy Grade -->
                <div class="finding-card">
                    <div class="head">
                        <span class="title">Diabetic Retinopathy (ICDR)</span>
                        <span class="badge" style="background:#e0f2fe; color:#0369a1;">
                            Grade: <%= s.getDrGrade() %>
                        </span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:12.5px; color:#64748b;">
                        <span>Top Class Confidence</span>
                        <strong><%= s.getDrPercent() %>%</strong>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill bar-dr" style="width: <%= s.getDrPercent() %>%;"></div>
                    </div>
                </div>

            </div>

        </div>

        <!-- Research & Clinical Disclaimer -->
        <div class="disclaimer-box">
            <strong>Medical Research Prototype Disclaimer:</strong>
            These findings are generated computationally by an integrated deep learning multi-task architecture (EfficientNet-B0 backbone) trained on retinal fundus benchmarks. The model provides assistive screening markers for cardiovascular and microvascular health. It is intended to assist medical practitioners and does not replace formal clinical examinations, ECG, or lab blood tests.
        </div>

    </div>

</div>

<% } else { %>
    <div style="text-align: center; padding: 50px;">
        <h2>Screening report not found</h2>
        <a href="${pageContext.request.contextPath}/CVDServlet?action=list">Return to List</a>
    </div>
<% } %>

</body>
</html>

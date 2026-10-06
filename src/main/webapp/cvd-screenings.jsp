<%@ page language="java"
    contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.CVDScreening" %>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CareConnect | CVD & Retinal AI Diagnostics</title>

    <link rel="stylesheet" href="${pageContext.request.contextPath}/css/style.css">

    <style>
        body {
            background: #f5f8fa;
            color: #172b4d;
            font-family: "Segoe UI", Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 1300px;
            margin: auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }

        .header h1 {
            font-size: 28px;
            color: #13233b;
            margin: 0 0 5px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header p {
            color: #8290a3;
            font-size: 14px;
            margin: 0;
        }

        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .btn-primary {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 11px 20px;
            background: #0f766e;
            color: white;
            text-decoration: none;
            border-radius: 9px;
            font-weight: 600;
            font-size: 14px;
            box-shadow: 0 4px 14px rgba(15, 118, 110, 0.25);
            transition: all 0.2s;
        }

        .btn-primary:hover {
            background: #115e59;
            transform: translateY(-1px);
        }

        .btn-secondary {
            display: inline-flex;
            align-items: center;
            padding: 11px 18px;
            background: white;
            color: #334155;
            text-decoration: none;
            border-radius: 9px;
            font-weight: 600;
            font-size: 14px;
            border: 1px solid #cbd5e1;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            background: #f1f5f9;
        }

        /* Status Badge for Python AI Microservice */
        .service-status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-online {
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #86efac;
        }

        .status-offline {
            background: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fca5a5;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: currentColor;
            display: inline-block;
        }

        /* Metric Cards */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 18px;
            margin-bottom: 25px;
        }

        .metric-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 18px 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }

        .metric-card .title {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            color: #64748b;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .metric-card .value {
            font-size: 26px;
            font-weight: 700;
            color: #0f172a;
        }

        .metric-card.alert .value {
            color: #dc2626;
        }

        .metric-card.success .value {
            color: #16a34a;
        }

        /* Table Card */
        .card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 12px 14px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
            border-bottom: 2px solid #f1f5f9;
        }

        td {
            padding: 14px 14px;
            font-size: 13.5px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
        }

        tr:hover td {
            background: #f8fafc;
        }

        /* Risk Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 700;
            text-align: center;
        }

        .badge-high {
            background: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fca5a5;
        }

        .badge-mod {
            background: #fef3c7;
            color: #b45309;
            border: 1px solid #fcd34d;
        }

        .badge-low {
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #86efac;
        }

        .badge-positive {
            background: #ffedd5;
            color: #c2410c;
        }

        .badge-negative {
            background: #f1f5f9;
            color: #475569;
        }

        .action-links {
            display: flex;
            gap: 8px;
        }

        .btn-view {
            background: #e0f2fe;
            color: #0369a1;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            text-decoration: none;
        }

        .btn-view:hover {
            background: #bae6fd;
        }

        .btn-del {
            background: #fee2e2;
            color: #b91c1c;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            text-decoration: none;
        }

        .btn-del:hover {
            background: #fecaca;
        }

        .empty-state {
            text-align: center;
            padding: 50px 20px;
            color: #64748b;
        }

        .empty-state h3 {
            color: #1e293b;
            margin-bottom: 8px;
        }
    </style>
</head>

<body>

<div class="container">

    <!-- HEADER -->
    <div class="header">
        <div>
            <h1>
                <span>❤️</span> Cardiovascular & Retinal AI Diagnostics
            </h1>
            <p>Integrated Multi-Task Deep Learning Screening (PyTorch EfficientNet-B0 + Java HMS)</p>
        </div>

        <div class="header-actions">
            <%
                Boolean isOnline = (Boolean) request.getAttribute("isAiOnline");
                if (isOnline != null && isOnline) {
            %>
                <div class="service-status status-online">
                    <span class="pulse-dot"></span> AI Service Online (Port 5000)
                </div>
            <% } else { %>
                <div class="service-status status-offline">
                    <span class="pulse-dot"></span> AI Service Offline
                </div>
            <% } %>

            <a href="${pageContext.request.contextPath}/dashboard.jsp" class="btn-secondary">
                ← Dashboard
            </a>

            <a href="${pageContext.request.contextPath}/CVDServlet?action=new" class="btn-primary">
                + New AI Screening
            </a>
        </div>
    </div>

    <!-- METRICS OVERVIEW -->
    <%
        List<CVDScreening> screenings = (List<CVDScreening>) request.getAttribute("screenings");
        int total = (request.getAttribute("totalCount") != null) ? (Integer) request.getAttribute("totalCount") : 0;
        int highRisk = (request.getAttribute("highRiskCount") != null) ? (Integer) request.getAttribute("highRiskCount") : 0;
        int normalCount = Math.max(0, total - highRisk);
    %>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="title">Total AI Screenings</div>
            <div class="value"><%= total %></div>
        </div>
        <div class="metric-card alert">
            <div class="title">High Cardiovascular Risk</div>
            <div class="value"><%= highRisk %></div>
        </div>
        <div class="metric-card success">
            <div class="title">Low / Moderate Risk</div>
            <div class="value"><%= normalCount %></div>
        </div>
    </div>

    <!-- TABLE OF SCREENINGS -->
    <div class="card">
        <table>
            <thead>
                <tr>
                    <th># ID</th>
                    <th>Date & Time</th>
                    <th>Patient</th>
                    <th>Doctor</th>
                    <th>CVD Status</th>
                    <th>Hypertension</th>
                    <th>Diabetic Retinopathy</th>
                    <th>Overall Risk</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
            <%
                if (screenings != null && !screenings.isEmpty()) {
                    for (CVDScreening s : screenings) {
                        String riskBadgeClass = "badge-low";
                        if ("High Risk".equalsIgnoreCase(s.getRiskLevel())) {
                            riskBadgeClass = "badge-high";
                        } else if ("Moderate Risk".equalsIgnoreCase(s.getRiskLevel())) {
                            riskBadgeClass = "badge-mod";
                        }
            %>
                <tr>
                    <td><strong>#<%= s.getScreeningId() %></strong></td>
                    <td style="color:#64748b; font-size:12.5px;">
                        <%= s.getScreeningDate() != null ? s.getScreeningDate().toString().substring(0, 16) : "-" %>
                    </td>
                    <td>
                        <strong><%= s.getPatientName() %></strong><br>
                        <span style="font-size:12px; color:#64748b;">
                            <%= s.getPatientAge() %> yrs, <%= s.getPatientGender() %>
                        </span>
                    </td>
                    <td>
                        <%= s.getDoctorName() != null ? s.getDoctorName() : "<span style='color:#94a3b8;'>Unassigned</span>" %>
                    </td>
                    <td>
                        <span class="badge <%= "Positive".equalsIgnoreCase(s.getCvdPrediction()) ? "badge-positive" : "badge-negative" %>">
                            <%= s.getCvdPrediction() %> (<%= s.getCvdPercent() %>%)
                        </span>
                    </td>
                    <td>
                        <span class="badge <%= "Positive".equalsIgnoreCase(s.getHypertensionPrediction()) ? "badge-positive" : "badge-negative" %>">
                            <%= s.getHypertensionPrediction() %> (<%= s.getHypertensionPercent() %>%)
                        </span>
                    </td>
                    <td>
                        <strong><%= s.getDrGrade() %></strong>
                        <span style="font-size:11px; color:#64748b;">(<%= s.getDrPercent() %>%)</span>
                    </td>
                    <td>
                        <span class="badge <%= riskBadgeClass %>">
                            <%= s.getRiskLevel() %>
                        </span>
                    </td>
                    <td>
                        <div class="action-links">
                            <a href="${pageContext.request.contextPath}/CVDServlet?action=view&id=<%= s.getScreeningId() %>" class="btn-view">
                                View Report
                            </a>
                            <a href="${pageContext.request.contextPath}/CVDServlet?action=delete&id=<%= s.getScreeningId() %>" class="btn-del"
                               onclick="return confirm('Are you sure you want to delete this AI screening record?');">
                                Delete
                            </a>
                        </div>
                    </td>
                </tr>
            <%
                    }
                } else {
            %>
                <tr>
                    <td colspan="9" class="empty-state">
                        <h3>No AI Screenings Recorded Yet</h3>
                        <p>Upload a retinal fundus photograph to perform automated cardiovascular risk assessment.</p>
                        <div style="margin-top: 15px;">
                            <a href="${pageContext.request.contextPath}/CVDServlet?action=new" class="btn-primary">
                                + Run First AI Screening
                            </a>
                        </div>
                    </td>
                </tr>
            <%
                }
            %>
            </tbody>
        </table>
    </div>

</div>

</body>
</html>

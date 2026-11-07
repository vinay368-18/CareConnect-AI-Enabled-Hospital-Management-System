<%@ page language="java"
    contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Patient" %>
<%@ page import="com.hms.model.Doctor" %>
<%@ page import="com.hms.model.User" %>
<%@ page import="com.hms.util.HtmlUtil" %>
<%@ page import="com.hms.util.CSRFUtil" %>

<%
    User u = (session != null) ? (User) session.getAttribute("user") : null;
    if (u == null) {
        response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized");
        return;
    }
    String csrfToken = CSRFUtil.getToken(session);
%>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CareConnect | New AI Retinal & CVD Screening</title>

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
            max-width: 900px;
            margin: auto;
        }

        .header {
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

        .card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 32px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        }

        .form-group {
            margin-bottom: 22px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        label {
            display: block;
            font-size: 13.5px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 8px;
        }

        .required {
            color: #ef4444;
        }

        input[type="text"],
        select,
        textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 12px 14px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            font-size: 14px;
            color: #1e293b;
            background: #f8fafc;
            transition: all 0.2s;
        }

        input:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #0f766e;
            background: white;
            box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
        }

        /* Upload Area */
        .upload-dropzone {
            border: 2px dashed #94a3b8;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            background: #f8fafc;
            cursor: pointer;
            transition: all 0.2s;
        }

        .upload-dropzone:hover {
            border-color: #0f766e;
            background: #f0fdfa;
        }

        .upload-icon {
            font-size: 36px;
            margin-bottom: 8px;
            color: #0f766e;
        }

        .upload-title {
            font-weight: 600;
            color: #1e293b;
            font-size: 15px;
            margin-bottom: 4px;
        }

        .upload-desc {
            font-size: 12.5px;
            color: #64748b;
        }

        #imagePreview {
            max-width: 200px;
            max-height: 200px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
            border: 2px solid #e2e8f0;
        }

        /* Sample Demo Selector */
        .sample-section {
            margin-top: 18px;
            padding-top: 18px;
            border-top: 1px dashed #cbd5e1;
        }

        .sample-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-top: 10px;
        }

        .sample-card {
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 8px;
            text-align: center;
            cursor: pointer;
            background: white;
            transition: all 0.2s;
        }

        .sample-card:hover, .sample-card.active {
            border-color: #0f766e;
            background: #f0fdfa;
            transform: translateY(-2px);
        }

        .sample-card img {
            width: 100%;
            height: 90px;
            object-fit: cover;
            border-radius: 6px;
        }

        .sample-card span {
            display: block;
            font-size: 11.5px;
            font-weight: 600;
            color: #334155;
            margin-top: 6px;
        }

        .actions-bar {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #f1f5f9;
        }

        .btn-cancel {
            padding: 12px 20px;
            background: white;
            color: #475569;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
        }

        .btn-submit {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            background: #0f766e;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(15, 118, 110, 0.25);
            transition: all 0.2s;
        }

        .btn-submit:hover {
            background: #115e59;
        }

        /* Alerts */
        .alert {
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }

        .alert-error {
            background: #fef2f2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }

        .alert-warning {
            background: #fffbeb;
            color: #92400e;
            border: 1px solid #fde68a;
        }

        /* Loading Spinner Overlay */
        #loadingOverlay {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15, 23, 42, 0.7);
            z-index: 9999;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            color: white;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(255, 255, 255, 0.3);
            border-top-color: #14b8a6;
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
            margin-bottom: 16px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>

<body>

<div class="container">

    <div class="header">
        <h1>
            <span>🔬</span> New AI Retinal & CVD Screening
        </h1>
        <p>Upload a retinal fundus photograph to analyze Cardiovascular Disease risk, Systemic Hypertension, and Diabetic Retinopathy.</p>
    </div>

    <!-- Error Alerts -->
    <%
        String error = request.getParameter("error");
        if ("ai_offline".equals(error)) {
    %>
        <div class="alert alert-error">
            <strong>AI Microservice Offline:</strong> Unable to connect to the Python PyTorch service at <code>http://127.0.0.1:5000</code>. Please ensure the Python service is running.
        </div>
    <% } else if ("missing_image".equals(error)) { %>
        <div class="alert alert-warning">
            <strong>Missing Retinal Image:</strong> Please select or upload a fundus photograph to perform the analysis.
        </div>
    <% } else if ("invalid_file_type".equals(error)) { %>
        <div class="alert alert-error">
            <strong>Invalid File Type:</strong> Only standard image formats (.jpg, .jpeg, .png) are permitted.
        </div>
    <% } else if ("corrupt_image".equals(error)) { %>
        <div class="alert alert-error">
            <strong>Corrupted Image:</strong> The uploaded file could not be decoded as a valid, uncorrupted retinal fundus image.
        </div>
    <% } else if ("invalid_patient".equals(error)) { %>
        <div class="alert alert-error">
            <strong>Invalid Patient:</strong> The selected patient does not exist or could not be found.
        </div>
    <% } else if ("processing_error".equals(error)) { %>
        <div class="alert alert-error">
            <strong>Processing Error:</strong> An error occurred during image tensor preprocessing or inference. Please try again.
        </div>
    <% } %>

    <div class="card">
        <form id="screeningForm" action="${pageContext.request.contextPath}/CVDServlet" method="post" enctype="multipart/form-data">
            <input type="hidden" name="action" value="analyze">
            <input type="hidden" name="csrf_token" value="<%= HtmlUtil.escapeHtml(csrfToken) %>">
            <input type="hidden" id="sampleImageInput" name="sampleImage" value="">

            <!-- Patient & Doctor Selection -->
            <div class="form-row">
                <div class="form-group">
                    <label for="patientId">Select Patient <span class="required">*</span></label>
                    <select id="patientId" name="patientId" required>
                        <option value="">-- Choose Patient --</option>
                        <%
                            List<Patient> patients = (List<Patient>) request.getAttribute("patients");
                            String preselected = (String) request.getAttribute("preselectedPatientId");
                            if (patients != null) {
                                for (Patient p : patients) {
                                    boolean sel = preselected != null && preselected.equals(String.valueOf(p.getId()));
                        %>
                            <option value="<%= p.getId() %>" <%= sel ? "selected" : "" %>>
                                #<%= p.getId() %> - <%= p.getName() %> (<%= p.getAge() %> yrs, <%= p.getGender() %>)
                            </option>
                        <%
                                }
                            }
                        %>
                    </select>
                </div>

                <div class="form-group">
                    <label for="doctorId">Assigned Doctor (Cardiologist / Physician)</label>
                    <select id="doctorId" name="doctorId">
                        <option value="">-- Optional / Unassigned --</option>
                        <%
                            List<Doctor> doctors = (List<Doctor>) request.getAttribute("doctors");
                            if (doctors != null) {
                                for (Doctor d : doctors) {
                        %>
                            <option value="<%= d.getId() %>">
                                <%= d.getName() %> (<%= d.getSpecialization() %>)
                            </option>
                        <%
                                }
                            }
                        %>
                    </select>
                </div>
            </div>

            <!-- Model Selection -->
            <div class="form-group">
                <label for="modelName">Segmentation Model</label>
                <select id="modelName" name="modelName">
                    <option value="Residual U-Net" selected>Residual U-Net (Default / Recommended)</option>
                    <option value="U-Net">U-Net (Baseline)</option>
                    <option value="Attention U-Net">Attention U-Net</option>
                    <option value="Compare All 3">Compare All 3</option>
                </select>
            </div>

            <!-- Notes -->
            <div class="form-group">
                <label for="notes">Clinical Notes / Patient Symptoms</label>
                <textarea id="notes" name="notes" rows="2" placeholder="e.g. History of elevated blood pressure, routine annual cardiac risk screening..."></textarea>
            </div>

            <!-- Retinal Scan Upload -->
            <div class="form-group">
                <label>Retinal Fundus Scan Image <span class="required">*</span></label>

                <div class="upload-dropzone" onclick="document.getElementById('fundusFileInput').click();">
                    <div class="upload-icon">📷</div>
                    <div class="upload-title">Click to browse or drop retinal fundus photograph</div>
                    <div class="upload-desc">Supports high-resolution JPEG or PNG fundus photography scans</div>
                    <input type="file" id="fundusFileInput" name="fundusImage" accept="image/jpeg,image/png,image/jpg" style="display:none;" onchange="handleFileSelected(this);">
                    <center><img id="imagePreview" alt="Scan Preview"></center>
                </div>

                <!-- Sample Demo Images for Quick Testing -->
                <div class="sample-section">
                    <label style="font-size:12.5px; color:#64748b; font-weight:600;">
                        💡 Or select a bundled sample fundus photograph for instant evaluation:
                    </label>

                    <div class="sample-grid">
                        <div class="sample-card" onclick="selectSample('img00330.jpg', this)">
                            <img src="${pageContext.request.contextPath}/uploads/fundus/samples/img00330.jpg" alt="Sample 1">
                            <span>Sample Scan #1</span>
                        </div>
                        <div class="sample-card" onclick="selectSample('img00332.jpg', this)">
                            <img src="${pageContext.request.contextPath}/uploads/fundus/samples/img00332.jpg" alt="Sample 2">
                            <span>Sample Scan #2</span>
                        </div>
                        <div class="sample-card" onclick="selectSample('img00333.jpg', this)">
                            <img src="${pageContext.request.contextPath}/uploads/fundus/samples/img00333.jpg" alt="Sample 3">
                            <span>Sample Scan #3</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="actions-bar">
                <a href="${pageContext.request.contextPath}/CVDServlet?action=list" class="btn-cancel">
                    Cancel
                </a>
                <button type="submit" class="btn-submit" id="submitBtn">
                    ⚡ Run PyTorch AI Analysis
                </button>
            </div>
        </form>
    </div>

</div>

<!-- Loading Overlay -->
<div id="loadingOverlay">
    <div class="spinner"></div>
    <div style="font-size: 18px; font-weight: 600;">Analyzing Retinal Microvasculature...</div>
    <div style="font-size: 13px; color: #94a3b8; margin-top: 6px;">Executing Multi-Task PyTorch Model (EfficientNet-B0)</div>
</div>

<script>
    function handleFileSelected(input) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function(e) {
                var preview = document.getElementById('imagePreview');
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(input.files[0]);

            // Clear sample selection
            document.getElementById('sampleImageInput').value = '';
            var cards = document.querySelectorAll('.sample-card');
            cards.forEach(function(c) { c.classList.remove('active'); });
        }
    }

    function selectSample(filename, element) {
        document.getElementById('sampleImageInput').value = filename;
        document.getElementById('fundusFileInput').value = '';

        var preview = document.getElementById('imagePreview');
        preview.src = '${pageContext.request.contextPath}/uploads/fundus/samples/' + filename;
        preview.style.display = 'block';

        var cards = document.querySelectorAll('.sample-card');
        cards.forEach(function(c) { c.classList.remove('active'); });
        element.classList.add('active');
    }

    document.getElementById('screeningForm').addEventListener('submit', function(e) {
        var fileInput = document.getElementById('fundusFileInput');
        var sampleInput = document.getElementById('sampleImageInput');

        if ((!fileInput.files || fileInput.files.length === 0) && (!sampleInput.value)) {
            alert('Please upload an image or choose one of the sample fundus scans.');
            e.preventDefault();
            return false;
        }

        document.getElementById('loadingOverlay').style.display = 'flex';
    });
</script>

</body>
</html>

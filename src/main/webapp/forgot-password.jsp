<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CareConnect | Password Assistance</title>
    <link rel="stylesheet" href="${pageContext.request.contextPath}/css/style.css">
    <style>
        .forgot-container {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f4f7fb;
            padding: 20px;
        }
        .forgot-card {
            background: white;
            max-width: 480px;
            width: 100%;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        }
        .forgot-card h2 {
            margin-top: 0;
            color: #111827;
            font-size: 26px;
        }
        .forgot-card p {
            color: #6b7280;
            font-size: 14px;
            line-height: 1.6;
        }
        .info-box {
            background: #eff6ff;
            border-left: 4px solid #2563eb;
            padding: 16px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 14px;
            color: #1e40af;
        }
        .info-box strong {
            display: block;
            margin-bottom: 6px;
        }
        .back-link {
            display: inline-block;
            margin-top: 20px;
            color: #2563eb;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
        }
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="forgot-container">
        <div class="forgot-card">
            <div class="brand" style="margin-bottom: 25px;">
                <span class="brand-icon">+</span>
                <span>Care<span>Connect</span></span>
            </div>
            <h2>Password Assistance</h2>
            <p>To maintain patient confidentiality and system security, passwords cannot be recovered or displayed directly.</p>
            
            <div class="info-box">
                <strong>Account Recovery Instructions:</strong>
                Please contact your designated Hospital Systems Administrator or IT Security Office to request a verified password reset.
            </div>

            <p>If you are an authorized administrator needing to provision or rotate system credentials, refer to the offline administrative setup protocol in the system documentation.</p>
            
            <a href="${pageContext.request.contextPath}/login.jsp" class="back-link">← Back to Login</a>
        </div>
    </div>
</body>
</html>

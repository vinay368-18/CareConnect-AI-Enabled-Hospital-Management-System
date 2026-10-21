<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Doctor" %>
<%@ page import="com.hms.model.User" %>
<%@ page import="com.hms.util.HtmlUtil" %>
<%@ page import="com.hms.util.CSRFUtil" %>

<%
    User sessionUser = (session != null) ? (User) session.getAttribute("user") : null;
    if (sessionUser == null) {
        response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized");
        return;
    }
    if (!"ADMIN".equalsIgnoreCase(sessionUser.getRole())) {
        response.sendRedirect(request.getContextPath() + "/dashboard.jsp?error=unauthorized");
        return;
    }

    String csrfToken = CSRFUtil.getToken(session);
%>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Provision Staff Account - CareConnect</title>

    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        body {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #f4f7fb;
            padding: 20px;
        }

        .container {
            width: 480px;
            background: white;
            padding: 35px;
            border-radius: 14px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.10);
        }

        .logo {
            text-align: center;
            margin-bottom: 8px;
            color: #2563eb;
            font-size: 30px;
            font-weight: bold;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 24px;
            font-size: 14px;
        }

        .admin-badge {
            display: inline-block;
            background: #e0e7ff;
            color: #3730a3;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            padding: 3px 8px;
            border-radius: 4px;
            margin-top: 4px;
        }

        .form-group {
            margin-bottom: 18px;
        }

        label {
            display: block;
            margin-bottom: 7px;
            font-size: 14px;
            font-weight: bold;
            color: #333;
        }

        input,
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #d5dbe5;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
        }

        input:focus,
        select:focus {
            border-color: #2563eb;
        }

        .doctor-section {
            display: none;
        }

        .btn {
            width: 100%;
            padding: 13px;
            border: none;
            border-radius: 8px;
            background: #2563eb;
            color: white;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 5px;
        }

        .btn:hover {
            background: #1d4ed8;
        }

        .back-link {
            text-align: center;
            margin-top: 22px;
            font-size: 14px;
            color: #666;
        }

        .back-link a {
            color: #2563eb;
            text-decoration: none;
            font-weight: bold;
        }

        .error {
            background: #fee2e2;
            color: #b91c1c;
            padding: 10px;
            border-radius: 7px;
            margin-bottom: 18px;
            text-align: center;
            font-size: 13px;
        }

        .success {
            background: #def7ec;
            color: #03543f;
            padding: 10px;
            border-radius: 7px;
            margin-bottom: 18px;
            text-align: center;
            font-size: 13px;
        }

        .info {
            background: #eff6ff;
            color: #1d4ed8;
            padding: 10px;
            border-radius: 7px;
            margin-bottom: 18px;
            font-size: 13px;
            line-height: 1.4;
        }
    </style>

    <script>
        function handleRoleChange() {
            const role = document.getElementById("role").value;
            const doctorSection = document.getElementById("doctorSection");
            const doctorId = document.getElementById("doctorId");

            if (role === "DOCTOR") {
                doctorSection.style.display = "block";
                doctorId.required = true;
            } else {
                doctorSection.style.display = "none";
                doctorId.required = false;
                doctorId.value = "";
            }
        }
    </script>
</head>

<body>

<div class="container">

    <div class="logo">CareConnect</div>

    <div class="subtitle">
        Administrative Staff Provisioning<br>
        <span class="admin-badge">Admin Authorization Required</span>
    </div>

    <%
        String error = request.getParameter("error");
        String registered = request.getParameter("registered");

        if ("empty".equals(error)) {
    %>
        <div class="error">
            Please fill in all required fields.
        </div>
    <%
        } else if ("password".equals(error)) {
    %>
        <div class="error">
            Passwords do not match.
        </div>
    <%
        } else if ("weakpassword".equals(error)) {
    %>
        <div class="error">
            Password must be at least 8 characters long.
        </div>
    <%
        } else if ("invalidusername".equals(error)) {
    %>
        <div class="error">
            Username must be 3-50 alphanumeric characters (or . - _).
        </div>
    <%
        } else if ("exists".equals(error)) {
    %>
        <div class="error">
            Username already exists in the system.
        </div>
    <%
        } else if ("invalidrole".equals(error)) {
    %>
        <div class="error">
            Invalid account role specified.
        </div>
    <%
        } else if ("doctor".equals(error)) {
    %>
        <div class="error">
            Please select an existing doctor profile.
        </div>
    <%
        } else if ("failed".equals(error)) {
    %>
        <div class="error">
            Account provisioning failed. Please try again.
        </div>
    <%
        } else if ("true".equals(registered)) {
    %>
        <div class="success">
            Staff account created successfully!
        </div>
    <%
        }
    %>

    <div class="info">
        Only authorized administrators can provision Receptionist and Doctor staff credentials.
    </div>

    <form action="RegisterServlet" method="post">
        <input type="hidden" name="csrf_token" value="<%= HtmlUtil.escapeHtml(csrfToken) %>">

        <div class="form-group">
            <label for="username">Staff Username</label>
            <input
                type="text"
                id="username"
                name="username"
                placeholder="Enter username (min 3 chars)"
                maxlength="50"
                required>
        </div>

        <div class="form-group">
            <label for="password">Temporary Password</label>
            <input
                type="password"
                id="password"
                name="password"
                placeholder="Minimum 8 characters"
                minlength="8"
                required>
        </div>

        <div class="form-group">
            <label for="confirmPassword">Confirm Password</label>
            <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                placeholder="Confirm password"
                minlength="8"
                required>
        </div>

        <div class="form-group">
            <label for="role">Staff Role</label>
            <select
                id="role"
                name="role"
                onchange="handleRoleChange()"
                required>
                <option value="">Select staff role</option>
                <option value="RECEPTIONIST">Receptionist</option>
                <option value="DOCTOR">Doctor</option>
            </select>
        </div>

        <div class="form-group doctor-section" id="doctorSection">
            <label for="doctorId">Linked Doctor Profile</label>
            <select id="doctorId" name="doctorId">
                <option value="">Select doctor profile</option>
                <%
                    List<Doctor> doctors = (List<Doctor>) request.getAttribute("doctors");
                    if (doctors != null) {
                        for (Doctor doctor : doctors) {
                %>
                    <option value="<%= doctor.getId() %>">
                        <%= HtmlUtil.escapeHtml(doctor.getName()) %>
                        -
                        <%= HtmlUtil.escapeHtml(doctor.getSpecialization()) %>
                    </option>
                <%
                        }
                    }
                %>
            </select>
        </div>

        <button type="submit" class="btn">
            Provision Staff Account
        </button>
    </form>

    <div class="back-link">
        <a href="${pageContext.request.contextPath}/dashboard.jsp">← Back to Dashboard</a>
    </div>

</div>

</body>
</html>

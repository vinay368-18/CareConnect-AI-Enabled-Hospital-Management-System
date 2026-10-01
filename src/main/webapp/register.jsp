<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Doctor" %>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Create Account - CareConnect</title>

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
        }

        .container {
            width: 430px;
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
            margin-bottom: 28px;
            font-size: 14px;
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

        .login-link {
            text-align: center;
            margin-top: 22px;
            font-size: 14px;
            color: #666;
        }

        .login-link a {
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

        .info {
            background: #eff6ff;
            color: #1d4ed8;
            padding: 10px;
            border-radius: 7px;
            margin-bottom: 18px;
            text-align: center;
            font-size: 13px;
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
        Create Staff Account
    </div>

    <%
        String error = request.getParameter("error");

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
        } else if ("exists".equals(error)) {
    %>
        <div class="error">
            Username already exists.
        </div>
    <%
        } else if ("invalidrole".equals(error)) {
    %>
        <div class="error">
            Invalid account role.
        </div>
    <%
        } else if ("doctor".equals(error)) {
    %>
        <div class="error">
            Please select a doctor.
        </div>
    <%
        } else if ("failed".equals(error)) {
    %>
        <div class="error">
            Account creation failed. Please try again.
        </div>
    <%
        }
    %>

    <div class="info">
        Only Receptionist and Doctor accounts can be created here.
    </div>

    <form action="RegisterServlet" method="post">

        <div class="form-group">
            <label for="username">Username</label>

            <input
                type="text"
                id="username"
                name="username"
                placeholder="Enter username"
                maxlength="50"
                required>
        </div>

        <div class="form-group">
            <label for="password">Password</label>

            <input
                type="password"
                id="password"
                name="password"
                placeholder="Enter password"
                required>
        </div>

        <div class="form-group">
            <label for="confirmPassword">Confirm Password</label>

            <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                placeholder="Confirm password"
                required>
        </div>

        <div class="form-group">
            <label for="role">Account Type</label>

            <select
                id="role"
                name="role"
                onchange="handleRoleChange()"
                required>

                <option value="">Select account type</option>
                <option value="RECEPTIONIST">Receptionist</option>
                <option value="DOCTOR">Doctor</option>

            </select>
        </div>

        <div
            class="form-group doctor-section"
            id="doctorSection">

            <label for="doctorId">Select Doctor</label>

            <select
                id="doctorId"
                name="doctorId">

                <option value="">Select doctor</option>

                <%
                    List<Doctor> doctors =
                        (List<Doctor>) request.getAttribute("doctors");

                    if (doctors != null) {

                        for (Doctor doctor : doctors) {
                %>

                    <option value="<%= doctor.getId() %>">
                        <%= doctor.getName() %>
                        -
                        <%= doctor.getSpecialization() %>
                    </option>

                <%
                        }
                    }
                %>

            </select>
        </div>

        <button type="submit" class="btn">
            Create Account
        </button>

    </form>

    <div class="login-link">
        Already have an account?
        <a href="login.jsp">Sign In</a>
    </div>

</div>

</body>
</html>
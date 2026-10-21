<%@ page import="com.hms.model.User" %>
<%@ page import="com.hms.util.HtmlUtil" %>
<%@ page import="com.hms.util.CSRFUtil" %>

<%
    User u = (session != null) ? (User) session.getAttribute("user") : null;
    if (u == null) {
        response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized");
        return;
    }
    if (!"ADMIN".equalsIgnoreCase(u.getRole()) && !"RECEPTIONIST".equalsIgnoreCase(u.getRole())) {
        response.sendRedirect(request.getContextPath() + "/dashboard.jsp?error=unauthorized");
        return;
    }
    String csrfToken = CSRFUtil.getToken(session);
%>
<%@ page language="java"
    contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>CareConnect | Add Patient</title>

    <style>

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Segoe UI", Arial, sans-serif;
        }

        body {
            background: #f5f8fa;
            color: #172b4d;
        }

        .container {
            max-width: 800px;
            margin: 50px auto;
            padding: 0 20px;
        }

        .header {
            margin-bottom: 25px;
        }

        .header h1 {
            font-size: 30px;
            color: #13233b;
            margin-bottom: 6px;
        }

        .header p {
            color: #8290a3;
            font-size: 14px;
        }

        .card {
            background: white;
            border: 1px solid #e8edf1;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 8px 30px rgba(25, 50, 75, 0.06);
        }

        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
        }

        .full {
            grid-column: 1 / -1;
        }

        label {
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #374151;
        }

        input,
        select,
        textarea {
            width: 100%;
            padding: 13px 14px;
            border: 1px solid #d8e0e5;
            border-radius: 9px;
            font-size: 14px;
            outline: none;
            background: white;
            transition: 0.2s;
        }

        input:focus,
        select:focus,
        textarea:focus {
            border-color: #087f75;
            box-shadow: 0 0 0 3px rgba(8, 127, 117, 0.10);
        }

        textarea {
            min-height: 100px;
            resize: vertical;
        }

        .buttons {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 25px;
        }

        .btn {
            padding: 12px 22px;
            border-radius: 9px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border: none;
        }

        .cancel {
            background: #f1f4f6;
            color: #536273;
        }

        .cancel:hover {
            background: #e5eaed;
        }

        .save {
            background: #087f75;
            color: white;
        }

        .save:hover {
            background: #056b63;
        }

        .error {
            background: #fff1f1;
            color: #c53030;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 13px;
        }

        @media (max-width: 650px) {

            .form-grid {
                grid-template-columns: 1fr;
            }

            .full {
                grid-column: auto;
            }

            .card {
                padding: 20px;
            }

        }

    </style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>Add New Patient</h1>

        <p>
            Register a new patient in CareConnect.
        </p>

    </div>


    <div class="card">

        <%
            String error = request.getParameter("error");

            if ("failed".equals(error)) {
        %>

            <div class="error">
                Unable to save patient. Please try again.
            </div>

        <%
            } else if ("invalid".equals(error)) {
        %>

            <div class="error">
                Please enter a valid age.
            </div>

        <%
            }
        %>


        <form action="${pageContext.request.contextPath}/PatientServlet"
      method="post">

   		 <input type="hidden" name="action" value="add">
            <input type="hidden" name="csrf_token" value="<%= HtmlUtil.escapeHtml(csrfToken) %>">

   		 <div class="form-grid">

                <!-- NAME -->

                <div class="form-group full">

                    <label for="name">
                        Patient Name
                    </label>

                    <input
                        type="text"
                        id="name"
                        name="name"
                        placeholder="Enter patient's full name"
                        required>

                </div>


                <!-- AGE -->

                <div class="form-group">

                    <label for="age">
                        Age
                    </label>

                    <input
                        type="number"
                        id="age"
                        name="age"
                        placeholder="Enter age"
                        min="1"
                        max="120"
                        required>

                </div>


                <!-- GENDER -->

                <div class="form-group">

                    <label for="gender">
                        Gender
                    </label>

                    <select id="gender"
                            name="gender"
                            required>

                        <option value="">
                            Select gender
                        </option>

                        <option value="Male">
                            Male
                        </option>

                        <option value="Female">
                            Female
                        </option>

                        <option value="Other">
                            Other
                        </option>

                    </select>

                </div>


                <!-- PHONE -->

                <div class="form-group">

                    <label for="phone">
                        Phone Number
                    </label>

                    <input
                        type="text"
                        id="phone"
                        name="phone"
                        placeholder="Enter phone number"
                        maxlength="15"
                        required>

                </div>


                <!-- ADDRESS -->

                <div class="form-group">

                    <label for="address">
                        Address
                    </label>

                    <input
                        type="text"
                        id="address"
                        name="address"
                        placeholder="Enter address">

                </div>


            </div>


            <div class="buttons">

                <a
                    href="${pageContext.request.contextPath}/PatientServlet?action=list"
                    class="btn cancel">
                    Cancel
                </a>

                <button
                    type="submit"
                    class="btn save">
                    Add Patient
                </button>

            </div>

        </form>

    </div>

</div>

</body>

</html>
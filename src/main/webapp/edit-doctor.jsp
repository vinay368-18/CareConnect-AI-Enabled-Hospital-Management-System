<%@ page pageEncoding="UTF-8" contentType="text/html; charset=UTF-8" %>
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
    if (!"ADMIN".equalsIgnoreCase(u.getRole())) {
        response.sendRedirect(request.getContextPath() + "/dashboard.jsp?error=unauthorized");
        return;
    }
    String csrfToken = CSRFUtil.getToken(session);
%>

<%
    Doctor doctor = (Doctor) request.getAttribute("doctor");

    if (doctor == null) {
        response.sendRedirect(
            request.getContextPath()
            + "/DoctorServlet?action=list"
        );
        return;
    }
%>

<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <title>CareConnect | Edit Doctor</title>

    <style>

        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #f5f8fa;
            color: #263b5a;
        }

        .container {
            width: 90%;
            max-width: 850px;
            margin: 50px auto;
        }

        .header {
            margin-bottom: 30px;
        }

        .header h1 {
            margin: 0;
            font-size: 32px;
        }

        .header p {
            margin-top: 8px;
            color: #8190a5;
        }

        .form-container {
            background: white;
            padding: 35px;
            border-radius: 18px;
            box-shadow: 0 5px 25px rgba(0, 0, 0, 0.06);
        }

        .doctor-id {
            background: #f4f7f9;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 25px;
            color: #5e6d82;
            font-weight: bold;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #43546b;
        }

        input, select {
            width: 100%;
            box-sizing: border-box;
            padding: 13px 14px;
            border: 1px solid #dce3ea;
            border-radius: 8px;
            font-size: 15px;
            outline: none;
            background: white;
        }

        input:focus, select:focus {
            border-color: #0b8f83;
        }

        .button-row {
            display: flex;
            gap: 12px;
            margin-top: 30px;
        }

        .update-btn {
            padding: 13px 24px;
            border: none;
            border-radius: 9px;
            background: #0b8f83;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        .update-btn:hover {
            background: #08766d;
        }

        .cancel-btn {
            padding: 13px 24px;
            border-radius: 9px;
            background: #eef2f5;
            color: #43546b;
            text-decoration: none;
            font-weight: bold;
        }

        .cancel-btn:hover {
            background: #e1e7eb;
        }

        .error-message {
            background: #fdecec;
            color: #c0392b;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        @media (max-width: 700px) {

            .form-row {
                grid-template-columns: 1fr;
            }

            .container {
                width: 94%;
            }

            .form-container {
                padding: 25px;
            }
        }

    </style>

</head>

<body>

<div class="container">

    <!-- HEADER -->

    <div class="header">

        <h1>Edit Doctor</h1>

        <p>Update doctor information in CareConnect.</p>

    </div>


    <!-- ERROR MESSAGE -->

    <%

        String error = request.getParameter("error");

        if (error != null) {

    %>

        <div class="error-message">

            <% if ("invalid".equals(error)) { %>

                Please enter valid doctor information.

            <% } else if ("failed".equals(error)) { %>

                Unable to update doctor. Please try again.

            <% } %>

        </div>

    <%

        }

    %>


    <!-- FORM -->

    <div class="form-container">

        <div class="doctor-id">

            Doctor ID:
            <%= doctor.getId() %>

        </div>


        <form action="${pageContext.request.contextPath}/DoctorServlet"
              method="post">

            <input type="hidden" name="action" value="update">
            <input type="hidden" name="csrf_token" value="<%= HtmlUtil.escapeHtml(csrfToken) %>">

            <input type="hidden"
                   name="id"
                   value="<%= doctor.getId() %>">


            <!-- NAME + SPECIALIZATION -->

            <div class="form-row">

                <div class="form-group">

                    <label for="name">
                        Doctor Name
                    </label>

                    <input type="text"
                           id="name"
                           name="name"
                           value="<%= doctor.getName() %>"
                           required>

                </div>


                <div class="form-group">

                    <label for="specialization">
                        Specialization (CVD / Retinal Care)
                    </label>

                    <%
                        String curSpec = doctor.getSpecialization() != null ? doctor.getSpecialization() : "";
                        String[] specs = {
                            "Preventive Cardiologist",
                            "Vitreo-Retinal Specialist (Ophthalmologist)",
                            "Interventional Cardiologist",
                            "General Cardiologist",
                            "Endocrinologist & Diabetologist",
                            "Vascular Medicine & Hypertension Specialist",
                            "Cardiac Electrophysiologist",
                            "Cardiothoracic Surgeon",
                            "Heart Failure & Transplant Cardiologist",
                            "Internal Medicine / Physician"
                        };
                    %>

                    <select id="specialization"
                            name="specialization"
                            required>
                        <%
                            boolean matched = false;
                            for (String sp : specs) {
                                boolean sel = sp.equalsIgnoreCase(curSpec);
                                if (sel) matched = true;
                        %>
                            <option value="<%= sp %>" <%= sel ? "selected" : "" %>><%= sp %></option>
                        <%  }
                            if (!matched && !curSpec.isEmpty()) {
                        %>
                            <option value="<%= curSpec %>" selected><%= curSpec %></option>
                        <%  } %>
                    </select>

                </div>

            </div>


            <!-- PHONE + EMAIL -->

            <div class="form-row">

                <div class="form-group">

                    <label for="phone">
                        Phone
                    </label>

                    <input type="tel"
                           id="phone"
                           name="phone"
                           value="<%= doctor.getPhone() %>"
                           required>

                </div>


                <div class="form-group">

                    <label for="email">
                        Email
                    </label>

                    <input type="email"
                           id="email"
                           name="email"
                           value="<%= doctor.getEmail() %>"
                           required>

                </div>

            </div>


            <!-- EXPERIENCE + FEE -->

            <div class="form-row">

                <div class="form-group">

                    <label for="experience">
                        Experience (Years)
                    </label>

                    <input type="number"
                           id="experience"
                           name="experience"
                           min="0"
                           max="70"
                           value="<%= doctor.getExperience() %>"
                           required>

                </div>


                <div class="form-group">

                    <label for="consultationFee">
                        Consultation Fee (₹)
                    </label>

                    <input type="number"
                           id="consultationFee"
                           name="consultationFee"
                           min="0"
                           step="0.01"
                           value="<%= doctor.getConsultationFee() %>"
                           required>

                </div>

            </div>


            <!-- BUTTONS -->

            <div class="button-row">

                <button type="submit"
                        class="update-btn">

                    Update Doctor

                </button>

                <a href="${pageContext.request.contextPath}/DoctorServlet?action=list"
                   class="cancel-btn">

                    Cancel

                </a>

            </div>

        </form>

    </div>

</div>

</body>

</html>
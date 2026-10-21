<%@ page pageEncoding="UTF-8" contentType="text/html; charset=UTF-8" %>
<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Patient" %>
<%@ page import="com.hms.model.Doctor" %>
<%@ page import="com.hms.dao.PatientDAO" %>
<%@ page import="com.hms.dao.DoctorDAO" %>
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

<%
    PatientDAO patientDAO = new PatientDAO();
    DoctorDAO doctorDAO = new DoctorDAO();

    List<Patient> patients = patientDAO.getAllPatients();
    List<Doctor> doctors = doctorDAO.getAllDoctors();

    String error = request.getParameter("error");
%>

<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <title>CareConnect | Add Appointment</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f8fa;
            color: #263b5a;
        }

        .container {
            width: 90%;
            max-width: 950px;
            margin: 50px auto;
        }

        .header {
            margin-bottom: 25px;
        }

        .header h1 {
            margin: 0;
            font-size: 34px;
        }

        .header p {
            margin-top: 8px;
            color: #8190a5;
            font-size: 16px;
        }

        .error {
            background: #fdecec;
            color: #c0392b;
            padding: 14px 18px;
            border-radius: 9px;
            margin-bottom: 20px;
        }

        .form-container {
            background: white;
            padding: 35px;
            border-radius: 18px;
            box-shadow: 0 5px 25px rgba(0, 0, 0, 0.06);
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 22px;
        }

        .form-group {
            margin-bottom: 22px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #43546b;
        }

        input,
        select,
        textarea {
            width: 100%;
            padding: 13px 14px;
            border: 1px solid #dce3ea;
            border-radius: 9px;
            font-size: 15px;
            font-family: Arial, sans-serif;
            outline: none;
        }

        input:focus,
        select:focus,
        textarea:focus {
            border-color: #0b9589;
        }

        textarea {
            resize: vertical;
            min-height: 100px;
        }

        .button-row {
            display: flex;
            gap: 12px;
            margin-top: 10px;
        }

        .add-btn {
            border: none;
            background: #0b9589;
            color: white;
            padding: 14px 24px;
            border-radius: 9px;
            font-weight: bold;
            font-size: 15px;
            cursor: pointer;
        }

        .add-btn:hover {
            background: #08766d;
        }

        .cancel-btn {
            background: #edf2f5;
            color: #43546b;
            text-decoration: none;
            padding: 14px 24px;
            border-radius: 9px;
            font-weight: bold;
        }

        .cancel-btn:hover {
            background: #e1e7eb;
        }

        @media (max-width: 700px) {

            .container {
                width: 94%;
            }

            .form-container {
                padding: 25px;
            }

            .form-row {
                grid-template-columns: 1fr;
                gap: 0;
            }

        }

    </style>

</head>

<body>

<div class="container">

    <!-- HEADER -->

    <div class="header">

        <h1>Add Appointment</h1>

        <p>
            Schedule a new patient appointment in CareConnect.
        </p>

    </div>


    <!-- ERROR -->

    <% if ("invalid".equals(error)) { %>

        <div class="error">
            Please enter valid appointment information.
        </div>

    <% } else if ("failed".equals(error)) { %>

        <div class="error">
            Unable to add appointment. Please try again.
        </div>

    <% } %>


    <!-- FORM -->

    <div class="form-container">

        <form action="${pageContext.request.contextPath}/AppointmentServlet"
              method="post">

            <input type="hidden" name="action" value="add">
            <input type="hidden" name="csrf_token" value="<%= HtmlUtil.escapeHtml(csrfToken) %>">


            <!-- PATIENT + DOCTOR -->

            <div class="form-row">

                <div class="form-group">

                    <label for="patientId">
                        Patient
                    </label>

                    <select id="patientId"
                            name="patientId"
                            required>

                        <option value="">
                            Select Patient
                        </option>

                        <%
                            if (patients != null) {

                                for (Patient patient : patients) {
                        %>

                            <option value="<%= patient.getId() %>">

                                <%= patient.getName() %>

                                - ID <%= patient.getId() %>

                            </option>

                        <%
                                }
                            }
                        %>

                    </select>

                </div>


                <div class="form-group">

                    <label for="doctorId">
                        Doctor
                    </label>

                    <select id="doctorId"
                            name="doctorId"
                            required>

                        <option value="">
                            Select Doctor
                        </option>

                        <%
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

            </div>


            <!-- DATE + TIME -->

            <div class="form-row">

                <div class="form-group">

                    <label for="appointmentDate">
                        Appointment Date
                    </label>

                    <input type="date"
                           id="appointmentDate"
                           name="appointmentDate"
                           required>

                </div>


                <div class="form-group">

                    <label for="appointmentTime">
                        Appointment Time
                    </label>

                    <input type="time"
                           id="appointmentTime"
                           name="appointmentTime"
                           required>

                </div>

            </div>


            <!-- REASON + STATUS -->

            <div class="form-row">

                <div class="form-group">

                    <label for="reason">
                        Reason
                    </label>

                    <textarea id="reason"
                              name="reason"
                              placeholder="Enter reason for appointment..."
                              required></textarea>

                </div>


                <div class="form-group">

                    <label for="status">
                        Status
                    </label>

                    <select id="status"
                            name="status"
                            required>

                        <option value="Scheduled">
                            Scheduled
                        </option>

                        <option value="Completed">
                            Completed
                        </option>

                        <option value="Cancelled">
                            Cancelled
                        </option>

                    </select>

                </div>

            </div>


            <!-- BUTTONS -->

            <div class="button-row">

                <button type="submit"
                        class="add-btn">

                    Add Appointment

                </button>


                <a href="${pageContext.request.contextPath}/AppointmentServlet?action=list"
                   class="cancel-btn">

                    Cancel

                </a>

            </div>

        </form>

    </div>

</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
    const dateInput = document.getElementById("appointmentDate");
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
    const timeInput = document.getElementById("appointmentTime");
    if (timeInput && !timeInput.value) {
        timeInput.value = "10:00";
    }
});
</script>

</body>

</html>
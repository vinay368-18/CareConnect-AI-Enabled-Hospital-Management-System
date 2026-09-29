<%@ page pageEncoding="UTF-8" contentType="text/html; charset=UTF-8" %>
<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Appointment" %>
<%@ page import="com.hms.model.Patient" %>
<%@ page import="com.hms.model.Doctor" %>
<%@ page import="com.hms.dao.PatientDAO" %>
<%@ page import="com.hms.dao.DoctorDAO" %>

<%
    Appointment appointment =
        (Appointment) request.getAttribute("appointment");

    PatientDAO patientDAO = new PatientDAO();
    DoctorDAO doctorDAO = new DoctorDAO();

    List<Patient> patients = patientDAO.getAllPatients();
    List<Doctor> doctors = doctorDAO.getAllDoctors();

    String error = request.getParameter("error");

    if (appointment == null) {
        response.sendRedirect(
            request.getContextPath()
            + "/AppointmentServlet?action=list"
        );
        return;
    }
%>

<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <title>CareConnect | Edit Appointment</title>

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

        .appointment-id {
            background: #f5f8fa;
            padding: 13px 15px;
            border-radius: 9px;
            margin-bottom: 25px;
            color: #52657d;
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

        .update-btn {
            border: none;
            background: #0b9589;
            color: white;
            padding: 14px 24px;
            border-radius: 9px;
            font-weight: bold;
            font-size: 15px;
            cursor: pointer;
        }

        .update-btn:hover {
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

        <h1>Edit Appointment</h1>

        <p>
            Update appointment information in CareConnect.
        </p>

    </div>


    <!-- ERROR -->

    <% if ("invalid".equals(error)) { %>

        <div class="error">
            Please enter valid appointment information.
        </div>

    <% } else if ("failed".equals(error)) { %>

        <div class="error">
            Unable to update appointment. Please try again.
        </div>

    <% } %>


    <!-- FORM -->

    <div class="form-container">

        <div class="appointment-id">

            <strong>Appointment ID:</strong>

            <%= appointment.getId() %>

        </div>


        <form action="${pageContext.request.contextPath}/AppointmentServlet"
              method="post">

            <input type="hidden"
                   name="action"
                   value="update">

            <input type="hidden"
                   name="id"
                   value="<%= appointment.getId() %>">


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

                                    boolean selected =
                                        patient.getId()
                                        == appointment.getPatientId();
                        %>

                            <option
                                value="<%= patient.getId() %>"
                                <%= selected ? "selected" : "" %>>

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

                                    boolean selected =
                                        doctor.getId()
                                        == appointment.getDoctorId();
                        %>

                            <option
                                value="<%= doctor.getId() %>"
                                <%= selected ? "selected" : "" %>>

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
                           value="<%= appointment.getAppointmentDate() %>"
                           required>

                </div>


                <div class="form-group">

                    <label for="appointmentTime">
                        Appointment Time
                    </label>

                    <input type="time"
                           id="appointmentTime"
                           name="appointmentTime"
                           value="<%= appointment.getAppointmentTime() %>"
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
                              required><%= appointment.getReason() %></textarea>

                </div>


                <div class="form-group">

                    <label for="status">
                        Status
                    </label>

                    <select id="status"
                            name="status"
                            required>

                        <option value="Scheduled"
                            <%= "Scheduled".equals(appointment.getStatus())
                                ? "selected" : "" %>>
                            Scheduled
                        </option>

                        <option value="Completed"
                            <%= "Completed".equals(appointment.getStatus())
                                ? "selected" : "" %>>
                            Completed
                        </option>

                        <option value="Cancelled"
                            <%= "Cancelled".equals(appointment.getStatus())
                                ? "selected" : "" %>>
                            Cancelled
                        </option>

                    </select>

                </div>

            </div>


            <!-- BUTTONS -->

            <div class="button-row">

                <button type="submit"
                        class="update-btn">

                    Update Appointment

                </button>


                <a href="${pageContext.request.contextPath}/AppointmentServlet?action=list"
                   class="cancel-btn">

                    Cancel

                </a>

            </div>

        </form>

    </div>

</div>

</body>

</html>
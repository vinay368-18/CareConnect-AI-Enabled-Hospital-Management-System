<%@ page pageEncoding="UTF-8" contentType="text/html; charset=UTF-8" %>
<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Appointment" %>

<%
    List<Appointment> appointments =
        (List<Appointment>) request.getAttribute("appointments");
%>

<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <title>CareConnect | Appointments</title>

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
            width: 92%;
            max-width: 1450px;
            margin: 55px auto;
        }

        /* =========================
           HEADER
           ========================= */

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
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

        .add-btn {
            background: #0b9589;
            color: white;
            text-decoration: none;
            padding: 15px 24px;
            border-radius: 10px;
            font-weight: bold;
            transition: 0.2s;
        }

        .add-btn:hover {
            background: #08766d;
        }

        /* =========================
           SEARCH
           ========================= */

        .search-container {
            background: white;
            padding: 22px;
            border-radius: 16px;
            box-shadow: 0 5px 25px rgba(0, 0, 0, 0.05);
            margin-bottom: 24px;
        }

        .search-form {
            display: flex;
            gap: 12px;
        }

        .search-input {
            flex: 1;
            padding: 14px 16px;
            border: 1px solid #dce3ea;
            border-radius: 9px;
            font-size: 15px;
            outline: none;
        }

        .search-input:focus {
            border-color: #0b9589;
        }

        .search-btn {
            border: none;
            background: #263f63;
            color: white;
            padding: 14px 25px;
            border-radius: 9px;
            font-weight: bold;
            cursor: pointer;
        }

        .search-btn:hover {
            background: #1c314f;
        }

        .clear-btn {
            display: flex;
            align-items: center;
            text-decoration: none;
            background: #edf2f5;
            color: #43546b;
            padding: 14px 20px;
            border-radius: 9px;
            font-weight: bold;
        }

        /* =========================
           TABLE
           ========================= */

        .table-container {
            background: white;
            padding: 14px;
            border-radius: 18px;
            box-shadow: 0 5px 25px rgba(0, 0, 0, 0.05);
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 1050px;
        }

        th {
            background: #f3f6f8;
            color: #52647b;
            text-align: left;
            padding: 17px 16px;
            font-size: 14px;
        }

        td {
            padding: 17px 16px;
            border-bottom: 1px solid #edf1f4;
            color: #52647b;
            font-size: 14px;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background: #fafcfd;
        }

        .id {
            color: #079488;
            font-weight: bold;
        }

        .patient-name,
        .doctor-name {
            font-weight: bold;
            color: #334b6c;
        }

        .date {
            white-space: nowrap;
        }

        .time {
            white-space: nowrap;
        }

        /* =========================
           STATUS
           ========================= */

        .status {
            display: inline-block;
            padding: 7px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }

        .scheduled {
            background: #e8f5ff;
            color: #1976b9;
        }

        .completed {
            background: #e6f7ef;
            color: #168354;
        }

        .cancelled {
            background: #fdeaea;
            color: #c0392b;
        }

        .default-status {
            background: #f0f2f4;
            color: #596878;
        }

        /* =========================
           ACTION BUTTONS
           ========================= */

        .actions {
            display: flex;
            gap: 8px;
        }

        .edit-btn {
            display: inline-block;
            text-decoration: none;
            background: #e7f7f5;
            color: #087f75;
            padding: 8px 13px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
        }

        .edit-btn:hover {
            background: #d4efec;
        }

        .delete-btn {
            display: inline-block;
            text-decoration: none;
            background: #fdecec;
            color: #c0392b;
            padding: 8px 13px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
        }

        .delete-btn:hover {
            background: #f8d8d8;
        }

        /* =========================
           EMPTY STATE
           ========================= */

        .empty {
            text-align: center;
            padding: 55px 20px;
            color: #8190a5;
            font-size: 16px;
        }

        /* =========================
           ERROR
           ========================= */

        .error-message {
            background: #fdecec;
            color: #c0392b;
            padding: 13px 17px;
            border-radius: 9px;
            margin-bottom: 20px;
        }

        /* =========================
           RESPONSIVE
           ========================= */

        @media (max-width: 700px) {

            .container {
                width: 94%;
                margin-top: 30px;
            }

            .header {
                flex-direction: column;
                align-items: flex-start;
                gap: 20px;
            }

            .search-form {
                flex-direction: column;
            }

            .search-btn,
            .clear-btn {
                justify-content: center;
                text-align: center;
            }
        }

    </style>

</head>

<body>

<div class="container">


    <!-- =========================
         HEADER
         ========================= -->

    <div class="header">

        <div>

            <h1>Appointment Management</h1>

            <p>
                Schedule and manage patient appointments.
            </p>

        </div>

        <div style="display: flex; gap: 10px;">

            <a href="${pageContext.request.contextPath}/dashboard.jsp"
               style="display: inline-flex; align-items: center; background: #263f63; color: white; text-decoration: none; padding: 15px 22px; border-radius: 10px; font-weight: bold;">
                ← Dashboard
            </a>

            <a href="${pageContext.request.contextPath}/CVDServlet?action=list"
               style="display: inline-flex; align-items: center; background: #0f766e; color: white; text-decoration: none; padding: 15px 22px; border-radius: 10px; font-weight: bold;">
                ❤️ CVD Diagnostics
            </a>

            <a href="${pageContext.request.contextPath}/add-appointment.jsp"
               class="add-btn">

                + Add Appointment

            </a>

        </div>

    </div>


    <!-- =========================
         ERROR MESSAGE
         ========================= -->

    <%
        String error = request.getParameter("error");

        if (error != null) {
    %>

        <div class="error-message">

            <% if ("delete".equals(error)) { %>

                Unable to delete appointment. Please try again.

            <% } else if ("invalid".equals(error)) { %>

                Invalid appointment information.

            <% } %>

        </div>

    <%
        }
    %>


    <!-- =========================
         SEARCH
         ========================= -->

    <div class="search-container">

        <form action="${pageContext.request.contextPath}/AppointmentServlet"
              method="get"
              class="search-form">

            <input type="hidden"
                   name="action"
                   value="search">


            <input type="text"
                   name="keyword"
                   class="search-input"
                   placeholder="Search by patient, doctor, reason or status..."
                   value="<%= request.getAttribute("searchKeyword") != null
                           ? request.getAttribute("searchKeyword")
                           : "" %>">


            <button type="submit"
                    class="search-btn">

                Search

            </button>


            <a href="${pageContext.request.contextPath}/AppointmentServlet?action=list"
               class="clear-btn">

                Clear

            </a>

        </form>

    </div>


    <!-- =========================
         APPOINTMENT TABLE
         ========================= -->

    <div class="table-container">

        <table>

            <thead>

                <tr>

                    <th>ID</th>

                    <th>Patient</th>

                    <th>Doctor</th>

                    <th>Date</th>

                    <th>Time</th>

                    <th>Reason</th>

                    <th>Status</th>

                    <th>Actions</th>

                </tr>

            </thead>


            <tbody>

            <%
                if (appointments != null &&
                    !appointments.isEmpty()) {

                    for (Appointment appointment : appointments) {
            %>

                <tr>

                    <td class="id">
                        <%= appointment.getId() %>
                    </td>


                    <td class="patient-name">
                        <%= appointment.getPatientName() %>
                    </td>


                    <td class="doctor-name">
                        <%= appointment.getDoctorName() %>
                    </td>


                    <td class="date">
                        <%= appointment.getAppointmentDate() %>
                    </td>


                    <td class="time">
                        <%= appointment.getAppointmentTime() %>
                    </td>


                    <td>
                        <%= appointment.getReason() != null
                            ? appointment.getReason()
                            : "-" %>
                    </td>


                    <td>

                        <%
                            String status =
                                appointment.getStatus();

                            String statusClass =
                                "default-status";

                            if ("Scheduled".equalsIgnoreCase(status)) {

                                statusClass = "scheduled";

                            } else if ("Completed".equalsIgnoreCase(status)) {

                                statusClass = "completed";

                            } else if ("Cancelled".equalsIgnoreCase(status)) {

                                statusClass = "cancelled";
                            }
                        %>

                        <span class="status <%= statusClass %>">

                            <%= status %>

                        </span>

                    </td>


                    <td>

                        <div class="actions">

                            <a href="${pageContext.request.contextPath}/AppointmentServlet?action=edit&id=<%= appointment.getId() %>"
                               class="edit-btn">

                                Edit

                            </a>


                            <a href="${pageContext.request.contextPath}/AppointmentServlet?action=delete&id=<%= appointment.getId() %>"
                               class="delete-btn"
                               onclick="return confirm('Are you sure you want to delete this appointment?');">

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

                    <td colspan="8"
                        class="empty">

                        No appointments found.

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
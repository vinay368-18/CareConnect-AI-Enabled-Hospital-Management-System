<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Appointment" %>

<%
    int totalPatients = (Integer) request.getAttribute("totalPatients");
    int totalDoctors = (Integer) request.getAttribute("totalDoctors");
    int totalAppointments = (Integer) request.getAttribute("totalAppointments");
    int totalBills = (Integer) request.getAttribute("totalBills");

    double totalPaidAmount =
        (Double) request.getAttribute("totalPaidAmount");

    double totalPendingAmount =
        (Double) request.getAttribute("totalPendingAmount");

    int cancelledBills =
        (Integer) request.getAttribute("cancelledBills");

    List<Appointment> recentAppointments =
        (List<Appointment>) request.getAttribute("recentAppointments");
%>

<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <title>CareConnect - Reports</title>

    <style>

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        body {
            background: #f4f7fb;
            color: #1f2937;
            padding: 30px;
        }

        .container {
            max-width: 1300px;
            margin: auto;
        }

        /* HEADER */

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #1e3a8a;
            font-size: 30px;
        }

        .header p {
            color: #6b7280;
            margin-top: 5px;
        }

        .back-btn {
            text-decoration: none;
            background: #1e3a8a;
            color: white;
            padding: 11px 18px;
            border-radius: 7px;
            font-weight: bold;
        }

        .back-btn:hover {
            background: #1d4ed8;
        }

        /* STAT CARDS */

        .cards {
            display: grid;
            grid-template-columns:
                repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }

        .card {
            background: white;
            padding: 22px;
            border-radius: 12px;
            box-shadow:
                0 4px 15px rgba(0,0,0,0.07);
        }

        .card-title {
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 10px;
        }

        .card-value {
            font-size: 30px;
            font-weight: bold;
            color: #1e3a8a;
        }

        .card-icon {
            font-size: 28px;
            margin-bottom: 10px;
        }

        /* FINANCIAL SECTION */

        .financial-section {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }

        .financial-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow:
                0 4px 15px rgba(0,0,0,0.07);
        }

        .financial-title {
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 10px;
        }

        .financial-value {
            font-size: 27px;
            font-weight: bold;
        }

        .paid {
            color: #15803d;
        }

        .pending {
            color: #d97706;
        }

        .cancelled {
            color: #dc2626;
        }

        /* APPOINTMENTS */

        .section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow:
                0 4px 15px rgba(0,0,0,0.07);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .section-header h2 {
            color: #1e3a8a;
            font-size: 21px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: #1e3a8a;
            color: white;
            padding: 13px;
            text-align: left;
        }

        td {
            padding: 13px;
            border-bottom: 1px solid #e5e7eb;
        }

        tr:hover {
            background: #f8fafc;
        }

        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }

        .scheduled {
            background: #dbeafe;
            color: #1d4ed8;
        }

        .completed {
            background: #dcfce7;
            color: #166534;
        }

        .cancelled-status {
            background: #fee2e2;
            color: #991b1b;
        }

        .empty {
            text-align: center;
            padding: 35px;
            color: #6b7280;
        }

        /* RESPONSIVE */

        @media (max-width: 1000px) {

            .cards {
                grid-template-columns:
                    repeat(2, 1fr);
            }

            .financial-section {
                grid-template-columns:
                    1fr;
            }
        }

        @media (max-width: 600px) {

            body {
                padding: 15px;
            }

            .header {
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }

            .cards {
                grid-template-columns:
                    1fr;
            }

            table {
                font-size: 13px;
            }

            th,
            td {
                padding: 8px;
            }
        }

    </style>

</head>

<body>

<div class="container">


    <!-- HEADER -->

    <div class="header">

        <div>

            <h1>CareConnect Reports</h1>

            <p>
                Hospital overview and management statistics
            </p>

        </div>

        <a href="${pageContext.request.contextPath}/dashboard.jsp"
           class="back-btn">
            Back to Dashboard
        </a>

    </div>


    <!-- STATISTICS -->

    <div class="cards">


        <!-- PATIENTS -->

        <div class="card">

            <div class="card-icon">
                👥
            </div>

            <div class="card-title">
                Total Patients
            </div>

            <div class="card-value">
                <%= totalPatients %>
            </div>

        </div>


        <!-- DOCTORS -->

        <div class="card">

            <div class="card-icon">
                🩺
            </div>

            <div class="card-title">
                Total Doctors
            </div>

            <div class="card-value">
                <%= totalDoctors %>
            </div>

        </div>


        <!-- APPOINTMENTS -->

        <div class="card">

            <div class="card-icon">
                📅
            </div>

            <div class="card-title">
                Total Appointments
            </div>

            <div class="card-value">
                <%= totalAppointments %>
            </div>

        </div>


        <!-- BILLS -->

        <div class="card">

            <div class="card-icon">
                💳
            </div>

            <div class="card-title">
                Total Bills
            </div>

            <div class="card-value">
                <%= totalBills %>
            </div>

        </div>

    </div>


    <!-- FINANCIAL REPORT -->

    <div class="financial-section">


        <!-- PAID -->

        <div class="financial-card">

            <div class="financial-title">
                Total Paid Amount
            </div>

            <div class="financial-value paid">

                ₹<%= String.format("%.2f",
                        totalPaidAmount) %>

            </div>

        </div>


        <!-- PENDING -->

        <div class="financial-card">

            <div class="financial-title">
                Total Pending Amount
            </div>

            <div class="financial-value pending">

                ₹<%= String.format("%.2f",
                        totalPendingAmount) %>

            </div>

        </div>


        <!-- CANCELLED -->

        <div class="financial-card">

            <div class="financial-title">
                Cancelled Bills
            </div>

            <div class="financial-value cancelled">

                <%= cancelledBills %>

            </div>

        </div>

    </div>


    <!-- RECENT APPOINTMENTS -->

    <div class="section">

        <div class="section-header">

            <h2>
                Recent Appointments
            </h2>

        </div>


        <% if (recentAppointments == null
                || recentAppointments.isEmpty()) { %>

            <div class="empty">

                <h3>No appointments found</h3>

                <p>
                    Recent appointments will appear here.
                </p>

            </div>

        <% } else { %>


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

                    </tr>

                </thead>


                <tbody>

                <% for (Appointment appointment
                        : recentAppointments) { %>

                    <tr>

                        <td>
                            <%= appointment.getId() %>
                        </td>

                        <td>
                            <%= appointment.getPatientName() %>
                        </td>

                        <td>
                            Dr. <%= appointment.getDoctorName() %>
                        </td>

                        <td>
                            <%= appointment.getAppointmentDate() %>
                        </td>

                        <td>
                            <%= appointment.getAppointmentTime() %>
                        </td>

                        <td>
                            <%= appointment.getReason() %>
                        </td>

                        <td>

                            <%
                                String status =
                                    appointment.getStatus();

                                String statusClass =
                                    "scheduled";

                                if ("Completed".equalsIgnoreCase(status)) {

                                    statusClass =
                                        "completed";

                                } else if ("Cancelled"
                                        .equalsIgnoreCase(status)) {

                                    statusClass =
                                        "cancelled-status";
                                }
                            %>

                            <span class="status <%= statusClass %>">

                                <%= status %>

                            </span>

                        </td>

                    </tr>

                <% } %>

                </tbody>

            </table>


        <% } %>

    </div>

</div>

</body>

</html>
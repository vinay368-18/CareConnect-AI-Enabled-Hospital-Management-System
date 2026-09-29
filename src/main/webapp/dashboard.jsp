<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>
<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Appointment" %>
<%@ page import="com.hms.dao.ReportDAO" %>

<%
    ReportDAO reportDAO = new ReportDAO();
    int livePatients = reportDAO.getTotalPatients();
    int liveDoctors = reportDAO.getTotalDoctors();
    int liveAppointments = reportDAO.getTotalAppointments();
    int livePendingBills = reportDAO.getPendingBillsCount();
    List<Appointment> recentAppts = reportDAO.getRecentAppointments();
    String currentUser = (session != null && session.getAttribute("user") != null) ? (String) session.getAttribute("user") : "Administrator";
    String initial = (!currentUser.isEmpty()) ? currentUser.substring(0, 1).toUpperCase() : "A";
%>

<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>CareConnect | Dashboard</title>

    <link rel="stylesheet"
          href="${pageContext.request.contextPath}/css/style.css">

</head>


<body>


<!-- =========================================================
     SIDEBAR
========================================================= -->

<aside class="sidebar">


    <!-- LOGO -->

    <div class="logo">

        <span class="logo-icon">+</span>

        <span class="logo-text">
            CareConnect
        </span>

    </div>


    <p class="menu-label">
        MAIN MENU
    </p>


    <!-- NAVIGATION -->

    <nav class="menu">


        <!-- Dashboard -->

        <a href="${pageContext.request.contextPath}/dashboard.jsp"
           class="active">

            <span class="menu-icon">⌂</span>

            <span>
                Dashboard
            </span>

        </a>


        <!-- Patients -->

        <a href="${pageContext.request.contextPath}/PatientServlet?action=list">

            <span class="menu-icon">♙</span>

            <span>
                Patients
            </span>

        </a>


        <!-- Doctors -->

        <a href="${pageContext.request.contextPath}/DoctorServlet?action=list">

            <span class="menu-icon">⚕</span>

            <span>
                Doctors
            </span>

        </a>


        <!-- Appointments -->

        <a href="${pageContext.request.contextPath}/AppointmentServlet?action=list">

            <span class="menu-icon">▣</span>

            <span>
                Appointments
            </span>

        </a>


        <!-- Billing -->

        <a href="${pageContext.request.contextPath}/BillingServlet?action=list">

            <span class="menu-icon">₹</span>

            <span>
                Billing
            </span>

        </a>


        <!-- Reports -->

        <a href="${pageContext.request.contextPath}/ReportServlet">

            <span class="menu-icon">▤</span>

            <span>
                Reports
            </span>

        </a>


    </nav>


    <!-- LOGOUT -->

    <div class="logout">

        <a href="${pageContext.request.contextPath}/LogoutServlet">
            Logout
        </a>

    </div>


</aside>



<!-- =========================================================
     MAIN CONTENT
========================================================= -->

<main class="main">


    <!-- =====================================================
         TOP BAR
    ====================================================== -->

    <header class="topbar">


        <div class="page-title">

            <h1>
                Dashboard
            </h1>

            <p>
                Hospital Management System
            </p>

        </div>


        <div class="top-actions">


            <!-- Search -->

            <label class="search">

                <input
                    id="dashboardSearch"
                    type="search"
                    placeholder="Search appointments..."
                    autocomplete="off">

            </label>


            <!-- Notifications -->

            <button
                class="notification"
                type="button"
                aria-label="Notifications">

                🔔

            </button>


            <!-- Profile -->

            <div class="profile">

                <span class="profile-icon">
                    <%= initial %>
                </span>


                <span class="profile-info">

                    <strong>
                        <%= currentUser %>
                    </strong>

                    <span>
                        Hospital Admin
                    </span>

                </span>

            </div>


        </div>


    </header>



    <!-- =====================================================
         CONTENT
    ====================================================== -->

    <section class="content">


        <!-- WELCOME -->

        <div class="welcome">

            <h2>
                Welcome, <%= currentUser %>
            </h2>

            <p>
                Here's a live overview of your hospital system.
            </p>

        </div>



        <!-- =================================================
             STATISTICS
        ================================================== -->

        <div class="stats">


            <!-- TOTAL PATIENTS -->

            <div class="stat-card">

                <div class="stat-top">

                    <span class="stat-label">
                        Total Patients
                    </span>

                    <span class="stat-icon">
                        ♙
                    </span>

                </div>


                <div class="stat-number">
                    <%= livePatients %>
                </div>


                <div class="trend">

                    <a href="${pageContext.request.contextPath}/PatientServlet?action=list" style="color: inherit; text-decoration: none;">
                        View all patients →
                    </a>

                </div>

            </div>



            <!-- TOTAL DOCTORS -->

            <div class="stat-card">

                <div class="stat-top">

                    <span class="stat-label">
                        Total Doctors
                    </span>

                    <span class="stat-icon">
                        ⚕
                    </span>

                </div>


                <div class="stat-number">
                    <%= liveDoctors %>
                </div>


                <div class="trend">

                    <a href="${pageContext.request.contextPath}/DoctorServlet?action=list" style="color: inherit; text-decoration: none;">
                        View all doctors →
                    </a>

                </div>

            </div>



            <!-- APPOINTMENTS -->

            <div class="stat-card">

                <div class="stat-top">

                    <span class="stat-label">
                        Total Appointments
                    </span>

                    <span class="stat-icon">
                        ▣
                    </span>

                </div>


                <div class="stat-number">
                    <%= liveAppointments %>
                </div>


                <div class="trend">

                    <a href="${pageContext.request.contextPath}/AppointmentServlet?action=list" style="color: inherit; text-decoration: none;">
                        View all appointments →
                    </a>

                </div>

            </div>



            <!-- PENDING BILLS -->

            <div class="stat-card">

                <div class="stat-top">

                    <span class="stat-label">
                        Pending Bills
                    </span>

                    <span class="stat-icon">
                        ₹
                    </span>

                </div>


                <div class="stat-number">
                    <%= livePendingBills %>
                </div>


                <div class="trend">

                    <a href="${pageContext.request.contextPath}/BillingServlet?action=list" style="color: inherit; text-decoration: none;">
                        View billing →
                    </a>

                </div>

            </div>


        </div>



        <!-- =================================================
             MAIN GRID
        ================================================== -->

        <div class="grid">


            <!-- =================================================
                 TODAY'S APPOINTMENTS
            ================================================== -->

            <section class="card">


                <div class="card-header">

                    <h3>
                        Recent Appointments
                    </h3>


                    <a
                        class="view"
                        href="${pageContext.request.contextPath}/AppointmentServlet?action=list">

                        View all →

                    </a>

                </div>



                <%
                    if (recentAppts != null && !recentAppts.isEmpty()) {
                        for (Appointment appt : recentAppts) {
                            String pName = appt.getPatientName() != null ? appt.getPatientName() : "Patient #" + appt.getPatientId();
                            String pInitials = pName.length() >= 2 ? pName.substring(0, 2).toUpperCase() : "PT";
                            String dName = appt.getDoctorName() != null ? "Dr. " + appt.getDoctorName() : "Doctor #" + appt.getDoctorId();
                            String apptStatus = appt.getStatus() != null ? appt.getStatus() : "Scheduled";
                            String badgeClass = "confirmed";
                            if ("Pending".equalsIgnoreCase(apptStatus)) badgeClass = "pending";
                            else if ("Cancelled".equalsIgnoreCase(apptStatus)) badgeClass = "pending";
                %>
                <div class="appointment">

                    <div class="patient">

                        <span class="avatar">
                            <%= pInitials %>
                        </span>

                        <div>

                            <strong>
                                <%= pName %>
                            </strong>

                            <span>
                                <%= appt.getReason() != null ? appt.getReason() : "Consultation" %>
                            </span>

                        </div>

                    </div>

                    <span class="doctor">
                        <%= dName %>
                    </span>

                    <span class="time">
                        <%= appt.getAppointmentDate() %> <%= appt.getAppointmentTime() %>
                    </span>

                    <span class="status <%= badgeClass %>">
                        <%= apptStatus %>
                    </span>

                </div>
                <%
                        }
                    } else {
                %>
                <div style="text-align: center; padding: 40px 20px; color: #8492a6;">
                    <p style="margin: 0 0 10px; font-size: 15px;">No appointments found in database.</p>
                    <a href="${pageContext.request.contextPath}/add-appointment.jsp" style="color: #0b9589; font-weight: 600; text-decoration: none;">+ Schedule First Appointment</a>
                </div>
                <%
                    }
                %>


            </section>



            <!-- =================================================
                 QUICK ACTIONS
            ================================================== -->

            <section class="card">


                <div class="card-header">

                    <h3>
                        Quick Actions
                    </h3>

                </div>



                <!-- ADD PATIENT -->

                <a
                    class="action"
                    href="${pageContext.request.contextPath}/add-patient.jsp">

                    <span class="action-icon">
                        +
                    </span>


                    <div>

                        <strong>
                            Add Patient
                        </strong>

                        <span>
                            Register a new patient
                        </span>

                    </div>

                </a>



                <!-- ADD DOCTOR -->

                <a
                    class="action"
                    href="${pageContext.request.contextPath}/add-doctor.jsp">

                    <span class="action-icon">
                        ⚕
                    </span>


                    <div>

                        <strong>
                            Add Doctor
                        </strong>

                        <span>
                            Register a new doctor
                        </span>

                    </div>

                </a>



                <!-- BOOK APPOINTMENT -->

                <a
                    class="action"
                    href="${pageContext.request.contextPath}/add-appointment.jsp">

                    <span class="action-icon">
                        +
                    </span>


                    <div>

                        <strong>
                            Book Appointment
                        </strong>

                        <span>
                            Schedule an appointment
                        </span>

                    </div>

                </a>



                <!-- CREATE BILL -->

                <a
                    class="action"
                    href="${pageContext.request.contextPath}/add-bill.jsp">

                    <span class="action-icon">
                        ₹
                    </span>


                    <div>

                        <strong>
                            Create Invoice
                        </strong>

                        <span>
                            Generate patient billing
                        </span>

                    </div>

                </a>


            </section>


        </div>



        <!-- =================================================
             BOTTOM GRID
        ================================================== -->

        <div class="bottom-grid">


            <!-- =================================================
                 DEPARTMENT OVERVIEW
            ================================================== -->

            <section class="card">


                <div class="card-header">

                    <h3>
                        Department Overview
                    </h3>


                    <a
                        class="view"
                        href="${pageContext.request.contextPath}/ReportServlet">

                        View all →

                    </a>

                </div>



                <!-- GENERAL MEDICINE -->

                <div class="department">

                    <div class="department-top">

                        <strong>
                            General Medicine
                        </strong>

                        <span>
                            82 patients
                        </span>

                    </div>


                    <div class="progress">

                        <div
                            class="progress-bar"
                            style="width: 82%;">

                        </div>

                    </div>

                </div>



                <!-- CARDIOLOGY -->

                <div class="department">

                    <div class="department-top">

                        <strong>
                            Cardiology
                        </strong>

                        <span>
                            64 patients
                        </span>

                    </div>


                    <div class="progress">

                        <div
                            class="progress-bar"
                            style="width: 64%;">

                        </div>

                    </div>

                </div>



                <!-- ORTHOPEDICS -->

                <div class="department">

                    <div class="department-top">

                        <strong>
                            Orthopedics
                        </strong>

                        <span>
                            51 patients
                        </span>

                    </div>


                    <div class="progress">

                        <div
                            class="progress-bar"
                            style="width: 51%;">

                        </div>

                    </div>

                </div>



                <!-- PEDIATRICS -->

                <div class="department">

                    <div class="department-top">

                        <strong>
                            Pediatrics
                        </strong>

                        <span>
                            36 patients
                        </span>

                    </div>


                    <div class="progress">

                        <div
                            class="progress-bar"
                            style="width: 36%;">

                        </div>

                    </div>

                </div>


            </section>



            <!-- =================================================
                 RECENT ACTIVITY
            ================================================== -->

            <section class="card">


                <div class="card-header">

                    <h3>
                        Recent Activity
                    </h3>

                </div>



                <!-- ACTIVITY 1 -->

                <div class="activity">

                    <span class="activity-icon">
                        +
                    </span>


                    <div>

                        <p>

                            <strong>
                                New patient
                            </strong>

                            Arun Kumar registered

                        </p>

                        <span>
                            10 minutes ago
                        </span>

                    </div>

                </div>



                <!-- ACTIVITY 2 -->

                <div class="activity">

                    <span class="activity-icon">
                        ▣
                    </span>


                    <div>

                        <p>

                            <strong>
                                Appointment
                            </strong>

                            Rahul Sharma checked in

                        </p>

                        <span>
                            35 minutes ago
                        </span>

                    </div>

                </div>



                <!-- ACTIVITY 3 -->

                <div class="activity">

                    <span class="activity-icon">
                        ₹
                    </span>


                    <div>

                        <p>

                            <strong>
                                Payment
                            </strong>

                            Invoice #1024 paid

                        </p>

                        <span>
                            1 hour ago
                        </span>

                    </div>

                </div>



                <!-- ACTIVITY 4 -->

                <div class="activity">

                    <span class="activity-icon">
                        ⚕
                    </span>


                    <div>

                        <p>

                            <strong>
                                Doctor
                            </strong>

                            Dr. Anjali updated profile

                        </p>

                        <span>
                            2 hours ago
                        </span>

                    </div>

                </div>


            </section>


        </div>


    </section>


</main>



<!-- =========================================================
     JAVASCRIPT
========================================================= -->

<script>

document.addEventListener("DOMContentLoaded", function () {


    /* =====================================================
       SEARCH APPOINTMENTS
    ===================================================== */

    const searchInput =
        document.getElementById("dashboardSearch");


    if (searchInput) {

        searchInput.addEventListener(
            "input",
            function () {

                const query =
                    this.value
                        .toLowerCase()
                        .trim();


                document
                    .querySelectorAll(".appointment")
                    .forEach(function (row) {

                        const matches =
                            row.textContent
                               .toLowerCase()
                               .includes(query);

                        row.hidden = !matches;

                    });

            }
        );

    }



    /* =====================================================
       PRESS "/" TO FOCUS SEARCH
    ===================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "/"
                &&
                document.activeElement !== searchInput
            ) {

                event.preventDefault();

                if (searchInput) {
                    searchInput.focus();
                }

            }

        }
    );



    /* =====================================================
       ANIMATE STATISTIC NUMBERS
    ===================================================== */

    document
        .querySelectorAll(".stat-number")
        .forEach(function (counter) {


            const target =
                Number(
                    counter.textContent.trim()
                );


            if (Number.isNaN(target)) {
                return;
            }


            const duration = 1000;

            const startTime =
                performance.now();


            function updateCounter(currentTime) {

                const progress =
                    Math.min(
                        (currentTime - startTime)
                        / duration,
                        1
                    );


                const smoothProgress =
                    1 -
                    Math.pow(
                        1 - progress,
                        3
                    );


                counter.textContent =
                    Math.floor(
                        target *
                        smoothProgress
                    );


                if (progress < 1) {

                    requestAnimationFrame(
                        updateCounter
                    );

                } else {

                    counter.textContent =
                        target;

                }

            }


            requestAnimationFrame(
                updateCounter
            );

        });



    /* =====================================================
       NOTIFICATION
    ===================================================== */

    const notification =
        document.querySelector(".notification");


    if (notification) {

        notification.addEventListener(
            "click",
            function () {


                alert(
                    "You have 3 new hospital notifications."
                );


                this.animate(
                    [
                        {
                            transform: "rotate(0deg)"
                        },

                        {
                            transform: "rotate(-15deg)"
                        },

                        {
                            transform: "rotate(15deg)"
                        },

                        {
                            transform: "rotate(0deg)"
                        }
                    ],
                    {
                        duration: 450,
                        easing: "ease-in-out"
                    }
                );

            }
        );

    }



    /* =====================================================
       LIVE GREETING
    ===================================================== */

    const greeting =
        document.querySelector(
            ".welcome h2"
        );


    if (greeting) {

        const hour =
            new Date().getHours();


        let message =
            "Good evening";


        if (hour < 12) {

            message =
                "Good morning";

        } else if (hour < 18) {

            message =
                "Good afternoon";

        }


        greeting.textContent =
            message +
            ", Administrator";

    }


});

</script>


</body>

</html>
<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>

    <%@ page import="java.util.List" %>
        <%@ page import="com.hms.dao.ReportDAO" %>
            <%@ page import="com.hms.dao.CVDScreeningDAO" %>
                <%@ page import="com.hms.model.Appointment" %>
                    <%@ page import="com.hms.model.CVDScreening" %>
                        <%@ page import="com.hms.model.User" %>
                            <%@ page import="com.hms.util.HtmlUtil" %>

                                <% if (session==null || session.getAttribute("user")==null) {
                                    response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized" );
                                    return; } %>

                                    <% ReportDAO reportDAO=new ReportDAO(); CVDScreeningDAO cvdDAO=new
                                        CVDScreeningDAO(); int livePatients=reportDAO.getTotalPatients(); int
                                        liveDoctors=reportDAO.getTotalDoctors(); int
                                        liveAppointments=reportDAO.getTotalAppointments(); int
                                        livePendingBills=reportDAO.getPendingBillsCount(); int
                                        liveCvdScreenings=cvdDAO.getTotalScreeningsCount(); List<Appointment>
                                        recentAppts =
                                        reportDAO.getRecentAppointments();
                                        List<CVDScreening> recentCvdScreenings =
                                            cvdDAO.getRecentScreenings(4);

                                            User currentUserObj = null;

                                            if (session != null) {
                                            currentUserObj =
                                            (User) session.getAttribute("user");
                                            }

                                            String currentUser = "Administrator";
                                            String role = "ADMIN";

                                            if (currentUserObj != null) {

                                            if (currentUserObj.getUsername() != null
                                            && !currentUserObj.getUsername().trim().isEmpty()) {

                                            currentUser =
                                            currentUserObj.getUsername();
                                            }

                                            if (currentUserObj.getRole() != null
                                            && !currentUserObj.getRole().trim().isEmpty()) {

                                            role =
                                            currentUserObj.getRole();
                                            }
                                            }

                                            String initial = "A";

                                            if (currentUser != null
                                            && !currentUser.trim().isEmpty()) {

                                            initial =
                                            currentUser.substring(0, 1).toUpperCase();
                                            }
                                            %>

                                            <!DOCTYPE html>
                                            <html lang="en">

                                            <head>

                                                <meta charset="UTF-8">

                                                <meta name="viewport" content="width=device-width, initial-scale=1.0">

                                                <title>CareConnect | Dashboard</title>

                                                <style>
                                                    * {
                                                        margin: 0;
                                                        padding: 0;
                                                        box-sizing: border-box;
                                                        font-family: Arial, sans-serif;
                                                    }

                                                    body {
                                                        background: #f5f7fb;
                                                        color: #1f2937;
                                                    }

                                                    .layout {
                                                        display: flex;
                                                        min-height: 100vh;
                                                    }

                                                    /* SIDEBAR */

                                                    .sidebar {
                                                        width: 250px;
                                                        background: #ffffff;
                                                        border-right: 1px solid #e5e7eb;
                                                        position: fixed;
                                                        top: 0;
                                                        bottom: 0;
                                                        left: 0;
                                                        overflow-y: auto;
                                                    }

                                                    .logo {
                                                        height: 80px;
                                                        display: flex;
                                                        align-items: center;
                                                        padding: 0 25px;
                                                        border-bottom: 1px solid #eef0f4;
                                                    }

                                                    .logo-icon {
                                                        width: 38px;
                                                        height: 38px;
                                                        background: #2563eb;
                                                        color: white;
                                                        border-radius: 10px;
                                                        display: flex;
                                                        justify-content: center;
                                                        align-items: center;
                                                        font-size: 25px;
                                                        font-weight: bold;
                                                        margin-right: 10px;
                                                    }

                                                    .logo-text {
                                                        font-size: 21px;
                                                        font-weight: bold;
                                                        color: #1f2937;
                                                    }

                                                    .logo-text span {
                                                        color: #2563eb;
                                                    }

                                                    .menu-title {
                                                        padding: 25px 25px 10px;
                                                        font-size: 11px;
                                                        font-weight: bold;
                                                        color: #9ca3af;
                                                        text-transform: uppercase;
                                                        letter-spacing: 1px;
                                                    }

                                                    .menu {
                                                        padding: 0 12px;
                                                    }

                                                    .menu a {
                                                        display: flex;
                                                        align-items: center;
                                                        gap: 13px;
                                                        padding: 13px 14px;
                                                        margin-bottom: 4px;
                                                        border-radius: 8px;
                                                        color: #4b5563;
                                                        text-decoration: none;
                                                        font-size: 14px;
                                                    }

                                                    .menu a:hover {
                                                        background: #eff6ff;
                                                        color: #2563eb;
                                                    }

                                                    .menu a.active {
                                                        background: #2563eb;
                                                        color: white;
                                                    }

                                                    .menu-icon {
                                                        width: 20px;
                                                        text-align: center;
                                                        font-size: 16px;
                                                    }

                                                    /* MAIN */

                                                    .main {
                                                        margin-left: 250px;
                                                        width: calc(100% - 250px);
                                                        min-height: 100vh;
                                                    }

                                                    /* HEADER */

                                                    .topbar {
                                                        height: 80px;
                                                        background: white;
                                                        border-bottom: 1px solid #e5e7eb;
                                                        display: flex;
                                                        align-items: center;
                                                        justify-content: space-between;
                                                        padding: 0 35px;
                                                    }

                                                    .page-title h1 {
                                                        font-size: 24px;
                                                        color: #111827;
                                                    }

                                                    .page-title p {
                                                        color: #6b7280;
                                                        font-size: 13px;
                                                        margin-top: 5px;
                                                    }

                                                    .profile {
                                                        display: flex;
                                                        align-items: center;
                                                        gap: 12px;
                                                    }

                                                    .profile-info {
                                                        text-align: right;
                                                    }

                                                    .profile-name {
                                                        font-size: 14px;
                                                        font-weight: bold;
                                                        color: #111827;
                                                    }

                                                    .profile-role {
                                                        font-size: 11px;
                                                        color: #6b7280;
                                                        margin-top: 3px;
                                                    }

                                                    .avatar {
                                                        width: 42px;
                                                        height: 42px;
                                                        border-radius: 50%;
                                                        background: #2563eb;
                                                        color: white;
                                                        display: flex;
                                                        align-items: center;
                                                        justify-content: center;
                                                        font-weight: bold;
                                                    }

                                                    /* CONTENT */

                                                    .content {
                                                        padding: 30px 35px;
                                                    }

                                                    .welcome {
                                                        background: linear-gradient(135deg,
                                                                #2563eb,
                                                                #1d4ed8);
                                                        color: white;
                                                        padding: 25px 30px;
                                                        border-radius: 14px;
                                                        margin-bottom: 25px;
                                                    }

                                                    .welcome h2 {
                                                        font-size: 23px;
                                                        margin-bottom: 8px;
                                                    }

                                                    .welcome p {
                                                        font-size: 14px;
                                                        opacity: 0.9;
                                                    }

                                                    /* STAT CARDS */

                                                    .stats {
                                                        display: grid;
                                                        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                                                        gap: 20px;
                                                        margin-bottom: 30px;
                                                    }

                                                    .stat-card {
                                                        background: white;
                                                        border-radius: 12px;
                                                        padding: 22px;
                                                        border: 1px solid #e5e7eb;
                                                        display: flex;
                                                        justify-content: space-between;
                                                        align-items: center;
                                                    }

                                                    .stat-info p {
                                                        color: #6b7280;
                                                        font-size: 13px;
                                                        margin-bottom: 8px;
                                                    }

                                                    .stat-info h2 {
                                                        font-size: 28px;
                                                        color: #111827;
                                                    }

                                                    .stat-icon {
                                                        width: 48px;
                                                        height: 48px;
                                                        border-radius: 12px;
                                                        background: #eff6ff;
                                                        color: #2563eb;
                                                        display: flex;
                                                        align-items: center;
                                                        justify-content: center;
                                                        font-size: 21px;
                                                    }

                                                    /* SECTION */

                                                    .section {
                                                        background: white;
                                                        border: 1px solid #e5e7eb;
                                                        border-radius: 12px;
                                                        margin-bottom: 25px;
                                                        overflow: hidden;
                                                    }

                                                    .section-header {
                                                        display: flex;
                                                        justify-content: space-between;
                                                        align-items: center;
                                                        padding: 20px 22px;
                                                        border-bottom: 1px solid #eef0f4;
                                                    }

                                                    .section-header h3 {
                                                        font-size: 17px;
                                                        color: #111827;
                                                    }

                                                    .view-all {
                                                        text-decoration: none;
                                                        color: #2563eb;
                                                        font-size: 13px;
                                                        font-weight: 600;
                                                    }

                                                    /* TABLE */

                                                    .table-container {
                                                        overflow-x: auto;
                                                    }

                                                    table {
                                                        width: 100%;
                                                        border-collapse: collapse;
                                                    }

                                                    th {
                                                        text-align: left;
                                                        padding: 14px 20px;
                                                        font-size: 12px;
                                                        color: #6b7280;
                                                        background: #f9fafb;
                                                        text-transform: uppercase;
                                                    }

                                                    td {
                                                        padding: 15px 20px;
                                                        border-top: 1px solid #f0f1f4;
                                                        font-size: 13px;
                                                        color: #374151;
                                                    }

                                                    .status {
                                                        display: inline-block;
                                                        padding: 5px 10px;
                                                        border-radius: 20px;
                                                        font-size: 11px;
                                                        font-weight: bold;
                                                    }

                                                    .status-scheduled {
                                                        background: #dbeafe;
                                                        color: #1d4ed8;
                                                    }

                                                    .status-completed {
                                                        background: #dcfce7;
                                                        color: #15803d;
                                                    }

                                                    .status-cancelled {
                                                        background: #fee2e2;
                                                        color: #b91c1c;
                                                    }

                                                    .status-default {
                                                        background: #f3f4f6;
                                                        color: #4b5563;
                                                    }

                                                    /* QUICK ACTIONS */

                                                    .quick-actions {
                                                        display: grid;
                                                        grid-template-columns:
                                                            repeat(4, 1fr);
                                                        gap: 15px;
                                                        padding: 22px;
                                                    }

                                                    .action {
                                                        text-decoration: none;
                                                        border: 1px solid #e5e7eb;
                                                        border-radius: 10px;
                                                        padding: 18px;
                                                        color: #374151;
                                                        transition: 0.2s;
                                                    }

                                                    .action:hover {
                                                        border-color: #2563eb;
                                                        background: #eff6ff;
                                                    }

                                                    .action-icon {
                                                        width: 40px;
                                                        height: 40px;
                                                        background: #eff6ff;
                                                        color: #2563eb;
                                                        border-radius: 8px;
                                                        display: flex;
                                                        align-items: center;
                                                        justify-content: center;
                                                        margin-bottom: 12px;
                                                        font-size: 18px;
                                                    }

                                                    .action strong {
                                                        display: block;
                                                        font-size: 14px;
                                                        margin-bottom: 5px;
                                                    }

                                                    .action span {
                                                        font-size: 12px;
                                                        color: #6b7280;
                                                    }

                                                    /* EMPTY */

                                                    .empty {
                                                        padding: 35px;
                                                        text-align: center;
                                                        color: #9ca3af;
                                                        font-size: 13px;
                                                    }

                                                    /* FOOTER */

                                                    .footer {
                                                        text-align: center;
                                                        color: #9ca3af;
                                                        font-size: 12px;
                                                        padding: 15px;
                                                    }

                                                    /* RESPONSIVE */

                                                    @media (max-width: 1100px) {

                                                        .stats {
                                                            grid-template-columns:
                                                                repeat(2, 1fr);
                                                        }

                                                        .quick-actions {
                                                            grid-template-columns:
                                                                repeat(2, 1fr);
                                                        }
                                                    }

                                                    @media (max-width: 750px) {

                                                        .sidebar {
                                                            width: 70px;
                                                        }

                                                        .logo {
                                                            justify-content: center;
                                                            padding: 0;
                                                        }

                                                        .logo-text,
                                                        .menu-title,
                                                        .menu a span:not(.menu-icon) {
                                                            display: none;
                                                        }

                                                        .menu a {
                                                            justify-content: center;
                                                        }

                                                        .main {
                                                            margin-left: 70px;
                                                            width: calc(100% - 70px);
                                                        }

                                                        .topbar {
                                                            padding: 0 20px;
                                                        }

                                                        .content {
                                                            padding: 20px;
                                                        }

                                                        .stats {
                                                            grid-template-columns: 1fr;
                                                        }

                                                        .quick-actions {
                                                            grid-template-columns: 1fr;
                                                        }

                                                        .profile-info {
                                                            display: none;
                                                        }
                                                    }
                                                </style>

                                            </head>

                                            <body>

                                                <div class="layout">

                                                    <!-- =====================================================
         SIDEBAR
         ===================================================== -->

                                                    <aside class="sidebar">

                                                        <div class="logo">

                                                            <div class="logo-icon">
                                                                +
                                                            </div>

                                                            <div class="logo-text">
                                                                Care<span>Connect</span>
                                                            </div>

                                                        </div>


                                                        <div class="menu-title">
                                                            Main Menu
                                                        </div>


                                                        <nav class="menu">

                                                            <a href="${pageContext.request.contextPath}/dashboard.jsp"
                                                                class="active">

                                                                <span class="menu-icon">⌂</span>

                                                                <span>Dashboard</span>

                                                            </a>


                                                            <a
                                                                href="${pageContext.request.contextPath}/PatientServlet?action=list">

                                                                <span class="menu-icon">♟</span>

                                                                <span>Patients</span>

                                                            </a>


                                                            <a
                                                                href="${pageContext.request.contextPath}/DoctorServlet?action=list">

                                                                <span class="menu-icon">⚕</span>

                                                                <span>Doctors</span>

                                                            </a>


                                                            <a
                                                                href="${pageContext.request.contextPath}/AppointmentServlet?action=list">

                                                                <span class="menu-icon">▣</span>

                                                                <span>Appointments</span>

                                                            </a>


                                                            <a
                                                                href="${pageContext.request.contextPath}/BillingServlet?action=list">

                                                                <span class="menu-icon">₹</span>

                                                                <span>Billing</span>

                                                            </a>


                                                            <a href="${pageContext.request.contextPath}/ReportServlet">

                                                                <span class="menu-icon">▤</span>

                                                                <span>Reports</span>

                                                            </a>


                                                            <a href="${pageContext.request.contextPath}/CVDServlet?action=list"
                                                                style="color: #0f766e; font-weight: bold;">

                                                                <span class="menu-icon">❤️</span>

                                                                <span>CVD Diagnostics</span>
                                                            </a>

                                                            <% if ("ADMIN".equalsIgnoreCase(role)) { %>
                                                                <a href="${pageContext.request.contextPath}/RegisterServlet"
                                                                    style="color: #4f46e5; font-weight: bold;">
                                                                    <span class="menu-icon">??</span>
                                                                    <span>Staff Provisioning</span>
                                                                </a>
                                                                <% } %>

                                                        </nav>


                                                        <!-- =================================================
             ACCOUNT
             ================================================= -->

                                                        <div class="menu-title">
                                                            Account
                                                        </div>


                                                        <nav class="menu">

                                                            <a href="${pageContext.request.contextPath}/LogoutServlet">

                                                                <span class="menu-icon">↪</span>

                                                                <span>Logout</span>

                                                            </a>

                                                        </nav>

                                                    </aside>


                                                    <!-- =====================================================
         MAIN
         ===================================================== -->

                                                    <main class="main">


                                                        <!-- TOP BAR -->

                                                        <header class="topbar">

                                                            <div class="page-title">

                                                                <h1>
                                                                    Dashboard
                                                                </h1>

                                                                <p>
                                                                    Hospital Management Overview
                                                                </p>

                                                            </div>


                                                            <div class="profile">

                                                                <div class="profile-info">

                                                                    <div class="profile-name">
                                                                        <%= HtmlUtil.escapeHtml(currentUser) %>
                                                                    </div>

                                                                    <div class="profile-role">
                                                                        <%= HtmlUtil.escapeHtml(role) %>
                                                                    </div>

                                                                </div>


                                                                <div class="avatar">
                                                                    <%= HtmlUtil.escapeHtml(initial) %>
                                                                </div>

                                                            </div>

                                                        </header>


                                                        <!-- CONTENT -->

                                                        <div class="content">


                                                            <!-- WELCOME -->

                                                            <div class="welcome">

                                                                <h2>
                                                                    Welcome back, <%= HtmlUtil.escapeHtml(currentUser)
                                                                        %>
                                                                </h2>

                                                                <p>
                                                                    Here's what's happening in your hospital today.
                                                                </p>

                                                            </div>


                                                            <!-- =================================================
                 STATISTICS
                 ================================================= -->

                                                            <div class="stats">


                                                                <div class="stat-card">

                                                                    <div class="stat-info">

                                                                        <p>
                                                                            Total Patients
                                                                        </p>

                                                                        <h2>
                                                                            <%= livePatients %>
                                                                        </h2>

                                                                    </div>

                                                                    <div class="stat-icon">
                                                                        ♟
                                                                    </div>

                                                                </div>


                                                                <div class="stat-card">

                                                                    <div class="stat-info">

                                                                        <p>
                                                                            Total Doctors
                                                                        </p>

                                                                        <h2>
                                                                            <%= liveDoctors %>
                                                                        </h2>

                                                                    </div>

                                                                    <div class="stat-icon">
                                                                        ⚕
                                                                    </div>

                                                                </div>


                                                                <div class="stat-card">

                                                                    <div class="stat-info">

                                                                        <p>
                                                                            Appointments
                                                                        </p>

                                                                        <h2>
                                                                            <%= liveAppointments %>
                                                                        </h2>

                                                                    </div>

                                                                    <div class="stat-icon">
                                                                        ▣
                                                                    </div>

                                                                </div>


                                                                <div class="stat-card">

                                                                    <div class="stat-info">

                                                                        <p>
                                                                            Pending Bills
                                                                        </p>

                                                                        <h2>
                                                                            <%= livePendingBills %>
                                                                        </h2>

                                                                    </div>

                                                                    <div class="stat-icon">
                                                                        ₹
                                                                    </div>

                                                                </div>


                                                                <div class="stat-card"
                                                                    style="border-left: 4px solid #0f766e;">

                                                                    <div class="stat-info">

                                                                        <p>
                                                                            CVD AI Screenings
                                                                        </p>

                                                                        <h2 style="color: #0f766e;">
                                                                            <%= liveCvdScreenings %>
                                                                        </h2>

                                                                    </div>

                                                                    <div class="stat-icon"
                                                                        style="background: #f0fdfa; color: #0f766e;">
                                                                        ❤️
                                                                    </div>

                                                                </div>

                                                            </div>


                                                            <!-- =================================================
                 RECENT APPOINTMENTS
                 ================================================= -->

                                                            <div class="section">

                                                                <div class="section-header">

                                                                    <h3>
                                                                        Recent Appointments
                                                                    </h3>

                                                                    <a href="${pageContext.request.contextPath}/AppointmentServlet?action=list"
                                                                        class="view-all">

                                                                        View All

                                                                    </a>

                                                                </div>


                                                                <div class="table-container">

                                                                    <table>

                                                                        <thead>

                                                                            <tr>

                                                                                <th>
                                                                                    Patient
                                                                                </th>

                                                                                <th>
                                                                                    Doctor
                                                                                </th>

                                                                                <th>
                                                                                    Date
                                                                                </th>

                                                                                <th>
                                                                                    Time
                                                                                </th>

                                                                                <th>
                                                                                    Status
                                                                                </th>

                                                                            </tr>

                                                                        </thead>


                                                                        <tbody>

                                                                            <% if (recentAppts !=null &&
                                                                                !recentAppts.isEmpty()) { for
                                                                                (Appointment appointment : recentAppts)
                                                                                { String
                                                                                appointmentStatus=appointment.getStatus();
                                                                                String statusClass="status-default" ; if
                                                                                (appointmentStatus !=null) { if
                                                                                ("Scheduled".equalsIgnoreCase(
                                                                                appointmentStatus)) {
                                                                                statusClass="status-scheduled" ; } else
                                                                                if ("Completed".equalsIgnoreCase(
                                                                                appointmentStatus)) {
                                                                                statusClass="status-completed" ; } else
                                                                                if ("Cancelled".equalsIgnoreCase(
                                                                                appointmentStatus)) {
                                                                                statusClass="status-cancelled" ; } } %>

                                                                                <tr>

                                                                                    <td>
                                                                                        <%= appointment.getPatientName()
                                                                                            %>
                                                                                    </td>

                                                                                    <td>
                                                                                        <%= appointment.getDoctorName()
                                                                                            %>
                                                                                    </td>

                                                                                    <td>
                                                                                        <%= appointment.getAppointmentDate()
                                                                                            %>
                                                                                    </td>

                                                                                    <td>
                                                                                        <%= appointment.getAppointmentTime()
                                                                                            %>
                                                                                    </td>

                                                                                    <td>

                                                                                        <span
                                                                                            class="status <%= statusClass %>">

                                                                                            <%= appointmentStatus !=null
                                                                                                ? appointmentStatus
                                                                                                : "Unknown" %>

                                                                                        </span>

                                                                                    </td>

                                                                                </tr>

                                                                                <% } } else { %>

                                                                                    <tr>

                                                                                        <td colspan="5">

                                                                                            <div class="empty">

                                                                                                No appointments found.

                                                                                            </div>

                                                                                        </td>

                                                                                    </tr>

                                                                                    <% } %>

                                                                        </tbody>

                                                                    </table>

                                                                </div>

                                                            </div>


                                                            <!-- =================================================
                 RECENT CVD SCREENINGS
                 ================================================= -->

                                                            <div class="section">

                                                                <div class="section-header">

                                                                    <h3>
                                                                        ❤️ Recent AI Retinal & CVD Screenings
                                                                    </h3>

                                                                    <a href="${pageContext.request.contextPath}/CVDServlet?action=list"
                                                                        class="view-all">

                                                                        View All Screenings

                                                                    </a>

                                                                </div>


                                                                <div class="table-container">

                                                                    <table>

                                                                        <thead>

                                                                            <tr>

                                                                                <th>
                                                                                    ID
                                                                                </th>

                                                                                <th>
                                                                                    Patient
                                                                                </th>

                                                                                <th>
                                                                                    Doctor
                                                                                </th>

                                                                                <th>
                                                                                    CVD Risk
                                                                                </th>

                                                                                <th>
                                                                                    Hypertension
                                                                                </th>

                                                                                <th>
                                                                                    Diabetic Retinopathy
                                                                                </th>

                                                                                <th>
                                                                                    Overall Risk
                                                                                </th>

                                                                                <th>
                                                                                    Action
                                                                                </th>

                                                                            </tr>

                                                                        </thead>


                                                                        <tbody>

                                                                            <% if (recentCvdScreenings !=null &&
                                                                                !recentCvdScreenings.isEmpty()) { for
                                                                                (CVDScreening cvdItem :
                                                                                recentCvdScreenings) { String
                                                                                cvdRiskClass="completed" ; if ("High Risk".equalsIgnoreCase(cvdItem.getRiskLevel()))
                                                                                { cvdRiskClass="cancelled" ; } else if
                                                                                ("Moderate Risk".equalsIgnoreCase(cvdItem.getRiskLevel()))
                                                                                { cvdRiskClass="scheduled" ; } %>

                                                                                <tr>

                                                                                    <td>
                                                                                        <strong>#<%=
                                                                                                cvdItem.getScreeningId()
                                                                                                %></strong>
                                                                                    </td>

                                                                                    <td>
                                                                                        <strong>
                                                                                            <%= cvdItem.getPatientName()
                                                                                                %>
                                                                                        </strong>
                                                                                    </td>

                                                                                    <td>
                                                                                        <%= cvdItem.getDoctorName()
                                                                                            !=null ?
                                                                                            cvdItem.getDoctorName()
                                                                                            : "General" %>
                                                                                    </td>

                                                                                    <td>
                                                                                        <%= cvdItem.getCvdPrediction()
                                                                                            %> (<%=
                                                                                                cvdItem.getCvdPercent()
                                                                                                %>%)
                                                                                    </td>

                                                                                    <td>
                                                                                        <%= cvdItem.getHypertensionPrediction()
                                                                                            %> (<%=
                                                                                                cvdItem.getHypertensionPercent()
                                                                                                %>%)
                                                                                    </td>

                                                                                    <td>
                                                                                        <%= cvdItem.getDrGrade() %>
                                                                                    </td>

                                                                                    <td>
                                                                                        <span
                                                                                            class="status <%= cvdRiskClass %>">
                                                                                            <%= cvdItem.getRiskLevel()
                                                                                                %>
                                                                                        </span>
                                                                                    </td>

                                                                                    <td>
                                                                                        <a href="${pageContext.request.contextPath}/CVDServlet?action=view&id=<%= cvdItem.getScreeningId() %>"
                                                                                            style="color: #0f766e; font-weight: bold; text-decoration: none;">
                                                                                            View Report
                                                                                        </a>
                                                                                    </td>

                                                                                </tr>

                                                                                <% } } else { %>

                                                                                    <tr>

                                                                                        <td colspan="8">

                                                                                            <div class="empty">

                                                                                                No AI screenings
                                                                                                recorded yet. Click "Run
                                                                                                CVD Screening" below to
                                                                                                start.

                                                                                            </div>

                                                                                        </td>

                                                                                    </tr>

                                                                                    <% } %>

                                                                        </tbody>

                                                                    </table>

                                                                </div>

                                                            </div>


                                                            <!-- =================================================
                 QUICK ACTIONS
                 ================================================= -->

                                                            <div class="section">

                                                                <div class="section-header">

                                                                    <h3>
                                                                        Quick Actions
                                                                    </h3>

                                                                </div>


                                                                <div class="quick-actions">


                                                                    <a href="${pageContext.request.contextPath}/add-patient.jsp"
                                                                        class="action">

                                                                        <div class="action-icon">
                                                                            ♟
                                                                        </div>

                                                                        <strong>
                                                                            Add Patient
                                                                        </strong>

                                                                        <span>
                                                                            Register a new patient
                                                                        </span>

                                                                    </a>


                                                                    <a href="${pageContext.request.contextPath}/add-doctor.jsp"
                                                                        class="action">

                                                                        <div class="action-icon">
                                                                            ⚕
                                                                        </div>

                                                                        <strong>
                                                                            Add Doctor
                                                                        </strong>

                                                                        <span>
                                                                            Register a new doctor
                                                                        </span>

                                                                    </a>


                                                                    <a href="${pageContext.request.contextPath}/add-appointment.jsp"
                                                                        class="action">

                                                                        <div class="action-icon">
                                                                            ▣
                                                                        </div>

                                                                        <strong>
                                                                            New Appointment
                                                                        </strong>

                                                                        <span>
                                                                            Schedule an appointment
                                                                        </span>

                                                                    </a>


                                                                    <a href="${pageContext.request.contextPath}/add-bill.jsp"
                                                                        class="action">

                                                                        <div class="action-icon">
                                                                            ₹
                                                                        </div>

                                                                        <strong>
                                                                            Create Bill
                                                                        </strong>

                                                                        <span>
                                                                            Generate a patient bill
                                                                        </span>

                                                                    </a>


                                                                    <a href="${pageContext.request.contextPath}/CVDServlet?action=new"
                                                                        class="action"
                                                                        style="border: 1px solid #99f6e4;">

                                                                        <div class="action-icon"
                                                                            style="background: #f0fdfa; color: #0f766e;">
                                                                            ❤️
                                                                        </div>

                                                                        <strong style="color: #0f766e;">
                                                                            Run CVD AI Screening
                                                                        </strong>

                                                                        <span>
                                                                            Retinal deep learning analysis
                                                                        </span>

                                                                    </a>

                                                                </div>

                                                            </div>


                                                            <!-- FOOTER -->

                                                            <div class="footer">

                                                                © 2026 CareConnect Hospital Management System

                                                            </div>

                                                        </div>

                                                    </main>

                                                </div>

                                            </body>

                                            </html>
<%@ page pageEncoding="UTF-8" contentType="text/html; charset=UTF-8" %>
    <%@ page import="java.util.List" %>
        <%@ page import="com.hms.model.Doctor" %>
            <%@ page import="com.hms.model.User" %>
                <%@ page import="com.hms.util.HtmlUtil" %>
                    <%@ page import="com.hms.util.CSRFUtil" %>

                        <% User u=(session !=null) ? (User) session.getAttribute("user") : null; if (u==null) {
                            response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized" ); return;
                            } String csrfToken=CSRFUtil.getToken(session); %>

                            <!DOCTYPE html>
                            <html>

                            <head>

                                <meta charset="UTF-8">

                                <title>CareConnect | Doctors</title>

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
                                        max-width: 1250px;
                                        margin: 50px auto;
                                    }

                                    .header {
                                        display: flex;
                                        justify-content: space-between;
                                        align-items: center;
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

                                    .add-btn {
                                        background: #0b8f83;
                                        color: white;
                                        text-decoration: none;
                                        padding: 14px 22px;
                                        border-radius: 10px;
                                        font-weight: bold;
                                    }

                                    .add-btn:hover {
                                        background: #08766d;
                                    }

                                    .search-section {
                                        background: white;
                                        padding: 20px;
                                        border-radius: 14px;
                                        margin-bottom: 20px;
                                        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.05);
                                    }

                                    .search-form {
                                        display: flex;
                                        gap: 10px;
                                    }

                                    .search-form input {
                                        flex: 1;
                                        padding: 12px 15px;
                                        border: 1px solid #dce3ea;
                                        border-radius: 8px;
                                        font-size: 15px;
                                    }

                                    .search-form button {
                                        padding: 12px 22px;
                                        border: none;
                                        border-radius: 8px;
                                        background: #263b5a;
                                        color: white;
                                        cursor: pointer;
                                        font-weight: bold;
                                    }

                                    .search-form button:hover {
                                        background: #1c2d45;
                                    }

                                    .table-container {
                                        background: white;
                                        padding: 26px;
                                        border-radius: 18px;
                                        box-shadow: 0 5px 25px rgba(0, 0, 0, 0.06);
                                        overflow-x: auto;
                                    }

                                    table {
                                        width: 100%;
                                        border-collapse: collapse;
                                    }

                                    th {
                                        background: #f4f7f9;
                                        padding: 16px;
                                        text-align: left;
                                        color: #5e6d82;
                                        font-size: 14px;
                                    }

                                    td {
                                        padding: 17px 16px;
                                        border-bottom: 1px solid #edf1f4;
                                        color: #43546b;
                                    }

                                    tr:hover {
                                        background: #fafcfd;
                                    }

                                    .edit-btn {
                                        display: inline-block;
                                        padding: 8px 14px;
                                        background: #e6f5f3;
                                        color: #08766d;
                                        text-decoration: none;
                                        border-radius: 8px;
                                        font-weight: bold;
                                        font-size: 13px;
                                    }

                                    .edit-btn:hover {
                                        background: #d3efeb;
                                    }

                                    .delete-btn {
                                        display: inline-block;
                                        padding: 8px 14px;
                                        margin-left: 5px;
                                        background: #fdecec;
                                        color: #d64545;
                                        text-decoration: none;
                                        border-radius: 8px;
                                        font-weight: bold;
                                        font-size: 13px;
                                    }

                                    .delete-btn:hover {
                                        background: #f9dada;
                                    }

                                    .no-data {
                                        text-align: center;
                                        padding: 35px;
                                        color: #8a99ad;
                                    }

                                    .error-message {
                                        background: #fdecec;
                                        color: #c0392b;
                                        padding: 12px 16px;
                                        border-radius: 8px;
                                        margin-bottom: 20px;
                                    }
                                </style>

                            </head>

                            <body>

                                <div class="container">

                                    <!-- HEADER -->

                                    <div class="header">

                                        <div>

                                            <h1>Doctor Management</h1>

                                            <p>Manage and view registered doctors.</p>

                                        </div>

                                        <div style="display: flex; gap: 10px;">

                                            <a href="${pageContext.request.contextPath}/dashboard.jsp"
                                                style="display: inline-flex; align-items: center; background: #263b5a; color: white; text-decoration: none; padding: 14px 20px; border-radius: 10px; font-weight: bold;">
                                                ← Dashboard
                                            </a>

                                            <a href="${pageContext.request.contextPath}/CVDServlet?action=list"
                                                style="display: inline-flex; align-items: center; background: #0f766e; color: white; text-decoration: none; padding: 14px 20px; border-radius: 10px; font-weight: bold;">
                                                ❤️ CVD Diagnostics
                                            </a>

                                            <a href="${pageContext.request.contextPath}/add-doctor.jsp" class="add-btn">

                                                + Add Doctor

                                            </a>

                                        </div>

                                    </div>


                                    <!-- ERROR MESSAGE -->

                                    <% String error=request.getParameter("error"); if (error !=null) { %>

                                        <div class="error-message">

                                            <% if ("delete".equals(error)) { %>

                                                Unable to delete doctor.

                                                <% } else if ("invalid".equals(error)) { %>

                                                    Invalid doctor information.

                                                    <% } %>

                                        </div>

                                        <% } %>


                                            <!-- SEARCH -->

                                            <div class="search-section">

                                                <form action="${pageContext.request.contextPath}/DoctorServlet"
                                                    method="get" class="search-form">

                                                    <input type="hidden" name="action" value="search">

                                                    <input type="text" name="keyword"
                                                        placeholder="Search by name, specialization or phone..."
                                                        value="<%= request.getAttribute(" searchKeyword") !=null ?
                                                        request.getAttribute("searchKeyword") : "" %>">

                                                    <button type="submit">
                                                        Search
                                                    </button>

                                                    <a href="${pageContext.request.contextPath}/DoctorServlet?action=list"
                                                        style="display: inline-flex; align-items: center; padding: 12px 20px; background: #edf2f5; color: #43546b; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px;">
                                                        Clear
                                                    </a>

                                                </form>

                                            </div>


                                            <!-- DOCTOR TABLE -->

                                            <div class="table-container">

                                                <table>

                                                    <thead>

                                                        <tr>

                                                            <th>ID</th>

                                                            <th>Name</th>

                                                            <th>Specialization</th>

                                                            <th>Phone</th>

                                                            <th>Email</th>

                                                            <th>Experience</th>

                                                            <th>Consultation Fee</th>

                                                            <th>Actions</th>

                                                        </tr>

                                                    </thead>

                                                    <tbody>

                                                        <% List<Doctor> doctors =
                                                            (List<Doctor>) request.getAttribute("doctors");

                                                                if (doctors != null && !doctors.isEmpty()) {

                                                                for (Doctor doctor : doctors) {

                                                                %>

                                                                <tr>

                                                                    <td>
                                                                        <%= doctor.getId() %>
                                                                    </td>

                                                                    <td>
                                                                        <%= doctor.getName() %>
                                                                    </td>

                                                                    <td>
                                                                        <%= doctor.getSpecialization() %>
                                                                    </td>

                                                                    <td>
                                                                        <%= doctor.getPhone() %>
                                                                    </td>

                                                                    <td>
                                                                        <%= doctor.getEmail() %>
                                                                    </td>

                                                                    <td>
                                                                        <%= doctor.getExperience() %> years
                                                                    </td>

                                                                    <td>
                                                                        ₹<%= String.format( "%.2f" ,
                                                                            doctor.getConsultationFee() ) %>
                                                                    </td>

                                                                    <td>

                                                                        <a href="${pageContext.request.contextPath}/DoctorServlet?action=edit&id=<%= doctor.getId() %>"
                                                                            class="edit-btn">

                                                                            Edit

                                                                        </a>

                                                                        <form
                                                                            action="${pageContext.request.contextPath}/DoctorServlet"
                                                                            method="post" style="display:inline;"
                                                                            onsubmit="return confirm('Are you sure you want to delete this doctor?');">
                                                                            <input type="hidden" name="action"
                                                                                value="delete">
                                                                            <input type="hidden" name="id"
                                                                                value="<%= doctor.getId() %>">
                                                                            <input type="hidden" name="csrf_token"
                                                                                value="<%= HtmlUtil.escapeHtml(csrfToken) %>">
                                                                            <button type="submit" class="delete-btn"
                                                                                style="background:none;border:none;cursor:pointer;font:inherit;">Delete</button>
                                                                        </form>

                                                                    </td>

                                                                </tr>

                                                                <% } } else { %>

                                                                    <tr>

                                                                        <td colspan="8" class="no-data">

                                                                            No doctors found.

                                                                        </td>

                                                                    </tr>

                                                                    <% } %>

                                                    </tbody>

                                                </table>

                                            </div>

                                </div>

                            </body>

                            </html>
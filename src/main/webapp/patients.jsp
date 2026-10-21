<%@ page language="java"
    contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Patient" %>
<%@ page import="com.hms.model.User" %>
<%@ page import="com.hms.util.HtmlUtil" %>
<%@ page import="com.hms.util.CSRFUtil" %>

<%
    User u = (session != null) ? (User) session.getAttribute("user") : null;
    if (u == null) {
        response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized");
        return;
    }
    String csrfToken = CSRFUtil.getToken(session);
%>

<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>CareConnect | Patients</title>

    <link rel="stylesheet"
          href="${pageContext.request.contextPath}/css/style.css">

    <style>

        body {
            background: #f5f8fa;
            color: #172b4d;
            font-family: "Segoe UI", Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }

        .container {
            max-width: 1250px;
            margin: auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }

        .header h1 {
            font-size: 30px;
            color: #13233b;
            margin-bottom: 5px;
            margin-top: 0;
        }

        .header p {
            color: #8290a3;
            font-size: 14px;
            margin: 0;
        }

        .header-actions {
            display: flex;
            gap: 10px;
        }

        .back-btn {
            display: inline-block;
            background: #263b5a;
            color: white;
            padding: 12px 18px;
            border-radius: 9px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
        }

        .back-btn:hover {
            background: #1c2d45;
        }

        .add-btn {
            display: inline-block;
            background: #087f75;
            color: white;
            padding: 12px 20px;
            border-radius: 9px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
        }

        .add-btn:hover {
            background: #056b63;
        }

        .search-section {
            background: white;
            padding: 20px;
            border-radius: 14px;
            margin-bottom: 22px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }

        .search-form {
            display: flex;
            gap: 12px;
        }

        .search-form input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #dce3ea;
            border-radius: 9px;
            font-size: 15px;
            outline: none;
        }

        .search-form input:focus {
            border-color: #087f75;
        }

        .search-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 9px;
            background: #263b5a;
            color: white;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
        }

        .search-btn:hover {
            background: #1c2d45;
        }

        .clear-btn {
            display: inline-flex;
            align-items: center;
            padding: 12px 20px;
            background: #edf2f5;
            color: #43546b;
            text-decoration: none;
            border-radius: 9px;
            font-weight: 600;
            font-size: 14px;
        }

        .card {
            background: white;
            border: 1px solid #e8edf1;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 30px rgba(25, 50, 75, 0.06);
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            background: #f5f8fa;
            color: #536273;
            font-size: 13px;
            font-weight: 600;
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid #e8edf1;
        }

        td {
            padding: 14px;
            font-size: 14px;
            border-bottom: 1px solid #eef2f4;
        }

        tr:hover {
            background: #fafcfc;
        }

        .id {
            font-weight: 600;
            color: #087f75;
        }

        .actions {
            display: flex;
            gap: 8px;
        }

        .edit-btn {
            display: inline-block;
            background: #e8f6f4;
            color: #087f75;
            padding: 7px 12px;
            border-radius: 7px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
        }

        .edit-btn:hover {
            background: #d5eeeb;
        }

        .delete-btn {
            display: inline-block;
            background: #fdecec;
            color: #d64545;
            padding: 7px 12px;
            border-radius: 7px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 600;
        }

        .delete-btn:hover {
            background: #f9dada;
        }

        .empty {
            text-align: center;
            color: #8290a3;
            padding: 40px;
        }

        .error-message {
            background: #fdecec;
            color: #c0392b;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }

        @media (max-width: 700px) {
            body {
                padding: 15px;
            }
            .header {
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }
            .search-form {
                flex-direction: column;
            }
        }

    </style>

</head>

<body>

<div class="container">

    <!-- HEADER -->

    <div class="header">

        <div>

            <h1>Patient Management</h1>

            <p>
                Manage and view registered hospital patients.
            </p>

        </div>

        <div class="header-actions">

            <a href="${pageContext.request.contextPath}/dashboard.jsp"
               class="back-btn">
                ← Dashboard
            </a>

            <a href="${pageContext.request.contextPath}/CVDServlet?action=list"
               style="display: inline-flex; align-items: center; gap: 6px; padding: 12px 18px; background: #0f766e; color: white; text-decoration: none; border-radius: 9px; font-weight: 600; font-size: 14px;">
                ❤️ CVD Diagnostics
            </a>

            <a href="${pageContext.request.contextPath}/add-patient.jsp"
               class="add-btn">
                + Add Patient
            </a>

        </div>

    </div>

    <!-- ERROR MESSAGE -->

    <%
        String error = request.getParameter("error");
        if (error != null) {
    %>
        <div class="error-message">
            <% if ("delete".equals(error)) { %>
                Unable to delete patient. Please try again.
            <% } else if ("invalid".equals(error)) { %>
                Invalid patient details provided.
            <% } %>
        </div>
    <%
        }
    %>

    <!-- SEARCH -->

    <div class="search-section">

        <form action="${pageContext.request.contextPath}/PatientServlet"
              method="get"
              class="search-form">

            <input type="hidden"
                   name="action"
                   value="search">

            <input type="text"
                   name="keyword"
                   placeholder="Search by name or phone number..."
                   value="<%= request.getAttribute("searchKeyword") != null
                           ? request.getAttribute("searchKeyword")
                           : "" %>">

            <button type="submit" class="search-btn">
                Search
            </button>

            <a href="${pageContext.request.contextPath}/PatientServlet?action=list"
               class="clear-btn">
                Clear
            </a>

        </form>

    </div>


    <!-- PATIENT TABLE -->

    <div class="card">

        <table>

            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Age</th>
                    <th>Gender</th>
                    <th>Phone</th>
                    <th>Address</th>
                    <th>Actions</th>
                </tr>
            </thead>

            <tbody>
            <%
                List<Patient> patients =
                    (List<Patient>) request.getAttribute("patients");

                if (patients != null && !patients.isEmpty()) {

                    for (Patient patient : patients) {
            %>

                <tr>

                    <td class="id">
                        #<%= patient.getId() %>
                    </td>

                    <td>
                        <strong><%= patient.getName() %></strong>
                    </td>

                    <td>
                        <%= patient.getAge() %> yrs
                    </td>

                    <td>
                        <%= patient.getGender() %>
                    </td>

                    <td>
                        <%= patient.getPhone() != null ? patient.getPhone() : "-" %>
                    </td>

                    <td>
                        <%= patient.getAddress() != null ? patient.getAddress() : "-" %>
                    </td>

                    <td>

                        <div class="actions">

                            <a href="${pageContext.request.contextPath}/CVDServlet?action=new&patientId=<%= patient.getId() %>"
                               style="display: inline-block; background: #e6fffa; color: #0f766e; padding: 7px 11px; border-radius: 7px; text-decoration: none; font-size: 12px; font-weight: 600;">
                                🔬 Retinal AI Screen
                            </a>

                            <a href="${pageContext.request.contextPath}/PatientServlet?action=edit&id=<%= patient.getId() %>"
                               class="edit-btn">
                                Edit
                            </a>

                            <form action="/PatientServlet" method="post" style="display:inline;" onsubmit="return confirm('Are you sure you want to delete this patient? Associated appointments and bills will also be removed.');">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="<%= patient.getId() %>">
                                <input type="hidden" name="csrf_token" value="<%= HtmlUtil.escapeHtml(csrfToken) %>">
                                <button type="submit" class="delete-btn" style="background:none;border:none;cursor:pointer;font:inherit;">Delete</button>
                            </form>

                        </div>

                    </td>

                </tr>

            <%
                    }

                } else {
            %>

                <tr>

                    <td colspan="7" class="empty">
                        <h3>No patients found</h3>
                        <p>No matching patient records. Add a patient to get started.</p>
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
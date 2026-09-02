<%@ page language="java"
    contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Patient" %>

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
            padding: 40px;
        }

        .container {
            max-width: 1200px;
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
        }

        .header p {
            color: #8290a3;
            font-size: 14px;
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

        .empty {
            text-align: center;
            color: #8290a3;
            padding: 30px;
        }

        @media (max-width: 700px) {

            body {
                padding: 20px;
            }

            .header {
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
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
                Manage and view registered patients.
            </p>

        </div>

        <a href="${pageContext.request.contextPath}/add-patient.jsp"
           class="add-btn">
            + Add Patient
        </a>

    </div>


    <!-- PATIENT TABLE -->

    <div class="card">

        <table>

            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Phone</th>
                <th>Address</th>
                <th>Actions</th>
            </tr>


            <%

                List<Patient> patients =
                    (List<Patient>) request.getAttribute("patients");

                if (patients != null && !patients.isEmpty()) {

                    for (Patient patient : patients) {

            %>

            <tr>

                <td class="id">
                    <%= patient.getId() %>
                </td>

                <td>
                    <%= patient.getName() %>
                </td>

                <td>
                    <%= patient.getAge() %>
                </td>

                <td>
                    <%= patient.getGender() %>
                </td>

                <td>
                    <%= patient.getPhone() %>
                </td>

                <td>
                    <%= patient.getAddress() %>
                </td>

                <td>

                    <div class="actions">

                        <a href="${pageContext.request.contextPath}/PatientServlet?action=edit&id=<%= patient.getId() %>"
                           class="edit-btn">
                            Edit
                        </a>

                    </div>

                </td>

            </tr>

            <%

                    }

                } else {

            %>

            <tr>

                <td colspan="7" class="empty">
                    No patients found.
                </td>

            </tr>

            <%

                }

            %>

        </table>

    </div>

</div>

</body>

</html>
<%@ page language="java"
    contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List"%>
<%@ page import="com.hms.model.Patient"%>

<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>CareConnect | Patients</title>

    <link rel="stylesheet"
          href="${pageContext.request.contextPath}/css/style.css">

</head>

<body>

    <h1>Patient Management</h1>

    <a href="${pageContext.request.contextPath}/add-patient.jsp">
        + Add Patient
    </a>

    <br><br>

    <table border="1" cellpadding="10">

        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Age</th>
            <th>Gender</th>
            <th>Phone</th>
            <th>Address</th>
        </tr>

        <%
            List<Patient> patients =
                (List<Patient>) request.getAttribute("patients");

            if (patients != null && !patients.isEmpty()) {

                for (Patient patient : patients) {
        %>

        <tr>

            <td>
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

        </tr>

        <%
                }

            } else {
        %>

        <tr>
            <td colspan="6">
                No patients found.
            </td>
        </tr>

        <%
            }
        %>

    </table>

</body>

</html>
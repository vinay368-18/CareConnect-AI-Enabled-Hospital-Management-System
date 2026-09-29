<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Patient" %>
<%@ page import="com.hms.model.Appointment" %>
<%@ page import="com.hms.dao.PatientDAO" %>
<%@ page import="com.hms.dao.AppointmentDAO" %>

<%
    PatientDAO patientDAO = new PatientDAO();
    AppointmentDAO appointmentDAO = new AppointmentDAO();

    List<Patient> patients = patientDAO.getAllPatients();
    List<Appointment> appointments = appointmentDAO.getAllAppointments();

    String error = request.getParameter("error");
%>

<!DOCTYPE html>
<html>
<head>

    <meta charset="UTF-8">

    <title>Add Bill</title>

    <style>

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }

        body {
            background: #f4f7fb;
            padding: 30px;
        }

        .container {
            max-width: 700px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }

        h1 {
            color: #1e3a8a;
            margin-bottom: 25px;
        }

        .form-group {
            margin-bottom: 18px;
        }

        label {
            display: block;
            margin-bottom: 7px;
            font-weight: bold;
            color: #374151;
        }

        input,
        select {
            width: 100%;
            padding: 11px;
            border: 1px solid #d1d5db;
            border-radius: 7px;
            font-size: 14px;
        }

        input:focus,
        select:focus {
            outline: none;
            border-color: #2563eb;
        }

        .required {
            color: #dc2626;
        }

        .optional {
            color: #6b7280;
            font-size: 12px;
            font-weight: normal;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 7px;
            margin-bottom: 20px;
        }

        .buttons {
            display: flex;
            gap: 10px;
            margin-top: 25px;
        }

        .submit-btn {
            border: none;
            background: #2563eb;
            color: white;
            padding: 12px 20px;
            border-radius: 7px;
            cursor: pointer;
            font-weight: bold;
        }

        .submit-btn:hover {
            background: #1d4ed8;
        }

        .cancel-btn {
            text-decoration: none;
            background: #e5e7eb;
            color: #374151;
            padding: 12px 20px;
            border-radius: 7px;
        }

        .cancel-btn:hover {
            background: #d1d5db;
        }

    </style>

</head>

<body>

<div class="container">

    <h1>Add New Bill</h1>


    <% if ("invalid".equals(error)) { %>

        <div class="error">
            Please enter valid bill information.
        </div>

    <% } else if ("failed".equals(error)) { %>

        <div class="error">
            Failed to add bill. Please try again.
        </div>

    <% } %>


    <form action="${pageContext.request.contextPath}/BillingServlet"
          method="post">

        <input type="hidden"
               name="action"
               value="add">


        <!-- Patient -->

        <div class="form-group">

            <label>
                Patient <span class="required">*</span>
            </label>

            <select name="patientId" required>

                <option value="">
                    -- Select Patient --
                </option>

                <% for (Patient patient : patients) { %>

                    <option value="<%= patient.getId() %>">

                        <%= patient.getName() %>
                        (ID: <%= patient.getId() %>)

                    </option>

                <% } %>

            </select>

        </div>


        <!-- Appointment -->

        <div class="form-group">

            <label>
                Appointment
                <span class="optional">(Optional)</span>
            </label>

            <select name="appointmentId">

                <option value="">
                    -- No Appointment --
                </option>

                <% for (Appointment appointment : appointments) { %>

                    <option value="<%= appointment.getId() %>" data-patient-id="<%= appointment.getPatientId() %>">

                        Appointment #<%= appointment.getId() %>
                        -
                        <%= appointment.getPatientName() %>
                        -
                        <%= appointment.getAppointmentDate() %>
                        -
                        <%= appointment.getAppointmentTime() %>

                    </option>

                <% } %>

            </select>

        </div>


        <!-- Amount -->

        <div class="form-group">

            <label>
                Amount (₹) <span class="required">*</span>
            </label>

            <input type="number"
                   name="amount"
                   step="0.01"
                   min="0"
                   placeholder="Enter amount"
                   required>

        </div>


        <!-- Payment Method -->

        <div class="form-group">

            <label>
                Payment Method
            </label>

            <select name="paymentMethod">

                <option value="">
                    -- Select Payment Method --
                </option>

                <option value="Cash">
                    Cash
                </option>

                <option value="UPI">
                    UPI
                </option>

                <option value="Card">
                    Card
                </option>

                <option value="Net Banking">
                    Net Banking
                </option>

            </select>

        </div>


        <!-- Payment Status -->

        <div class="form-group">

            <label>
                Payment Status
            </label>

            <select name="paymentStatus">

                <option value="Pending">
                    Pending
                </option>

                <option value="Paid">
                    Paid
                </option>

                <option value="Cancelled">
                    Cancelled
                </option>

            </select>

        </div>


        <!-- Bill Date -->

        <div class="form-group">

            <label>
                Bill Date <span class="required">*</span>
            </label>

            <input type="date"
                   id="billDateInput"
                   name="billDate"
                   required>

        </div>


        <!-- Buttons -->

        <div class="buttons">

            <button type="submit"
                    class="submit-btn">
                Add Bill
            </button>

            <a href="${pageContext.request.contextPath}/BillingServlet?action=list"
               class="cancel-btn">
                Cancel
            </a>

        </div>

    </form>

</div>

<script>
document.addEventListener("DOMContentLoaded", function() {
    const apptSelect = document.querySelector('select[name="appointmentId"]');
    const patientSelect = document.querySelector('select[name="patientId"]');
    if (apptSelect && patientSelect) {
        apptSelect.addEventListener("change", function() {
            const selectedOpt = this.options[this.selectedIndex];
            const patientId = selectedOpt.getAttribute("data-patient-id");
            if (patientId) {
                patientSelect.value = patientId;
            }
        });
    }

    const billDateInput = document.getElementById("billDateInput");
    if (billDateInput && !billDateInput.value) {
        billDateInput.value = new Date().toISOString().split('T')[0];
    }
});
</script>

</body>
</html>
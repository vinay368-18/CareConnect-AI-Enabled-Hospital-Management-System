<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<%@ page import="java.util.List" %>
<%@ page import="com.hms.model.Bill" %>

<!DOCTYPE html>
<html>
<head>

    <meta charset="UTF-8">

    <title>Billing Management</title>

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
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }

        .header h1 {
            color: #1e3a8a;
        }

        .add-btn {
            text-decoration: none;
            background: #2563eb;
            color: white;
            padding: 11px 18px;
            border-radius: 7px;
            font-weight: bold;
        }

        .add-btn:hover {
            background: #1d4ed8;
        }

        .search-section {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
        }

        .search-section input {
            flex: 1;
            padding: 11px;
            border: 1px solid #ccc;
            border-radius: 7px;
            font-size: 14px;
        }

        .search-btn {
            border: none;
            background: #374151;
            color: white;
            padding: 11px 20px;
            border-radius: 7px;
            cursor: pointer;
        }

        .search-btn:hover {
            background: #111827;
        }

        .clear-btn {
            text-decoration: none;
            background: #e5e7eb;
            color: #333;
            padding: 11px 18px;
            border-radius: 7px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
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
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }

        .paid {
            background: #dcfce7;
            color: #166534;
        }

        .pending {
            background: #fef3c7;
            color: #92400e;
        }

        .cancelled {
            background: #fee2e2;
            color: #991b1b;
        }

        .edit-btn {
            text-decoration: none;
            background: #f59e0b;
            color: white;
            padding: 6px 10px;
            border-radius: 5px;
            margin-right: 5px;
            font-size: 13px;
        }

        .delete-btn {
            text-decoration: none;
            background: #dc2626;
            color: white;
            padding: 6px 10px;
            border-radius: 5px;
            font-size: 13px;
        }

        .edit-btn:hover {
            background: #d97706;
        }

        .delete-btn:hover {
            background: #b91c1c;
        }

        .empty {
            text-align: center;
            padding: 40px;
            color: #777;
        }

        .amount {
            font-weight: bold;
            color: #166534;
        }

    </style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>Billing Management</h1>

        <div style="display: flex; gap: 10px;">
            <a href="${pageContext.request.contextPath}/dashboard.jsp"
               style="display: inline-flex; align-items: center; background: #374151; color: white; text-decoration: none; padding: 11px 18px; border-radius: 7px; font-weight: bold;">
                ← Dashboard
            </a>
            <a href="${pageContext.request.contextPath}/CVDServlet?action=list"
               style="display: inline-flex; align-items: center; background: #0f766e; color: white; text-decoration: none; padding: 11px 18px; border-radius: 7px; font-weight: bold;">
                ❤️ CVD Diagnostics
            </a>
            <a href="${pageContext.request.contextPath}/add-bill.jsp"
               class="add-btn">
                + Add Bill
            </a>
        </div>

    </div>

    <%
        String error = request.getParameter("error");
        if (error != null) {
    %>
        <div style="background: #fee2e2; color: #991b1b; padding: 12px 16px; border-radius: 7px; margin-bottom: 20px;">
            <% if ("delete".equals(error)) { %>
                Unable to delete bill. Please try again.
            <% } else if ("invalid".equals(error)) { %>
                Invalid billing information provided.
            <% } %>
        </div>
    <%
        }
    %>


    <!-- Search -->

    <form action="${pageContext.request.contextPath}/BillingServlet"
          method="get"
          class="search-section">

        <input type="hidden"
               name="action"
               value="search">

        <input type="text"
               name="keyword"
               placeholder="Search by patient, payment method or status..."
               value="<%= request.getAttribute("searchKeyword") != null
                       ? request.getAttribute("searchKeyword")
                       : "" %>">

        <button type="submit" class="search-btn">
            Search
        </button>

        <a href="${pageContext.request.contextPath}/BillingServlet?action=list"
           class="clear-btn">
            Clear
        </a>

    </form>


    <!-- Bills Table -->

    <%
        List<Bill> bills =
            (List<Bill>) request.getAttribute("bills");
    %>


    <% if (bills == null || bills.isEmpty()) { %>

        <div class="empty">
            <h3>No bills found</h3>
            <p>Add a bill to get started.</p>
        </div>

    <% } else { %>

        <table>

            <thead>

                <tr>
                    <th>Bill ID</th>
                    <th>Patient</th>
                    <th>Appointment ID</th>
                    <th>Amount</th>
                    <th>Payment Method</th>
                    <th>Status</th>
                    <th>Bill Date</th>
                    <th>Actions</th>
                </tr>

            </thead>

            <tbody>

            <% for (Bill bill : bills) { %>

                <tr>

                    <td>
                        <%= bill.getId() %>
                    </td>

                    <td>
                        <%= bill.getPatientName() %>
                    </td>

                    <td>

                        <%
                            if (bill.getAppointmentId() > 0) {
                        %>

                            <%= bill.getAppointmentId() %>

                        <%
                            } else {
                        %>

                            N/A

                        <%
                            }
                        %>

                    </td>

                    <td class="amount">

                        ₹<%= String.format("%.2f", bill.getAmount()) %>

                    </td>

                    <td>
                        <%= bill.getPaymentMethod() != null
                                ? bill.getPaymentMethod()
                                : "N/A" %>
                    </td>

                    <td>

                        <%
                            String status = bill.getPaymentStatus();

                            String statusClass = "pending";

                            if ("Paid".equalsIgnoreCase(status)) {
                                statusClass = "paid";
                            } else if ("Cancelled".equalsIgnoreCase(status)) {
                                statusClass = "cancelled";
                            }
                        %>

                        <span class="status <%= statusClass %>">

                            <%= status != null ? status : "Pending" %>

                        </span>

                    </td>

                    <td>
                        <%= bill.getBillDate() %>
                    </td>

                    <td>

                        <a class="edit-btn"
                           href="${pageContext.request.contextPath}/BillingServlet?action=edit&id=<%= bill.getId() %>">
                            Edit
                        </a>

                        <a class="delete-btn"
                           href="${pageContext.request.contextPath}/BillingServlet?action=delete&id=<%= bill.getId() %>"
                           onclick="return confirm('Are you sure you want to delete this bill?');">
                            Delete
                        </a>

                    </td>

                </tr>

            <% } %>

            </tbody>

        </table>

    <% } %>

</div>

</body>
</html>
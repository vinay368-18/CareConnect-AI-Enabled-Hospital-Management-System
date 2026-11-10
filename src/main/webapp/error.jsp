<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8" isErrorPage="true"%>
<%
    // Mapped in web.xml for 403, 404 and 500. Shows a plain explanation and a
    // way back; never prints exception details or stack traces to the browser.
    Object codeAttr = request.getAttribute("jakarta.servlet.error.status_code");
    int code = (codeAttr instanceof Integer) ? (Integer) codeAttr : 500;

    String title;
    String message;
    if (code == 404) {
        title = "Page not found";
        message = "The page you asked for does not exist or has moved.";
    } else if (code == 403) {
        title = "Access denied";
        message = "Your account does not have permission to open this page.";
    } else {
        title = "Something went wrong";
        message = "The server could not complete this request. Please try again. "
                + "If it keeps happening, an administrator can find the cause in the server log.";
    }

    boolean loggedIn = (session != null && session.getAttribute("user") != null);
    String ctx = request.getContextPath();
    String backHref = loggedIn ? ctx + "/dashboard.jsp" : ctx + "/login.jsp";
    String backLabel = loggedIn ? "Back to dashboard" : "Go to sign in";
%>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><%= title %> - CareConnect</title>
    <style>
        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f1f5f9;
            font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
            color: #0f172a;
        }
        .card {
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
            padding: 40px 44px;
            max-width: 460px;
            width: calc(100% - 32px);
            text-align: center;
        }
        .code {
            font-size: 56px;
            font-weight: 800;
            color: #0f766e;
            margin: 0 0 8px;
        }
        h1 {
            font-size: 22px;
            margin: 0 0 12px;
        }
        p {
            color: #475569;
            line-height: 1.6;
            margin: 0 0 28px;
            font-size: 15px;
        }
        a.btn {
            display: inline-block;
            background: #0f766e;
            color: #ffffff;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
        }
        a.btn:hover {
            background: #115e59;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="code"><%= code %></div>
        <h1><%= title %></h1>
        <p><%= message %></p>
        <a class="btn" href="<%= backHref %>"><%= backLabel %></a>
    </div>
</body>
</html>

<%@ page language="java" contentType="text/html; charset=UTF-8"
    pageEncoding="UTF-8"%>

<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>CareConnect | Login</title>

    <link rel="stylesheet"
          href="${pageContext.request.contextPath}/css/style.css">

    <style>

        .register-link {
            text-align: center;
            margin-top: 18px;
            font-size: 14px;
            color: #666;
        }

        .register-link a {
            color: #2563eb;
            text-decoration: none;
            font-weight: 600;
        }

        .register-link a:hover {
            text-decoration: underline;
        }

    </style>

</head>

<body>

<div class="login-page">

    <!-- =====================================================
         LEFT SIDE
         ===================================================== -->

    <section class="login-info">

        <!-- BRAND -->

        <div class="brand">

            <span class="brand-icon">+</span>

            <span>
                Care<span>Connect</span>
            </span>

        </div>


        <!-- WELCOME CONTENT -->

        <div class="welcome-content">

            <p class="tagline">
                HOSPITAL MANAGEMENT SYSTEM
            </p>


            <h1>

                Smarter care.<br>

                Better <span>healthcare.</span>

            </h1>


            <p class="description">

                Manage patients, doctors, appointments,
                billing and hospital operations from one
                simple and secure platform.

            </p>


            <!-- FEATURES -->

            <div class="features">


                <!-- FEATURE 1 -->

                <div class="feature">

                    <span class="feature-icon">
                        ✓
                    </span>

                    <div>

                        <strong>
                            Complete Patient Management
                        </strong>

                        <p>
                            Maintain accurate patient records
                            and medical information.
                        </p>

                    </div>

                </div>


                <!-- FEATURE 2 -->

                <div class="feature">

                    <span class="feature-icon">
                        ⚕
                    </span>

                    <div>

                        <strong>
                            Doctor &amp; Appointment Management
                        </strong>

                        <p>
                            Organize doctors and appointments
                            efficiently.
                        </p>

                    </div>

                </div>


                <!-- FEATURE 3 -->

                <div class="feature">

                    <span class="feature-icon">
                        ₹
                    </span>

                    <div>

                        <strong>
                            Simple Billing
                        </strong>

                        <p>
                            Manage invoices and payments
                            in one place.
                        </p>

                    </div>

                </div>


            </div>

        </div>


        <!-- COPYRIGHT -->

        <small class="copyright">

            © 2026 CareConnect. All rights reserved.

        </small>

    </section>


    <!-- =====================================================
         RIGHT SIDE
         ===================================================== -->

    <section class="login-section">

        <div class="login-card">


            <!-- MOBILE BRAND -->

            <div class="mobile-brand">

                <span class="brand-icon">
                    +
                </span>

                CareConnect

            </div>


            <!-- LOGIN HEADER -->

            <div class="login-header">

                <h2>
                    Welcome back
                </h2>

                <p>
                    Sign in to access your hospital
                    management dashboard.
                </p>

            </div>


            <!-- =================================================
                 MESSAGES
                 ================================================= -->

            <%

                String error = request.getParameter("error");

                String msg = request.getParameter("msg");

                String registered =
                    request.getParameter("registered");


                if ("invalid".equals(error)) {

            %>

                <div style="
                    background:#fde8e8;
                    color:#9b1c1c;
                    border-left:4px solid #f05252;
                    padding:12px 16px;
                    border-radius:8px;
                    margin-bottom:20px;
                    font-size:14px;
                ">

                    Invalid username or password.
                    Please try again.

                </div>

            <%

                } else if ("logged_out".equals(msg)) {

            %>

                <div style="
                    background:#def7ec;
                    color:#03543f;
                    border-left:4px solid #31c48d;
                    padding:12px 16px;
                    border-radius:8px;
                    margin-bottom:20px;
                    font-size:14px;
                ">

                    You have been logged out successfully.

                </div>

            <%

                } else if ("true".equals(registered)) {

            %>

                <div style="
                    background:#def7ec;
                    color:#03543f;
                    border-left:4px solid #31c48d;
                    padding:12px 16px;
                    border-radius:8px;
                    margin-bottom:20px;
                    font-size:14px;
                ">

                    Account created successfully.
                    Please sign in.

                </div>

            <%

                }

            %>


            <!-- =================================================
                 LOGIN FORM
                 ================================================= -->

            <form
                action="${pageContext.request.contextPath}/LoginServlet"
                method="post">


                <!-- USERNAME -->

                <div class="form-group">

                    <label for="username">
                        Username
                    </label>

                    <input
                        id="username"
                        name="username"
                        type="text"
                        placeholder="Enter your username"
                        autocomplete="username"
                        required>

                </div>


                <!-- PASSWORD -->

                <div class="form-group">

                    <div class="label-row">

                        <label for="password">
                            Password
                        </label>

                        <a
                            href="${pageContext.request.contextPath}/forgot-password.jsp">

                            Forgot password?

                        </a>

                    </div>


                    <input
                        id="password"
                        name="password"
                        type="password"
                        placeholder="Enter your password"
                        autocomplete="current-password"
                        required>

                </div>


                <!-- REMEMBER ME -->

                <div class="remember">

                    <label>

                        <input
                            name="remember"
                            type="checkbox"
                            value="true">

                        Remember me

                    </label>

                </div>


                <!-- LOGIN BUTTON -->

                <button
                    class="login-button"
                    type="submit">

                    Sign in

                    <span>
                        →
                    </span>

                </button>


                <!-- CREATE ACCOUNT -->

                <div class="register-link">

                    Don't have an account?

                    <a href="${pageContext.request.contextPath}/RegisterServlet">
                        Create Account
                    </a>

                </div>


            </form>


            <!-- =================================================
                 SECURITY NOTE
                 ================================================= -->

            <div class="security-note">

                <span>
                    🔒
                </span>

                <div>

                    <strong>
                        Secure Login
                    </strong>

                    <p>
                        Your hospital data is protected
                        with secure authentication.
                    </p>

                </div>

            </div>


        </div>

    </section>


</div>

</body>

</html>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>HMS | Login</title>

    <link rel="stylesheet"
          href="${pageContext.request.contextPath}/css/style.css">
</head>

<body>

    <div class="login-page">

        <!-- Left Section -->
        <div class="login-info">

            <div class="brand">
                <div class="brand-icon">+</div>
                <span>Care<span>Connect</span></span>
            </div>

            <div class="welcome-content">

                <p class="tagline">SMART HEALTHCARE MANAGEMENT</p>

                <h1>
                    Healthcare made
                    <span>simpler.</span>
                </h1>

                <p class="description">
                    Manage patients, doctors, appointments and billing
                    from one secure and intelligent platform.
                </p>

                <div class="features">

                    <div class="feature">
                        <div class="feature-icon">✓</div>
                        <div>
                            <strong>Patient Management</strong>
                            <p>Manage patient records efficiently.</p>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">✓</div>
                        <div>
                            <strong>Smart Appointments</strong>
                            <p>Schedule and manage appointments easily.</p>
                        </div>
                    </div>

                    <div class="feature">
                        <div class="feature-icon">✓</div>
                        <div>
                            <strong>Secure & Reliable</strong>
                            <p>Keep healthcare information protected.</p>
                        </div>
                    </div>

                </div>

            </div>

            <p class="copyright">
                © 2026 CareConnect Hospital Management System
            </p>

        </div>


        <!-- Right Section -->
        <div class="login-section">

            <div class="login-card">

                <div class="mobile-brand">
                    <div class="brand-icon">+</div>
                    <span>Care<span>Connect</span></span>
                </div>

                <div class="login-header">

                    <h2>Welcome back</h2>

                    <p>
                        Sign in to access your hospital dashboard
                    </p>

                </div>


                <form action="LoginServlet" method="post">

                    <div class="form-group">

                        <label for="username">
                            Username
                        </label>

                        <input
                            type="text"
                            id="username"
                            name="username"
                            placeholder="Enter your username"
                            autocomplete="username"
                            required>

                    </div>


                    <div class="form-group">

                        <div class="label-row">

                            <label for="password">
                                Password
                            </label>

                            <a href="#">
                                Forgot password?
                            </a>

                        </div>

                        <input
                            type="password"
                            id="password"
                            name="password"
                            placeholder="Enter your password"
                            autocomplete="current-password"
                            required>

                    </div>


                    <div class="remember">

                        <label>
                            <input type="checkbox" name="remember">
                            <span>Remember me</span>
                        </label>

                    </div>


                    <button type="submit" class="login-button">

                        <span>Sign In</span>

                        <span class="arrow">→</span>

                    </button>

                </form>


                <div class="security-note">

                    <span>Secure</span>

                    <p>
                        Your information is protected with
                        secure authentication.
                    </p>

                </div>

            </div>

        </div>

    </div>

</body>
</html>
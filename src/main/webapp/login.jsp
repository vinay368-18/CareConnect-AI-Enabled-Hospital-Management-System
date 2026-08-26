<%@ page language="java" contentType="text/html; charset=UTF-8"
	pageEncoding="UTF-8"%>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CareConnect | Login</title>
<link rel="stylesheet"
	href="${pageContext.request.contextPath}/style.css">
</head>
<body>
	<div class="login-page">
		<section class="login-info">
			<div class="brand">
				<span class="brand-icon">+</span><span>Care<span>Connect</span></span>
			</div>

			<div class="welcome-content">
				<p class="tagline">HOSPITAL MANAGEMENT SYSTEM</p>
				<h1>
					Smarter care.<br>Better <span>healthcare.</span>
				</h1>
				<p class="description">Manage patients, doctors, appointments,
					billing and hospital operations from one simple and secure
					platform.</p>

				<div class="features">
					<div class="feature">
						<span class="feature-icon">✓</span>
						<div>
							<strong>Complete Patient Management</strong>
							<p>Maintain accurate patient records and medical information.</p>
						</div>
					</div>
					<div class="feature">
						<span class="feature-icon">⚕</span>
						<div>
							<strong>Doctor &amp; Appointment Management</strong>
							<p>Organize doctors and appointments efficiently.</p>
						</div>
					</div>
					<div class="feature">
						<span class="feature-icon">₹</span>
						<div>
							<strong>Simple Billing</strong>
							<p>Manage invoices and payments in one place.</p>
						</div>
					</div>
				</div>
			</div>

			<small class="copyright">© 2026 CareConnect. All rights
				reserved.</small>
		</section>

		<section class="login-section">
			<div class="login-card">
				<div class="mobile-brand">
					<span class="brand-icon">+</span>CareConnect
				</div>
				<div class="login-header">
					<h2>Welcome back</h2>
					<p>Sign in to access your hospital management dashboard.</p>
				</div>

				<form action="${pageContext.request.contextPath}/login"
					method="post">
					<div class="form-group">
						<label for="username">Username</label> <input id="username"
							name="username" type="text" placeholder="Enter your username"
							autocomplete="username" required>
					</div>

					<div class="form-group">
						<div class="label-row">
							<label for="password">Password</label> <a
								href="${pageContext.request.contextPath}/forgot-password.jsp">Forgot
								password?</a>
						</div>
						<input id="password" name="password" type="password"
							placeholder="Enter your password" autocomplete="current-password"
							required>
					</div>

					<div class="remember">
						<label><input name="remember" type="checkbox" value="true">
							Remember me</label>
					</div>

					<button class="login-button" type="submit">
						Sign in <span>→</span>
					</button>
				</form>

				<div class="security-note">
					<span>🔒</span>
					<div>
						<strong>Secure Login</strong>
						<p>Your hospital data is protected with secure authentication.</p>
					</div>
				</div>
			</div>
		</section>
	</div>
</body>
</html>
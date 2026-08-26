<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>CareConnect | Dashboard</title>

    <link rel="stylesheet" href="css/style.css">
</head>

<body>

<aside class="sidebar">

    <div class="logo">
        <span class="logo-icon">+</span>
        <span class="logo-text">CareConnect</span>
    </div>

    <p class="menu-label">MAIN MENU</p>

    <nav class="menu">
        <a href="dashboard.jsp" class="active">
            <span class="menu-icon">⌂</span>
            <span>Dashboard</span>
        </a>

        <a href="patients.jsp">
            <span class="menu-icon">♙</span>
            <span>Patients</span>
        </a>

        <a href="doctors.jsp">
            <span class="menu-icon">⚕</span>
            <span>Doctors</span>
        </a>

        <a href="appointments.jsp">
            <span class="menu-icon">▣</span>
            <span>Appointments</span>
        </a>

        <a href="billing.jsp">
            <span class="menu-icon">₹</span>
            <span>Billing</span>
        </a>

        <a href="reports.jsp">
            <span class="menu-icon">▤</span>
            <span>Reports</span>
        </a>
    </nav>

    <div class="logout">
        <a href="login.jsp">Logout</a>
    </div>

</aside>

<main class="main">

    <header class="topbar">

        <div class="page-title">
            <h1>Dashboard</h1>
            <p>Hospital Management System</p>
        </div>

        <div class="top-actions">

            <label class="search">
                <input id="dashboardSearch"
                       type="search"
                       placeholder="Search appointments..."
                       autocomplete="off">
            </label>

            <button class="notification"
                    type="button"
                    aria-label="Notifications">
                🔔
            </button>

            <div class="profile">
                <span class="profile-icon">V</span>

                <span class="profile-info">
                    <strong>Administrator</strong>
                    <span>Hospital Admin</span>
                </span>
            </div>

        </div>

    </header>

    <section class="content">

        <div class="welcome">
            <h2>Good evening, Administrator</h2>
            <p>Here’s an overview of your hospital today.</p>
        </div>

        <div class="stats">

            <div class="stat-card">
                <div class="stat-top">
                    <span class="stat-label">Total Patients</span>
                    <span class="stat-icon">♙</span>
                </div>

                <div class="stat-number">248</div>

                <div class="trend">
                    ↑ 12.5% <span>vs last month</span>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-top">
                    <span class="stat-label">Total Doctors</span>
                    <span class="stat-icon">⚕</span>
                </div>

                <div class="stat-number">32</div>

                <div class="trend">
                    ↑ 4.2% <span>vs last month</span>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-top">
                    <span class="stat-label">Appointments Today</span>
                    <span class="stat-icon">▣</span>
                </div>

                <div class="stat-number">18</div>

                <div class="trend">
                    ↑ 8.1% <span>vs yesterday</span>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-top">
                    <span class="stat-label">Pending Bills</span>
                    <span class="stat-icon">₹</span>
                </div>

                <div class="stat-number">7</div>

                <div class="trend">
                    ↓ 3.4% <span>vs last week</span>
                </div>
            </div>

        </div>

        <div class="grid">

            <section class="card">

                <div class="card-header">
                    <h3>Today’s Appointments</h3>
                    <a class="view" href="appointments.jsp">View all →</a>
                </div>

                <div class="appointment">
                    <div class="patient">
                        <span class="avatar">AK</span>
                        <div>
                            <strong>Arun Kumar</strong>
                            <span>General Consultation</span>
                        </div>
                    </div>

                    <span class="doctor">Dr. Rajesh</span>
                    <span class="time">09:30 AM</span>
                    <span class="status confirmed">Confirmed</span>
                </div>

                <div class="appointment">
                    <div class="patient">
                        <span class="avatar">RS</span>
                        <div>
                            <strong>Rahul Sharma</strong>
                            <span>Cardiology</span>
                        </div>
                    </div>

                    <span class="doctor">Dr. Mehta</span>
                    <span class="time">10:30 AM</span>
                    <span class="status confirmed">Confirmed</span>
                </div>

                <div class="appointment">
                    <div class="patient">
                        <span class="avatar">PM</span>
                        <div>
                            <strong>Priya Mehta</strong>
                            <span>Dermatology</span>
                        </div>
                    </div>

                    <span class="doctor">Dr. Anjali</span>
                    <span class="time">12:00 PM</span>
                    <span class="status pending">Pending</span>
                </div>

                <div class="appointment">
                    <div class="patient">
                        <span class="avatar">VK</span>
                        <div>
                            <strong>Vikas Kumar</strong>
                            <span>Orthopedics</span>
                        </div>
                    </div>

                    <span class="doctor">Dr. Arjun</span>
                    <span class="time">02:30 PM</span>
                    <span class="status confirmed">Confirmed</span>
                </div>

            </section>

            <section class="card">

                <div class="card-header">
                    <h3>Quick Actions</h3>
                </div>

                <a class="action" href="patients.jsp">
                    <span class="action-icon">+</span>
                    <div>
                        <strong>Add Patient</strong>
                        <span>Register a new patient</span>
                    </div>
                </a>

                <a class="action" href="doctors.jsp">
                    <span class="action-icon">⚕</span>
                    <div>
                        <strong>Add Doctor</strong>
                        <span>Register a new doctor</span>
                    </div>
                </a>

                <a class="action" href="appointments.jsp">
                    <span class="action-icon">+</span>
                    <div>
                        <strong>Book Appointment</strong>
                        <span>Schedule an appointment</span>
                    </div>
                </a>

                <a class="action" href="billing.jsp">
                    <span class="action-icon">₹</span>
                    <div>
                        <strong>Create Invoice</strong>
                        <span>Generate patient billing</span>
                    </div>
                </a>

            </section>

        </div>

        <div class="bottom-grid">

            <section class="card">

                <div class="card-header">
                    <h3>Department Overview</h3>
                    <a class="view" href="reports.jsp">View all →</a>
                </div>

                <div class="department">
                    <div class="department-top">
                        <strong>General Medicine</strong>
                        <span>82 patients</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: 82%;"></div>
                    </div>
                </div>

                <div class="department">
                    <div class="department-top">
                        <strong>Cardiology</strong>
                        <span>64 patients</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: 64%;"></div>
                    </div>
                </div>

                <div class="department">
                    <div class="department-top">
                        <strong>Orthopedics</strong>
                        <span>51 patients</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: 51%;"></div>
                    </div>
                </div>

                <div class="department">
                    <div class="department-top">
                        <strong>Pediatrics</strong>
                        <span>36 patients</span>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: 36%;"></div>
                    </div>
                </div>

            </section>

            <section class="card">

                <div class="card-header">
                    <h3>Recent Activity</h3>
                </div>

                <div class="activity">
                    <span class="activity-icon">+</span>
                    <div>
                        <p><strong>New patient</strong> Arun Kumar registered</p>
                        <span>10 minutes ago</span>
                    </div>
                </div>

                <div class="activity">
                    <span class="activity-icon">▣</span>
                    <div>
                        <p><strong>Appointment</strong> Rahul Sharma checked in</p>
                        <span>35 minutes ago</span>
                    </div>
                </div>

                <div class="activity">
                    <span class="activity-icon">₹</span>
                    <div>
                        <p><strong>Payment</strong> Invoice #1024 paid</p>
                        <span>1 hour ago</span>
                    </div>
                </div>

                <div class="activity">
                    <span class="activity-icon">⚕</span>
                    <div>
                        <p><strong>Doctor</strong> Dr. Anjali updated profile</p>
                        <span>2 hours ago</span>
                    </div>
                </div>

            </section>

        </div>

    </section>

</main>

<script>
<script>
document.addEventListener("DOMContentLoaded", function () {

    /* Search appointments */
    const searchInput = document.getElementById("dashboardSearch");

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const query = this.value.toLowerCase().trim();

            document.querySelectorAll(".appointment").forEach(function (row) {
                const matches = row.textContent.toLowerCase().includes(query);
                row.hidden = !matches;
            });
        });
    }

    /* Press / to focus search */
    document.addEventListener("keydown", function (event) {
        if (event.key === "/" && document.activeElement !== searchInput) {
            event.preventDefault();
            searchInput.focus();
        }
    });

    /* Animate statistic numbers */
    document.querySelectorAll(".stat-number").forEach(function (counter) {
        const target = Number(counter.textContent.trim());

        if (Number.isNaN(target)) {
            return;
        }

        const duration = 1000;
        const startTime = performance.now();

        function updateCounter(currentTime) {
            const progress = Math.min((currentTime - startTime) / duration, 1);
            const smoothProgress = 1 - Math.pow(1 - progress, 3);

            counter.textContent = Math.floor(target * smoothProgress);

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        }

        requestAnimationFrame(updateCounter);
    });

    /* Notification interaction */
    const notification = document.querySelector(".notification");

    if (notification) {
        notification.addEventListener("click", function () {
            alert("You have 3 new hospital notifications.");

            this.animate(
                [
                    { transform: "rotate(0deg)" },
                    { transform: "rotate(-15deg)" },
                    { transform: "rotate(15deg)" },
                    { transform: "rotate(0deg)" }
                ],
                {
                    duration: 450,
                    easing: "ease-in-out"
                }
            );
        });
    }

    /* Show live greeting based on current time */
    const greeting = document.querySelector(".welcome h2");

    if (greeting) {
        const hour = new Date().getHours();
        let message = "Good evening";

        if (hour < 12) {
            message = "Good morning";
        } else if (hour < 18) {
            message = "Good afternoon";
        }

        greeting.textContent = message + ", Administrator";
    }

});
</script>
</script>

</body>
</html>
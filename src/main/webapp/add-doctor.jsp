<%@ page pageEncoding="UTF-8" contentType="text/html; charset=UTF-8" %>

<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <title>CareConnect | Add Doctor</title>

    <style>

        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #f5f8fa;
            color: #263b5a;
        }

        .container {
            width: 90%;
            max-width: 850px;
            margin: 50px auto;
        }

        .header {
            margin-bottom: 30px;
        }

        .header h1 {
            margin: 0;
            font-size: 32px;
        }

        .header p {
            margin-top: 8px;
            color: #8190a5;
        }

        .form-container {
            background: white;
            padding: 35px;
            border-radius: 18px;
            box-shadow: 0 5px 25px rgba(0, 0, 0, 0.06);
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #43546b;
        }

        input, select {
            width: 100%;
            box-sizing: border-box;
            padding: 13px 14px;
            border: 1px solid #dce3ea;
            border-radius: 8px;
            font-size: 15px;
            outline: none;
            background: white;
        }

        input:focus, select:focus {
            border-color: #0b8f83;
        }

        .button-row {
            display: flex;
            gap: 12px;
            margin-top: 30px;
        }

        .submit-btn {
            padding: 13px 24px;
            border: none;
            border-radius: 9px;
            background: #0b8f83;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        .submit-btn:hover {
            background: #08766d;
        }

        .cancel-btn {
            padding: 13px 24px;
            border-radius: 9px;
            background: #eef2f5;
            color: #43546b;
            text-decoration: none;
            font-weight: bold;
        }

        .cancel-btn:hover {
            background: #e1e7eb;
        }

        .error-message {
            background: #fdecec;
            color: #c0392b;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        @media (max-width: 700px) {

            .form-row {
                grid-template-columns: 1fr;
            }

            .container {
                width: 94%;
            }

            .form-container {
                padding: 25px;
            }
        }

    </style>

</head>

<body>

<div class="container">

    <!-- HEADER -->

    <div class="header">

        <h1>Add Doctor</h1>

        <p>Register a new doctor in CareConnect.</p>

    </div>


    <!-- ERROR MESSAGE -->

    <%

        String error = request.getParameter("error");

        if (error != null) {

    %>

        <div class="error-message">

            <% if ("invalid".equals(error)) { %>

                Please enter valid doctor information.

            <% } else if ("failed".equals(error)) { %>

                Unable to add doctor. Please try again.

            <% } %>

        </div>

    <%

        }

    %>


    <!-- FORM -->

    <div class="form-container">

        <form action="${pageContext.request.contextPath}/DoctorServlet"
              method="post">

            <input type="hidden"
                   name="action"
                   value="add">


            <!-- NAME + SPECIALIZATION -->

            <div class="form-row">

                <div class="form-group">

                    <label for="name">
                        Doctor Name
                    </label>

                    <input type="text"
                           id="name"
                           name="name"
                           placeholder="Enter doctor name"
                           required>

                </div>


                <div class="form-group">

                    <label for="specialization">
                        Specialization (CVD / Retinal Care)
                    </label>

                    <select id="specialization"
                           name="specialization"
                           required>
                        <option value="">-- Select Specialization --</option>
                        <option value="Preventive Cardiologist" selected>Preventive Cardiologist</option>
                        <option value="Vitreo-Retinal Specialist (Ophthalmologist)">Vitreo-Retinal Specialist (Ophthalmologist)</option>
                        <option value="Interventional Cardiologist">Interventional Cardiologist</option>
                        <option value="General Cardiologist">General Cardiologist</option>
                        <option value="Endocrinologist &amp; Diabetologist">Endocrinologist &amp; Diabetologist</option>
                        <option value="Vascular Medicine &amp; Hypertension Specialist">Vascular Medicine &amp; Hypertension Specialist</option>
                        <option value="Cardiac Electrophysiologist">Cardiac Electrophysiologist</option>
                        <option value="Cardiothoracic Surgeon">Cardiothoracic Surgeon</option>
                        <option value="Heart Failure &amp; Transplant Cardiologist">Heart Failure &amp; Transplant Cardiologist</option>
                        <option value="Internal Medicine / Physician">Internal Medicine / Physician</option>
                    </select>

                </div>

            </div>


            <!-- PHONE + EMAIL -->

            <div class="form-row">

                <div class="form-group">

                    <label for="phone">
                        Phone
                    </label>

                    <input type="tel"
                           id="phone"
                           name="phone"
                           placeholder="Enter phone number"
                           required>

                </div>


                <div class="form-group">

                    <label for="email">
                        Email
                    </label>

                    <input type="email"
                           id="email"
                           name="email"
                           placeholder="doctor@example.com"
                           required>

                </div>

            </div>


            <!-- EXPERIENCE + FEE -->

            <div class="form-row">

                <div class="form-group">

                    <label for="experience">
                        Experience (Years)
                    </label>

                    <input type="number"
                           id="experience"
                           name="experience"
                           min="0"
                           max="70"
                           placeholder="e.g. 10"
                           required>

                </div>


                <div class="form-group">

                    <label for="consultationFee">
                        Consultation Fee (₹)
                    </label>

                    <input type="number"
                           id="consultationFee"
                           name="consultationFee"
                           min="0"
                           step="0.01"
                           placeholder="e.g. 500"
                           required>

                </div>

            </div>


            <!-- BUTTONS -->

            <div class="button-row">

                <button type="submit"
                        class="submit-btn">

                    Add Doctor

                </button>

                <a href="${pageContext.request.contextPath}/DoctorServlet?action=list"
                   class="cancel-btn">

                    Cancel

                </a>

            </div>

        </form>

    </div>

</div>

</body>

</html>
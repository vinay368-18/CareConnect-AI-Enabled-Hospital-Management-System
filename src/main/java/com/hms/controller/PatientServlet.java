package com.hms.controller;

import java.io.IOException;
import java.util.List;

import com.hms.dao.PatientDAO;
import com.hms.model.Patient;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@WebServlet("/PatientServlet")
public class PatientServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private PatientDAO patientDAO;

    @Override
    public void init() throws ServletException {
        patientDAO = new PatientDAO();
    }

    // GET: Display all patients
    @Override
    protected void doGet(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        try {

            List<Patient> patients = patientDAO.getAllPatients();

            request.setAttribute("patients", patients);

            request.getRequestDispatcher("/patients.jsp")
                   .forward(request, response);

        } catch (Exception e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/dashboard.jsp?error=patients"
            );
        }
    }

    // POST: Add a new patient
    @Override
    protected void doPost(HttpServletRequest request,
                           HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");

        String name = request.getParameter("name");
        String ageValue = request.getParameter("age");
        String gender = request.getParameter("gender");
        String phone = request.getParameter("phone");
        String address = request.getParameter("address");

        // Validate name
        if (name == null || name.trim().isEmpty()) {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?error=name"
            );

            return;
        }

        // Validate age
        int age;

        try {

            age = Integer.parseInt(ageValue);

            if (age <= 0 || age > 150) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?error=age"
                );

                return;
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?error=age"
            );

            return;
        }

        // Create Patient object
        Patient patient = new Patient();

        patient.setName(name.trim());
        patient.setAge(age);
        patient.setGender(gender);
        patient.setPhone(phone);
        patient.setAddress(address);

        // Save patient
        boolean success = patientDAO.addPatient(patient);

        if (success) {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?success=added"
            );

        } else {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?error=add"
            );
        }
    }
}	
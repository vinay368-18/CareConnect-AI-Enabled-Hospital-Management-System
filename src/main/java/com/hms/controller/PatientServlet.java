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

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        if (action == null || action.equals("list")) {

            listPatients(request, response);

        } else {

            response.sendRedirect(
                request.getContextPath() + "/PatientServlet?action=list"
            );
        }
    }

    @Override
    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        if ("add".equals(action)) {

            addPatient(request, response);

        } else {

            response.sendRedirect(
                request.getContextPath() + "/PatientServlet?action=list"
            );
        }
    }

    // =========================
    // LIST PATIENTS
    // =========================

    private void listPatients(HttpServletRequest request,
                              HttpServletResponse response)
            throws ServletException, IOException {

        List<Patient> patients = patientDAO.getAllPatients();

        request.setAttribute("patients", patients);

        request.getRequestDispatcher("/patients.jsp")
               .forward(request, response);
    }

    // =========================
    // ADD PATIENT
    // =========================

    private void addPatient(HttpServletRequest request,
                            HttpServletResponse response)
            throws IOException {

        String name = request.getParameter("name");
        String ageText = request.getParameter("age");
        String gender = request.getParameter("gender");
        String phone = request.getParameter("phone");
        String address = request.getParameter("address");

        try {

            int age = Integer.parseInt(ageText);

            if (age < 1 || age > 120) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-patient.jsp?error=invalid"
                );

                return;
            }

            Patient patient = new Patient();

            patient.setName(name);
            patient.setAge(age);
            patient.setGender(gender);
            patient.setPhone(phone);
            patient.setAddress(address);

            boolean success = patientDAO.addPatient(patient);

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-patient.jsp?error=failed"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/add-patient.jsp?error=invalid"
            );
        }
    }
}
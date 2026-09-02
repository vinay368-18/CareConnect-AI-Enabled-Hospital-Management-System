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

    // =========================
    // GET REQUESTS
    // =========================

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        // LIST
        if (action == null || action.equals("list")) {

            listPatients(request, response);

        }

        // SEARCH
        else if ("search".equals(action)) {

            searchPatients(request, response);

        }

        // EDIT
        else if ("edit".equals(action)) {

            try {

                int id = Integer.parseInt(
                    request.getParameter("id")
                );

                Patient patient =
                    patientDAO.getPatientById(id);

                request.setAttribute("patient", patient);

                request.getRequestDispatcher(
                    "/edit-patient.jsp"
                ).forward(request, response);

            } catch (NumberFormatException e) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=list"
                );
            }
        }

        // DELETE
        else if ("delete".equals(action)) {

            deletePatient(request, response);

        }

        // UNKNOWN ACTION
        else {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?action=list"
            );
        }
    }


    // =========================
    // POST REQUESTS
    // =========================

    @Override
    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        // ADD
        if ("add".equals(action)) {

            addPatient(request, response);

        }

        // UPDATE
        else if ("update".equals(action)) {

            updatePatient(request, response);

        }

        // UNKNOWN ACTION
        else {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?action=list"
            );
        }
    }


    // =========================
    // LIST PATIENTS
    // =========================

    private void listPatients(HttpServletRequest request,
                              HttpServletResponse response)
            throws ServletException, IOException {

        List<Patient> patients =
            patientDAO.getAllPatients();

        request.setAttribute("patients", patients);

        request.getRequestDispatcher(
            "/patients.jsp"
        ).forward(request, response);
    }


    // =========================
    // SEARCH PATIENTS
    // =========================

    private void searchPatients(HttpServletRequest request,
                                HttpServletResponse response)
            throws ServletException, IOException {

        String keyword =
            request.getParameter("keyword");

        if (keyword == null) {
            keyword = "";
        }

        List<Patient> patients =
            patientDAO.searchPatients(keyword);

        request.setAttribute("patients", patients);

        request.setAttribute(
            "searchKeyword",
            keyword
        );

        request.getRequestDispatcher(
            "/patients.jsp"
        ).forward(request, response);
    }


    // =========================
    // ADD PATIENT
    // =========================

    private void addPatient(HttpServletRequest request,
                            HttpServletResponse response)
            throws IOException {

        String name =
            request.getParameter("name");

        String ageText =
            request.getParameter("age");

        String gender =
            request.getParameter("gender");

        String phone =
            request.getParameter("phone");

        String address =
            request.getParameter("address");

        try {

            int age =
                Integer.parseInt(ageText);

            // AGE VALIDATION

            if (age < 1 || age > 120) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-patient.jsp?error=invalid"
                );

                return;
            }

            Patient patient =
                new Patient();

            patient.setName(name);
            patient.setAge(age);
            patient.setGender(gender);
            patient.setPhone(phone);
            patient.setAddress(address);

            boolean success =
                patientDAO.addPatient(patient);

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


    // =========================
    // UPDATE PATIENT
    // =========================

    private void updatePatient(HttpServletRequest request,
                               HttpServletResponse response)
            throws IOException {

        try {

            int id =
                Integer.parseInt(
                    request.getParameter("id")
                );

            int age =
                Integer.parseInt(
                    request.getParameter("age")
                );

            // AGE VALIDATION

            if (age < 1 || age > 120) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=edit&id="
                    + id
                    + "&error=invalid"
                );

                return;
            }

            Patient patient =
                new Patient();

            patient.setId(id);

            patient.setName(
                request.getParameter("name")
            );

            patient.setAge(age);

            patient.setGender(
                request.getParameter("gender")
            );

            patient.setPhone(
                request.getParameter("phone")
            );

            patient.setAddress(
                request.getParameter("address")
            );

            boolean success =
                patientDAO.updatePatient(patient);

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=edit&id="
                    + id
                    + "&error=failed"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?action=list"
            );
        }
    }


    // =========================
    // DELETE PATIENT
    // =========================

    private void deletePatient(HttpServletRequest request,
                               HttpServletResponse response)
            throws IOException {

        try {

            int id =
                Integer.parseInt(
                    request.getParameter("id")
                );

            boolean success =
                patientDAO.deletePatient(id);

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=list&error=delete"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?action=list&error=invalid"
            );
        }
    }

}
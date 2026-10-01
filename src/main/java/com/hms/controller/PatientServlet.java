package com.hms.controller;

import java.io.IOException;
import java.util.List;

import com.hms.dao.PatientDAO;
import com.hms.model.Patient;
import com.hms.model.User;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

@WebServlet("/PatientServlet")
public class PatientServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private PatientDAO patientDAO;

    @Override
    public void init() throws ServletException {
        patientDAO = new PatientDAO();
    }

    // =========================
    // AUTHORIZATION
    // =========================

    private User getLoggedInUser(
            HttpServletRequest request) {

        HttpSession session =
                request.getSession(false);

        if (session == null) {
            return null;
        }

        Object userObject =
                session.getAttribute("user");

        if (!(userObject instanceof User)) {
            return null;
        }

        return (User) userObject;
    }

    private boolean isAdmin(
            HttpServletRequest request) {

        User user =
                getLoggedInUser(request);

        return user != null
                && "ADMIN".equalsIgnoreCase(
                        user.getRole()
                );
    }

    private boolean isAdminOrReceptionist(
            HttpServletRequest request) {

        User user =
                getLoggedInUser(request);

        if (user == null) {
            return false;
        }

        String role =
                user.getRole();

        return "ADMIN".equalsIgnoreCase(role)
                || "RECEPTIONIST".equalsIgnoreCase(role);
    }

    private boolean checkLogin(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        User user =
                getLoggedInUser(request);

        if (user == null) {

            response.sendRedirect(
                request.getContextPath()
                + "/login.jsp"
            );

            return false;
        }

        return true;
    }

    private boolean checkAdminOrReceptionist(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        if (!checkLogin(request, response)) {
            return false;
        }

        if (!isAdminOrReceptionist(request)) {

            response.sendRedirect(
                request.getContextPath()
                + "/dashboard.jsp?error=unauthorized"
            );

            return false;
        }

        return true;
    }

    private boolean checkAdmin(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        if (!checkLogin(request, response)) {
            return false;
        }

        if (!isAdmin(request)) {

            response.sendRedirect(
                request.getContextPath()
                + "/PatientServlet?action=list&error=unauthorized"
            );

            return false;
        }

        return true;
    }

    // =========================
    // GET REQUESTS
    // =========================

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String action =
                request.getParameter("action");

        // =========================
        // LIST
        // ADMIN + RECEPTIONIST
        // =========================

        if (action == null
                || "list".equals(action)) {

            if (!checkAdminOrReceptionist(
                    request,
                    response)) {

                return;
            }

            listPatients(
                    request,
                    response
            );
        }

        // =========================
        // SEARCH
        // ADMIN + RECEPTIONIST
        // =========================

        else if ("search".equals(action)) {

            if (!checkAdminOrReceptionist(
                    request,
                    response)) {

                return;
            }

            searchPatients(
                    request,
                    response
            );
        }

        // =========================
        // EDIT
        // ADMIN + RECEPTIONIST
        // =========================

        else if ("edit".equals(action)) {

            if (!checkAdminOrReceptionist(
                    request,
                    response)) {

                return;
            }

            try {

                int id =
                        Integer.parseInt(
                            request.getParameter("id")
                        );

                Patient patient =
                        patientDAO.getPatientById(id);

                if (patient == null) {

                    response.sendRedirect(
                        request.getContextPath()
                        + "/PatientServlet?action=list"
                    );

                    return;
                }

                request.setAttribute(
                        "patient",
                        patient
                );

                request.getRequestDispatcher(
                        "/edit-patient.jsp"
                ).forward(
                        request,
                        response
                );

            } catch (NumberFormatException e) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=list"
                );
            }
        }

        // =========================
        // DELETE
        // ADMIN ONLY
        // =========================

        else if ("delete".equals(action)) {

            if (!checkAdmin(
                    request,
                    response)) {

                return;
            }

            deletePatient(
                    request,
                    response
            );
        }

        // =========================
        // UNKNOWN ACTION
        // =========================

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
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        if (!checkAdminOrReceptionist(
                request,
                response)) {

            return;
        }

        request.setCharacterEncoding(
                "UTF-8"
        );

        response.setCharacterEncoding(
                "UTF-8"
        );

        String action =
                request.getParameter("action");

        // =========================
        // ADD
        // ADMIN + RECEPTIONIST
        // =========================

        if ("add".equals(action)) {

            addPatient(
                    request,
                    response
            );
        }

        // =========================
        // UPDATE
        // ADMIN + RECEPTIONIST
        // =========================

        else if ("update".equals(action)) {

            updatePatient(
                    request,
                    response
            );
        }

        // =========================
        // UNKNOWN ACTION
        // =========================

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

    private void listPatients(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        List<Patient> patients =
                patientDAO.getAllPatients();

        request.setAttribute(
                "patients",
                patients
        );

        request.getRequestDispatcher(
                "/patients.jsp"
        ).forward(
                request,
                response
        );
    }

    // =========================
    // SEARCH PATIENTS
    // =========================

    private void searchPatients(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String keyword =
                request.getParameter("keyword");

        if (keyword == null) {
            keyword = "";
        }

        List<Patient> patients =
                patientDAO.searchPatients(
                        keyword
                );

        request.setAttribute(
                "patients",
                patients
        );

        request.setAttribute(
                "searchKeyword",
                keyword
        );

        request.getRequestDispatcher(
                "/patients.jsp"
        ).forward(
                request,
                response
        );
    }

    // =========================
    // ADD PATIENT
    // =========================

    private void addPatient(
            HttpServletRequest request,
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

        if (name == null
                || name.trim().isEmpty()
                || ageText == null
                || ageText.trim().isEmpty()) {

            response.sendRedirect(
                request.getContextPath()
                + "/add-patient.jsp?error=invalid"
            );

            return;
        }

        try {

            int age =
                    Integer.parseInt(
                        ageText.trim()
                    );

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

            patient.setName(
                    name
            );

            patient.setAge(
                    age
            );

            patient.setGender(
                    gender
            );

            patient.setPhone(
                    phone
            );

            patient.setAddress(
                    address
            );

            boolean success =
                    patientDAO.addPatient(
                            patient
                    );

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

    private void updatePatient(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        int id = 0;

        try {

            id =
                    Integer.parseInt(
                        request.getParameter("id")
                    );

            String name =
                    request.getParameter("name");

            String ageText =
                    request.getParameter("age");

            if (name == null
                    || name.trim().isEmpty()
                    || ageText == null
                    || ageText.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/PatientServlet?action=edit&id="
                    + id
                    + "&error=invalid"
                );

                return;
            }

            int age =
                    Integer.parseInt(
                        ageText.trim()
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

            patient.setId(
                    id
            );

            patient.setName(
                    name
            );

            patient.setAge(
                    age
            );

            patient.setGender(
                    request.getParameter(
                            "gender"
                    )
            );

            patient.setPhone(
                    request.getParameter(
                            "phone"
                    )
            );

            patient.setAddress(
                    request.getParameter(
                            "address"
                    )
            );

            boolean success =
                    patientDAO.updatePatient(
                            patient
                    );

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

    private void deletePatient(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        try {

            int id =
                    Integer.parseInt(
                        request.getParameter("id")
                    );

            boolean success =
                    patientDAO.deletePatient(
                            id
                    );

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
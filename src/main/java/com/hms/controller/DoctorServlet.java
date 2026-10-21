package com.hms.controller;

import java.io.IOException;
import java.util.List;

import com.hms.dao.DoctorDAO;
import com.hms.model.Doctor;
import com.hms.model.User;
import com.hms.util.CSRFUtil;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

@WebServlet("/DoctorServlet")
public class DoctorServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private DoctorDAO doctorDAO;

    @Override
    public void init() throws ServletException {
        doctorDAO = new DoctorDAO();
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
                + "/DoctorServlet?action=list&error=unauthorized"
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

            listDoctors(
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

            searchDoctors(
                    request,
                    response
            );

        }

        // =========================
        // EDIT
        // ADMIN ONLY
        // =========================

        else if ("edit".equals(action)) {

            if (!checkAdmin(
                    request,
                    response)) {

                return;
            }

            try {

                int id =
                        Integer.parseInt(
                            request.getParameter("id")
                        );

                Doctor doctor =
                        doctorDAO.getDoctorById(id);

                if (doctor == null) {

                    response.sendRedirect(
                        request.getContextPath()
                        + "/DoctorServlet?action=list"
                    );

                    return;
                }

                request.setAttribute(
                        "doctor",
                        doctor
                );

                request.getRequestDispatcher(
                        "/edit-doctor.jsp"
                ).forward(
                        request,
                        response
                );

            } catch (NumberFormatException e) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );
            }
        }

        // =========================
        // DELETE
        // ADMIN ONLY
        // =========================

        else if ("delete".equals(action)) { response.sendRedirect(request.getContextPath() + "/DoctorServlet?action=list&error=method_not_allowed"); return; }

        // =========================
        // UNKNOWN ACTION
        // =========================

        else {

            response.sendRedirect(
                request.getContextPath()
                + "/DoctorServlet?action=list"
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

        if (!checkAdmin(
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
        // ADMIN ONLY
        // =========================

        if (!CSRFUtil.isValid(request)) {
            response.sendRedirect(request.getContextPath() + "/DoctorServlet?action=list&error=csrf");
            return;
        }

        if ("delete".equals(action)) {
            deleteDoctor(request, response);
        } else if ("add".equals(action)) {

            addDoctor(
                    request,
                    response
            );
        }

        // =========================
        // UPDATE
        // ADMIN ONLY
        // =========================

        else if ("update".equals(action)) {

            updateDoctor(
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
                + "/DoctorServlet?action=list"
            );
        }
    }

    // =========================
    // LIST DOCTORS
    // =========================

    private void listDoctors(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        List<Doctor> doctors =
                doctorDAO.getAllDoctors();

        request.setAttribute(
                "doctors",
                doctors
        );

        request.getRequestDispatcher(
                "/doctors.jsp"
        ).forward(
                request,
                response
        );
    }

    // =========================
    // SEARCH DOCTORS
    // =========================

    private void searchDoctors(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String keyword =
                request.getParameter("keyword");

        if (keyword == null) {
            keyword = "";
        }

        List<Doctor> doctors =
                doctorDAO.searchDoctors(
                        keyword
                );

        request.setAttribute(
                "doctors",
                doctors
        );

        request.setAttribute(
                "searchKeyword",
                keyword
        );

        request.getRequestDispatcher(
                "/doctors.jsp"
        ).forward(
                request,
                response
        );
    }

    // =========================
    // ADD DOCTOR
    // =========================

    private void addDoctor(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        String name =
                request.getParameter("name");

        String specialization =
                request.getParameter("specialization");

        String phone =
                request.getParameter("phone");

        String email =
                request.getParameter("email");

        String experienceText =
                request.getParameter("experience");

        String feeText =
                request.getParameter("consultationFee");

        if (name == null
                || name.trim().isEmpty()
                || specialization == null
                || specialization.trim().isEmpty()
                || experienceText == null
                || feeText == null) {

            response.sendRedirect(
                request.getContextPath()
                + "/add-doctor.jsp?error=invalid"
            );

            return;
        }

        try {

            int experience =
                    Integer.parseInt(
                            experienceText.trim()
                    );

            double consultationFee =
                    Double.parseDouble(
                            feeText.trim()
                    );

            if (experience < 0
                    || experience > 70
                    || consultationFee < 0) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-doctor.jsp?error=invalid"
                );

                return;
            }

            Doctor doctor =
                    new Doctor();

            doctor.setName(
                    name
            );

            doctor.setSpecialization(
                    specialization
            );

            doctor.setPhone(
                    phone
            );

            doctor.setEmail(
                    email
            );

            doctor.setExperience(
                    experience
            );

            doctor.setConsultationFee(
                    consultationFee
            );

            boolean success =
                    doctorDAO.addDoctor(
                            doctor
                    );

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-doctor.jsp?error=failed"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/add-doctor.jsp?error=invalid"
            );
        }
    }

    // =========================
    // UPDATE DOCTOR
    // =========================

    private void updateDoctor(
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

            String specialization =
                    request.getParameter(
                            "specialization"
                    );

            if (name == null
                    || name.trim().isEmpty()
                    || specialization == null
                    || specialization.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=edit&id="
                    + id
                    + "&error=invalid"
                );

                return;
            }

            int experience =
                    Integer.parseInt(
                        request.getParameter(
                                "experience"
                        )
                    );

            double consultationFee =
                    Double.parseDouble(
                        request.getParameter(
                                "consultationFee"
                        )
                    );

            if (experience < 0
                    || experience > 70
                    || consultationFee < 0) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=edit&id="
                    + id
                    + "&error=invalid"
                );

                return;
            }

            Doctor doctor =
                    new Doctor();

            doctor.setId(
                    id
            );

            doctor.setName(
                    name
            );

            doctor.setSpecialization(
                    specialization
            );

            doctor.setPhone(
                    request.getParameter(
                            "phone"
                    )
            );

            doctor.setEmail(
                    request.getParameter(
                            "email"
                    )
            );

            doctor.setExperience(
                    experience
            );

            doctor.setConsultationFee(
                    consultationFee
            );

            boolean success =
                    doctorDAO.updateDoctor(
                            doctor
                    );

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=edit&id="
                    + id
                    + "&error=failed"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/DoctorServlet?action=list"
            );
        }
    }

    // =========================
    // DELETE DOCTOR
    // =========================

    private void deleteDoctor(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        try {

            int id =
                    Integer.parseInt(
                        request.getParameter("id")
                    );

            boolean success =
                    doctorDAO.deleteDoctor(
                            id
                    );

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list&error=delete"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/DoctorServlet?action=list&error=invalid"
            );
        }
    }
}
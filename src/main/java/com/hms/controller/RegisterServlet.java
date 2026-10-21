package com.hms.controller;

import java.io.IOException;
import java.util.List;

import com.hms.dao.DoctorDAO;
import com.hms.dao.UserDAO;
import com.hms.model.Doctor;
import com.hms.model.User;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

@WebServlet("/RegisterServlet")
public class RegisterServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private UserDAO userDAO;
    private DoctorDAO doctorDAO;

    @Override
    public void init() throws ServletException {
        userDAO = new UserDAO();
        doctorDAO = new DoctorDAO();
    }

    /**
     * Helper to verify if the active session belongs to an authorized Administrator.
     */
    private boolean isAdmin(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session == null) {
            return false;
        }
        Object userObj = session.getAttribute("user");
        if (!(userObj instanceof User)) {
            return false;
        }
        User user = (User) userObj;
        return "ADMIN".equalsIgnoreCase(user.getRole());
    }

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        // Enforce administrative authorization: only ADMIN can access staff provisioning
        if (!isAdmin(request)) {
            HttpSession session = request.getSession(false);
            if (session == null || session.getAttribute("user") == null) {
                response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized");
            } else {
                response.sendRedirect(request.getContextPath() + "/dashboard.jsp?error=unauthorized");
            }
            return;
        }

        List<Doctor> doctors = doctorDAO.getAllDoctors();
        request.setAttribute("doctors", doctors);

        request.getRequestDispatcher("/register.jsp")
               .forward(request, response);
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        // Strict Server-Side Authorization: Reject unauthenticated or non-admin callers immediately
        if (!isAdmin(request)) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, "Only administrators can provision staff accounts.");
            return;
        }

        String username = request.getParameter("username");
        String password = request.getParameter("password");
        String confirmPassword = request.getParameter("confirmPassword");
        String role = request.getParameter("role");

        if (username == null || username.trim().isEmpty()
                || password == null || password.trim().isEmpty()
                || confirmPassword == null || confirmPassword.trim().isEmpty()
                || role == null || role.trim().isEmpty()) {

            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=empty"
            );
            return;
        }

        username = username.trim();
        role = role.trim().toUpperCase();

        // Enforce input validation on username (alphanumeric, underscore, dash, length 3-50)
        if (!username.matches("^[a-zA-Z0-9_.-]{3,50}$")) {
            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=invalidusername"
            );
            return;
        }

        // Enforce minimum password length (minimum 8 characters)
        if (password.length() < 8) {
            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=weakpassword"
            );
            return;
        }

        // Only allow explicit staff roles: RECEPTIONIST and DOCTOR. Reject any unauthorized role escalation (e.g. forged ADMIN)
        if (!role.equals("RECEPTIONIST") && !role.equals("DOCTOR")) {
            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=invalidrole"
            );
            return;
        }

        if (!password.equals(confirmPassword)) {
            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=password"
            );
            return;
        }

        if (userDAO.usernameExists(username)) {
            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=exists"
            );
            return;
        }

        User user = new User();
        user.setUsername(username);
        user.setPassword(password); // UserDAO will hash this securely before insertion
        user.setRole(role);

        if ("DOCTOR".equals(role)) {

            String doctorIdParameter = request.getParameter("doctorId");

            if (doctorIdParameter == null
                    || doctorIdParameter.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/register.jsp?error=doctor"
                );
                return;
            }

            try {
                int doctorId = Integer.parseInt(doctorIdParameter.trim());

                if (doctorId <= 0) {
                    response.sendRedirect(
                        request.getContextPath()
                        + "/register.jsp?error=doctor"
                    );
                    return;
                }

                // Verify the doctor ID actually exists in the database
                Doctor existingDoctor = doctorDAO.getDoctorById(doctorId);
                if (existingDoctor == null) {
                    response.sendRedirect(
                        request.getContextPath()
                        + "/register.jsp?error=doctor"
                    );
                    return;
                }

                user.setDoctorId(doctorId);

            } catch (NumberFormatException e) {
                response.sendRedirect(
                    request.getContextPath()
                    + "/register.jsp?error=doctor"
                );
                return;
            }

        } else {
            user.setDoctorId(0);
        }

        boolean registered = userDAO.registerUser(user);

        if (registered) {
            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?registered=true"
            );
        } else {
            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=failed"
            );
        }
    }
}

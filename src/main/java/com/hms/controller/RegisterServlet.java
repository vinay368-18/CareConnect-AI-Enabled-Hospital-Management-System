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

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

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
        user.setPassword(password);
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

                int doctorId = Integer.parseInt(doctorIdParameter);

                if (doctorId <= 0) {

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
                + "/login.jsp?registered=true"
            );

        } else {

            response.sendRedirect(
                request.getContextPath()
                + "/register.jsp?error=failed"
            );
        }
    }
}
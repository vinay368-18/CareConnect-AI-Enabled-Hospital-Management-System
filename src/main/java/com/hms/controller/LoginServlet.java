package com.hms.controller;

import java.io.IOException;

import com.hms.dao.UserDAO;
import com.hms.model.User;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

@WebServlet("/LoginServlet")
public class LoginServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private UserDAO userDAO;

    @Override
    public void init() throws ServletException {
        userDAO = new UserDAO();
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String username = request.getParameter("username");
        String password = request.getParameter("password");

        if (username == null || password == null || username.trim().isEmpty() || password.isEmpty()) {
            response.sendRedirect(
                request.getContextPath() + "/login.jsp?error=invalid"
            );
            return;
        }

        User user;
        try {
            user = userDAO.login(username.trim(), password);
        } catch (RuntimeException e) {
            // DBConnection returns null when credentials are missing or MySQL
            // is unreachable; the DAO then fails. Tell the user instead of
            // surfacing a generic 500.
            System.err.println("[LoginServlet] Login failed because the database is unavailable: " + e);
            response.sendRedirect(
                request.getContextPath() + "/login.jsp?error=db_unavailable"
            );
            return;
        }

        if (user != null) {
            // Prevent session fixation
            HttpSession oldSession = request.getSession(false);
            if (oldSession != null) {
                oldSession.invalidate();
            }
            HttpSession session = request.getSession(true);

            user.setPassword(null); // Never retain password in session
            session.setAttribute("user", user);
            session.setAttribute("username", user.getUsername());
            session.setAttribute("role", user.getRole());
            session.setAttribute("doctorId", user.getDoctorId());

            String role = user.getRole();

            if ("ADMIN".equalsIgnoreCase(role) || "RECEPTIONIST".equalsIgnoreCase(role) || "DOCTOR".equalsIgnoreCase(role)) {
                response.sendRedirect(
                    request.getContextPath() + "/dashboard.jsp"
                );
            } else {
                session.invalidate();
                response.sendRedirect(
                    request.getContextPath() + "/login.jsp?error=invalid"
                );
            }

        } else {

            response.sendRedirect(
                request.getContextPath() + "/login.jsp?error=invalid"
            );
        }
    }

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        response.sendRedirect(
            request.getContextPath() + "/login.jsp"
        );
    }
}
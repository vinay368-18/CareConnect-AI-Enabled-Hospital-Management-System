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

        User user = userDAO.login(username, password);

        if (user != null) {

            HttpSession session = request.getSession();

            session.setAttribute("user", user);
            session.setAttribute("username", user.getUsername());
            session.setAttribute("role", user.getRole());
            session.setAttribute("doctorId", user.getDoctorId());

            String role = user.getRole();

            if ("ADMIN".equalsIgnoreCase(role)) {

                response.sendRedirect(
                    request.getContextPath() + "/dashboard.jsp"
                );

            } else if ("RECEPTIONIST".equalsIgnoreCase(role)) {

                response.sendRedirect(
                    request.getContextPath() + "/dashboard.jsp"
                );

            } else if ("DOCTOR".equalsIgnoreCase(role)) {

                response.sendRedirect(
                    request.getContextPath() + "/dashboard.jsp"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath() + "/login.jsp?error=invalidrole"
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
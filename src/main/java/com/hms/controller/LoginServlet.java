package com.hms.controller;

import java.io.IOException;

import com.hms.dao.UserDAO;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

@WebServlet("/LoginServlet")
public class LoginServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    @Override
    protected void doPost(HttpServletRequest request,
                           HttpServletResponse response)
            throws ServletException, IOException {

        System.out.println("LOGIN SERVLET CALLED");

        String username = request.getParameter("username");
        String password = request.getParameter("password");

        UserDAO userDAO = new UserDAO();

        boolean loginSuccess = userDAO.login(username, password);

        if (loginSuccess) {

            // Create session
            HttpSession session = request.getSession();
            session.setAttribute("username", username);

            // Go to dashboard
            response.sendRedirect(request.getContextPath() + "/dashboard.jsp");

        } else {

            // Invalid login
            response.sendRedirect(
                request.getContextPath() + "/login.jsp?error=invalid"
            );
        }
    }
}
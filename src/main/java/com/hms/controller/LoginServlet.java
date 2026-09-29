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

        request.setCharacterEncoding("UTF-8");
        response.setCharacterEncoding("UTF-8");

        String username = request.getParameter("username");
        String password = request.getParameter("password");

        UserDAO userDAO = new UserDAO();

        if (username != null && password != null && userDAO.login(username.trim(), password.trim())) {
            HttpSession session = request.getSession();
            session.setAttribute("user", username.trim());
            session.setAttribute("role", "ADMIN");

            response.sendRedirect(
                request.getContextPath() + "/dashboard.jsp"
            );
        } else {
            response.sendRedirect(
                request.getContextPath()
                + "/login.jsp?error=invalid"
            );
        }
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.sendRedirect(request.getContextPath() + "/login.jsp");
    }
}
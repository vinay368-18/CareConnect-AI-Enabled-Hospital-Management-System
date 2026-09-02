package com.hms.controller;

import java.io.IOException;

import com.hms.dao.UserDAO;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

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

        if (userDAO.login(username, password)) {

            System.out.println("LOGIN SUCCESS");

            response.sendRedirect(
                request.getContextPath() + "/dashboard.jsp"
            );

        } else {

            System.out.println("LOGIN FAILED");

            response.sendRedirect(
                request.getContextPath()
                + "/login.jsp?error=invalid"
            );
        }
    }
}	
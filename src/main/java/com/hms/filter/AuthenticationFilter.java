package com.hms.filter;

import java.io.IOException;

import com.hms.model.User;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

/**
 * Centralized authentication filter.
 * Intercepts all requests and enforces session-based authentication
 * for protected resources.
 */
@WebFilter("/*")
public class AuthenticationFilter implements Filter {

    @Override
    public void doFilter(ServletRequest req,
                         ServletResponse res,
                         FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest request = (HttpServletRequest) req;
        HttpServletResponse response = (HttpServletResponse) res;

        String path = request.getRequestURI()
                .substring(request.getContextPath().length());

        // Allow public resources without authentication
        if (isPublicResource(path)) {
            chain.doFilter(request, response);
            return;
        }

        // Check for valid authenticated session
        HttpSession session = request.getSession(false);

        if (session != null) {

            Object userObj = session.getAttribute("user");

            if (userObj instanceof User) {
                chain.doFilter(request, response);
                return;
            }
        }

        // No valid session — redirect to login
        response.sendRedirect(
            request.getContextPath()
            + "/login.jsp?error=unauthorized"
        );
    }

    /**
     * Determines if the given path is a public resource
     * that does not require authentication.
     */
    private boolean isPublicResource(String path) {

        // Login, logout, and landing pages
        if ("/login.jsp".equals(path)
                || "/LoginServlet".equals(path)
                || "/LogoutServlet".equals(path)
                || "/index.jsp".equals(path)
                || "/".equals(path)
                || "/forgot-password.jsp".equals(path)) {

            return true;
        }

        // Static resources
        if (path.startsWith("/css/")
                || path.startsWith("/js/")
                || path.startsWith("/images/")
                || path.startsWith("/uploads/")) {

            return true;
        }

        return false;
    }
}

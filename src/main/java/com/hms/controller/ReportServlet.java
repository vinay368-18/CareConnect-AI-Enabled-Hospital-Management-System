package com.hms.controller;

import java.io.IOException;
import java.util.List;

import com.hms.dao.ReportDAO;
import com.hms.model.Appointment;
import com.hms.model.User;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

@WebServlet("/ReportServlet")
public class ReportServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private ReportDAO reportDAO;

    @Override
    public void init() throws ServletException {
        reportDAO = new ReportDAO();
    }

    private User getLoggedInUser(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session == null) {
            return null;
        }
        Object userObj = session.getAttribute("user");
        if (!(userObj instanceof User)) {
            return null;
        }
        return (User) userObj;
    }

    private boolean isAuthorized(HttpServletRequest request) {
        User user = getLoggedInUser(request);
        if (user == null) {
            return false;
        }
        String role = user.getRole();
        // Hospital administrative & financial reports are restricted to ADMIN and RECEPTIONIST
        return "ADMIN".equalsIgnoreCase(role) || "RECEPTIONIST".equalsIgnoreCase(role);
    }

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        User user = getLoggedInUser(request);
        if (user == null) {
            response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized");
            return;
        }

        if (!isAuthorized(request)) {
            response.sendRedirect(request.getContextPath() + "/dashboard.jsp?error=unauthorized");
            return;
        }

        int totalPatients = reportDAO.getTotalPatients();
        int totalDoctors = reportDAO.getTotalDoctors();
        int totalAppointments = reportDAO.getTotalAppointments();
        int totalBills = reportDAO.getTotalBills();
        double totalPaidAmount = reportDAO.getTotalPaidAmount();
        double totalPendingAmount = reportDAO.getTotalPendingAmount();
        int cancelledBills = reportDAO.getCancelledBills();
        List<Appointment> recentAppointments = reportDAO.getRecentAppointments();

        request.setAttribute("totalPatients", totalPatients);
        request.setAttribute("totalDoctors", totalDoctors);
        request.setAttribute("totalAppointments", totalAppointments);
        request.setAttribute("totalBills", totalBills);
        request.setAttribute("totalPaidAmount", totalPaidAmount);
        request.setAttribute("totalPendingAmount", totalPendingAmount);
        request.setAttribute("cancelledBills", cancelledBills);
        request.setAttribute("recentAppointments", recentAppointments);

        request.getRequestDispatcher("/reports.jsp").forward(request, response);
    }
}

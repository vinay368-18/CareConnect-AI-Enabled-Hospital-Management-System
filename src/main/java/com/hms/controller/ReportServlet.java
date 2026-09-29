package com.hms.controller;

import java.io.IOException;
import java.util.List;

import com.hms.dao.ReportDAO;
import com.hms.model.Appointment;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@WebServlet("/ReportServlet")
public class ReportServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private ReportDAO reportDAO;

    @Override
    public void init() throws ServletException {
        reportDAO = new ReportDAO();
    }

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        int totalPatients =
            reportDAO.getTotalPatients();

        int totalDoctors =
            reportDAO.getTotalDoctors();

        int totalAppointments =
            reportDAO.getTotalAppointments();

        int totalBills =
            reportDAO.getTotalBills();

        double totalPaidAmount =
            reportDAO.getTotalPaidAmount();

        double totalPendingAmount =
            reportDAO.getTotalPendingAmount();

        int cancelledBills =
            reportDAO.getCancelledBills();

        List<Appointment> recentAppointments =
            reportDAO.getRecentAppointments();


        request.setAttribute(
            "totalPatients",
            totalPatients
        );

        request.setAttribute(
            "totalDoctors",
            totalDoctors
        );

        request.setAttribute(
            "totalAppointments",
            totalAppointments
        );

        request.setAttribute(
            "totalBills",
            totalBills
        );

        request.setAttribute(
            "totalPaidAmount",
            totalPaidAmount
        );

        request.setAttribute(
            "totalPendingAmount",
            totalPendingAmount
        );

        request.setAttribute(
            "cancelledBills",
            cancelledBills
        );

        request.setAttribute(
            "recentAppointments",
            recentAppointments
        );


        request.getRequestDispatcher(
            "/reports.jsp"
        ).forward(request, response);
    }
}
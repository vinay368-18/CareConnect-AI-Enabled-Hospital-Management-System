package com.hms.controller;

import java.io.IOException;
import java.sql.Date;
import java.sql.Time;
import java.util.List;

import com.hms.dao.AppointmentDAO;
import com.hms.model.Appointment;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@WebServlet("/AppointmentServlet")
public class AppointmentServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private AppointmentDAO appointmentDAO;

    // =========================
    // INITIALIZE
    // =========================

    @Override
    public void init() throws ServletException {
        appointmentDAO = new AppointmentDAO();
    }

    // =========================
    // GET REQUESTS
    // =========================

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        // LIST
        if (action == null || "list".equals(action)) {

            listAppointments(request, response);

        }

        // SEARCH
        else if ("search".equals(action)) {

            searchAppointments(request, response);

        }

        // EDIT
        else if ("edit".equals(action)) {

            editAppointment(request, response);

        }

        // DELETE
        else if ("delete".equals(action)) {

            deleteAppointment(request, response);

        }

        // UNKNOWN ACTION
        else {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

    // =========================
    // POST REQUESTS
    // =========================

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        // ADD
        if ("add".equals(action)) {

            addAppointment(request, response);

        }

        // UPDATE
        else if ("update".equals(action)) {

            updateAppointment(request, response);

        }

        // UNKNOWN ACTION
        else {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

    // =========================
    // LIST APPOINTMENTS
    // =========================

    private void listAppointments(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        List<Appointment> appointments =
            appointmentDAO.getAllAppointments();

        request.setAttribute(
            "appointments",
            appointments
        );

        request.getRequestDispatcher(
            "/appointments.jsp"
        ).forward(request, response);
    }

    // =========================
    // ADD APPOINTMENT
    // =========================

    private void addAppointment(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        try {

            // Patient ID
            int patientId = Integer.parseInt(
                request.getParameter("patientId")
            );

            // Doctor ID
            int doctorId = Integer.parseInt(
                request.getParameter("doctorId")
            );

            // Appointment Date
            Date appointmentDate = Date.valueOf(
                request.getParameter("appointmentDate")
            );

            // Appointment Time
            String timeText =
                request.getParameter("appointmentTime");

            /*
             * HTML <input type="time"> normally sends:
             *
             * HH:mm
             *
             * Example:
             * 19:40
             *
             * java.sql.Time.valueOf() expects:
             *
             * HH:mm:ss
             *
             * Example:
             * 19:40:00
             */

            if (timeText != null && timeText.length() == 5) {

                timeText = timeText + ":00";
            }

            Time appointmentTime =
                Time.valueOf(timeText);

            // Reason
            String reason =
                request.getParameter("reason");

            // Status
            String status =
                request.getParameter("status");

            // Default status
            if (status == null ||
                status.trim().isEmpty()) {

                status = "Scheduled";
            }

            // =========================
            // VALIDATION
            // =========================

            if (patientId <= 0 ||
                doctorId <= 0 ||
                reason == null ||
                reason.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-appointment.jsp?error=invalid"
                );

                return;
            }

            // =========================
            // CREATE APPOINTMENT
            // =========================

            Appointment appointment =
                new Appointment();

            appointment.setPatientId(patientId);

            appointment.setDoctorId(doctorId);

            appointment.setAppointmentDate(
                appointmentDate
            );

            appointment.setAppointmentTime(
                appointmentTime
            );

            appointment.setReason(
                reason.trim()
            );

            appointment.setStatus(
                status
            );

            // =========================
            // SAVE
            // =========================

            boolean success =
                appointmentDAO.addAppointment(
                    appointment
                );

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-appointment.jsp?error=failed"
                );
            }

        }

        // Invalid date/time/number
        catch (IllegalArgumentException e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/add-appointment.jsp?error=invalid"
            );

        }

        // Database or other error
        catch (Exception e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/add-appointment.jsp?error=failed"
            );
        }
    }

    // =========================
    // EDIT APPOINTMENT
    // =========================

    private void editAppointment(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        try {

            int id = Integer.parseInt(
                request.getParameter("id")
            );

            Appointment appointment =
                appointmentDAO.getAppointmentById(id);

            if (appointment == null) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=list"
                );

                return;
            }

            request.setAttribute(
                "appointment",
                appointment
            );

            request.getRequestDispatcher(
                "/edit-appointment.jsp"
            ).forward(request, response);

        }

        catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

    // =========================
    // UPDATE APPOINTMENT
    // =========================

    private void updateAppointment(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        try {

            // Appointment ID
            int id = Integer.parseInt(
                request.getParameter("id")
            );

            // Patient ID
            int patientId = Integer.parseInt(
                request.getParameter("patientId")
            );

            // Doctor ID
            int doctorId = Integer.parseInt(
                request.getParameter("doctorId")
            );

            // Date
            Date appointmentDate = Date.valueOf(
                request.getParameter("appointmentDate")
            );

            // Time
            String timeText =
                request.getParameter("appointmentTime");

            /*
             * HTML time input:
             *
             * HH:mm
             *
             * Convert to:
             *
             * HH:mm:ss
             */

            if (timeText != null &&
                timeText.length() == 5) {

                timeText = timeText + ":00";
            }

            Time appointmentTime =
                Time.valueOf(timeText);

            // Reason
            String reason =
                request.getParameter("reason");

            // Status
            String status =
                request.getParameter("status");

            // Default status
            if (status == null ||
                status.trim().isEmpty()) {

                status = "Scheduled";
            }

            // =========================
            // VALIDATION
            // =========================

            if (id <= 0 ||
                patientId <= 0 ||
                doctorId <= 0 ||
                reason == null ||
                reason.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=edit&id="
                    + id
                    + "&error=invalid"
                );

                return;
            }

            // =========================
            // CREATE APPOINTMENT
            // =========================

            Appointment appointment =
                new Appointment();

            appointment.setId(id);

            appointment.setPatientId(patientId);

            appointment.setDoctorId(doctorId);

            appointment.setAppointmentDate(
                appointmentDate
            );

            appointment.setAppointmentTime(
                appointmentTime
            );

            appointment.setReason(
                reason.trim()
            );

            appointment.setStatus(
                status
            );

            // =========================
            // UPDATE DATABASE
            // =========================

            boolean success =
                appointmentDAO.updateAppointment(
                    appointment
                );

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=edit&id="
                    + id
                    + "&error=failed"
                );
            }

        }

        catch (IllegalArgumentException e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );

        }

        catch (Exception e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

    // =========================
    // DELETE APPOINTMENT
    // =========================

    private void deleteAppointment(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        try {

            int id = Integer.parseInt(
                request.getParameter("id")
            );

            boolean success =
                appointmentDAO.deleteAppointment(id);

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=list&error=delete"
                );
            }

        }

        catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list&error=invalid"
            );
        }
    }

    // =========================
    // SEARCH APPOINTMENTS
    // =========================

    private void searchAppointments(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        String keyword =
            request.getParameter("keyword");

        if (keyword == null) {

            keyword = "";
        }

        List<Appointment> appointments =
            appointmentDAO.searchAppointments(
                keyword
            );

        request.setAttribute(
            "appointments",
            appointments
        );

        request.setAttribute(
            "searchKeyword",
            keyword
        );

        request.getRequestDispatcher(
            "/appointments.jsp"
        ).forward(request, response);
    }
}
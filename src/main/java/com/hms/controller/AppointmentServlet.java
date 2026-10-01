package com.hms.controller;

import java.io.IOException;
import java.sql.Date;
import java.sql.Time;
import java.util.List;

import com.hms.dao.AppointmentDAO;
import com.hms.model.Appointment;
import com.hms.model.User;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

@WebServlet("/AppointmentServlet")
public class AppointmentServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private AppointmentDAO appointmentDAO;

    @Override
    public void init() throws ServletException {
        appointmentDAO = new AppointmentDAO();
    }

    private User getLoggedInUser(HttpServletRequest request) {
        HttpSession session = request.getSession(false);

        if (session == null) {
            return null;
        }

        Object userObject = session.getAttribute("user");

        if (userObject instanceof User) {
            return (User) userObject;
        }

        return null;
    }

    private boolean isAdminOrReceptionist(User user) {
        return user != null &&
               ("ADMIN".equalsIgnoreCase(user.getRole()) ||
                "RECEPTIONIST".equalsIgnoreCase(user.getRole()));
    }

    private boolean isDoctor(User user) {
        return user != null &&
               "DOCTOR".equalsIgnoreCase(user.getRole());
    }

    private boolean isLoggedIn(User user) {
        return user != null;
    }

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        User user = getLoggedInUser(request);

        if (!isLoggedIn(user)) {
            response.sendRedirect(
                request.getContextPath() + "/login.jsp"
            );
            return;
        }

        String action = request.getParameter("action");

        if (action == null || "list".equals(action)) {

            listAppointments(request, response, user);

        } else if ("search".equals(action)) {

            searchAppointments(request, response, user);

        } else if ("edit".equals(action)) {

            if (!isAdminOrReceptionist(user)) {
                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=list&error=unauthorized"
                );
                return;
            }

            editAppointment(request, response);

        } else if ("delete".equals(action)) {

            if (!isAdminOrReceptionist(user)) {
                response.sendRedirect(
                    request.getContextPath()
                    + "/AppointmentServlet?action=list&error=unauthorized"
                );
                return;
            }

            deleteAppointment(request, response);

        } else {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

    @Override
    protected void doPost(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");
        response.setCharacterEncoding("UTF-8");

        User user = getLoggedInUser(request);

        if (!isLoggedIn(user)) {
            response.sendRedirect(
                request.getContextPath() + "/login.jsp"
            );
            return;
        }

        if (!isAdminOrReceptionist(user)) {
            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list&error=unauthorized"
            );
            return;
        }

        String action = request.getParameter("action");

        if ("add".equals(action)) {

            addAppointment(request, response);

        } else if ("update".equals(action)) {

            updateAppointment(request, response);

        } else {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

    private void listAppointments(
            HttpServletRequest request,
            HttpServletResponse response,
            User user)
            throws ServletException, IOException {

        List<Appointment> appointments;

        if (isDoctor(user) && user.getDoctorId() > 0) {

            appointments =
                appointmentDAO.getAllAppointments()
                    .stream()
                    .filter(a -> a.getDoctorId() == user.getDoctorId())
                    .toList();

        } else {

            appointments =
                appointmentDAO.getAllAppointments();
        }

        request.setAttribute(
            "appointments",
            appointments
        );

        request.getRequestDispatcher(
            "/appointments.jsp"
        ).forward(request, response);
    }

    private void addAppointment(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        try {

            int patientId = Integer.parseInt(
                request.getParameter("patientId")
            );

            int doctorId = Integer.parseInt(
                request.getParameter("doctorId")
            );

            String dateText =
                request.getParameter("appointmentDate");

            String timeText =
                request.getParameter("appointmentTime");

            String reason =
                request.getParameter("reason");

            if (patientId <= 0 ||
                doctorId <= 0 ||
                dateText == null ||
                dateText.trim().isEmpty() ||
                timeText == null ||
                timeText.trim().isEmpty() ||
                reason == null ||
                reason.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-appointment.jsp?error=invalid"
                );

                return;
            }

            Date appointmentDate =
                Date.valueOf(dateText.trim());

            timeText = timeText.trim();

            if (timeText.length() == 5) {
                timeText = timeText + ":00";
            }

            Time appointmentTime =
                Time.valueOf(timeText);

            String status =
                request.getParameter("status");

            if (status == null ||
                status.trim().isEmpty()) {

                status = "Scheduled";
            }

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

        } catch (IllegalArgumentException e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/add-appointment.jsp?error=invalid"
            );

        } catch (Exception e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/add-appointment.jsp?error=failed"
            );
        }
    }

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

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

    private void updateAppointment(
            HttpServletRequest request,
            HttpServletResponse response)
            throws IOException {

        try {

            int id = Integer.parseInt(
                request.getParameter("id")
            );

            int patientId = Integer.parseInt(
                request.getParameter("patientId")
            );

            int doctorId = Integer.parseInt(
                request.getParameter("doctorId")
            );

            String dateText =
                request.getParameter("appointmentDate");

            String timeText =
                request.getParameter("appointmentTime");

            String reason =
                request.getParameter("reason");

            String status =
                request.getParameter("status");

            if (id <= 0 ||
                patientId <= 0 ||
                doctorId <= 0 ||
                dateText == null ||
                dateText.trim().isEmpty() ||
                timeText == null ||
                timeText.trim().isEmpty() ||
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

            Date appointmentDate =
                Date.valueOf(dateText.trim());

            timeText = timeText.trim();

            if (timeText.length() == 5) {
                timeText = timeText + ":00";
            }

            Time appointmentTime =
                Time.valueOf(timeText);

            if (status == null ||
                status.trim().isEmpty()) {

                status = "Scheduled";
            }

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

        } catch (IllegalArgumentException e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );

        } catch (Exception e) {

            e.printStackTrace();

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list"
            );
        }
    }

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

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/AppointmentServlet?action=list&error=invalid"
            );
        }
    }

    private void searchAppointments(
            HttpServletRequest request,
            HttpServletResponse response,
            User user)
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

        if (isDoctor(user) && user.getDoctorId() > 0) {

            int doctorId = user.getDoctorId();

            appointments = appointments.stream()
                .filter(a -> a.getDoctorId() == doctorId)
                .toList();
        }

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
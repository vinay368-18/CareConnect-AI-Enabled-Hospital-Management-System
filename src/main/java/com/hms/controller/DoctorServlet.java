package com.hms.controller;

import java.io.IOException;
import java.util.List;

import com.hms.dao.DoctorDAO;
import com.hms.model.Doctor;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@WebServlet("/DoctorServlet")
public class DoctorServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private DoctorDAO doctorDAO;

    @Override
    public void init() throws ServletException {
        doctorDAO = new DoctorDAO();
    }


    // =========================
    // GET REQUESTS
    // =========================

    @Override
    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
            throws ServletException, IOException {

        String action = request.getParameter("action");

        // LIST
        if (action == null || action.equals("list")) {

            listDoctors(request, response);

        }

        // SEARCH
        else if ("search".equals(action)) {

            searchDoctors(request, response);

        }

        // EDIT
        else if ("edit".equals(action)) {

            try {

                int id = Integer.parseInt(
                    request.getParameter("id")
                );

                Doctor doctor =
                    doctorDAO.getDoctorById(id);

                if (doctor == null) {

                    response.sendRedirect(
                        request.getContextPath()
                        + "/DoctorServlet?action=list"
                    );

                    return;
                }

                request.setAttribute(
                    "doctor",
                    doctor
                );

                request.getRequestDispatcher(
                    "/edit-doctor.jsp"
                ).forward(request, response);

            } catch (NumberFormatException e) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );
            }
        }

        // DELETE
        else if ("delete".equals(action)) {

            deleteDoctor(request, response);

        }

        // UNKNOWN ACTION
        else {

            response.sendRedirect(
                request.getContextPath()
                + "/DoctorServlet?action=list"
            );
        }
    }


    // =========================
    // POST REQUESTS
    // =========================

    @Override
    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");
        response.setCharacterEncoding("UTF-8");

        String action = request.getParameter("action");

        // ADD
        if ("add".equals(action)) {

            addDoctor(request, response);

        }

        // UPDATE
        else if ("update".equals(action)) {

            updateDoctor(request, response);

        }

        // UNKNOWN ACTION
        else {

            response.sendRedirect(
                request.getContextPath()
                + "/DoctorServlet?action=list"
            );
        }
    }


    // =========================
    // LIST DOCTORS
    // =========================

    private void listDoctors(HttpServletRequest request,
                             HttpServletResponse response)
            throws ServletException, IOException {

        List<Doctor> doctors =
            doctorDAO.getAllDoctors();

        request.setAttribute(
            "doctors",
            doctors
        );

        request.getRequestDispatcher(
            "/doctors.jsp"
        ).forward(request, response);
    }


    // =========================
    // SEARCH DOCTORS
    // =========================

    private void searchDoctors(HttpServletRequest request,
                               HttpServletResponse response)
            throws ServletException, IOException {

        String keyword =
            request.getParameter("keyword");

        if (keyword == null) {
            keyword = "";
        }

        List<Doctor> doctors =
            doctorDAO.searchDoctors(keyword);

        request.setAttribute(
            "doctors",
            doctors
        );

        request.setAttribute(
            "searchKeyword",
            keyword
        );

        request.getRequestDispatcher(
            "/doctors.jsp"
        ).forward(request, response);
    }


    // =========================
    // ADD DOCTOR
    // =========================

    private void addDoctor(HttpServletRequest request,
                           HttpServletResponse response)
            throws IOException {

        String name =
            request.getParameter("name");

        String specialization =
            request.getParameter("specialization");

        String phone =
            request.getParameter("phone");

        String email =
            request.getParameter("email");

        String experienceText =
            request.getParameter("experience");

        String feeText =
            request.getParameter("consultationFee");

        if (name == null || name.trim().isEmpty() ||
            specialization == null || specialization.trim().isEmpty() ||
            experienceText == null || feeText == null) {

            response.sendRedirect(
                request.getContextPath()
                + "/add-doctor.jsp?error=invalid"
            );
            return;
        }

        try {

            int experience =
                Integer.parseInt(experienceText.trim());

            double consultationFee =
                Double.parseDouble(feeText.trim());

            // VALIDATION

            if (experience < 0 || experience > 70 || consultationFee < 0) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-doctor.jsp?error=invalid"
                );

                return;
            }

            Doctor doctor =
                new Doctor();

            doctor.setName(name);
            doctor.setSpecialization(specialization);
            doctor.setPhone(phone);
            doctor.setEmail(email);
            doctor.setExperience(experience);
            doctor.setConsultationFee(
                consultationFee
            );

            boolean success =
                doctorDAO.addDoctor(doctor);

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/add-doctor.jsp?error=failed"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/add-doctor.jsp?error=invalid"
            );
        }
    }


    // =========================
    // UPDATE DOCTOR
    // =========================

    private void updateDoctor(HttpServletRequest request,
                              HttpServletResponse response)
            throws IOException {

        try {

            int id =
                Integer.parseInt(
                    request.getParameter("id")
                );

            String name = request.getParameter("name");
            String specialization = request.getParameter("specialization");

            if (name == null || name.trim().isEmpty() ||
                specialization == null || specialization.trim().isEmpty()) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=edit&id="
                    + id
                    + "&error=invalid"
                );
                return;
            }

            int experience =
                Integer.parseInt(
                    request.getParameter("experience")
                );

            double consultationFee =
                Double.parseDouble(
                    request.getParameter("consultationFee")
                );

            // VALIDATION

            if (experience < 0 || experience > 70 || consultationFee < 0) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=edit&id="
                    + id
                    + "&error=invalid"
                );

                return;
            }

            Doctor doctor =
                new Doctor();

            doctor.setId(id);

            doctor.setName(
                request.getParameter("name")
            );

            doctor.setSpecialization(
                request.getParameter("specialization")
            );

            doctor.setPhone(
                request.getParameter("phone")
            );

            doctor.setEmail(
                request.getParameter("email")
            );

            doctor.setExperience(experience);

            doctor.setConsultationFee(
                consultationFee
            );

            boolean success =
                doctorDAO.updateDoctor(doctor);

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=edit&id="
                    + id
                    + "&error=failed"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/DoctorServlet?action=list"
            );
        }
    }


    // =========================
    // DELETE DOCTOR
    // =========================

    private void deleteDoctor(HttpServletRequest request,
                              HttpServletResponse response)
            throws IOException {

        try {

            int id =
                Integer.parseInt(
                    request.getParameter("id")
                );

            boolean success =
                doctorDAO.deleteDoctor(id);

            if (success) {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list"
                );

            } else {

                response.sendRedirect(
                    request.getContextPath()
                    + "/DoctorServlet?action=list&error=delete"
                );
            }

        } catch (NumberFormatException e) {

            response.sendRedirect(
                request.getContextPath()
                + "/DoctorServlet?action=list&error=invalid"
            );
        }
    }

}
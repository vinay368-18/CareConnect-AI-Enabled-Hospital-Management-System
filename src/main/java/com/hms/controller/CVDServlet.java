package com.hms.controller;

import com.hms.dao.CVDScreeningDAO;
import com.hms.dao.DoctorDAO;
import com.hms.dao.PatientDAO;
import com.hms.model.CVDScreening;
import com.hms.model.Doctor;
import com.hms.model.Patient;
import com.hms.model.User;
import com.hms.service.CVDClient;
import com.hms.util.CSRFUtil;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.MultipartConfig;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import jakarta.servlet.http.Part;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * Servlet controller for CVD AI Screening operations.
 *
 * AUDIT FIX (2026-11-07):
 * - Reads modelName from request parameter and passes to CVDClient + entity.
 * - Persists AI recommendation from Python response.
 */
@WebServlet("/CVDServlet")
@MultipartConfig(fileSizeThreshold = 1024 * 1024 * 2, // 2MB
        maxFileSize = 1024 * 1024 * 25, // 25MB
        maxRequestSize = 1024 * 1024 * 50 // 50MB
)
public class CVDServlet extends HttpServlet {

    private static final long serialVersionUID = 1L;

    private static final Set<String> ALLOWED_EXTENSIONS = new HashSet<>(
            Arrays.asList(".jpg", ".jpeg", ".png"));

    private final CVDScreeningDAO cvdDAO = new CVDScreeningDAO();
    private final PatientDAO patientDAO = new PatientDAO();
    private final DoctorDAO doctorDAO = new DoctorDAO();
    private final CVDClient cvdClient = new CVDClient();

    // ==========================================
    // AUTHENTICATION & AUTHORIZATION HELPERS
    // ==========================================

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

    private boolean checkAuthorized(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        User user = getLoggedInUser(request);
        if (user == null) {
            response.sendRedirect(request.getContextPath() + "/login.jsp?error=unauthorized");
            return false;
        }
        String role = user.getRole();
        if (!"ADMIN".equalsIgnoreCase(role) && !"DOCTOR".equalsIgnoreCase(role)
                && !"RECEPTIONIST".equalsIgnoreCase(role)) {
            response.sendRedirect(request.getContextPath() + "/dashboard.jsp?error=forbidden");
            return false;
        }
        return true;
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");
        response.setCharacterEncoding("UTF-8");

        if (!checkAuthorized(request, response)) {
            return;
        }

        String action = request.getParameter("action");
        if (action == null || action.trim().isEmpty()) {
            action = "list";
        }

        switch (action) {
            case "new":
                showNewScreeningForm(request, response);
                break;
            case "view":
                viewScreeningReport(request, response);
                break;
            case "delete":
                // Security: GET-based deletion is strictly disallowed
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&error=method_not_allowed");
                break;
            case "list":
            default:
                listScreenings(request, response);
                break;
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");
        response.setCharacterEncoding("UTF-8");

        if (!checkAuthorized(request, response)) {
            return;
        }

        String action = request.getParameter("action");
        if ("analyze".equalsIgnoreCase(action)) {
            if (!CSRFUtil.isValid(request)) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&error=csrf");
                return;
            }
            analyzeFundusScan(request, response);
        } else if ("delete".equalsIgnoreCase(action)) {
            if (!CSRFUtil.isValid(request)) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&error=csrf");
                return;
            }
            deleteScreening(request, response);
        } else {
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list");
        }
    }

    private void listScreenings(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        List<CVDScreening> screenings = cvdDAO.getAllScreenings();
        boolean isAiOnline = cvdClient.isServiceAvailable();

        request.setAttribute("screenings", screenings);
        request.setAttribute("isAiOnline", isAiOnline);
        request.setAttribute("totalCount", cvdDAO.getTotalScreeningsCount());
        request.setAttribute("highRiskCount", cvdDAO.getHighRiskCount());

        request.getRequestDispatcher("/cvd-screenings.jsp").forward(request, response);
    }

    private void showNewScreeningForm(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        List<Patient> patients = patientDAO.getAllPatients();
        List<Doctor> doctors = doctorDAO.getAllDoctors();
        boolean isAiOnline = cvdClient.isServiceAvailable();

        request.setAttribute("patients", patients);
        request.setAttribute("doctors", doctors);
        request.setAttribute("isAiOnline", isAiOnline);

        String preselectedPatientId = request.getParameter("patientId");
        if (preselectedPatientId != null && !preselectedPatientId.trim().isEmpty()) {
            try {
                int pid = Integer.parseInt(preselectedPatientId.trim());
                Patient p = patientDAO.getPatientById(pid);
                if (p != null) {
                    request.setAttribute("preselectedPatientId", String.valueOf(pid));
                }
            } catch (NumberFormatException ignored) {
            }
        }

        request.getRequestDispatcher("/new-screening.jsp").forward(request, response);
    }

    private void viewScreeningReport(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        try {
            int id = Integer.parseInt(request.getParameter("id"));
            CVDScreening screening = cvdDAO.getScreeningById(id);

            if (screening == null) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&error=not_found");
                return;
            }

            request.setAttribute("screening", screening);
            request.getRequestDispatcher("/cvd-report.jsp").forward(request, response);

        } catch (NumberFormatException e) {
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list");
        }
    }

    private void deleteScreening(HttpServletRequest request, HttpServletResponse response)
            throws IOException {

        User user = getLoggedInUser(request);
        if (user == null || (!"ADMIN".equalsIgnoreCase(user.getRole()) && !"DOCTOR".equalsIgnoreCase(user.getRole()))) {
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&error=unauthorized_delete");
            return;
        }

        try {
            int id = Integer.parseInt(request.getParameter("id"));
            CVDScreening screening = cvdDAO.getScreeningById(id);
            if (screening == null) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&error=not_found");
                return;
            }

            if ("DOCTOR".equalsIgnoreCase(user.getRole()) && user.getDoctorId() > 0) {
                if (screening.getDoctorId() == null || screening.getDoctorId() != user.getDoctorId()) {
                    response.sendRedirect(
                            request.getContextPath() + "/CVDServlet?action=list&error=unauthorized_delete");
                    return;
                }
            }

            cvdDAO.deleteScreening(id);
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&msg=deleted");
        } catch (NumberFormatException e) {
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list");
        }
    }

    /**
     * Vessel segmentation with selected model. Optional: any failure is logged and
     * the screening is kept.
     */
    private void runVesselSegmentation(int screeningId, byte[] imageBytes, String savedFilename, String modelName) {
        try {
            String name = savedFilename != null ? savedFilename : "scan.jpg";
            CVDClient.VesselResult vessels = cvdClient.segmentVessels(imageBytes, name, modelName);

            String baseName = Paths.get(name).getFileName().toString();
            int dot = baseName.lastIndexOf('.');
            if (dot > 0) {
                baseName = baseName.substring(0, dot);
            }
            String overlayName = "vessel_" + baseName + ".png";

            String uploadPath = getServletContext().getRealPath("/uploads/fundus");
            Path uploadDirPath = (uploadPath != null)
                    ? Path.of(uploadPath)
                    : Path.of("src", "main", "webapp", "uploads", "fundus").toAbsolutePath();

            if (!Files.exists(uploadDirPath)) {
                Files.createDirectories(uploadDirPath);
            }
            Files.write(uploadDirPath.resolve(overlayName), vessels.getOverlayPng());

            cvdDAO.updateVesselResult(screeningId, "uploads/fundus/" + overlayName, vessels.getDensityPercent());
        } catch (Exception e) {
            System.err.println("[CVD] Vessel segmentation skipped: " + e.getMessage());
        }
    }

    private void analyzeFundusScan(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        User currentUser = getLoggedInUser(request);

        try {
            String patientIdStr = request.getParameter("patientId");
            if (patientIdStr == null || patientIdStr.trim().isEmpty()) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&error=invalid_patient");
                return;
            }
            int patientId = Integer.parseInt(patientIdStr.trim());

            Patient targetPatient = patientDAO.getPatientById(patientId);
            if (targetPatient == null) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&error=invalid_patient");
                return;
            }

            String doctorIdStr = request.getParameter("doctorId");
            Integer doctorId = null;
            if (currentUser != null && "DOCTOR".equalsIgnoreCase(currentUser.getRole())
                    && currentUser.getDoctorId() > 0) {
                doctorId = currentUser.getDoctorId();
            } else if (doctorIdStr != null && !doctorIdStr.trim().isEmpty()) {
                doctorId = Integer.parseInt(doctorIdStr.trim());
                Doctor d = doctorDAO.getDoctorById(doctorId);
                if (d == null) {
                    doctorId = null;
                }
            }

            String appointmentIdStr = request.getParameter("appointmentId");
            Integer appointmentId = (appointmentIdStr != null && !appointmentIdStr.trim().isEmpty())
                    ? Integer.parseInt(appointmentIdStr.trim())
                    : null;

            String notes = request.getParameter("notes");
            String sampleImage = request.getParameter("sampleImage");

            String modelName = request.getParameter("modelName");
            if (modelName == null || modelName.trim().isEmpty()) {
                modelName = "Residual U-Net";
            }

            byte[] imageBytes = null;
            String savedFilename = null;

            Part filePart = null;
            try {
                filePart = request.getPart("fundusImage");
            } catch (Exception ignored) {
            }

            if (filePart != null && filePart.getSize() > 0 && filePart.getSubmittedFileName() != null
                    && !filePart.getSubmittedFileName().trim().isEmpty()) {

                String rawFileName = Paths.get(filePart.getSubmittedFileName()).getFileName().toString();
                String ext = ".jpg";
                if (rawFileName.contains(".")) {
                    ext = rawFileName.substring(rawFileName.lastIndexOf(".")).toLowerCase();
                }

                if (!ALLOWED_EXTENSIONS.contains(ext)) {
                    response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&patientId=" + patientId
                            + "&error=invalid_file_type");
                    return;
                }

                savedFilename = "fundus_" + UUID.randomUUID().toString().substring(0, 8) + "_"
                        + System.currentTimeMillis() + ext;

                String uploadPath = getServletContext().getRealPath("/uploads/fundus");
                Path uploadDirPath = (uploadPath != null)
                        ? Path.of(uploadPath)
                        : Path.of("src", "main", "webapp", "uploads", "fundus").toAbsolutePath();

                if (!Files.exists(uploadDirPath)) {
                    Files.createDirectories(uploadDirPath);
                }

                Path destinationFile = uploadDirPath.resolve(savedFilename);
                try (InputStream input = filePart.getInputStream()) {
                    Files.copy(input, destinationFile, StandardCopyOption.REPLACE_EXISTING);
                }

                imageBytes = Files.readAllBytes(destinationFile);

            } else if (sampleImage != null && !sampleImage.trim().isEmpty()) {
                String cleanSample = Paths.get(sampleImage).getFileName().toString();
                String sampleRealPath = getServletContext().getRealPath("/uploads/fundus/samples/" + cleanSample);
                Path samplePath = (sampleRealPath != null) ? Path.of(sampleRealPath) : null;

                if (samplePath == null || !Files.exists(samplePath)) {
                    samplePath = Path.of("src", "main", "webapp", "uploads", "fundus", "samples", cleanSample);
                }

                if (Files.exists(samplePath)) {
                    imageBytes = Files.readAllBytes(samplePath);
                    savedFilename = "samples/" + cleanSample;
                }
            }

            if (imageBytes == null || imageBytes.length == 0) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&patientId=" + patientId
                        + "&error=missing_image");
                return;
            }

            if (!cvdClient.isServiceAvailable()) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&patientId=" + patientId
                        + "&error=ai_offline");
                return;
            }

            CVDScreening screeningResult;
            try {
                screeningResult = cvdClient.analyzeImage(imageBytes,
                        savedFilename != null ? savedFilename : "scan.jpg",
                        modelName);
            } catch (IOException e) {
                if (e.getMessage() != null && e.getMessage().contains("HTTP 400")) {
                    response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&patientId=" + patientId
                            + "&error=corrupt_image");
                    return;
                }
                throw e;
            }

            screeningResult.setPatientId(patientId);
            screeningResult.setDoctorId(doctorId);
            screeningResult.setAppointmentId(appointmentId);
            screeningResult.setImagePath("uploads/fundus/" + savedFilename);
            screeningResult.setNotes(notes);

            if (screeningResult.getModelName() == null || screeningResult.getModelName().trim().isEmpty()) {
                screeningResult.setModelName(modelName);
            }

            int savedId = cvdDAO.saveScreening(screeningResult);

            if (savedId > 0) {
                runVesselSegmentation(savedId, imageBytes, savedFilename, modelName);
                response.sendRedirect(
                        request.getContextPath() + "/CVDServlet?action=view&id=" + savedId + "&msg=analyzed");
            } else {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&error=save_failed");
            }

        } catch (Exception e) {
            e.printStackTrace();
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&error=processing_error");
        }
    }
}

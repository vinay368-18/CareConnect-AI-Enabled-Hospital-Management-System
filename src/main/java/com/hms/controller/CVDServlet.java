package com.hms.controller;

import com.hms.dao.AppointmentDAO;
import com.hms.dao.CVDScreeningDAO;
import com.hms.dao.DoctorDAO;
import com.hms.dao.PatientDAO;
import com.hms.model.CVDScreening;
import com.hms.model.Doctor;
import com.hms.model.Patient;
import com.hms.service.CVDClient;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.MultipartConfig;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.Part;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.UUID;

@WebServlet("/CVDServlet")
@MultipartConfig(
        fileSizeThreshold = 1024 * 1024 * 2,  // 2MB
        maxFileSize = 1024 * 1024 * 25,        // 25MB
        maxRequestSize = 1024 * 1024 * 50      // 50MB
)
public class CVDServlet extends HttpServlet {

    private final CVDScreeningDAO cvdDAO = new CVDScreeningDAO();
    private final PatientDAO patientDAO = new PatientDAO();
    private final DoctorDAO doctorDAO = new DoctorDAO();
    private final CVDClient cvdClient = new CVDClient();

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        request.setCharacterEncoding("UTF-8");
        response.setCharacterEncoding("UTF-8");

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
                deleteScreening(request, response);
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

        String action = request.getParameter("action");
        if ("analyze".equalsIgnoreCase(action)) {
            analyzeFundusScan(request, response);
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
        if (preselectedPatientId != null) {
            request.setAttribute("preselectedPatientId", preselectedPatientId);
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

        try {
            int id = Integer.parseInt(request.getParameter("id"));
            cvdDAO.deleteScreening(id);
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&msg=deleted");
        } catch (NumberFormatException e) {
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list");
        }
    }

    /**
     * Residual U-Net vessel segmentation. Optional: any failure is logged and the screening is kept as it is.
     */
    private void runVesselSegmentation(int screeningId, byte[] imageBytes, String savedFilename) {
        try {
            String name = savedFilename != null ? savedFilename : "scan.jpg";
            CVDClient.VesselResult vessels = cvdClient.segmentVessels(imageBytes, name);

            String baseName = Paths.get(name).getFileName().toString();
            int dot = baseName.lastIndexOf('.');
            if (dot > 0) {
                baseName = baseName.substring(0, dot);
            }
            String overlayName = "vessel_" + baseName + ".png";

            String uploadPath = getServletContext().getRealPath("/uploads/fundus");
            if (uploadPath == null) {
                uploadPath = new File("src/main/webapp/uploads/fundus").getAbsolutePath();
            }
            File uploadDir = new File(uploadPath);
            if (!uploadDir.exists()) {
                uploadDir.mkdirs();
            }
            Files.write(new File(uploadDir, overlayName).toPath(), vessels.getOverlayPng());

            cvdDAO.updateVesselResult(screeningId, "uploads/fundus/" + overlayName, vessels.getDensityPercent());
        } catch (Exception e) {
            System.err.println("[CVD] Vessel segmentation skipped: " + e.getMessage());
        }
    }

    private void analyzeFundusScan(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        try {
            int patientId = Integer.parseInt(request.getParameter("patientId"));
            String doctorIdStr = request.getParameter("doctorId");
            Integer doctorId = (doctorIdStr != null && !doctorIdStr.trim().isEmpty())
                    ? Integer.parseInt(doctorIdStr) : null;

            String appointmentIdStr = request.getParameter("appointmentId");
            Integer appointmentId = (appointmentIdStr != null && !appointmentIdStr.trim().isEmpty())
                    ? Integer.parseInt(appointmentIdStr) : null;

            String notes = request.getParameter("notes");
            String sampleImage = request.getParameter("sampleImage");

            byte[] imageBytes = null;
            String savedFilename = null;

            Part filePart = request.getPart("fundusImage");

            if (filePart != null && filePart.getSize() > 0 && filePart.getSubmittedFileName() != null
                    && !filePart.getSubmittedFileName().trim().isEmpty()) {

                String originalFileName = Paths.get(filePart.getSubmittedFileName()).getFileName().toString();
                String ext = ".jpg";
                if (originalFileName.contains(".")) {
                    ext = originalFileName.substring(originalFileName.lastIndexOf("."));
                }

                savedFilename = "fundus_" + UUID.randomUUID().toString().substring(0, 8) + "_" + System.currentTimeMillis() + ext;

                // Save to webapp uploads folder
                String uploadPath = getServletContext().getRealPath("/uploads/fundus");
                if (uploadPath == null) {
                    uploadPath = new File("src/main/webapp/uploads/fundus").getAbsolutePath();
                }
                File uploadDir = new File(uploadPath);
                if (!uploadDir.exists()) {
                    uploadDir.mkdirs();
                }

                File destinationFile = new File(uploadDir, savedFilename);
                try (InputStream input = filePart.getInputStream()) {
                    Files.copy(input, destinationFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                }

                imageBytes = Files.readAllBytes(destinationFile.toPath());

            } else if (sampleImage != null && !sampleImage.trim().isEmpty()) {
                // Use bundled sample image
                String sampleRealPath = getServletContext().getRealPath("/uploads/fundus/samples/" + sampleImage);
                File sampleFile = (sampleRealPath != null) ? new File(sampleRealPath) : null;

                if (sampleFile == null || !sampleFile.exists()) {
                    sampleFile = new File("src/main/webapp/uploads/fundus/samples/" + sampleImage);
                }

                if (sampleFile.exists()) {
                    imageBytes = Files.readAllBytes(sampleFile.toPath());
                    savedFilename = "samples/" + sampleImage;
                }
            }

            if (imageBytes == null || imageBytes.length == 0) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&patientId=" + patientId + "&error=missing_image");
                return;
            }

            // Check if Python PyTorch AI microservice is reachable
            if (!cvdClient.isServiceAvailable()) {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&patientId=" + patientId + "&error=ai_offline");
                return;
            }

            // Call Python PyTorch AI Microservice
            CVDScreening screeningResult = cvdClient.analyzeImage(imageBytes, savedFilename != null ? savedFilename : "scan.jpg");

            // Fill metadata
            screeningResult.setPatientId(patientId);
            screeningResult.setDoctorId(doctorId);
            screeningResult.setAppointmentId(appointmentId);
            screeningResult.setImagePath("uploads/fundus/" + savedFilename);
            screeningResult.setNotes(notes);

            // Persist into MySQL
            int savedId = cvdDAO.saveScreening(screeningResult);

            if (savedId > 0) {
                runVesselSegmentation(savedId, imageBytes, savedFilename);
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=view&id=" + savedId + "&msg=analyzed");
            } else {
                response.sendRedirect(request.getContextPath() + "/CVDServlet?action=list&error=save_failed");
            }

        } catch (Exception e) {
            e.printStackTrace();
            response.sendRedirect(request.getContextPath() + "/CVDServlet?action=new&error=processing_error");
        }
    }
}

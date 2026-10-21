package com.hms.test;

import com.hms.dao.CVDScreeningDAO;
import com.hms.dao.PatientDAO;
import com.hms.model.CVDScreening;
import com.hms.model.Patient;
import com.hms.service.CVDClient;

import java.io.File;
import java.nio.file.Files;
import java.util.List;

/**
 * End-to-End Live Integration Test:
 * Tests Java CVDClient communicating with running Python FastAPI microservice
 * on http://127.0.0.1:5000 and persisting results in MySQL database.
 */
public class EndToEndServiceTest {

    public static void main(String[] args) {
        System.out.println("=========================================================");
        System.out.println(" CARECONNECT HMS: END-TO-END LIVE SERVICE TEST");
        System.out.println("=========================================================");

        CVDClient client = new CVDClient("http://127.0.0.1:5000");

        System.out.print("[E2E] Checking AI Microservice /health ... ");
        boolean available = client.isServiceAvailable();
        if (!available) {
            System.out.println("OFFLINE (Microservice not running on port 5000)");
            System.out.println("[E2E] Please start Python service: python cvd-ai-service/api_server.py");
            System.exit(2);
        }
        System.out.println("ONLINE & HEALTHY");

        File sampleFile = new File("src/main/webapp/uploads/fundus/samples/img00330.jpg");
        if (!sampleFile.exists()) {
            System.err.println("[E2E] Sample image not found at: " + sampleFile.getAbsolutePath());
            System.exit(1);
        }

        try {
            System.out.print("[E2E] Reading sample retinal image bytes ... ");
            byte[] imageBytes = Files.readAllBytes(sampleFile.toPath());
            System.out.println(imageBytes.length + " bytes loaded.");

            System.out.print("[E2E] Sending image to Python /predict endpoint ... ");
            long t0 = System.currentTimeMillis();
            CVDScreening screening = client.analyzeImage(imageBytes, "img00330.jpg");
            long elapsed = System.currentTimeMillis() - t0;
            System.out.println("COMPLETED in " + elapsed + " ms");

            System.out.println("\n--- AI PREDICTION RESULTS ---");
            System.out.println("Vascular Disease (CVD): " + screening.getCvdPrediction() + " (Prob: " + screening.getCvdProbability() + ", Percent: " + screening.getCvdPercent() + "%)");
            System.out.println("Systemic Hypertension:  " + screening.getHypertensionPrediction() + " (Prob: " + screening.getHypertensionProbability() + ", Percent: " + screening.getHypertensionPercent() + "%)");
            System.out.println("Diabetic Retinopathy:   " + screening.getDrGrade() + " (Confidence: " + screening.getDrConfidence() + ")");
            System.out.println("Assessment Status:      " + screening.getRiskLevel());
            System.out.println("Clinical Direction:     " + screening.getRecommendation());
            System.out.println("-----------------------------\n");

            // Verify non-trivial values
            if (screening.getCvdProbability() < 0.0 || screening.getCvdProbability() > 1.0) {
                throw new AssertionError("Invalid CVD probability: " + screening.getCvdProbability());
            }
            if (screening.getDrGrade() == null || screening.getDrGrade().trim().isEmpty()) {
                throw new AssertionError("DR grade should not be empty");
            }

            // Test Database Persistence
            System.out.print("[E2E] Testing database persistence ... ");
            PatientDAO patientDAO = new PatientDAO();
            List<Patient> patients = patientDAO.getAllPatients();
            int patientId = (patients != null && !patients.isEmpty()) ? patients.get(0).getId() : 1;

            screening.setPatientId(patientId);
            screening.setImagePath("uploads/fundus/samples/img00330.jpg");
            screening.setNotes("End-to-End automated validation screening test record.");

            CVDScreeningDAO cvdDAO = new CVDScreeningDAO();
            int savedId = cvdDAO.saveScreening(screening);
            if (savedId <= 0) {
                throw new AssertionError("Failed to persist screening to MySQL database");
            }
            System.out.println("SAVED as Screening ID #" + savedId);

            // Verify retrieval
            System.out.print("[E2E] Verifying screening retrieval from DB ... ");
            CVDScreening retrieved = cvdDAO.getScreeningById(savedId);
            if (retrieved == null) {
                throw new AssertionError("Could not retrieve screening #" + savedId + " from database");
            }
            if (!retrieved.getDrGrade().equals(screening.getDrGrade())) {
                throw new AssertionError("Retrieved DR grade mismatch");
            }
            System.out.println("VERIFIED OK");

            // Clean up test screening record
            System.out.print("[E2E] Cleaning up test screening record #" + savedId + " ... ");
            boolean deleted = cvdDAO.deleteScreening(savedId);
            if (!deleted) {
                System.out.println("WARNING: Could not delete test screening");
            } else {
                System.out.println("DELETED OK");
            }

            System.out.println("\n=========================================================");
            System.out.println(" END-TO-END SERVICE INTEGRATION TEST PASSED SUCCESSFULLY!");
            System.out.println("=========================================================");
            System.exit(0);

        } catch (Exception e) {
            System.err.println("\n[E2E] TEST FAILED WITH EXCEPTION: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}

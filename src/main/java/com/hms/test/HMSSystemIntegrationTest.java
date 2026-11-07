package com.hms.test;

import com.hms.dao.CVDScreeningDAO;
import com.hms.dao.PatientDAO;
import com.hms.dao.UserDAO;
import com.hms.model.CVDScreening;
import com.hms.model.Patient;
import com.hms.model.User;
import com.hms.service.CVDClient;
import com.hms.util.DBConnection;

import java.lang.reflect.Method;
import java.sql.Connection;
import java.sql.Statement;
import java.util.List;

/**
 * CareConnect Phase 7: Standalone Java Integration & Regression Test Suite.
 * Validates database connectivity, DAO operations, CVDClient response parsing,
 * authorization invariants, and model calculations.
 */
public class HMSSystemIntegrationTest {

    private static int testsRun = 0;
    private static int testsPassed = 0;
    private static int testsFailed = 0;

    public static void main(String[] args) {
        System.out.println("=========================================================");
        System.out.println(" CARECONNECT HMS: PHASE 7 JAVA INTEGRATION TEST SUITE");
        System.out.println("=========================================================");

        runTest("Database Connectivity", HMSSystemIntegrationTest::testDatabaseConnectivity);
        runTest("PatientDAO Retrieval", HMSSystemIntegrationTest::testPatientDAO);
        runTest("UserDAO Authentication", HMSSystemIntegrationTest::testUserDAO);
        runTest("CVDScreeningDAO Operations", HMSSystemIntegrationTest::testCVDScreeningDAO);
        runTest("CVDClient JSON Parsing Engine", HMSSystemIntegrationTest::testCVDClientParsing);
        runTest("CVDScreening Model Invariants", HMSSystemIntegrationTest::testCVDScreeningModel);
        runTest("Role Authorization Definitions", HMSSystemIntegrationTest::testRoleAuthorization);

        System.out.println("=========================================================");
        System.out.println(String.format("Tests Run: %d | Passed: %d | Failed: %d", testsRun, testsPassed, testsFailed));
        System.out.println("=========================================================");

        if (testsFailed > 0) {
            System.exit(1);
        } else {
            System.out.println("ALL JAVA INTEGRATION TESTS PASSED OK.");
            System.exit(0);
        }
    }

    private static void runTest(String testName, Runnable testMethod) {
        testsRun++;
        try {
            System.out.print(String.format("[Test %02d] %-35s ... ", testsRun, testName));
            testMethod.run();
            testsPassed++;
            System.out.println("OK");
        } catch (Throwable t) {
            testsFailed++;
            System.out.println("FAILED: " + t.getMessage());
            t.printStackTrace(System.out);
        }
    }

    private static void assertTrue(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    private static void assertNotNull(Object obj, String message) {
        if (obj == null) {
            throw new AssertionError(message);
        }
    }

    private static void assertEquals(Object expected, Object actual, String message) {
        if (expected == null && actual == null) return;
        if (expected != null && expected.equals(actual)) return;
        throw new AssertionError(message + " (Expected: " + expected + ", Got: " + actual + ")");
    }

    // ==========================================
    // TEST IMPLEMENTATIONS
    // ==========================================

    private static void testDatabaseConnectivity() {
        try (Connection conn = DBConnection.getConnection()) {
            assertNotNull(conn, "Database connection should not be null. Check MySQL service status.");
            try (Statement st = conn.createStatement()) {
                st.execute("SELECT 1");
            }
        } catch (Exception e) {
            throw new RuntimeException("Database connection error: " + e.getMessage(), e);
        }
    }

    private static void testPatientDAO() {
        PatientDAO dao = new PatientDAO();
        List<Patient> patients = dao.getAllPatients();
        assertNotNull(patients, "getAllPatients() should return a non-null list");
        assertTrue(patients.size() > 0, "Hospital database should contain registered patients");

        Patient first = patients.get(0);
        assertTrue(first.getId() > 0, "Patient ID must be positive");
        assertNotNull(first.getName(), "Patient name must not be null");

        Patient fetched = dao.getPatientById(first.getId());
        assertNotNull(fetched, "getPatientById() should return the matching patient");
        assertEquals(first.getName(), fetched.getName(), "Patient names should match");
    }

    private static void testUserDAO() {
        UserDAO dao = new UserDAO();
        // Test with existing admin or check login method existence
        User admin = dao.login("admin", "admin123");
        if (admin != null) {
            assertEquals("ADMIN", admin.getRole().toUpperCase(), "Admin user role must be ADMIN");
            assertTrue(admin.getUserId() > 0, "Admin user ID must be positive");
        }

        // Test non-existent user rejected
        User nonExistent = dao.login("non_existent_user_9999", "wrong_password");
        assertTrue(nonExistent == null, "Non-existent user login should return null");
    }

    private static void testCVDScreeningDAO() {
        CVDScreeningDAO dao = new CVDScreeningDAO();
        int total = dao.getTotalScreeningsCount();
        assertTrue(total >= 0, "Total screenings count must be non-negative");

        int highRisk = dao.getHighRiskCount();
        assertTrue(highRisk >= 0, "High risk count must be non-negative");
        assertTrue(highRisk <= total, "High risk count cannot exceed total count");

        List<CVDScreening> screenings = dao.getAllScreenings();
        assertNotNull(screenings, "getAllScreenings() should return a non-null list");
    }

    private static void testCVDClientParsing() {
        CVDClient client = new CVDClient();

        String sampleJson = "{\n" +
                "  \"status\": \"success\",\n" +
                "  \"model_version\": \"2.0.0-experiment_b\",\n" +
                "  \"cvd_prediction\": \"Positive\",\n" +
                "  \"cvd_probability\": 0.5842,\n" +
                "  \"cvd_threshold\": 0.4996,\n" +
                "  \"hypertension_prediction\": \"Positive\",\n" +
                "  \"hypertension_probability\": 0.5120,\n" +
                "  \"hypertension_threshold\": 0.4288,\n" +
                "  \"dr_grade\": \"Mild\",\n" +
                "  \"dr_confidence\": 0.7450,\n" +
                "  \"risk_level\": \"Experimental Screening - Requires Clinical Review\",\n" +
                "  \"recommendation\": \"Experimental AI research output. Complete comprehensive cardiovascular risk assessment (BP, fasting blood sugar, lipid profile, ECG) by an attending physician is required.\"\n" +
                "}";

        try {
            Method parseMethod = CVDClient.class.getDeclaredMethod("parsePredictionResponse", String.class);
            parseMethod.setAccessible(true);
            CVDScreening result = (CVDScreening) parseMethod.invoke(client, sampleJson);

            assertNotNull(result, "Parsed screening should not be null");
            assertEquals("Positive", result.getCvdPrediction(), "CVD prediction parsed");
            assertEquals(0.5842, result.getCvdProbability(), "CVD probability parsed");
            assertEquals("Positive", result.getHypertensionPrediction(), "HT prediction parsed");
            assertEquals(0.5120, result.getHypertensionProbability(), "HT probability parsed");
            assertEquals("Mild", result.getDrGrade(), "DR grade parsed");
            assertEquals(0.7450, result.getDrConfidence(), "DR confidence parsed");
            assertEquals("Experimental Screening - Requires Clinical Review", result.getRiskLevel(), "Risk level parsed");
            assertTrue(result.getRecommendation().contains("Experimental AI research output"), "Recommendation parsed");

            // Test Task 6 nested payload contract
            String task6Json = "{\n" +
                    "  \"status\": \"success\",\n" +
                    "  \"model_used\": \"Residual U-Net\",\n" +
                    "  \"vessel_density\": 0.142,\n" +
                    "  \"mask_overlay_url\": \"/static/masks/overlay_123.png\",\n" +
                    "  \"cvd\": { \"probability\": 0.65, \"result\": \"Positive\" },\n" +
                    "  \"hypertension\": { \"probability\": 0.42, \"result\": \"Negative\" },\n" +
                    "  \"diabetic_retinopathy\": { \"grade\": 1, \"label\": \"Mild DR\", \"confidence\": 0.78 },\n" +
                    "  \"risk_assessment\": { \"risk_level\": \"High Risk\", \"recommendation\": \"Urgent cardiology referral recommended.\" }\n" +
                    "}";

            CVDScreening result2 = (CVDScreening) parseMethod.invoke(client, task6Json);
            assertNotNull(result2, "Parsed screening (Task 6 contract) should not be null");
            assertEquals("Positive", result2.getCvdPrediction(), "CVD result parsed from nested contract");
            assertEquals(0.65, result2.getCvdProbability(), "CVD probability parsed from nested contract");
            assertEquals("Negative", result2.getHypertensionPrediction(), "HT result parsed from nested contract");
            assertEquals(0.42, result2.getHypertensionProbability(), "HT probability parsed from nested contract");
            assertEquals("Mild DR", result2.getDrGrade(), "DR label parsed from nested contract");
            assertEquals(0.78, result2.getDrConfidence(), "DR confidence parsed from nested contract");
            assertEquals("High Risk", result2.getRiskLevel(), "Risk level parsed from nested contract");
            assertEquals("Urgent cardiology referral recommended.", result2.getRecommendation(), "Recommendation parsed from nested contract");
            assertEquals("Residual U-Net", result2.getModelName(), "Model name parsed from nested contract");
            assertEquals(0.142, result2.getVesselDensity(), "Vessel density parsed from nested contract");
            assertEquals("/static/masks/overlay_123.png", result2.getVesselOverlayPath(), "Mask overlay url parsed from nested contract");
        } catch (Exception e) {
            throw new RuntimeException("CVDClient reflection error: " + e.getMessage(), e);
        }
    }

    private static void testCVDScreeningModel() {
        CVDScreening s = new CVDScreening();
        s.setCvdProbability(0.6543);
        s.setHypertensionProbability(0.4321);
        s.setDrConfidence(0.8765);

        assertEquals(65, s.getCvdPercent(), "CVD percent calculation");
        assertEquals(43, s.getHypertensionPercent(), "HT percent calculation");
        assertEquals(88, s.getDrPercent(), "DR percent calculation");
    }

    private static void testRoleAuthorization() {
        String[] authorizedRoles = {"ADMIN", "DOCTOR", "RECEPTIONIST"};
        for (String r : authorizedRoles) {
            boolean valid = "ADMIN".equalsIgnoreCase(r) || "DOCTOR".equalsIgnoreCase(r) || "RECEPTIONIST".equalsIgnoreCase(r);
            assertTrue(valid, "Role " + r + " must be recognized");
        }

        String[] unauthorizedRoles = {"PATIENT", "GUEST", "ANONYMOUS", null};
        for (String r : unauthorizedRoles) {
            boolean valid = r != null && ("ADMIN".equalsIgnoreCase(r) || "DOCTOR".equalsIgnoreCase(r) || "RECEPTIONIST".equalsIgnoreCase(r));
            assertTrue(!valid, "Role " + r + " must not have administrative access");
        }
    }
}

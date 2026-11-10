package com.hms.dao;

import com.hms.model.CVDScreening;
import com.hms.util.DBConnection;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Data Access Object for CVD Screening records.
 *
 * AUDIT FIX (2026-11-07):
 * - Added model_name and recommendation columns to INSERT.
 * - mapResultSetToScreening reads model_name and recommendation from DB;
 *   only falls back to default recommendation if stored value is null/empty.
 */
public class CVDScreeningDAO {

    public int saveScreening(CVDScreening screening) {
        String sql = "INSERT INTO cvd_screenings "
                   + "(patient_id, doctor_id, appointment_id, image_path, model_name, "
                   + "cvd_prediction, cvd_probability, hypertension_prediction, hypertension_probability, "
                   + "dr_grade, dr_confidence, risk_level, recommendation, notes) "
                   + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

        int generatedId = -1;

        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {

            ps.setInt(1, screening.getPatientId());

            if (screening.getDoctorId() != null && screening.getDoctorId() > 0) {
                ps.setInt(2, screening.getDoctorId());
            } else {
                ps.setNull(2, Types.INTEGER);
            }

            if (screening.getAppointmentId() != null && screening.getAppointmentId() > 0) {
                ps.setInt(3, screening.getAppointmentId());
            } else {
                ps.setNull(3, Types.INTEGER);
            }

            ps.setString(4, screening.getImagePath());
            ps.setString(5, screening.getModelName());
            ps.setString(6, screening.getCvdPrediction());
            ps.setDouble(7, screening.getCvdProbability());
            ps.setString(8, screening.getHypertensionPrediction());
            ps.setDouble(9, screening.getHypertensionProbability());
            ps.setString(10, screening.getDrGrade());
            ps.setDouble(11, screening.getDrConfidence());
            ps.setString(12, screening.getRiskLevel());
            ps.setString(13, screening.getRecommendation());
            ps.setString(14, screening.getNotes());

            int affected = ps.executeUpdate();
            if (affected > 0) {
                try (ResultSet rs = ps.getGeneratedKeys()) {
                    if (rs.next()) {
                        generatedId = rs.getInt(1);
                    }
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return generatedId;
    }

    public CVDScreening getScreeningById(int id) {
        String sql = "SELECT s.*, "
                   + "p.name AS patient_name, p.age AS patient_age, p.gender AS patient_gender, p.phone AS patient_phone, "
                   + "d.name AS doctor_name, d.specialization AS doctor_spec "
                   + "FROM cvd_screenings s "
                   + "JOIN patients p ON s.patient_id = p.patient_id "
                   + "LEFT JOIN doctors d ON s.doctor_id = d.doctor_id "
                   + "WHERE s.screening_id = ?";

        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setInt(1, id);

            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return mapResultSetToScreening(rs);
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return null;
    }

    public List<CVDScreening> getAllScreenings() {
        List<CVDScreening> list = new ArrayList<>();
        String sql = "SELECT s.*, "
                   + "p.name AS patient_name, p.age AS patient_age, p.gender AS patient_gender, p.phone AS patient_phone, "
                   + "d.name AS doctor_name, d.specialization AS doctor_spec "
                   + "FROM cvd_screenings s "
                   + "JOIN patients p ON s.patient_id = p.patient_id "
                   + "LEFT JOIN doctors d ON s.doctor_id = d.doctor_id "
                   + "ORDER BY s.screening_date DESC";

        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            while (rs.next()) {
                list.add(mapResultSetToScreening(rs));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return list;
    }

    public List<CVDScreening> getRecentScreenings(int limit) {
        List<CVDScreening> list = new ArrayList<>();
        String sql = "SELECT s.*, "
                   + "p.name AS patient_name, p.age AS patient_age, p.gender AS patient_gender, p.phone AS patient_phone, "
                   + "d.name AS doctor_name, d.specialization AS doctor_spec "
                   + "FROM cvd_screenings s "
                   + "JOIN patients p ON s.patient_id = p.patient_id "
                   + "LEFT JOIN doctors d ON s.doctor_id = d.doctor_id "
                   + "ORDER BY s.screening_date DESC LIMIT ?";

        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setInt(1, limit);

            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    list.add(mapResultSetToScreening(rs));
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return list;
    }

    public List<CVDScreening> getScreeningsByPatientId(int patientId) {
        List<CVDScreening> list = new ArrayList<>();
        String sql = "SELECT s.*, "
                   + "p.name AS patient_name, p.age AS patient_age, p.gender AS patient_gender, p.phone AS patient_phone, "
                   + "d.name AS doctor_name, d.specialization AS doctor_spec "
                   + "FROM cvd_screenings s "
                   + "JOIN patients p ON s.patient_id = p.patient_id "
                   + "LEFT JOIN doctors d ON s.doctor_id = d.doctor_id "
                   + "WHERE s.patient_id = ? "
                   + "ORDER BY s.screening_date DESC";

        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setInt(1, patientId);

            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    list.add(mapResultSetToScreening(rs));
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return list;
    }

    public boolean deleteScreening(int id) {
        String sql = "DELETE FROM cvd_screenings WHERE screening_id = ?";

        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            ps.setInt(1, id);
            return ps.executeUpdate() > 0;
        } catch (SQLException e) {
            e.printStackTrace();
        }

        return false;
    }

    public int getTotalScreeningsCount() {
        String sql = "SELECT COUNT(*) FROM cvd_screenings";
        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            if (rs.next()) {
                return rs.getInt(1);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return 0;
    }

    /**
     * Number of screenings whose experimental CVD head was Positive.
     * Shown as "Elevated CVD Markers (Exp)". The AI service never emits a
     * 'High Risk' risk_level (every result is labelled as requiring clinical
     * review), so the prediction column is the meaningful signal.
     */
    public int getHighRiskCount() {
        String sql = "SELECT COUNT(*) FROM cvd_screenings WHERE cvd_prediction = 'Positive'";
        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            if (rs.next()) {
                return rs.getInt(1);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return 0;
    }

    /**
     * Stores the vessel-segmentation result for a saved screening.
     * Needs the columns from db/add_vessel_columns.sql; if they are missing the screening itself is unaffected.
     */
    public void updateVesselResult(int screeningId, String overlayPath, double densityPercent) {
        String sql = "UPDATE cvd_screenings SET vessel_overlay_path = ?, vessel_density = ? WHERE screening_id = ?";
        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, overlayPath);
            ps.setDouble(2, densityPercent);
            ps.setInt(3, screeningId);
            ps.executeUpdate();
        } catch (SQLException e) {
            // Fallback for schema using mask_path instead of vessel_overlay_path
            try {
                String sqlAlt = "UPDATE cvd_screenings SET mask_path = ?, vessel_density = ? WHERE screening_id = ?";
                try (Connection conn = DBConnection.getConnection();
                     PreparedStatement ps = conn.prepareStatement(sqlAlt)) {
                    ps.setString(1, overlayPath);
                    ps.setDouble(2, densityPercent);
                    ps.setInt(3, screeningId);
                    ps.executeUpdate();
                }
            } catch (SQLException ignored) {
                System.err.println("[CVD] Could not save vessel result (run db/cvd_screenings_schema.sql?): " + e.getMessage());
            }
        }
    }

    private CVDScreening mapResultSetToScreening(ResultSet rs) throws SQLException {
        CVDScreening s = new CVDScreening();
        s.setScreeningId(rs.getInt("screening_id"));
        s.setPatientId(rs.getInt("patient_id"));
        s.setPatientName(rs.getString("patient_name"));
        s.setPatientAge(rs.getInt("patient_age"));
        s.setPatientGender(rs.getString("patient_gender"));
        s.setPatientPhone(rs.getString("patient_phone"));

        int docId = rs.getInt("doctor_id");
        if (!rs.wasNull()) {
            s.setDoctorId(docId);
            s.setDoctorName(rs.getString("doctor_name"));
            s.setDoctorSpecialization(rs.getString("doctor_spec"));
        }

        int aptId = rs.getInt("appointment_id");
        if (!rs.wasNull()) {
            s.setAppointmentId(aptId);
        }

        s.setImagePath(rs.getString("image_path"));

        // cvd_prediction / cvd_result
        try {
            s.setCvdPrediction(rs.getString("cvd_prediction"));
        } catch (SQLException e) {
            try { s.setCvdPrediction(rs.getString("cvd_result")); } catch (SQLException ignored) {}
        }
        if (s.getCvdPrediction() == null) {
            try { s.setCvdPrediction(rs.getString("cvd_result")); } catch (SQLException ignored) {}
        }

        // cvd_probability
        try {
            s.setCvdProbability(rs.getDouble("cvd_probability"));
        } catch (SQLException ignored) {}

        // hypertension_prediction / ht_result
        try {
            s.setHypertensionPrediction(rs.getString("hypertension_prediction"));
        } catch (SQLException e) {
            try { s.setHypertensionPrediction(rs.getString("ht_result")); } catch (SQLException ignored) {}
        }
        if (s.getHypertensionPrediction() == null) {
            try { s.setHypertensionPrediction(rs.getString("ht_result")); } catch (SQLException ignored) {}
        }

        // hypertension_probability / ht_probability
        try {
            s.setHypertensionProbability(rs.getDouble("hypertension_probability"));
        } catch (SQLException e) {
            try { s.setHypertensionProbability(rs.getDouble("ht_probability")); } catch (SQLException ignored) {}
        }

        s.setDrGrade(rs.getString("dr_grade"));
        s.setDrConfidence(rs.getDouble("dr_confidence"));
        s.setRiskLevel(rs.getString("risk_level"));
        s.setNotes(rs.getString("notes"));

        // screening_date / created_at
        try {
            s.setScreeningDate(rs.getTimestamp("screening_date"));
        } catch (SQLException e) {
            try { s.setScreeningDate(rs.getTimestamp("created_at")); } catch (SQLException ignored) {}
        }
        if (s.getScreeningDate() == null) {
            try { s.setScreeningDate(rs.getTimestamp("created_at")); } catch (SQLException ignored) {}
        }

        // Read model_name (added in schema migration)
        try {
            s.setModelName(rs.getString("model_name"));
        } catch (SQLException ignored) {
            // Column may not exist in older schema
        }

        // Read recommendation / recommendations from DB
        try {
            String storedRec = rs.getString("recommendation");
            if (storedRec != null && !storedRec.trim().isEmpty()) {
                s.setRecommendation(storedRec);
            } else {
                storedRec = rs.getString("recommendations");
                if (storedRec != null && !storedRec.trim().isEmpty()) {
                    s.setRecommendation(storedRec);
                }
            }
        } catch (SQLException ignored) {
            try {
                String storedRec = rs.getString("recommendations");
                if (storedRec != null && !storedRec.trim().isEmpty()) {
                    s.setRecommendation(storedRec);
                }
            } catch (SQLException ignored2) {}
        }

        // Default recommendation if none was stored
        if (s.getRecommendation() == null || s.getRecommendation().trim().isEmpty()) {
            if ("High Risk".equalsIgnoreCase(s.getRiskLevel())) {
                s.setRecommendation("Immediate cardiovascular assessment recommended. Schedule ECG, lipid profile, and comprehensive cardiology consult.");
            } else if ("Moderate Risk".equalsIgnoreCase(s.getRiskLevel())) {
                s.setRecommendation("Elevated cardiovascular / hypertension markers detected. Recommend routine blood pressure monitoring and preventive lifestyle modifications.");
            } else {
                s.setRecommendation("Retinal markers within normal parameters. Continue annual preventive health check-ups.");
            }
        }

        // Vessel segmentation columns (vessel_overlay_path or mask_path)
        try {
            String mask = rs.getString("vessel_overlay_path");
            if (mask == null || mask.trim().isEmpty()) {
                mask = rs.getString("mask_path");
            }
            s.setVesselOverlayPath(mask);
            double density = rs.getDouble("vessel_density");
            s.setVesselDensity(rs.wasNull() ? null : density);
        } catch (SQLException ignored) {
            try {
                s.setVesselOverlayPath(rs.getString("mask_path"));
            } catch (SQLException ignored2) {}
        }

        return s;
    }
}

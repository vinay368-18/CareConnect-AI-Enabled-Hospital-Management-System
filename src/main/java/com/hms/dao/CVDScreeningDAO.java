package com.hms.dao;

import com.hms.model.CVDScreening;
import com.hms.util.DBConnection;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class CVDScreeningDAO {

    public int saveScreening(CVDScreening screening) {
        String sql = "INSERT INTO cvd_screenings "
                   + "(patient_id, doctor_id, appointment_id, image_path, "
                   + "cvd_prediction, cvd_probability, hypertension_prediction, hypertension_probability, "
                   + "dr_grade, dr_confidence, risk_level, notes) "
                   + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

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
            ps.setString(5, screening.getCvdPrediction());
            ps.setDouble(6, screening.getCvdProbability());
            ps.setString(7, screening.getHypertensionPrediction());
            ps.setDouble(8, screening.getHypertensionProbability());
            ps.setString(9, screening.getDrGrade());
            ps.setDouble(10, screening.getDrConfidence());
            ps.setString(11, screening.getRiskLevel());
            ps.setString(12, screening.getNotes());

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

    public int getHighRiskCount() {
        String sql = "SELECT COUNT(*) FROM cvd_screenings WHERE risk_level = 'High Risk'";
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
        s.setCvdPrediction(rs.getString("cvd_prediction"));
        s.setCvdProbability(rs.getDouble("cvd_probability"));
        s.setHypertensionPrediction(rs.getString("hypertension_prediction"));
        s.setHypertensionProbability(rs.getDouble("hypertension_probability"));
        s.setDrGrade(rs.getString("dr_grade"));
        s.setDrConfidence(rs.getDouble("dr_confidence"));
        s.setRiskLevel(rs.getString("risk_level"));
        s.setNotes(rs.getString("notes"));
        s.setScreeningDate(rs.getTimestamp("screening_date"));

        // Default clinical recommendations based on risk
        if ("High Risk".equalsIgnoreCase(s.getRiskLevel())) {
            s.setRecommendation("Immediate cardiovascular assessment recommended. Schedule ECG, lipid profile, and comprehensive cardiology consult.");
        } else if ("Moderate Risk".equalsIgnoreCase(s.getRiskLevel())) {
            s.setRecommendation("Elevated cardiovascular / hypertension markers detected. Recommend routine blood pressure monitoring and preventive lifestyle modifications.");
        } else {
            s.setRecommendation("Retinal markers within normal parameters. Continue annual preventive health check-ups.");
        }

        return s;
    }
}

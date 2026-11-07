package com.hms.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import com.hms.model.Appointment;
import com.hms.util.DBConnection;

/**
 * Data Access Object for Appointment records.
 *
 * AUDIT FIX (2026-11-07):
 * - Wrapped all JDBC resources in try-with-resources to eliminate connection leaks.
 * - Added transactional boundary to deleteAppointment() and handled CVD screening FK reference.
 */
public class AppointmentDAO {

    // =========================
    // GET ALL APPOINTMENTS
    // =========================

    public List<Appointment> getAllAppointments() {
        List<Appointment> appointments = new ArrayList<>();
        String sql =
            "SELECT a.appointment_id, "
          + "a.patient_id, "
          + "a.doctor_id, "
          + "p.name AS patient_name, "
          + "d.name AS doctor_name, "
          + "a.appointment_date, "
          + "a.appointment_time, "
          + "a.reason, "
          + "a.status "
          + "FROM appointments a "
          + "JOIN patients p ON a.patient_id = p.patient_id "
          + "JOIN doctors d ON a.doctor_id = d.doctor_id "
          + "ORDER BY a.appointment_date DESC, "
          + "a.appointment_time DESC";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            while (rs.next()) {
                Appointment appointment = new Appointment();
                appointment.setId(rs.getInt("appointment_id"));
                appointment.setPatientId(rs.getInt("patient_id"));
                appointment.setDoctorId(rs.getInt("doctor_id"));
                appointment.setPatientName(rs.getString("patient_name"));
                appointment.setDoctorName(rs.getString("doctor_name"));
                appointment.setAppointmentDate(rs.getDate("appointment_date"));
                appointment.setAppointmentTime(rs.getTime("appointment_time"));
                appointment.setReason(rs.getString("reason"));
                appointment.setStatus(rs.getString("status"));
                appointments.add(appointment);
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

        return appointments;
    }

    // =========================
    // ADD APPOINTMENT
    // =========================

    public boolean addAppointment(Appointment appointment) {
        String sql =
            "INSERT INTO appointments "
          + "(patient_id, doctor_id, appointment_date, "
          + "appointment_time, reason, status) "
          + "VALUES (?, ?, ?, ?, ?, ?)";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setInt(1, appointment.getPatientId());
            ps.setInt(2, appointment.getDoctorId());
            ps.setDate(3, appointment.getAppointmentDate());
            ps.setTime(4, appointment.getAppointmentTime());
            ps.setString(5, appointment.getReason());
            ps.setString(6, appointment.getStatus());

            return ps.executeUpdate() > 0;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    // =========================
    // GET APPOINTMENT BY ID
    // =========================

    public Appointment getAppointmentById(int id) {
        Appointment appointment = null;
        String sql =
            "SELECT appointment_id, patient_id, doctor_id, "
          + "appointment_date, appointment_time, reason, status "
          + "FROM appointments "
          + "WHERE appointment_id = ?";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setInt(1, id);

            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    appointment = new Appointment();
                    appointment.setId(rs.getInt("appointment_id"));
                    appointment.setPatientId(rs.getInt("patient_id"));
                    appointment.setDoctorId(rs.getInt("doctor_id"));
                    appointment.setAppointmentDate(rs.getDate("appointment_date"));
                    appointment.setAppointmentTime(rs.getTime("appointment_time"));
                    appointment.setReason(rs.getString("reason"));
                    appointment.setStatus(rs.getString("status"));
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

        return appointment;
    }

    // =========================
    // UPDATE APPOINTMENT
    // =========================

    public boolean updateAppointment(Appointment appointment) {
        String sql =
            "UPDATE appointments SET "
          + "patient_id = ?, "
          + "doctor_id = ?, "
          + "appointment_date = ?, "
          + "appointment_time = ?, "
          + "reason = ?, "
          + "status = ? "
          + "WHERE appointment_id = ?";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setInt(1, appointment.getPatientId());
            ps.setInt(2, appointment.getDoctorId());
            ps.setDate(3, appointment.getAppointmentDate());
            ps.setTime(4, appointment.getAppointmentTime());
            ps.setString(5, appointment.getReason());
            ps.setString(6, appointment.getStatus());
            ps.setInt(7, appointment.getId());

            return ps.executeUpdate() > 0;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    // =========================
    // DELETE APPOINTMENT (Transactional Cascade)
    // =========================

    public boolean deleteAppointment(int id) {
        String updateBillsSql = "UPDATE bills SET appointment_id = NULL WHERE appointment_id = ?";
        String updateCvdScreeningsSql = "UPDATE cvd_screenings SET appointment_id = NULL WHERE appointment_id = ?";
        String sql = "DELETE FROM appointments WHERE appointment_id = ?";

        Connection con = null;
        try {
            con = DBConnection.getConnection();
            if (con == null) {
                return false;
            }
            con.setAutoCommit(false);

            // 1. Detach bills referencing this appointment
            try (PreparedStatement psUpdate = con.prepareStatement(updateBillsSql)) {
                psUpdate.setInt(1, id);
                psUpdate.executeUpdate();
            }

            // 2. Detach CVD screenings referencing this appointment
            try (PreparedStatement psCvd = con.prepareStatement(updateCvdScreeningsSql)) {
                psCvd.setInt(1, id);
                psCvd.executeUpdate();
            } catch (SQLException ignored) {
                // Table might not exist or appointment_id is already nullable
            }

            // 3. Delete the appointment
            int result;
            try (PreparedStatement ps = con.prepareStatement(sql)) {
                ps.setInt(1, id);
                result = ps.executeUpdate();
            }

            con.commit();
            return result > 0;

        } catch (Exception e) {
            if (con != null) {
                try {
                    con.rollback();
                } catch (SQLException ex) {
                    ex.printStackTrace();
                }
            }
            e.printStackTrace();
            return false;
        } finally {
            if (con != null) {
                try {
                    con.setAutoCommit(true);
                    con.close();
                } catch (SQLException ex) {
                    ex.printStackTrace();
                }
            }
        }
    }

    // =========================
    // SEARCH APPOINTMENTS
    // =========================

    public List<Appointment> searchAppointments(String keyword) {
        List<Appointment> appointments = new ArrayList<>();
        String sql =
            "SELECT a.appointment_id, "
          + "a.patient_id, "
          + "a.doctor_id, "
          + "p.name AS patient_name, "
          + "d.name AS doctor_name, "
          + "a.appointment_date, "
          + "a.appointment_time, "
          + "a.reason, "
          + "a.status "
          + "FROM appointments a "
          + "JOIN patients p ON a.patient_id = p.patient_id "
          + "JOIN doctors d ON a.doctor_id = d.doctor_id "
          + "WHERE p.name LIKE ? "
          + "OR d.name LIKE ? "
          + "OR a.reason LIKE ? "
          + "OR a.status LIKE ? "
          + "ORDER BY a.appointment_date DESC, "
          + "a.appointment_time DESC";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            String searchKeyword = "%" + keyword + "%";
            ps.setString(1, searchKeyword);
            ps.setString(2, searchKeyword);
            ps.setString(3, searchKeyword);
            ps.setString(4, searchKeyword);

            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Appointment appointment = new Appointment();
                    appointment.setId(rs.getInt("appointment_id"));
                    appointment.setPatientId(rs.getInt("patient_id"));
                    appointment.setDoctorId(rs.getInt("doctor_id"));
                    appointment.setPatientName(rs.getString("patient_name"));
                    appointment.setDoctorName(rs.getString("doctor_name"));
                    appointment.setAppointmentDate(rs.getDate("appointment_date"));
                    appointment.setAppointmentTime(rs.getTime("appointment_time"));
                    appointment.setReason(rs.getString("reason"));
                    appointment.setStatus(rs.getString("status"));
                    appointments.add(appointment);
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

        return appointments;
    }
}

package com.hms.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import com.hms.model.Patient;
import com.hms.util.DBConnection;

public class PatientDAO {

    public List<Patient> getAllPatients() {

        List<Patient> patients = new ArrayList<>();

        String sql = "SELECT patient_id, name, age, gender, phone, address "
                   + "FROM patients ORDER BY patient_id DESC";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            while (rs.next()) {
                Patient patient = new Patient();
                patient.setId(rs.getInt("patient_id"));
                patient.setName(rs.getString("name"));
                patient.setAge(rs.getInt("age"));
                patient.setGender(rs.getString("gender"));
                patient.setPhone(rs.getString("phone"));
                patient.setAddress(rs.getString("address"));

                patients.add(patient);
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

        return patients;
    }

    public boolean addPatient(Patient patient) {

        String sql = "INSERT INTO patients "
                   + "(name, age, gender, phone, address) "
                   + "VALUES (?, ?, ?, ?, ?)";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setString(1, patient.getName());
            ps.setInt(2, patient.getAge());
            ps.setString(3, patient.getGender());
            ps.setString(4, patient.getPhone());
            ps.setString(5, patient.getAddress());

            return ps.executeUpdate() > 0;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    /**
     * Deletes a patient and all dependent records (CVD screenings, bills, appointments) atomically.
     * Prevents leaving inconsistent or orphaned medical screening records.
     */
    public boolean deletePatient(int id) {

        String deleteScreeningsSql = "DELETE FROM cvd_screenings WHERE patient_id = ?";
        String deleteBillsSql = "DELETE FROM bills WHERE patient_id = ?";
        String deleteBillingSql = "DELETE FROM billing WHERE patient_id = ?";
        String deleteAppointmentsSql = "DELETE FROM appointments WHERE patient_id = ?";
        String deletePatientSql = "DELETE FROM patients WHERE patient_id = ?";

        Connection con = null;
        try {
            con = DBConnection.getConnection();
            if (con == null) {
                return false;
            }
            con.setAutoCommit(false);

            // 1. Delete associated CVD screenings to prevent inconsistent / orphaned records
            try (PreparedStatement psScreenings = con.prepareStatement(deleteScreeningsSql)) {
                psScreenings.setInt(1, id);
                psScreenings.executeUpdate();
            }

            // 2. Delete associated bills
            try (PreparedStatement psBills = con.prepareStatement(deleteBillsSql)) {
                psBills.setInt(1, id);
                psBills.executeUpdate();
            }

            // 3. Delete legacy billing rows if any
            try (PreparedStatement psBilling = con.prepareStatement(deleteBillingSql)) {
                psBilling.setInt(1, id);
                psBilling.executeUpdate();
            } catch (SQLException ignored) {
                // Legacy table might not exist
            }

            // 4. Delete associated appointments
            try (PreparedStatement psAppt = con.prepareStatement(deleteAppointmentsSql)) {
                psAppt.setInt(1, id);
                psAppt.executeUpdate();
            }

            // 5. Delete patient record
            int result;
            try (PreparedStatement ps = con.prepareStatement(deletePatientSql)) {
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

    public Patient getPatientById(int id) {

        Patient patient = null;

        String sql = "SELECT patient_id, name, age, gender, phone, address "
                   + "FROM patients WHERE patient_id = ?";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setInt(1, id);

            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    patient = new Patient();
                    patient.setId(rs.getInt("patient_id"));
                    patient.setName(rs.getString("name"));
                    patient.setAge(rs.getInt("age"));
                    patient.setGender(rs.getString("gender"));
                    patient.setPhone(rs.getString("phone"));
                    patient.setAddress(rs.getString("address"));
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

        return patient;
    }

    public List<Patient> searchPatients(String keyword) {

        List<Patient> patients = new ArrayList<>();

        String sql = "SELECT patient_id, name, age, gender, phone, address "
                   + "FROM patients "
                   + "WHERE name LIKE ? OR phone LIKE ? "
                   + "ORDER BY patient_id DESC";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            String search = "%" + keyword + "%";

            ps.setString(1, search);
            ps.setString(2, search);

            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Patient patient = new Patient();
                    patient.setId(rs.getInt("patient_id"));
                    patient.setName(rs.getString("name"));
                    patient.setAge(rs.getInt("age"));
                    patient.setGender(rs.getString("gender"));
                    patient.setPhone(rs.getString("phone"));
                    patient.setAddress(rs.getString("address"));

                    patients.add(patient);
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

        return patients;
    }

    public boolean updatePatient(Patient patient) {

        String sql = "UPDATE patients SET name = ?, age = ?, gender = ?, "
                   + "phone = ?, address = ? WHERE patient_id = ?";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setString(1, patient.getName());
            ps.setInt(2, patient.getAge());
            ps.setString(3, patient.getGender());
            ps.setString(4, patient.getPhone());
            ps.setString(5, patient.getAddress());
            ps.setInt(6, patient.getId());

            return ps.executeUpdate() > 0;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }
}

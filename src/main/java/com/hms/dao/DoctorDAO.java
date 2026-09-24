package com.hms.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

import com.hms.model.Doctor;
import com.hms.util.DBConnection;

public class DoctorDAO {

    // =========================
    // GET ALL DOCTORS
    // =========================

    public List<Doctor> getAllDoctors() {

        List<Doctor> doctors = new ArrayList<>();

        String sql = "SELECT doctor_id, name, specialization, phone, "
                   + "email, experience, consultation_fee "
                   + "FROM doctors ORDER BY doctor_id DESC";

        try {

            Connection con = DBConnection.getConnection();

            PreparedStatement ps =
                con.prepareStatement(sql);

            ResultSet rs =
                ps.executeQuery();

            while (rs.next()) {

                Doctor doctor = new Doctor();

                doctor.setId(
                    rs.getInt("doctor_id")
                );

                doctor.setName(
                    rs.getString("name")
                );

                doctor.setSpecialization(
                    rs.getString("specialization")
                );

                doctor.setPhone(
                    rs.getString("phone")
                );

                doctor.setEmail(
                    rs.getString("email")
                );

                doctor.setExperience(
                    rs.getInt("experience")
                );

                doctor.setConsultationFee(
                    rs.getDouble("consultation_fee")
                );

                doctors.add(doctor);
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {

            e.printStackTrace();
        }

        return doctors;
    }


    // =========================
    // ADD DOCTOR
    // =========================

    public boolean addDoctor(Doctor doctor) {

        String sql = "INSERT INTO doctors "
                   + "(name, specialization, phone, email, "
                   + "experience, consultation_fee) "
                   + "VALUES (?, ?, ?, ?, ?, ?)";

        try {

            Connection con =
                DBConnection.getConnection();

            PreparedStatement ps =
                con.prepareStatement(sql);

            ps.setString(
                1,
                doctor.getName()
            );

            ps.setString(
                2,
                doctor.getSpecialization()
            );

            ps.setString(
                3,
                doctor.getPhone()
            );

            ps.setString(
                4,
                doctor.getEmail()
            );

            ps.setInt(
                5,
                doctor.getExperience()
            );

            ps.setDouble(
                6,
                doctor.getConsultationFee()
            );

            int result =
                ps.executeUpdate();

            ps.close();
            con.close();

            return result > 0;

        } catch (Exception e) {

            e.printStackTrace();

            return false;
        }
    }


    // =========================
    // GET DOCTOR BY ID
    // =========================

    public Doctor getDoctorById(int id) {

        Doctor doctor = null;

        String sql = "SELECT doctor_id, name, specialization, phone, "
                   + "email, experience, consultation_fee "
                   + "FROM doctors WHERE doctor_id = ?";

        try {

            Connection con =
                DBConnection.getConnection();

            PreparedStatement ps =
                con.prepareStatement(sql);

            ps.setInt(1, id);

            ResultSet rs =
                ps.executeQuery();

            if (rs.next()) {

                doctor = new Doctor();

                doctor.setId(
                    rs.getInt("doctor_id")
                );

                doctor.setName(
                    rs.getString("name")
                );

                doctor.setSpecialization(
                    rs.getString("specialization")
                );

                doctor.setPhone(
                    rs.getString("phone")
                );

                doctor.setEmail(
                    rs.getString("email")
                );

                doctor.setExperience(
                    rs.getInt("experience")
                );

                doctor.setConsultationFee(
                    rs.getDouble("consultation_fee")
                );
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {

            e.printStackTrace();
        }

        return doctor;
    }


    // =========================
    // UPDATE DOCTOR
    // =========================

    public boolean updateDoctor(Doctor doctor) {

        String sql = "UPDATE doctors SET "
                   + "name = ?, "
                   + "specialization = ?, "
                   + "phone = ?, "
                   + "email = ?, "
                   + "experience = ?, "
                   + "consultation_fee = ? "
                   + "WHERE doctor_id = ?";

        try {

            Connection con =
                DBConnection.getConnection();

            PreparedStatement ps =
                con.prepareStatement(sql);

            ps.setString(
                1,
                doctor.getName()
            );

            ps.setString(
                2,
                doctor.getSpecialization()
            );

            ps.setString(
                3,
                doctor.getPhone()
            );

            ps.setString(
                4,
                doctor.getEmail()
            );

            ps.setInt(
                5,
                doctor.getExperience()
            );

            ps.setDouble(
                6,
                doctor.getConsultationFee()
            );

            ps.setInt(
                7,
                doctor.getId()
            );

            int result =
                ps.executeUpdate();

            ps.close();
            con.close();

            return result > 0;

        } catch (Exception e) {

            e.printStackTrace();

            return false;
        }
    }


    // =========================
    // DELETE DOCTOR
    // =========================

    public boolean deleteDoctor(int id) {

        String sql =
            "DELETE FROM doctors WHERE doctor_id = ?";

        try {

            Connection con =
                DBConnection.getConnection();

            PreparedStatement ps =
                con.prepareStatement(sql);

            ps.setInt(1, id);

            int result =
                ps.executeUpdate();

            ps.close();
            con.close();

            return result > 0;

        } catch (Exception e) {

            e.printStackTrace();

            return false;
        }
    }


    // =========================
    // SEARCH DOCTORS
    // =========================

    public List<Doctor> searchDoctors(String keyword) {

        List<Doctor> doctors =
            new ArrayList<>();

        String sql = "SELECT doctor_id, name, specialization, phone, "
                   + "email, experience, consultation_fee "
                   + "FROM doctors "
                   + "WHERE name LIKE ? "
                   + "OR specialization LIKE ? "
                   + "OR phone LIKE ? "
                   + "ORDER BY doctor_id DESC";

        try {

            Connection con =
                DBConnection.getConnection();

            PreparedStatement ps =
                con.prepareStatement(sql);

            String searchKeyword =
                "%" + keyword + "%";

            ps.setString(1, searchKeyword);
            ps.setString(2, searchKeyword);
            ps.setString(3, searchKeyword);

            ResultSet rs =
                ps.executeQuery();

            while (rs.next()) {

                Doctor doctor =
                    new Doctor();

                doctor.setId(
                    rs.getInt("doctor_id")
                );

                doctor.setName(
                    rs.getString("name")
                );

                doctor.setSpecialization(
                    rs.getString("specialization")
                );

                doctor.setPhone(
                    rs.getString("phone")
                );

                doctor.setEmail(
                    rs.getString("email")
                );

                doctor.setExperience(
                    rs.getInt("experience")
                );

                doctor.setConsultationFee(
                    rs.getDouble("consultation_fee")
                );

                doctors.add(doctor);
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {

            e.printStackTrace();
        }

        return doctors;
    }
}
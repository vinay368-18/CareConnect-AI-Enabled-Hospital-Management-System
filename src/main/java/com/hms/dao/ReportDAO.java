package com.hms.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

import com.hms.model.Appointment;
import com.hms.util.DBConnection;

public class ReportDAO {

    // =========================
    // TOTAL PATIENTS
    // =========================

    public int getTotalPatients() {

        String sql = "SELECT COUNT(*) FROM patients";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                int count = rs.getInt(1);

                rs.close();
                ps.close();
                con.close();

                return count;
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return 0;
    }


    // =========================
    // TOTAL DOCTORS
    // =========================

    public int getTotalDoctors() {

        String sql = "SELECT COUNT(*) FROM doctors";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                int count = rs.getInt(1);

                rs.close();
                ps.close();
                con.close();

                return count;
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return 0;
    }


    // =========================
    // TOTAL APPOINTMENTS
    // =========================

    public int getTotalAppointments() {

        String sql = "SELECT COUNT(*) FROM appointments";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                int count = rs.getInt(1);

                rs.close();
                ps.close();
                con.close();

                return count;
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return 0;
    }


    // =========================
    // TOTAL BILLS
    // =========================

    public int getTotalBills() {

        String sql = "SELECT COUNT(*) FROM bills";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                int count = rs.getInt(1);

                rs.close();
                ps.close();
                con.close();

                return count;
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return 0;
    }


    // =========================
    // TOTAL PAID AMOUNT
    // =========================

    public double getTotalPaidAmount() {

        String sql = "SELECT COALESCE(SUM(amount), 0) "
                   + "FROM bills "
                   + "WHERE payment_status = 'Paid'";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                double amount = rs.getDouble(1);

                rs.close();
                ps.close();
                con.close();

                return amount;
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return 0;
    }


    // =========================
    // TOTAL PENDING AMOUNT
    // =========================

    public double getTotalPendingAmount() {

        String sql = "SELECT COALESCE(SUM(amount), 0) "
                   + "FROM bills "
                   + "WHERE payment_status = 'Pending'";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                double amount = rs.getDouble(1);

                rs.close();
                ps.close();
                con.close();

                return amount;
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return 0;
    }


    // =========================
    // CANCELLED BILLS
    // =========================

    public int getCancelledBills() {

        String sql = "SELECT COUNT(*) "
                   + "FROM bills "
                   + "WHERE payment_status = 'Cancelled'";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                int count = rs.getInt(1);

                rs.close();
                ps.close();
                con.close();

                return count;
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return 0;
    }


    // =========================
    // RECENT APPOINTMENTS
    // =========================

    public List<Appointment> getRecentAppointments() {

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
          + "JOIN patients p "
          + "ON a.patient_id = p.patient_id "
          + "JOIN doctors d "
          + "ON a.doctor_id = d.doctor_id "
          + "ORDER BY a.appointment_date DESC, "
          + "a.appointment_time DESC "
          + "LIMIT 5";

        try {

            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            while (rs.next()) {

                Appointment appointment = new Appointment();

                appointment.setId(
                    rs.getInt("appointment_id")
                );

                appointment.setPatientId(
                    rs.getInt("patient_id")
                );

                appointment.setDoctorId(
                    rs.getInt("doctor_id")
                );

                appointment.setPatientName(
                    rs.getString("patient_name")
                );

                appointment.setDoctorName(
                    rs.getString("doctor_name")
                );

                appointment.setAppointmentDate(
                    rs.getDate("appointment_date")
                );

                appointment.setAppointmentTime(
                    rs.getTime("appointment_time")
                );

                appointment.setReason(
                    rs.getString("reason")
                );

                appointment.setStatus(
                    rs.getString("status")
                );

                appointments.add(appointment);
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return appointments;
    }
}
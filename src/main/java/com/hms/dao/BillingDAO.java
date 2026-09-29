package com.hms.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

import com.hms.model.Bill;
import com.hms.util.DBConnection;

public class BillingDAO {

    // Get all bills
    public List<Bill> getAllBills() {

        List<Bill> bills = new ArrayList<>();

        String sql = "SELECT b.bill_id, b.patient_id, b.appointment_id, "
                   + "p.name AS patient_name, b.amount, b.payment_method, "
                   + "b.payment_status, b.bill_date "
                   + "FROM bills b "
                   + "JOIN patients p ON b.patient_id = p.patient_id "
                   + "ORDER BY b.bill_id DESC";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            while (rs.next()) {

                Bill bill = new Bill();

                bill.setId(rs.getInt("bill_id"));
                bill.setPatientId(rs.getInt("patient_id"));
                bill.setAppointmentId(rs.getInt("appointment_id"));
                bill.setPatientName(rs.getString("patient_name"));
                bill.setAmount(rs.getDouble("amount"));
                bill.setPaymentMethod(rs.getString("payment_method"));
                bill.setPaymentStatus(rs.getString("payment_status"));
                bill.setBillDate(rs.getDate("bill_date"));

                bills.add(bill);
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return bills;
    }


    // Add a new bill
    public boolean addBill(Bill bill) {

        String sql = "INSERT INTO bills "
                   + "(patient_id, appointment_id, amount, payment_method, "
                   + "payment_status, bill_date) "
                   + "VALUES (?, ?, ?, ?, ?, ?)";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);

            ps.setInt(1, bill.getPatientId());

            if (bill.getAppointmentId() > 0) {
                ps.setInt(2, bill.getAppointmentId());
            } else {
                ps.setNull(2, java.sql.Types.INTEGER);
            }

            ps.setDouble(3, bill.getAmount());
            ps.setString(4, bill.getPaymentMethod());
            ps.setString(5, bill.getPaymentStatus());
            ps.setDate(6, bill.getBillDate());

            int result = ps.executeUpdate();

            ps.close();
            con.close();

            return result > 0;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }


    // Get bill by ID
    public Bill getBillById(int id) {

        Bill bill = null;

        String sql = "SELECT b.bill_id, b.patient_id, b.appointment_id, "
                   + "p.name AS patient_name, b.amount, b.payment_method, "
                   + "b.payment_status, b.bill_date "
                   + "FROM bills b "
                   + "JOIN patients p ON b.patient_id = p.patient_id "
                   + "WHERE b.bill_id = ?";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);

            ps.setInt(1, id);

            ResultSet rs = ps.executeQuery();

            if (rs.next()) {

                bill = new Bill();

                bill.setId(rs.getInt("bill_id"));
                bill.setPatientId(rs.getInt("patient_id"));
                bill.setAppointmentId(rs.getInt("appointment_id"));
                bill.setPatientName(rs.getString("patient_name"));
                bill.setAmount(rs.getDouble("amount"));
                bill.setPaymentMethod(rs.getString("payment_method"));
                bill.setPaymentStatus(rs.getString("payment_status"));
                bill.setBillDate(rs.getDate("bill_date"));
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return bill;
    }


    // Update bill
    public boolean updateBill(Bill bill) {

        String sql = "UPDATE bills SET patient_id = ?, appointment_id = ?, "
                   + "amount = ?, payment_method = ?, payment_status = ?, "
                   + "bill_date = ? WHERE bill_id = ?";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);

            ps.setInt(1, bill.getPatientId());

            if (bill.getAppointmentId() > 0) {
                ps.setInt(2, bill.getAppointmentId());
            } else {
                ps.setNull(2, java.sql.Types.INTEGER);
            }

            ps.setDouble(3, bill.getAmount());
            ps.setString(4, bill.getPaymentMethod());
            ps.setString(5, bill.getPaymentStatus());
            ps.setDate(6, bill.getBillDate());
            ps.setInt(7, bill.getId());

            int result = ps.executeUpdate();

            ps.close();
            con.close();

            return result > 0;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }


    // Delete bill
    public boolean deleteBill(int id) {

        String sql = "DELETE FROM bills WHERE bill_id = ?";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);

            ps.setInt(1, id);

            int result = ps.executeUpdate();

            ps.close();
            con.close();

            return result > 0;

        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }


    // Search bills
    public List<Bill> searchBills(String keyword) {

        List<Bill> bills = new ArrayList<>();

        String sql = "SELECT b.bill_id, b.patient_id, b.appointment_id, "
                   + "p.name AS patient_name, b.amount, b.payment_method, "
                   + "b.payment_status, b.bill_date "
                   + "FROM bills b "
                   + "JOIN patients p ON b.patient_id = p.patient_id "
                   + "WHERE p.name LIKE ? "
                   + "OR b.payment_method LIKE ? "
                   + "OR b.payment_status LIKE ? "
                   + "ORDER BY b.bill_id DESC";

        try {
            Connection con = DBConnection.getConnection();
            PreparedStatement ps = con.prepareStatement(sql);

            String search = "%" + keyword + "%";

            ps.setString(1, search);
            ps.setString(2, search);
            ps.setString(3, search);

            ResultSet rs = ps.executeQuery();

            while (rs.next()) {

                Bill bill = new Bill();

                bill.setId(rs.getInt("bill_id"));
                bill.setPatientId(rs.getInt("patient_id"));
                bill.setAppointmentId(rs.getInt("appointment_id"));
                bill.setPatientName(rs.getString("patient_name"));
                bill.setAmount(rs.getDouble("amount"));
                bill.setPaymentMethod(rs.getString("payment_method"));
                bill.setPaymentStatus(rs.getString("payment_status"));
                bill.setBillDate(rs.getDate("bill_date"));

                bills.add(bill);
            }

            rs.close();
            ps.close();
            con.close();

        } catch (Exception e) {
            e.printStackTrace();
        }

        return bills;
    }
}
package com.hms.util;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import com.hms.model.User;
import com.hms.dao.UserDAO;

/**
 * Utility for secure, one-time administrator provisioning.
 * Allows safe initialization of an administrative account when no administrators exist,
 * and command-line password rotation without exposing credentials in logs or version control.
 */
public class AdminProvisioner {

    /**
     * Checks if at least one Administrator account exists in the database.
     */
    public static boolean hasAdministrator() {
        String sql = "SELECT COUNT(*) FROM users WHERE UPPER(role) = 'ADMIN'";
        try (Connection conn = DBConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            if (rs.next()) {
                return rs.getInt(1) > 0;
            }
        } catch (SQLException e) {
            System.err.println("[AdminProvisioner] Database error during admin existence check: " + e.getMessage());
        }
        return false;
    }

    /**
     * Provisions the initial administrator account ONLY if no admin accounts exist.
     * Rejects creation if an administrator already exists.
     *
     * @param username the admin username (minimum 3 chars)
     * @param password the admin password (minimum 8 chars)
     * @return true if provisioned successfully, false otherwise
     */
    public static boolean provisionInitialAdmin(String username, String password) {
        if (username == null || username.trim().isEmpty() || password == null || password.length() < 8) {
            System.err.println("[AdminProvisioner] Error: Invalid username or password (minimum 8 characters required).");
            return false;
        }

        if (hasAdministrator()) {
            System.err.println("[AdminProvisioner] Denied: An administrator account already exists. One-time setup is closed.");
            return false;
        }

        UserDAO userDAO = new UserDAO();
        if (userDAO.usernameExists(username.trim())) {
            System.err.println("[AdminProvisioner] Denied: Username already in use.");
            return false;
        }

        User admin = new User();
        admin.setUsername(username.trim());
        admin.setPassword(password); // Will be hashed by userDAO.registerUser using PasswordUtil
        admin.setRole("ADMIN");
        admin.setDoctorId(0);

        boolean success = userDAO.registerUser(admin);
        if (success) {
            System.out.println("[AdminProvisioner] Initial administrator account provisioned successfully.");
        }
        return success;
    }

    /**
     * CLI entry point for secure offline administrator provisioning or password reset.
     * Usage:
     *   java -cp ... com.hms.util.AdminProvisioner provision <username> <password>
     *   java -cp ... com.hms.util.AdminProvisioner rotate-password <username> <new_password>
     */
    public static void main(String[] args) {
        if (args.length < 3) {
            System.out.println("Usage:");
            System.out.println("  AdminProvisioner provision <username> <password>");
            System.out.println("  AdminProvisioner rotate-password <username> <new_password>");
            System.exit(1);
        }

        String action = args[0];
        String username = args[1];
        String password = args[2];

        if ("provision".equalsIgnoreCase(action)) {
            boolean result = provisionInitialAdmin(username, password);
            System.exit(result ? 0 : 1);
        } else if ("rotate-password".equalsIgnoreCase(action)) {
            if (password.length() < 8) {
                System.err.println("Password must be at least 8 characters long.");
                System.exit(1);
            }
            UserDAO dao = new UserDAO();
            String checkSql = "SELECT user_id, role FROM users WHERE username = ?";
            try (Connection conn = DBConnection.getConnection();
                 PreparedStatement ps = conn.prepareStatement(checkSql)) {
                ps.setString(1, username);
                try (ResultSet rs = ps.executeQuery()) {
                    if (rs.next()) {
                        int userId = rs.getInt("user_id");
                        String role = rs.getString("role");
                        if (!"ADMIN".equalsIgnoreCase(role)) {
                            System.err.println("Target user is not an administrator.");
                            System.exit(1);
                        }
                        String hashed = PasswordUtil.hashPassword(password);
                        boolean updated = dao.updatePassword(userId, hashed);
                        if (updated) {
                            System.out.println("Administrator password rotated successfully.");
                            System.exit(0);
                        }
                    } else {
                        System.err.println("User not found.");
                    }
                }
            } catch (SQLException e) {
                System.err.println("Database error: " + e.getMessage());
            }
            System.exit(1);
        } else {
            System.err.println("Unknown command: " + action);
            System.exit(1);
        }
    }
}

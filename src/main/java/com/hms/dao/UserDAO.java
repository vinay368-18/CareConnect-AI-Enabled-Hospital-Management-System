package com.hms.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import com.hms.model.User;
import com.hms.util.DBConnection;
import com.hms.util.PasswordUtil;

public class UserDAO {

    public User login(String username, String password) {

        User user = null;

        // Query by username ONLY — never include password in WHERE clause
        String sql = "SELECT user_id, username, password, role, doctor_id "
                   + "FROM users "
                   + "WHERE username = ?";

        try (Connection connection = DBConnection.getConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {

            statement.setString(1, username);

            try (ResultSet resultSet = statement.executeQuery()) {

                if (resultSet.next()) {

                    String storedPassword = resultSet.getString("password");

                    // Verify password using PasswordUtil (supports hashed and legacy plaintext)
                    if (PasswordUtil.verifyPassword(password, storedPassword)) {

                        user = new User();

                        user.setUserId(resultSet.getInt("user_id"));
                        user.setUsername(resultSet.getString("username"));
                        user.setRole(resultSet.getString("role"));
                        user.setDoctorId(resultSet.getInt("doctor_id"));

                        // Never store the password in the User object
                        user.setPassword(null);

                        // Auto-migrate: if stored password is legacy plaintext, upgrade to hash
                        if (!PasswordUtil.isHashed(storedPassword)) {
                            String hashed = PasswordUtil.hashPassword(password);
                            updatePassword(user.getUserId(), hashed);
                        }
                    }
                }
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }

        return user;
    }

    /**
     * Updates the password for a user by their user ID.
     *
     * @param userId         the user's ID
     * @param hashedPassword the new hashed password
     * @return true if the update was successful
     */
    public boolean updatePassword(int userId, String hashedPassword) {

        String sql = "UPDATE users SET password = ? WHERE user_id = ?";

        try (Connection connection = DBConnection.getConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {

            statement.setString(1, hashedPassword);
            statement.setInt(2, userId);

            return statement.executeUpdate() > 0;

        } catch (SQLException e) {
            e.printStackTrace();
        }

        return false;
    }

    public boolean usernameExists(String username) {

        String sql = "SELECT user_id FROM users WHERE username = ?";

        try (Connection connection = DBConnection.getConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {

            statement.setString(1, username);

            try (ResultSet resultSet = statement.executeQuery()) {
                return resultSet.next();
            }

        } catch (SQLException e) {
            e.printStackTrace();
        }

        return false;
    }

    public boolean registerUser(User user) {

        // Hash the password before storing
        String hashedPassword = PasswordUtil.hashPassword(user.getPassword());

        String sql = "INSERT INTO users "
                   + "(username, password, role, doctor_id) "
                   + "VALUES (?, ?, ?, ?)";

        try (Connection connection = DBConnection.getConnection();
             PreparedStatement statement = connection.prepareStatement(sql)) {

            statement.setString(1, user.getUsername());
            statement.setString(2, hashedPassword);
            statement.setString(3, user.getRole());

            if (user.getDoctorId() > 0) {
                statement.setInt(4, user.getDoctorId());
            } else {
                statement.setNull(4, java.sql.Types.INTEGER);
            }

            return statement.executeUpdate() > 0;

        } catch (SQLException e) {
            e.printStackTrace();
        }

        return false;
    }
}

package com.hms.util;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DBConnection {

    private static final String ENV_URL = "HMS_DB_URL";
    private static final String ENV_USER = "HMS_DB_USER";
    private static final String ENV_PASSWORD = "HMS_DB_PASSWORD";

    private static final String PROP_URL = "hms.db.url";
    private static final String PROP_USER = "hms.db.user";
    private static final String PROP_PASSWORD = "hms.db.password";

    private static final String DEFAULT_URL = "jdbc:mysql://localhost:3306/hospital";
    private static final String FALLBACK_PASSWORD = "Vinay@368";

    static {
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            System.err.println("[DBConnection] MySQL JDBC driver not found: " + e.getMessage());
        }
    }

    /**
     * Resolves configuration setting from environment variables or system properties.
     * When retrieving password settings, blank or empty values (e.g., "") return "" rather than null,
     * ensuring empty password configurations do not trigger null credential errors.
     */
    private static String getSetting(String envName, String propName) {
        String val = System.getenv(envName);
        if (val != null) {
            return val.trim();
        }
        val = System.getProperty(propName);
        if (val != null) {
            return val.trim();
        }
        if (ENV_PASSWORD.equals(envName) || PROP_PASSWORD.equals(propName)) {
            return "";
        }
        return null;
    }

    /**
     * Validates whether all required database connection settings are present.
     * Blank/empty passwords are valid and accepted without returning null.
     */
    public static boolean isConfigured() {
        String user = getSetting(ENV_USER, PROP_USER);
        String pass = getSetting(ENV_PASSWORD, PROP_PASSWORD);
        return user != null && !user.trim().isEmpty() && pass != null;
    }

    public static Connection getConnection() {
        String url = getSetting(ENV_URL, PROP_URL);
        if (url == null || url.trim().isEmpty()) {
            url = DEFAULT_URL;
        }

        String user = getSetting(ENV_USER, PROP_USER);
        String pass = getSetting(ENV_PASSWORD, PROP_PASSWORD);

        if (user == null || user.trim().isEmpty() || pass == null) {
            System.err.println("[DBConnection] Error: Database credentials not configured. Please set HMS_DB_USER and HMS_DB_PASSWORD environment variables.");
            return null;
        }

        try {
            return DriverManager.getConnection(url, user, pass);
        } catch (SQLException e) {
            if ((pass == null || pass.isEmpty()) && "root".equals(user)) {
                try {
                    return DriverManager.getConnection(url, user, FALLBACK_PASSWORD);
                } catch (SQLException ignored) {
                }
            }
            System.err.println("[DBConnection] Failed to connect to database: " + e.getMessage());
            return null;
        }
    }
}

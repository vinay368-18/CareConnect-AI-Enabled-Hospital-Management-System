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

    static {
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            System.err.println("[DBConnection] MySQL JDBC driver not found: " + e.getMessage());
        }
    }

    /**
     * Resolves a setting via AppConfig (environment variable, then system
     * property, then the local careconnect.env file).
     * A missing password resolves to "" so a passwordless local MySQL works.
     */
    private static String getSetting(String envName, String propName) {
        String val = AppConfig.get(envName, propName);
        if (val != null) {
            return val;
        }
        if (ENV_PASSWORD.equals(envName)) {
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
            System.err.println("[DBConnection] Error: Database credentials not configured. "
                    + "Set HMS_DB_USER and HMS_DB_PASSWORD as environment variables, or put them in "
                    + AppConfig.CONFIG_FILE_NAME + " at one of: " + AppConfig.searchLocations());
            return null;
        }

        try {
            return DriverManager.getConnection(url, user, pass);
        } catch (SQLException e) {
            System.err.println("[DBConnection] Failed to connect to database: " + e.getMessage());
            return null;
        }
    }
}

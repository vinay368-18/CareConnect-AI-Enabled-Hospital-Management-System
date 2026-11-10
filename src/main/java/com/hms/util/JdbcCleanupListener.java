package com.hms.util;

import jakarta.servlet.ServletContextEvent;
import jakarta.servlet.ServletContextListener;

import java.sql.Driver;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Collections;

/**
 * Releases the MySQL driver when the web application stops.
 *
 * The driver JAR lives in WEB-INF/lib, so DriverManager and the driver's
 * "abandoned connection cleanup" thread keep references to this webapp's
 * class loader. Without this listener every redeploy or reload logs
 * "registered the JDBC driver ... but failed to unregister it" and
 * "appears to have started a thread named [mysql-cj-abandoned-connection-cleanup]"
 * and leaks the old copy of the application in memory.
 *
 * Registered in WEB-INF/web.xml.
 */
public class JdbcCleanupListener implements ServletContextListener {

    @Override
    public void contextInitialized(ServletContextEvent sce) {
        // nothing to do at startup
    }

    @Override
    public void contextDestroyed(ServletContextEvent sce) {
        ClassLoader webappLoader = Thread.currentThread().getContextClassLoader();

        // Deregister only drivers loaded by this web application
        for (Driver driver : Collections.list(DriverManager.getDrivers())) {
            if (driver.getClass().getClassLoader() == webappLoader) {
                try {
                    DriverManager.deregisterDriver(driver);
                } catch (SQLException e) {
                    System.err.println("[JdbcCleanup] Could not deregister " + driver + ": " + e.getMessage());
                }
            }
        }

        // Stop MySQL Connector/J's background cleanup thread (looked up by name so
        // this class does not fail if a different driver is ever used)
        try {
            Class.forName("com.mysql.cj.jdbc.AbandonedConnectionCleanupThread", false, webappLoader)
                 .getMethod("checkedShutdown")
                 .invoke(null);
        } catch (ClassNotFoundException e) {
            // MySQL driver not present: nothing to stop
        } catch (ReflectiveOperationException | RuntimeException e) {
            System.err.println("[JdbcCleanup] Could not stop the MySQL cleanup thread: " + e);
        }
    }
}

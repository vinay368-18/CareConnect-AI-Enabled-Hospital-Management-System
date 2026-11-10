package com.hms.util;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Central configuration lookup for the web application.
 *
 * Each setting is resolved in this order, first match wins:
 *   1. Environment variable      (e.g. HMS_DB_USER)
 *   2. Java system property      (e.g. -Dhms.db.user=...)
 *   3. Local config file         (KEY=VALUE lines, same format as .env.example)
 *
 * The config file is looked for, in order, at:
 *   - the path in HMS_CONFIG_FILE (environment) or -Dhms.config.file
 *   - ${catalina.base}/conf/careconnect.env
 *   - ${user.home}/.careconnect/careconnect.env
 *
 * The file lives outside the project folder, so credentials never enter Git.
 * It exists because many launchers (Eclipse, the VS Code server connector,
 * Windows services) start Tomcat without the caller's environment variables.
 *
 * File format: one KEY=VALUE per line; blank lines and lines starting with '#'
 * are ignored; surrounding quotes on a value are removed; no escape sequences,
 * so backslashes and special characters in passwords are taken literally.
 * Values are never logged.
 */
public final class AppConfig {

    public static final String CONFIG_FILE_NAME = "careconnect.env";

    private static volatile Map<String, String> fileValues;
    private static volatile Path loadedFrom;

    private AppConfig() {
    }

    /**
     * Returns the setting, or null when it is not defined anywhere.
     * Environment and system-property values are trimmed; an empty value that
     * is explicitly set is returned as "" (callers decide whether "" is valid).
     */
    public static String get(String envName, String propName) {
        String val = System.getenv(envName);
        if (val != null) {
            return val.trim();
        }
        if (propName != null) {
            val = System.getProperty(propName);
            if (val != null) {
                return val.trim();
            }
        }
        return values().get(envName);
    }

    /** Returns the setting, or the default when it is undefined or blank. */
    public static String getOrDefault(String envName, String propName, String defaultValue) {
        String val = get(envName, propName);
        return (val == null || val.isEmpty()) ? defaultValue : val;
    }

    /** The config file that was loaded, or null if none was found. */
    public static Path configFile() {
        values();
        return loadedFrom;
    }

    /** All locations searched for the config file, in order. Used for error messages. */
    public static List<Path> searchLocations() {
        List<Path> paths = new ArrayList<>();
        String explicit = System.getenv("HMS_CONFIG_FILE");
        if (explicit == null || explicit.trim().isEmpty()) {
            explicit = System.getProperty("hms.config.file");
        }
        if (explicit != null && !explicit.trim().isEmpty()) {
            paths.add(Paths.get(explicit.trim()));
        }
        String catalinaBase = System.getProperty("catalina.base");
        if (catalinaBase != null && !catalinaBase.trim().isEmpty()) {
            paths.add(Paths.get(catalinaBase.trim(), "conf", CONFIG_FILE_NAME));
        }
        String home = System.getProperty("user.home");
        if (home != null && !home.trim().isEmpty()) {
            paths.add(Paths.get(home.trim(), ".careconnect", CONFIG_FILE_NAME));
        }
        return paths;
    }

    private static Map<String, String> values() {
        Map<String, String> v = fileValues;
        if (v == null) {
            synchronized (AppConfig.class) {
                v = fileValues;
                if (v == null) {
                    v = load();
                    fileValues = v;
                }
            }
        }
        return v;
    }

    private static Map<String, String> load() {
        for (Path p : searchLocations()) {
            if (Files.isRegularFile(p)) {
                try {
                    Map<String, String> parsed = parse(Files.readAllLines(p, StandardCharsets.UTF_8));
                    loadedFrom = p;
                    System.out.println("[AppConfig] Loaded settings from " + p);
                    return Collections.unmodifiableMap(parsed);
                } catch (IOException e) {
                    System.err.println("[AppConfig] Could not read " + p + ": " + e.getMessage());
                }
            }
        }
        return Collections.emptyMap();
    }

    static Map<String, String> parse(List<String> lines) {
        Map<String, String> map = new HashMap<>();
        for (String raw : lines) {
            String line = raw.trim();
            if (line.startsWith("﻿")) {
                line = line.substring(1).trim();
            }
            if (line.isEmpty() || line.startsWith("#")) {
                continue;
            }
            if (line.startsWith("export ")) {
                line = line.substring(7).trim();
            }
            int eq = line.indexOf('=');
            if (eq <= 0) {
                continue;
            }
            String key = line.substring(0, eq).trim();
            String value = line.substring(eq + 1).trim();
            if (value.length() >= 2
                    && ((value.startsWith("\"") && value.endsWith("\""))
                        || (value.startsWith("'") && value.endsWith("'")))) {
                value = value.substring(1, value.length() - 1);
            }
            map.put(key, value);
        }
        return map;
    }
}

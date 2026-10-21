package com.hms.util;

import java.security.SecureRandom;
import java.util.Base64;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;

/**
 * Cross-Site Request Forgery (CSRF) protection utility.
 */
public class CSRFUtil {

    public static final String CSRF_SESSION_ATTR = "csrf_token";
    public static final String CSRF_PARAM_NAME = "csrf_token";
    public static final String CSRF_HEADER_NAME = "X-CSRF-Token";

    private static final SecureRandom RANDOM = new SecureRandom();

    /**
     * Retrieves the existing CSRF token for the session or generates a new one.
     */
    public static String getToken(HttpSession session) {
        if (session == null) {
            return "";
        }
        synchronized (session) {
            String token = (String) session.getAttribute(CSRF_SESSION_ATTR);
            if (token == null || token.trim().isEmpty()) {
                byte[] bytes = new byte[32];
                RANDOM.nextBytes(bytes);
                token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
                session.setAttribute(CSRF_SESSION_ATTR, token);
            }
            return token;
        }
    }

    /**
     * Validates that the request contains a valid CSRF token matching the session.
     */
    public static boolean isValid(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session == null) {
            return false;
        }
        String sessionToken = (String) session.getAttribute(CSRF_SESSION_ATTR);
        if (sessionToken == null || sessionToken.trim().isEmpty()) {
            return false;
        }

        // Try parameter first, then header
        String requestToken = request.getParameter(CSRF_PARAM_NAME);
        if (requestToken == null || requestToken.trim().isEmpty()) {
            requestToken = request.getHeader(CSRF_HEADER_NAME);
        }

        if (requestToken == null || requestToken.trim().isEmpty()) {
            return false;
        }

        return constantTimeEquals(sessionToken, requestToken.trim());
    }

    private static boolean constantTimeEquals(String a, String b) {
        byte[] bytesA = a.getBytes();
        byte[] bytesB = b.getBytes();
        if (bytesA.length != bytesB.length) {
            return false;
        }
        int result = 0;
        for (int i = 0; i < bytesA.length; i++) {
            result |= bytesA[i] ^ bytesB[i];
        }
        return result == 0;
    }
}

package com.hms.util;

import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.InvalidKeySpecException;
import java.util.Base64;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/**
 * Utility class for secure password hashing and verification
 * using PBKDF2WithHmacSHA256.
 *
 * Storage format: PBKDF2:iterations:base64(salt):base64(hash)
 */
public class PasswordUtil {

    private static final String ALGORITHM = "PBKDF2WithHmacSHA256";
    private static final String PREFIX = "PBKDF2:";
    private static final int ITERATIONS = 210_000;  // OWASP recommendation
    private static final int SALT_LENGTH = 16;      // 16-byte random salt
    private static final int KEY_LENGTH = 256;       // 32-byte derived key (256 bits)

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();

    /**
     * Hashes a plaintext password using PBKDF2WithHmacSHA256.
     *
     * @param plaintext the plaintext password to hash
     * @return the hashed password in the format PBKDF2:iterations:base64(salt):base64(hash)
     */
    public static String hashPassword(String plaintext) {

        byte[] salt = new byte[SALT_LENGTH];
        SECURE_RANDOM.nextBytes(salt);

        byte[] hash = deriveKey(plaintext, salt, ITERATIONS);

        String saltBase64 = Base64.getEncoder().encodeToString(salt);
        String hashBase64 = Base64.getEncoder().encodeToString(hash);

        return PREFIX + ITERATIONS + ":" + saltBase64 + ":" + hashBase64;
    }

    /**
     * Verifies a plaintext password against a stored value.
     * Supports both PBKDF2 hashes and legacy plaintext passwords
     * (for migration: if stored doesn't start with "PBKDF2:", treat
     * it as legacy plaintext and compare directly).
     *
     * @param plaintext the plaintext password to verify
     * @param stored    the stored password (hashed or legacy plaintext)
     * @return true if the password matches
     */
    public static boolean verifyPassword(String plaintext, String stored) {

        if (stored == null || plaintext == null) {
            return false;
        }

        // Handle PBKDF2 hashed passwords
        if (isHashed(stored)) {

            String[] parts = stored.split(":");

            if (parts.length != 4) {
                return false;
            }

            try {

                int iterations = Integer.parseInt(parts[1]);
                byte[] salt = Base64.getDecoder().decode(parts[2]);
                byte[] storedHash = Base64.getDecoder().decode(parts[3]);

                byte[] computedHash = deriveKey(plaintext, salt, iterations);

                return constantTimeEquals(storedHash, computedHash);

            } catch (IllegalArgumentException e) {
                return false;
            }
        }

        // Legacy plaintext comparison (for migration)
        return stored.equals(plaintext);
    }

    /**
     * Returns true if the stored value looks like a PBKDF2 hash.
     *
     * @param stored the stored password value
     * @return true if it starts with the PBKDF2 prefix
     */
    public static boolean isHashed(String stored) {
        return stored != null && stored.startsWith(PREFIX);
    }

    /**
     * Derives a key from a password using PBKDF2WithHmacSHA256.
     */
    private static byte[] deriveKey(String password, byte[] salt, int iterations) {

        try {

            PBEKeySpec spec = new PBEKeySpec(
                password.toCharArray(), salt, iterations, KEY_LENGTH
            );

            SecretKeyFactory factory = SecretKeyFactory.getInstance(ALGORITHM);

            return factory.generateSecret(spec).getEncoded();

        } catch (NoSuchAlgorithmException | InvalidKeySpecException e) {
            throw new RuntimeException("Password hashing failed", e);
        }
    }

    /**
     * Constant-time byte array comparison to prevent timing attacks.
     */
    private static boolean constantTimeEquals(byte[] a, byte[] b) {

        if (a.length != b.length) {
            return false;
        }

        int result = 0;

        for (int i = 0; i < a.length; i++) {
            result |= a[i] ^ b[i];
        }

        return result == 0;
    }
}

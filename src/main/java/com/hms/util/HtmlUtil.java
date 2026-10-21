package com.hms.util;

/**
 * Utility for HTML escaping to protect against Cross-Site Scripting (XSS).
 */
public class HtmlUtil {

    /**
     * Escapes HTML special characters in the input string.
     *
     * @param input the raw string
     * @return the HTML-escaped string, or empty string if input is null
     */
    public static String escapeHtml(String input) {
        if (input == null) {
            return "";
        }
        StringBuilder out = new StringBuilder(Math.max(16, input.length()));
        for (int i = 0; i < input.length(); i++) {
            char c = input.charAt(i);
            switch (c) {
                case '&':
                    out.append("&amp;");
                    break;
                case '<':
                    out.append("&lt;");
                    break;
                case '>':
                    out.append("&gt;");
                    break;
                case '"':
                    out.append("&quot;");
                    break;
                case '\'':
                    out.append("&#x27;");
                    break;
                case '/':
                    out.append("&#x2F;");
                    break;
                default:
                    out.append(c);
            }
        }
        return out.toString();
    }
}

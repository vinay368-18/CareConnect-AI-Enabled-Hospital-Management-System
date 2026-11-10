package com.hms.service;

import com.hms.model.CVDScreening;
import com.hms.util.AppConfig;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public class CVDClient {

    private static final String DEFAULT_API_URL = "http://127.0.0.1:5000";
    private final String baseUrl;
    private final String apiKey;
    private volatile HttpClient httpClient;

    public CVDClient() {
        this(resolveBaseUrl(), resolveApiKey());
    }

    public CVDClient(String baseUrl) {
        this(baseUrl, resolveApiKey());
    }

    public CVDClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl != null ? baseUrl : DEFAULT_API_URL;
        this.apiKey = apiKey != null ? apiKey : "";
    }

    private HttpClient getClient() {
        if (httpClient == null) {
            synchronized (this) {
                if (httpClient == null) {
                    httpClient = HttpClient.newBuilder()
                            .connectTimeout(Duration.ofSeconds(15))
                            .build();
                }
            }
        }
        return httpClient;
    }

    /** Environment variable, then -Dhms.ai.api.url, then careconnect.env (see AppConfig). */
    private static String resolveBaseUrl() {
        return AppConfig.getOrDefault("HMS_AI_API_URL", "hms.ai.api.url", DEFAULT_API_URL);
    }

    /** Environment variable, then -Dhms.ai.api.key, then careconnect.env (see AppConfig). */
    private static String resolveApiKey() {
        return AppConfig.getOrDefault("HMS_AI_API_KEY", "hms.ai.api.key", "");
    }

    public String getApiKey() { return apiKey; }
    public String getBaseUrl() { return baseUrl; }

    public boolean isServiceAvailable() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/health"))
                    .timeout(Duration.ofSeconds(5))
                    .GET()
                    .build();
            HttpResponse<String> response = getClient().send(request, HttpResponse.BodyHandlers.ofString());
            return response.statusCode() == 200 && response.body().contains("healthy");
        } catch (Exception e) {
            return false;
        }
    }

    public CVDScreening analyzeImage(byte[] imageBytes, String filename, String modelName)
            throws IOException, InterruptedException {
        String boundary = "----WebKitFormBoundary" + UUID.randomUUID().toString().replace("-", "");
        byte[] multipartBody = createMultipartBody(boundary, imageBytes, filename, modelName);

        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/predict"))
                .timeout(Duration.ofSeconds(60))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(HttpRequest.BodyPublishers.ofByteArray(multipartBody));

        if (!apiKey.isEmpty()) {
            builder.header("X-API-Key", apiKey);
        }

        HttpResponse<String> response = getClient().send(builder.build(), HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() == 401) {
            throw new IOException("AI Microservice authentication failed (HTTP 401). Verify HMS_AI_API_KEY configuration.");
        }
        if (response.statusCode() != 200) {
            throw new IOException("AI Microservice returned error HTTP " + response.statusCode());
        }

        return parsePredictionResponse(response.body());
    }

    public CVDScreening analyzeImage(byte[] imageBytes, String filename) throws IOException, InterruptedException {
        return analyzeImage(imageBytes, filename, null);
    }

    public static class VesselResult {
        private final byte[] overlayPng;
        private final double densityPercent;

        public VesselResult(byte[] overlayPng, double densityPercent) {
            this.overlayPng = overlayPng;
            this.densityPercent = densityPercent;
        }
        public byte[] getOverlayPng() { return overlayPng; }
        public double getDensityPercent() { return densityPercent; }
    }

    public VesselResult segmentVessels(byte[] imageBytes, String filename) throws IOException, InterruptedException {
        return segmentVessels(imageBytes, filename, null);
    }

    public VesselResult segmentVessels(byte[] imageBytes, String filename, String modelName) throws IOException, InterruptedException {
        String boundary = "----WebKitFormBoundary" + UUID.randomUUID().toString().replace("-", "");
        byte[] multipartBody = createMultipartBody(boundary, imageBytes, filename, modelName);

        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/segment"))
                .timeout(Duration.ofSeconds(120))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(HttpRequest.BodyPublishers.ofByteArray(multipartBody));

        if (!apiKey.isEmpty()) {
            builder.header("X-API-Key", apiKey);
        }

        HttpResponse<byte[]> response = getClient().send(builder.build(), HttpResponse.BodyHandlers.ofByteArray());
        if (response.statusCode() == 401) {
            throw new IOException("AI Microservice authentication failed during segmentation (HTTP 401).");
        }
        if (response.statusCode() != 200) {
            throw new IOException("Vessel segmentation returned HTTP " + response.statusCode());
        }

        double density = 0.0;
        String header = response.headers().firstValue("X-Vessel-Density").orElse(null);
        if (header != null) {
            try {
                density = Double.parseDouble(header.trim());
            } catch (NumberFormatException ignored) {}
        }
        return new VesselResult(response.body(), density);
    }

    private String detectContentType(String filename) {
        if (filename != null && filename.toLowerCase().endsWith(".png")) {
            return "image/png";
        }
        return "image/jpeg";
    }

    private byte[] createMultipartBody(String boundary, byte[] fileBytes, String filename, String modelName)
            throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        String safeFilename = filename != null ? filename.replaceAll("[^a-zA-Z0-9._-]", "_") : "scan.jpg";
        String contentType = detectContentType(safeFilename);

        String fileHeader = "--" + boundary + "\r\n"
                          + "Content-Disposition: form-data; name=\"file\"; filename=\"" + safeFilename + "\"\r\n"
                          + "Content-Type: " + contentType + "\r\n\r\n";

        baos.write(fileHeader.getBytes(StandardCharsets.UTF_8));
        baos.write(fileBytes);
        baos.write("\r\n".getBytes(StandardCharsets.UTF_8));

        if (modelName != null && !modelName.trim().isEmpty()) {
            String modelPart = "--" + boundary + "\r\n"
                             + "Content-Disposition: form-data; name=\"model_name\"\r\n\r\n"
                             + modelName.trim() + "\r\n";
            baos.write(modelPart.getBytes(StandardCharsets.UTF_8));
        }

        String footer = "--" + boundary + "--\r\n";
        baos.write(footer.getBytes(StandardCharsets.UTF_8));
        return baos.toByteArray();
    }

    private CVDScreening parsePredictionResponse(String json) {
        CVDScreening screening = new CVDScreening();
        try {
            Map<String, Object> root = SimpleJsonParser.parseObject(json);

            Map<String, Object> cvdObj = jsonMap(root, "cvd");
            if (cvdObj != null) {
                screening.setCvdPrediction(jsonString(cvdObj, "result", "Negative"));
                screening.setCvdProbability(jsonDouble(cvdObj, "probability", 0.0));
            } else {
                screening.setCvdPrediction(jsonString(root, "cvd_prediction", "Negative"));
                screening.setCvdProbability(jsonDouble(root, "cvd_probability", 0.0));
            }

            Map<String, Object> htObj = jsonMap(root, "hypertension");
            if (htObj != null) {
                screening.setHypertensionPrediction(jsonString(htObj, "result", "Negative"));
                screening.setHypertensionProbability(jsonDouble(htObj, "probability", 0.0));
            } else {
                screening.setHypertensionPrediction(jsonString(root, "hypertension_prediction", "Negative"));
                screening.setHypertensionProbability(jsonDouble(root, "hypertension_probability", 0.0));
            }

            Map<String, Object> drObj = jsonMap(root, "diabetic_retinopathy");
            if (drObj != null) {
                String drLabel = jsonString(drObj, "label", null);
                if (drLabel == null) {
                    Object gradeObj = drObj.get("grade");
                    drLabel = gradeObj != null ? "Grade " + gradeObj : "No DR";
                }
                screening.setDrGrade(drLabel);
                screening.setDrConfidence(jsonDouble(drObj, "confidence", 0.0));
            } else {
                screening.setDrGrade(jsonString(root, "dr_grade", "No DR"));
                screening.setDrConfidence(jsonDouble(root, "dr_confidence", 0.0));
            }

            Map<String, Object> riskObj = jsonMap(root, "risk_assessment");
            if (riskObj != null) {
                screening.setRiskLevel(jsonString(riskObj, "risk_level", "Low Risk"));
                screening.setRecommendation(jsonString(riskObj, "recommendation",
                        "Continue annual preventive health check-ups."));
            } else {
                screening.setRiskLevel(jsonString(root, "risk_level", "Low Risk"));
                screening.setRecommendation(jsonString(root, "recommendation",
                        "Continue annual preventive health check-ups."));
            }

            String modelUsed = jsonString(root, "model_used", null);
            if (modelUsed == null) modelUsed = jsonString(root, "model_name", null);
            if (modelUsed != null) screening.setModelName(modelUsed);

            if (root.containsKey("vessel_density")) {
                double vd = jsonDouble(root, "vessel_density", -1.0);
                if (vd >= 0) screening.setVesselDensity(vd);
            }
            if (root.containsKey("mask_overlay_url")) {
                String maskUrl = jsonString(root, "mask_overlay_url", null);
                if (maskUrl != null && !maskUrl.isEmpty()) screening.setVesselOverlayPath(maskUrl);
            }
        } catch (Exception e) {
            System.err.println("[CVDClient] JSON parsing fallback applied: " + e.getMessage());
            screening.setCvdPrediction("Negative");
            screening.setCvdProbability(0.0);
            screening.setHypertensionPrediction("Negative");
            screening.setHypertensionProbability(0.0);
            screening.setDrGrade("No DR");
            screening.setDrConfidence(0.0);
            screening.setRiskLevel("Low Risk");
            screening.setRecommendation("Continue annual preventive health check-ups.");
        }
        return screening;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> jsonMap(Map<String, Object> map, String key) {
        Object val = map.get(key);
        return (val instanceof Map) ? (Map<String, Object>) val : null;
    }

    private String jsonString(Map<String, Object> map, String key, String defaultValue) {
        Object val = map.get(key);
        return (val instanceof String) ? (String) val : defaultValue;
    }

    private double jsonDouble(Map<String, Object> map, String key, double defaultValue) {
        Object val = map.get(key);
        if (val instanceof Number) return ((Number) val).doubleValue();
        if (val instanceof String) {
            try { return Double.parseDouble((String) val); } catch (NumberFormatException ignored) {}
        }
        return defaultValue;
    }

    static class SimpleJsonParser {
        private final String input;
        private int pos;

        private SimpleJsonParser(String input) {
            this.input = input;
            this.pos = 0;
        }

        static Map<String, Object> parseObject(String json) {
            SimpleJsonParser parser = new SimpleJsonParser(json.trim());
            Object result = parser.parseValue();
            if (result instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> map = (Map<String, Object>) result;
                return map;
            }
            throw new RuntimeException("Expected JSON object at root");
        }

        private void skipWhitespace() {
            while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) pos++;
        }

        private char peek() {
            skipWhitespace();
            if (pos >= input.length()) throw new RuntimeException("Unexpected end of JSON input");
            return input.charAt(pos);
        }

        private char next() {
            skipWhitespace();
            if (pos >= input.length()) throw new RuntimeException("Unexpected end of JSON input");
            return input.charAt(pos++);
        }

        private void expect(char c) {
            char actual = next();
            if (actual != c) throw new RuntimeException("Expected '" + c + "' but got '" + actual + "'");
        }

        private Object parseValue() {
            char c = peek();
            switch (c) {
                case '{': return parseObjectInternal();
                case '[': return parseArray();
                case '"': return parseString();
                case 't': case 'f': return parseBoolean();
                case 'n': return parseNull();
                default:
                    if (c == '-' || (c >= '0' && c <= '9')) return parseNumber();
                    throw new RuntimeException("Unexpected character '" + c + "' at position " + pos);
            }
        }

        private Map<String, Object> parseObjectInternal() {
            Map<String, Object> map = new HashMap<>();
            expect('{');
            if (peek() == '}') { pos++; return map; }
            while (true) {
                String key = parseString();
                expect(':');
                Object value = parseValue();
                map.put(key, value);
                char c = next();
                if (c == '}') break;
                if (c != ',') throw new RuntimeException("Expected ',' or '}' at position " + (pos - 1));
            }
            return map;
        }

        private java.util.List<Object> parseArray() {
            java.util.List<Object> list = new java.util.ArrayList<>();
            expect('[');
            if (peek() == ']') { pos++; return list; }
            while (true) {
                list.add(parseValue());
                char c = next();
                if (c == ']') break;
                if (c != ',') throw new RuntimeException("Expected ',' or ']' at position " + (pos - 1));
            }
            return list;
        }

        private String parseString() {
            expect('"');
            StringBuilder sb = new StringBuilder();
            while (pos < input.length()) {
                char c = input.charAt(pos++);
                if (c == '"') return sb.toString();
                if (c == '\\') {
                    char escaped = input.charAt(pos++);
                    switch (escaped) {
                        case '"': sb.append('"'); break;
                        case '\\': sb.append('\\'); break;
                        case '/': sb.append('/'); break;
                        case 'b': sb.append('\b'); break;
                        case 'f': sb.append('\f'); break;
                        case 'n': sb.append('\n'); break;
                        case 'r': sb.append('\r'); break;
                        case 't': sb.append('\t'); break;
                        case 'u':
                            String hex = input.substring(pos, pos + 4);
                            sb.append((char) Integer.parseInt(hex, 16));
                            pos += 4;
                            break;
                        default: sb.append(escaped);
                    }
                } else {
                    sb.append(c);
                }
            }
            throw new RuntimeException("Unterminated string");
        }

        private Number parseNumber() {
            skipWhitespace();
            int start = pos;
            if (pos < input.length() && input.charAt(pos) == '-') pos++;
            while (pos < input.length() && Character.isDigit(input.charAt(pos))) pos++;
            boolean isFloat = false;
            if (pos < input.length() && input.charAt(pos) == '.') {
                isFloat = true; pos++;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) pos++;
            }
            if (pos < input.length() && (input.charAt(pos) == 'e' || input.charAt(pos) == 'E')) {
                isFloat = true; pos++;
                if (pos < input.length() && (input.charAt(pos) == '+' || input.charAt(pos) == '-')) pos++;
                while (pos < input.length() && Character.isDigit(input.charAt(pos))) pos++;
            }
            String numStr = input.substring(start, pos);
            if (isFloat) return Double.parseDouble(numStr);
            long val = Long.parseLong(numStr);
            if (val >= Integer.MIN_VALUE && val <= Integer.MAX_VALUE) return (int) val;
            return val;
        }

        private Boolean parseBoolean() {
            if (input.startsWith("true", pos)) { pos += 4; return Boolean.TRUE; }
            if (input.startsWith("false", pos)) { pos += 5; return Boolean.FALSE; }
            throw new RuntimeException("Expected boolean at position " + pos);
        }

        private Object parseNull() {
            if (input.startsWith("null", pos)) { pos += 4; return null; }
            throw new RuntimeException("Expected null at position " + pos);
        }
    }
}

package com.hms.service;

import com.hms.model.CVDScreening;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Service client communicating with the Python PyTorch CVD Microservice.
 */
public class CVDClient {

    private static final String DEFAULT_API_URL = "http://127.0.0.1:5000";
    private final String baseUrl;
    private final HttpClient httpClient;

    public CVDClient() {
        this(DEFAULT_API_URL);
    }

    public CVDClient(String baseUrl) {
        this.baseUrl = baseUrl;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    /**
     * Checks if the Python PyTorch AI microservice is online and healthy.
     */
    public boolean isServiceAvailable() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/health"))
                    .timeout(Duration.ofSeconds(4))
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            return response.statusCode() == 200 && response.body().contains("healthy");
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Sends the retinal fundus image bytes to the AI microservice and returns the predictions.
     */
    public CVDScreening analyzeImage(byte[] imageBytes, String filename) throws IOException, InterruptedException {
        String boundary = "----WebKitFormBoundary" + UUID.randomUUID().toString().replace("-", "");
        byte[] multipartBody = createMultipartBody(boundary, imageBytes, filename);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/predict"))
                .timeout(Duration.ofSeconds(45))
                .header("Content-Type", "multipart/form-data; boundary=" + boundary)
                .POST(HttpRequest.BodyPublishers.ofByteArray(multipartBody))
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new IOException("AI Microservice returned error HTTP " + response.statusCode() + ": " + response.body());
        }

        return parsePredictionResponse(response.body());
    }

    private byte[] createMultipartBody(String boundary, byte[] fileBytes, String filename) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();

        String header = "--" + boundary + "\r\n"
                      + "Content-Disposition: form-data; name=\"file\"; filename=\"" + filename + "\"\r\n"
                      + "Content-Type: image/jpeg\r\n\r\n";

        String footer = "\r\n--" + boundary + "--\r\n";

        baos.write(header.getBytes(StandardCharsets.UTF_8));
        baos.write(fileBytes);
        baos.write(footer.getBytes(StandardCharsets.UTF_8));

        return baos.toByteArray();
    }

    /**
     * Lightweight JSON parser for the AI service response.
     */
    private CVDScreening parsePredictionResponse(String json) {
        CVDScreening screening = new CVDScreening();

        screening.setCvdPrediction(extractString(json, "cvd_prediction", "Negative"));
        screening.setCvdProbability(extractDouble(json, "cvd_probability", 0.0));
        screening.setHypertensionPrediction(extractString(json, "hypertension_prediction", "Negative"));
        screening.setHypertensionProbability(extractDouble(json, "hypertension_probability", 0.0));
        screening.setDrGrade(extractString(json, "dr_grade", "No DR"));
        screening.setDrConfidence(extractDouble(json, "dr_confidence", 0.0));
        screening.setRiskLevel(extractString(json, "risk_level", "Low Risk"));
        screening.setRecommendation(extractString(json, "recommendation", "Continue annual preventive health check-ups."));

        return screening;
    }

    private String extractString(String json, String key, String defaultValue) {
        Pattern pattern = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*\"([^\"]*)\"");
        Matcher matcher = pattern.matcher(json);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return defaultValue;
    }

    private double extractDouble(String json, String key, double defaultValue) {
        Pattern pattern = Pattern.compile("\"" + Pattern.quote(key) + "\"\\s*:\\s*([0-9.]+)");
        Matcher matcher = pattern.matcher(json);
        if (matcher.find()) {
            try {
                return Double.parseDouble(matcher.group(1));
            } catch (NumberFormatException e) {
                return defaultValue;
            }
        }
        return defaultValue;
    }
}

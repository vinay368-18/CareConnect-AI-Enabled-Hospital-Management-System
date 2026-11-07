package com.hms.model;

import java.sql.Timestamp;

/**
 * Model representing an AI-powered Cardiovascular Disease (CVD) and
 * Retinal Multi-Task Screening result.
 */
public class CVDScreening {

    private int screeningId;
    private int patientId;
    private String patientName;
    private int patientAge;
    private String patientGender;
    private String patientPhone;

    private Integer doctorId;
    private String doctorName;
    private String doctorSpecialization;

    private Integer appointmentId;
    private String imagePath;

    // Segmentation model used (e.g., "Residual U-Net", "U-Net", "Attention U-Net")
    private String modelName;

    // Residual U-Net vessel segmentation (optional; null when not available)
    private String vesselOverlayPath;
    private Double vesselDensity;           // % of the retinal area classified as vessel

    // AI Prediction Results
    private String cvdPrediction;              // "Positive" or "Negative"
    private double cvdProbability;             // 0.0 to 1.0
    private String hypertensionPrediction;     // "Positive" or "Negative"
    private double hypertensionProbability;    // 0.0 to 1.0
    private String drGrade;                    // "No DR", "Mild", "Moderate", "Severe", "Proliferative"
    private double drConfidence;               // 0.0 to 1.0
    private String riskLevel;                  // "Low Risk", "Moderate Risk", "High Risk"
    private String notes;
    private String recommendation;
    private Timestamp screeningDate;

    public CVDScreening() {
    }

    public int getScreeningId() {
        return screeningId;
    }

    public void setScreeningId(int screeningId) {
        this.screeningId = screeningId;
    }

    public int getPatientId() {
        return patientId;
    }

    public void setPatientId(int patientId) {
        this.patientId = patientId;
    }

    public String getPatientName() {
        return patientName;
    }

    public void setPatientName(String patientName) {
        this.patientName = patientName;
    }

    public int getPatientAge() {
        return patientAge;
    }

    public void setPatientAge(int patientAge) {
        this.patientAge = patientAge;
    }

    public String getPatientGender() {
        return patientGender;
    }

    public void setPatientGender(String patientGender) {
        this.patientGender = patientGender;
    }

    public String getPatientPhone() {
        return patientPhone;
    }

    public void setPatientPhone(String patientPhone) {
        this.patientPhone = patientPhone;
    }

    public Integer getDoctorId() {
        return doctorId;
    }

    public void setDoctorId(Integer doctorId) {
        this.doctorId = doctorId;
    }

    public String getDoctorName() {
        return doctorName;
    }

    public void setDoctorName(String doctorName) {
        this.doctorName = doctorName;
    }

    public String getDoctorSpecialization() {
        return doctorSpecialization;
    }

    public void setDoctorSpecialization(String doctorSpecialization) {
        this.doctorSpecialization = doctorSpecialization;
    }

    public Integer getAppointmentId() {
        return appointmentId;
    }

    public void setAppointmentId(Integer appointmentId) {
        this.appointmentId = appointmentId;
    }

    public String getImagePath() {
        return imagePath;
    }

    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }

    public String getModelName() {
        return modelName;
    }

    public void setModelName(String modelName) {
        this.modelName = modelName;
    }

    public String getCvdPrediction() {
        return cvdPrediction;
    }

    public void setCvdPrediction(String cvdPrediction) {
        this.cvdPrediction = cvdPrediction;
    }

    // Alias for specification compatibility
    public String getCvdResult() {
        return cvdPrediction;
    }

    public void setCvdResult(String cvdResult) {
        this.cvdPrediction = cvdResult;
    }

    public double getCvdProbability() {
        return cvdProbability;
    }

    public void setCvdProbability(double cvdProbability) {
        this.cvdProbability = cvdProbability;
    }

    public String getHypertensionPrediction() {
        return hypertensionPrediction;
    }

    public void setHypertensionPrediction(String hypertensionPrediction) {
        this.hypertensionPrediction = hypertensionPrediction;
    }

    // Alias for specification compatibility
    public String getHtResult() {
        return hypertensionPrediction;
    }

    public void setHtResult(String htResult) {
        this.hypertensionPrediction = htResult;
    }

    public double getHypertensionProbability() {
        return hypertensionProbability;
    }

    public void setHypertensionProbability(double hypertensionProbability) {
        this.hypertensionProbability = hypertensionProbability;
    }

    // Alias for specification compatibility
    public double getHtProbability() {
        return hypertensionProbability;
    }

    public void setHtProbability(double htProbability) {
        this.hypertensionProbability = htProbability;
    }

    public String getDrGrade() {
        return drGrade;
    }

    public void setDrGrade(String drGrade) {
        this.drGrade = drGrade;
    }

    public double getDrConfidence() {
        return drConfidence;
    }

    public void setDrConfidence(double drConfidence) {
        this.drConfidence = drConfidence;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    public String getRecommendation() {
        return recommendation;
    }

    public void setRecommendation(String recommendation) {
        this.recommendation = recommendation;
    }

    // Alias for specification compatibility
    public String getRecommendations() {
        return recommendation;
    }

    public void setRecommendations(String recommendations) {
        this.recommendation = recommendations;
    }

    public Timestamp getScreeningDate() {
        return screeningDate;
    }

    public void setScreeningDate(Timestamp screeningDate) {
        this.screeningDate = screeningDate;
    }

    // Alias for specification compatibility
    public Timestamp getCreatedAt() {
        return screeningDate;
    }

    public void setCreatedAt(Timestamp createdAt) {
        this.screeningDate = createdAt;
    }

    public String getVesselOverlayPath() {
        return vesselOverlayPath;
    }

    public void setVesselOverlayPath(String vesselOverlayPath) {
        this.vesselOverlayPath = vesselOverlayPath;
    }

    // Alias for specification compatibility
    public String getMaskPath() {
        return vesselOverlayPath;
    }

    public void setMaskPath(String maskPath) {
        this.vesselOverlayPath = maskPath;
    }

    public Double getVesselDensity() {
        return vesselDensity;
    }

    public void setVesselDensity(Double vesselDensity) {
        this.vesselDensity = vesselDensity;
    }

    // Helper formatting methods for UI presentation
    public int getCvdPercent() {
        return (int) Math.round(cvdProbability * 100);
    }

    public int getHypertensionPercent() {
        return (int) Math.round(hypertensionProbability * 100);
    }

    public int getDrPercent() {
        return (int) Math.round(drConfidence * 100);
    }
}

package com.hms.model;

public class Doctor {

    private int id;
    private String name;
    private String specialization;
    private String phone;
    private String email;
    private int experience;
    private double consultationFee;

    public Doctor() {
    }

    public Doctor(int id, String name, String specialization,
                  String phone, String email,
                  int experience, double consultationFee) {

        this.id = id;
        this.name = name;
        this.specialization = specialization;
        this.phone = phone;
        this.email = email;
        this.experience = experience;
        this.consultationFee = consultationFee;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getSpecialization() {
        return specialization;
    }

    public void setSpecialization(String specialization) {
        this.specialization = specialization;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public int getExperience() {
        return experience;
    }

    public void setExperience(int experience) {
        this.experience = experience;
    }

    public double getConsultationFee() {
        return consultationFee;
    }

    public void setConsultationFee(double consultationFee) {
        this.consultationFee = consultationFee;
    }
}
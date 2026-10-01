package com.hms.model;

public class User {

    private int userId;
    private String username;
    private String password;
    private String role;
    private int doctorId;

    public User() {
    }

    public User(int userId, String username, String password, String role, int doctorId) {
        this.userId = userId;
        this.username = username;
        this.password = password;
        this.role = role;
        this.doctorId = doctorId;
    }

    public int getUserId() {
        return userId;
    }

    public void setUserId(int userId) {
        this.userId = userId;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public int getDoctorId() {
        return doctorId;
    }

    public void setDoctorId(int doctorId) {
        this.doctorId = doctorId;
    }
}
package com.hms.dao;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import com.hms.util.DBConnection;

public class UserDAO {
	public boolean login(String username,String password) {
		String sql = "SELECT * FROM users WHERE username = ? AND password = ?";
		try {
			Connection con = DBConnection.getConnection();

            PreparedStatement ps = con.prepareStatement(sql);

            ps.setString(1, username);
            ps.setString(2, password);

            ResultSet rs = ps.executeQuery();

            if (rs.next()) {
                System.out.println("USER FOUND");
                return true;
            } else {
                System.out.println("USER NOT FOUND");
                return false;
            }
		}catch (Exception e) {
            e.printStackTrace();
            return false;
        }
	}
}

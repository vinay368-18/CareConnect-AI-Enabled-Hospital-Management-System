package com.hms;

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

            return rs.next();
		}catch (Exception e) {
            e.printStackTrace();
            return false;
        }
	}
}

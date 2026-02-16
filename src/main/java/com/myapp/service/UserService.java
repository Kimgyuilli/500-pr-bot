package com.myapp.service;

import java.util.Map;
import java.util.HashMap;

public class UserService {

    private Map<Long, String> users = new HashMap<>();

    public String getUser(Long id) {
        String name = users.get(id);
        if (name == null) {
            return "User not found"; // Handle the null case appropriately
        }
        return name.toUpperCase();
    }
}
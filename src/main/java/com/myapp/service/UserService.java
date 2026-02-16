package com.myapp.service;

import java.util.Map;
import java.util.HashMap;

public class UserService {

    private Map<Long, String> users = new HashMap<>();

    public String getUser(Long id) {
        String name = users.get(id);
        // NPE 방지를 위해 name이 null인지 체크
        return name != null ? name.toUpperCase() : "User not found";
    }
}
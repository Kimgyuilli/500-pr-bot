package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}

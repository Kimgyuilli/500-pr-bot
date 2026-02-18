package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;
        if (value == null) {
            return "User not found"; // null일 경우 처리
        }
        return "User name length: " + value.length();
    }
}
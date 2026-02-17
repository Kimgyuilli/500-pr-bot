package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null; // 해당 값은 사용자로부터 받아오는 로직 필요
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}
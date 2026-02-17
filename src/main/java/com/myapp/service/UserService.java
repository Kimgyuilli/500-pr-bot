package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;

        // value가 null인지 체크하여 예외를 방지
        if (value == null) {
            return "User not found";
        }

        return "User name length: " + value.length();
    }
}
package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null; // 이 값은 나중에 DB에서 조회된다고 가정
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}

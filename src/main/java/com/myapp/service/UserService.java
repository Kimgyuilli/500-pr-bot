package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null; // 사용자 이름 가져오는 로직 필요
        if (value == null) {
            return "User name length: 0";
        }
        return "User name length: " + value.length();
    }
}

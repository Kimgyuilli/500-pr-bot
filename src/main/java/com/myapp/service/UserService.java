package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null; // 실제 사용자 이름을 가져오는 메소드가 필요

        if (value != null) {
            return "User name length: " + value.length();
        } else {
            return "User not found";
        }
    }
}
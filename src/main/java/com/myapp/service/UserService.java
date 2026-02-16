package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = "Default User"; // 기본 사용자 문자열로 초기화
        return "User name length: " + value.length();
    }
}
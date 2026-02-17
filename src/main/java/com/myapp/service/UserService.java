package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = "Default User"; // 기본값 설정
        // value가 null인지 체크
        return "User name length: " + (value != null ? value.length() : 0);
    }
}
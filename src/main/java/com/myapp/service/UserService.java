package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null; // 예시로 null 사용. 실제로는 데이터베이스나 다른 소스로부터 사용자 정보를 가져와야 함.
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}
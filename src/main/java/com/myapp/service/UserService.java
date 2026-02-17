package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null; // 실제 로직에서는 데이터베이스 호출 등을 통해 사용자 이름을 가져와야 함
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}

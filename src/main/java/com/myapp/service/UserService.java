package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        // 예시 사용자 이름을 하드코딩하여 반환
        String value = (id != null && id == 1L) ? "John Doe" : null;
        // value가 null인지 체크 후 length() 호출
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}
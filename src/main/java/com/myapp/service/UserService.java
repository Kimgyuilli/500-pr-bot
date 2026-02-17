package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = ""; // 기본값으로 빈 문자열 초기화
        // value가 null이 아닐 때만 length() 호출
        return "User name length: " + (value != null ? value.length() : 0);
    }
}

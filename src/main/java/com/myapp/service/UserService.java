package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null; // 실제 사용자 이름을 가져오는 로직이 필요합니다.
        // 예를 들어 사용자 정보를 DB에서 조회하는 로직이 여기에 들어갈 수 있습니다.
        if (value == null) {
            return "User not found"; // 사용자가 존재하지 않을 때의 처리
        }
        return "User name length: " + value.length();
    }
}
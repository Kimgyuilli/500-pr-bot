package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = fetchUserNameById(id); // 사용자 이름을 가져오는 메소드 호출
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }

    // 사용자 이름을 가져오는 가상의 메소드
    private String fetchUserNameById(Long id) {
        // 실제 데이터베이스 또는 다른 방법으로 사용자 이름을 조회합니다.
        return null; // 여기서는 예시로 null을 반환
    }
}

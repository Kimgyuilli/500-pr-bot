package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;
        // 사용자 ID에 따라 실제 값 설정 (예시로 임의의 값 사용)
        // 실제 DB에서 사용자 정보를 조회할 코드가 필요함
        if (id != null && id > 0) {
            value = "User" + id;
        }
        // null 체크 추가
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}

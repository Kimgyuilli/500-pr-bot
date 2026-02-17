package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        // 사용자 이름을 가져온다고 가정하고 value 변수 초기화
        String value = getUserNameById(id);

        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }

    // 사용자 이름을 가져오는 메소드 예시
    private String getUserNameById(Long id) {
        // 실제 로직으로 변경 필요
        return null; // 예를 들어, id에 대한 사용자가 존재하지 않는 경우
    }
}

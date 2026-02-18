package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        // 예시: 사용자 이름을 가져오는 로직 추가
        String value = findUserNameById(id);
        // null 안전 체크
        return "User name length: " + (value != null ? value.length() : 0);
    }

    private String findUserNameById(Long id) {
        // 사용자 이름을 가져오는 더미 로직 또는 DB 조회
        if (id == 1L) return "John Doe"; // 예제용 반환 값
        return null; // 사용자가 존재하지 않는 경우
    }
}
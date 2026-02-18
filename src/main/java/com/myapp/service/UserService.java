package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;
        // 예시를 위해 value를 id에 따라 dummy data로 변경합니다. 실제 구현에선 DB 조회 등을 해야 할 수 있습니다.
        if (id != null) {
            value = "UserName";  // 여기서는 사용자 이름을 찾은 경우로 가정합니다.
        }
        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}
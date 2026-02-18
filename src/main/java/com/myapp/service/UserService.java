package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;
        // 사용자 ID에 기반하여 값을 찾아오는 로직 추가 필요
        // 예를 들어, value = findUserNameById(id);

        if (value == null) {
            return "User not found";
        }
        return "User name length: " + value.length();
    }
}
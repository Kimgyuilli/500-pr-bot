package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;
        // BUG: null 체크 없이 length() 호출
        return "User name length: " + value.length();
    }
}

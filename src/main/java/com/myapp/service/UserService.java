package com.myapp.service;

import org.springframework.stereotype.Service;

@Service
public class UserService {

    public String getUser(Long id) {
        String value = null;
        // value가 null인지 체크하고, null이 아닐 경우에만 length() 호출
        int length = (value != null) ? value.length() : 0;
        return "User name length: " + length;
    }
}

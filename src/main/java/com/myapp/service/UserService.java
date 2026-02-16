package com.myapp.service;

import java.util.Map;
import java.util.HashMap;

public class UserService {

    private Map<Long, String> users = new HashMap<>();

    public String getUser(Long id) {
        // Bug: users.get() can return null, calling .toUpperCase() on null throws NPE
        String name = users.get(id);
        return name.toUpperCase();
    }
}

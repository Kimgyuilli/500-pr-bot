package com.example.errorreporter;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/test")
public class TestController {

    @GetMapping("/npe")
    public String triggerNpe() {
        String value = null;
        return value.length() + "";
    }

    @GetMapping("/illegal-argument")
    public String triggerIllegalArgument(@RequestParam(defaultValue = "-1") int id) {
        if (id < 0) {
            throw new IllegalArgumentException("ID must be positive: " + id);
        }
        return "ok";
    }

    @GetMapping("/runtime")
    public String triggerRuntime() {
        throw new RuntimeException("테스트용 런타임 에러");
    }
}

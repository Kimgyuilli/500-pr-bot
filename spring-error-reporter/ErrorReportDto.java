package com.example.errorreporter;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class ErrorReportDto {
    private String errorType;
    private String errorMessage;
    private String stackTrace;
    private String requestUrl;
    private String timestamp;
}

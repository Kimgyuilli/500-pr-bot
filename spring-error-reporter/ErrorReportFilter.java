package com.example.errorreporter;

import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.time.Instant;
import java.util.Map;

@Slf4j
@RestControllerAdvice
@Order(Ordered.LOWEST_PRECEDENCE)
public class ErrorReportFilter {

    private final WebClient webClient;

    public ErrorReportFilter(@Value("${error-bot.url}") String botUrl) {
        this.webClient = WebClient.builder().baseUrl(botUrl).build();
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Object> handleException(Exception ex, HttpServletRequest request) {
        sendErrorReport(ex, request);

        return ResponseEntity.status(500)
            .body(Map.of("error", "Internal Server Error"));
    }

    private void sendErrorReport(Exception ex, HttpServletRequest request) {
        try {
            ErrorReportDto report = ErrorReportDto.builder()
                .errorType(ex.getClass().getName())
                .errorMessage(ex.getMessage())
                .stackTrace(getStackTraceString(ex))
                .requestUrl(request.getMethod() + " " + request.getRequestURI())
                .timestamp(Instant.now().toString())
                .build();

            webClient.post()
                .uri("/webhook/error")
                .bodyValue(report)
                .retrieve()
                .toBodilessEntity()
                .subscribe();
        } catch (Exception e) {
            log.warn("Failed to send error report", e);
        }
    }

    private String getStackTraceString(Exception ex) {
        StringWriter sw = new StringWriter();
        ex.printStackTrace(new PrintWriter(sw));
        return sw.toString();
    }
}

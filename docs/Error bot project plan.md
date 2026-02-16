# 500 Error Auto-Fix Bot

> 내 Spring Boot 프로젝트에서 500 에러 발생 시 AI가 자동으로 분석/수정하고 PR을 올려주는 봇
> 프로토타입 목적 - AI 자동화 파이프라인 학습 및 실험

---

## 프로젝트 개요

### 목표
내가 운영 중인 Spring Boot 프로젝트에서 500 에러가 터지면:
1. 에러 정보를 자동으로 수집
2. AI가 코드를 분석하고 수정안 생성
3. GitHub에 자동으로 PR 생성
4. Discord로 알림

### 이 프로젝트로 배우고 싶은 것
- AI API를 활용한 코드 자동 수정 파이프라인
- Webhook 기반 이벤트 드리븐 아키텍처

### 범위 (Scope)
- 대상: **내 Spring Boot 프로젝트 1개**
- 에러: **500 Internal Server Error만**
- 환경: **로컬 개발 환경에서 테스트** → 추후 서버 배포 고려

---

## 시스템 아키텍처

```
[내 Spring Boot 앱]
    │
    │ 500 에러 발생 시 HTTP POST (에러 정보 + 스택트레이스)
    ▼
[Error Bot Service]  ← Python FastAPI 서버
    │
    ├─ 1. Discord 알림 (에러 발생 알림)
    │
    ├─ 2. GitHub API로 관련 소스코드 조회
    │
    ├─ 3. Claude API로 코드 분석 + 수정안 생성
    │
    ├─ 4. GitHub API로 브랜치 생성 + 수정 코드 커밋 + PR 생성
    │
    └─ 5. Discord 알림 (PR 링크 포함)
```

### 핵심 흐름 상세

```
1. Spring Boot 앱에서 500 에러 발생
   └─ @ControllerAdvice가 잡아서 에러 정보 JSON으로 봇에 POST

2. 봇이 에러 수신
   ├─ 에러 타입, 메시지, 스택트레이스 파싱
   ├─ 스택트레이스에서 내 프로젝트 코드 파일 경로 추출
   └─ Discord에 "에러 발생" 알림

3. 코드 조회
   ├─ 스택트레이스의 클래스명 → 파일 경로 변환
   │   (예: com.myapp.service.UserService → src/main/java/com/myapp/service/UserService.java)
   └─ GitHub API로 해당 파일(들) 조회

4. AI 분석
   ├─ Claude API에 에러 정보 + 소스코드 전달
   └─ 수정된 코드 + 분석 리포트 수신

5. PR 생성
   ├─ fix/error-{timestamp} 브랜치 생성
   ├─ 수정된 파일 커밋
   ├─ PR 생성 (에러 분석 내용을 PR 본문에 포함)
   └─ Discord에 "PR 생성 완료" 알림
```

---

## 기술 스택

### 왜 Python FastAPI인가
스택트레이스 파싱 → 파일 경로 추출 → 여러 파일 조회 → Claude 응답 파싱 등 **중간에 복잡한 데이터 가공**이 핵심이므로, 코드로 직접 제어할 수 있는 서버가 적합하다. FastAPI는 비동기 지원 + 빠른 프로토타이핑이 가능하고, Pydantic으로 데이터 검증도 간편하다.

| 컴포넌트 | 기술 | 이유 |
|---------|------|------|
| 봇 서버 | Python + FastAPI | 빠른 프로토타이핑, 비동기 지원 |
| AI | Claude API (Sonnet 4.5) | 코드 분석 능력 우수 |
| VCS | GitHub REST API (PyGithub) | PR 생성 자동화 |
| 알림 | Discord Webhook | 간단한 HTTP POST로 알림 |
| 에러 전송 | Spring Boot @ControllerAdvice | 500 에러 캐치 후 봇에 POST |

---

## 프로젝트 구조

```
500-pr-bot/
├── bot/                          # 봇 서버 (Python)
│   ├── main.py                   # FastAPI 엔트리포인트
│   ├── config.py                 # 환경 변수 설정
│   ├── error_handler.py          # 에러 수신 및 처리 로직
│   ├── github_service.py         # GitHub API 연동 (코드 조회, PR 생성)
│   ├── claude_service.py         # Claude API 연동 (코드 분석)
│   ├── discord_service.py        # Discord 알림
│   ├── stack_trace_parser.py     # 스택트레이스 → 파일 경로 변환
│   ├── requirements.txt
│   └── .env.example
│
├── spring-error-reporter/        # Spring Boot 에러 리포터 (내 프로젝트에 복붙할 코드)
│   ├── ErrorReportFilter.java    # 500 에러 캐치 + 봇에 POST
│   └── ErrorReportDto.java       # 전송 데이터 구조
│
├── docker-compose.yml            # 로컬 실행용 (봇 서버)
├── .env.example
└── Error bot project plan.md
```

---

## 구현 플랜

### Phase 1: 뼈대 잡기 (2-3일)

**목표: 500 에러 → 봇 수신 → Discord 알림까지 연결**

- [ ] Python FastAPI 프로젝트 세팅 (`bot/`)
- [ ] Webhook 엔드포인트 구현 (`POST /webhook/error`)
- [ ] 에러 데이터 모델 정의
- [ ] Discord Webhook 알림 구현
- [ ] Spring Boot 쪽 에러 리포터 구현 (`ErrorReportFilter.java`)
  - `@ControllerAdvice`로 500 에러 캐치
  - 비동기로 봇 서버에 HTTP POST
  - 기존 에러 응답은 그대로 유지 (봇은 관찰만)
- [ ] 로컬에서 연동 테스트 (의도적 500 에러 발생 → Discord 알림 확인)

**에러 전송 데이터 구조:**
```json
{
  "errorType": "java.lang.NullPointerException",
  "errorMessage": "Cannot invoke method on null reference",
  "stackTrace": "java.lang.NullPointerException: ...\n\tat com.myapp.service.UserService.getUser(UserService.java:45)\n\t...",
  "requestUrl": "GET /api/users/123",
  "timestamp": "2026-02-16T10:30:00Z"
}
```

---

### Phase 2: AI 분석 연동 (3-4일)

**목표: Claude API로 에러 분석 + 수정안 생성**

- [ ] 스택트레이스 파서 구현 (`stack_trace_parser.py`)
  - 스택트레이스에서 내 프로젝트 패키지의 클래스만 추출
  - 패키지명 → 파일 경로 변환
  - 에러 발생 지점 + 호출 체인의 관련 파일 목록 생성
- [ ] GitHub API 연동 (`github_service.py`)
  - 파일 내용 조회 (단일/다중 파일)
  - 특정 브랜치 기준으로 조회
- [ ] Claude API 연동 (`claude_service.py`)
  - 에러 정보 + 소스코드를 Claude에 전달
  - 수정안 JSON 응답 파싱
- [ ] 프롬프트 설계 및 테스트

**Claude 프롬프트 설계:**
```
[System]
너는 Spring Boot 코드를 분석하고 수정하는 봇이다.
에러 정보와 소스코드를 받아서 수정된 코드를 반환한다.

[User]
## 에러
- 타입: {error_type}
- 메시지: {error_message}
- 발생 위치: {file_path}:{line_number}

## 스택 트레이스
{stack_trace}

## 소스 코드
### {file_path_1}
```java
{code_1}
```

### {file_path_2}
```java
{code_2}
```

## 지시사항
1. 에러 원인을 분석하라
2. 수정이 필요한 파일의 전체 코드를 제공하라
3. 수정 사항을 설명하라

아래 JSON 형식으로 응답하라:
{
  "analysis": "에러 원인 분석",
  "files": [
    {
      "path": "파일 경로",
      "content": "수정된 전체 코드"
    }
  ],
  "summary": "변경 사항 요약 (PR 제목용, 한 줄)"
}
```

---

### Phase 3: PR 자동 생성 (2-3일)

**목표: Claude가 생성한 수정안으로 GitHub PR 자동 생성**

- [ ] GitHub API로 브랜치 생성 (`fix/error-{short-hash}-{timestamp}`)
- [ ] 수정된 파일 커밋
- [ ] PR 생성 (본문에 에러 분석 내용 포함)
- [ ] Discord에 PR 링크 포함 완료 알림
- [ ] E2E 테스트: 500 에러 → Discord 알림 → PR 생성 → Discord 완료 알림

**PR 본문 템플릿:**
```markdown
## 자동 생성된 에러 수정 PR

### 에러 정보
- **타입**: {error_type}
- **메시지**: {error_message}
- **발생 위치**: {file_path}:{line_number}
- **요청**: {request_url}
- **발생 시간**: {timestamp}

### AI 분석
{analysis}

### 변경 사항
{summary}

---
> 이 PR은 Error Bot이 자동으로 생성했습니다.
> 반드시 코드 리뷰 후 머지하세요.
```

---

### Phase 4: 안정화 + 개선 (필요할 때)

- [ ] 중복 에러 필터링 (같은 에러가 반복 발생 시 무시)
  - 인메모리 딕셔너리로 충분 (단일 서버이므로 Redis 불필요)
  - 에러 타입 + 메시지 + 파일 경로 조합의 해시값으로 판단
  - 기본 30분 TTL
- [ ] Claude 응답 실패 시 fallback (분석 리포트만 Discord에 전송)
- [ ] 에러 리포터 전송 실패 시 로깅 (봇 서버 다운 시 Spring Boot 앱에 영향 없도록)

---

## 핵심 구현 상세

### 1. Spring Boot 에러 리포터 (내 프로젝트에 추가할 코드)

```java
@RestControllerAdvice
@Order(Ordered.LOWEST_PRECEDENCE) // 기존 핸들러보다 낮은 우선순위
public class ErrorReportFilter {

    private final WebClient webClient;

    public ErrorReportFilter(@Value("${error-bot.url}") String botUrl) {
        this.webClient = WebClient.builder().baseUrl(botUrl).build();
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Object> handleException(Exception ex, HttpServletRequest request) {
        // 1. 봇에 비동기 전송 (응답 대기 안 함)
        sendErrorReport(ex, request);

        // 2. 기존 에러 응답 그대로 반환
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
                .subscribe(); // fire-and-forget
        } catch (Exception e) {
            // 봇 전송 실패가 앱에 영향주면 안됨
            log.warn("Failed to send error report", e);
        }
    }
}
```

**application.yml (내 프로젝트):**
```yaml
error-bot:
  url: http://localhost:8000  # 봇 서버 주소
```

### 2. 스택트레이스 파서

```python
# stack_trace_parser.py
import re

def parse_stack_trace(stack_trace: str, base_package: str) -> list[dict]:
    """
    스택트레이스에서 내 프로젝트 코드만 추출

    예: base_package = "com.myapp"
    입력: "at com.myapp.service.UserService.getUser(UserService.java:45)"
    출력: [{"class": "com.myapp.service.UserService",
            "file": "src/main/java/com/myapp/service/UserService.java",
            "line": 45}]
    """
    pattern = rf'at ({re.escape(base_package)}[\w.]+)\.(\w+)\((\w+\.java):(\d+)\)'
    matches = re.findall(pattern, stack_trace)

    results = []
    seen = set()
    for class_name, method, filename, line in matches:
        file_path = "src/main/java/" + class_name.replace(".", "/") + ".java"
        if file_path not in seen:
            seen.add(file_path)
            results.append({
                "class": class_name,
                "file": file_path,
                "line": int(line),
                "method": method
            })
    return results
```

### 3. 에러 전송 데이터 구조

```python
# main.py - FastAPI 엔드포인트
from pydantic import BaseModel

class ErrorReport(BaseModel):
    errorType: str          # "java.lang.NullPointerException"
    errorMessage: str       # "Cannot invoke method on null reference"
    stackTrace: str         # 전체 스택트레이스
    requestUrl: str         # "GET /api/users/123"
    timestamp: str          # ISO 8601

@app.post("/webhook/error")
async def receive_error(report: ErrorReport):
    # 비동기로 처리 (Spring Boot 앱이 기다리지 않도록 즉시 응답)
    asyncio.create_task(process_error(report))
    return {"status": "received"}
```

---

## 설정 (환경 변수)

```env
# .env
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
GITHUB_REPO=myname/my-project        # 대상 레포지토리
GITHUB_BASE_BRANCH=main              # PR의 base 브랜치
BASE_PACKAGE=com.myapp               # 스택트레이스 필터링용 패키지명
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
BOT_PORT=8000
```

---

## 예상 비용

프로토타입이므로 거의 무료:

| 항목 | 비용 |
|------|------|
| Claude API | 건당 ~$0.01-0.05 (Sonnet 4.5 기준) |
| GitHub API | 무료 |
| Discord Webhook | 무료 |
| 서버 | 로컬 실행이면 $0 |
| **총계** | 테스트 기간 중 **$1-5 이하** |

---

## 알려진 한계 및 주의사항

1. **AI가 만든 코드는 반드시 리뷰 필요** - 자동 머지 절대 금지
2. **단일 파일 수정에 적합** - 여러 파일에 걸친 복잡한 버그는 AI가 정확히 고치기 어려움
3. **컴파일 보장 안 됨** - Claude가 생성한 코드가 빌드 안 될 수 있음
4. **비즈니스 로직 에러는 한계** - NPE, 타입 에러 등 단순 에러에서 효과적
5. **GitHub API에서 조회하는 코드와 실제 실행 중인 코드가 다를 수 있음** - 배포 후 커밋이 있으면 불일치 발생

---

## 다음 단계

Phase 1부터 시작:
1. `bot/` 디렉터리에 FastAPI 프로젝트 생성
2. `/webhook/error` 엔드포인트 구현
3. Discord 알림 연동
4. 내 Spring Boot 프로젝트에 `ErrorReportFilter` 추가
5. 로컬에서 테스트

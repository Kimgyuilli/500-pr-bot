# 500 Error Auto-Fix Bot

Spring Boot 앱에서 500 에러 발생 시 AI가 자동으로 코드를 분석/수정하고 GitHub PR을 생성하는 봇

```
Spring Boot 500 에러 → POST /webhook/error → 봇
  → Discord 에러 알림
  → GitHub 코드 조회 (스택트레이스 파일 + import 관련 파일)
  → AI 분석/수정 (근본 원인 + 수정 내용 상세 분석)
  → PR 생성 (에러 정보 테이블, 근본 원인, AI 분석, 수정 내용, 수정 파일 목록)
  → Discord PR 알림
```

---

## 빠른 시작

### 1. 봇 서버 설정

```bash
cp bot/.env.example bot/.env
```

`bot/.env` 편집:

```env
OPENAI_API_KEY=sk-...              # OpenAI API 키
GITHUB_TOKEN=ghp_...               # GitHub 토큰 (Contents + Pull requests 읽기/쓰기)
GITHUB_REPO=owner/repo             # 대상 레포지토리
GITHUB_BASE_BRANCH=main            # PR의 base 브랜치
BASE_PACKAGE=com.myapp             # 스택트레이스 필터링용 패키지명
DISCORD_WEBHOOK_URL=https://...    # Discord Webhook URL
```

### 2. 봇 실행

```bash
docker compose up --build -d
```

Health check:
```bash
curl http://localhost:8000/health
```

### 3. Spring Boot 프로젝트에 에러 리포터 추가

`spring-error-reporter/` 안의 두 파일을 프로젝트에 복사:

- `ErrorReportFilter.java` — 500 에러를 캐치해서 봇에 전송
- `ErrorReportDto.java` — 전송 데이터 구조

`application.yml`에 봇 주소 추가:

```yaml
error-bot:
  url: http://localhost:8000
```

의존성 필요: `spring-boot-starter-webflux` (WebClient 사용)

---

## 프로젝트 구조

```
500-pr-bot/
├── bot/
│   ├── app/
│   │   ├── main.py              # FastAPI 엔트리포인트
│   │   ├── config.py            # 환경 변수 설정
│   │   ├── error_handler.py     # 에러 처리 오케스트레이션
│   │   ├── services/
│   │   │   ├── ai_service.py        # AI 분석 (에러/참고 파일 분리 프롬프트)
│   │   │   ├── discord_service.py   # Discord 알림
│   │   │   └── github_service.py    # GitHub API (코드 조회, PR 생성)
│   │   └── utils/
│   │       └── stack_trace_parser.py  # 스택트레이스 파싱 + import 관련 파일 추출
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── spring-error-reporter/       # Spring Boot에 복사할 에러 리포터
├── docs/
└── docker-compose.yml
```

---

## 다른 프로젝트에 적용하기

### 변경이 필요한 것

1. **`bot/.env`** — 대상 레포, 패키지명, 토큰 등 환경 변수만 변경
2. **Spring Boot 프로젝트** — `ErrorReportFilter`, `ErrorReportDto` 복사 + `application.yml`에 봇 URL 추가

### AI 모델 교체

`bot/app/services/ai_service.py` 하나만 수정하면 됨. `analyze_error()` 함수의 시그니처를 유지하면 나머지 코드는 변경 불필요.

---

## AI 분석 흐름

1. **파일 분리 수집**: 스택트레이스에 등장한 파일(`error_files`)과 import로 연결된 참고 파일(`context_files`)을 구분하여 조회
2. **구조화된 프롬프트**: 에러 파일과 참고 파일을 분리된 섹션으로 AI에 전달 → AI가 에러 발생 지점과 참고 맥락을 혼동하지 않음
3. **상세 응답**: AI가 `root_cause`(근본 원인), `fix_description`(수정 내용 상세), `analysis`(분석), `files`(수정 코드)를 반환
4. **리뷰어 친화적 PR**: 에러 정보 테이블 + 근본 원인 + AI 분석 + 수정 내용 + 수정 파일 목록으로 구성된 PR 본문 자동 생성

---

## Webhook 요청 형식

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

## 주의사항

- AI가 생성한 코드는 **반드시 리뷰 후 머지** — 자동 머지 금지
- 단순 에러(NPE, 타입 에러 등)에 효과적, 복잡한 비즈니스 로직 에러는 한계 있음
- GitHub API로 조회하는 코드와 실제 실행 중인 코드가 다를 수 있음 (배포 후 추가 커밋이 있는 경우)

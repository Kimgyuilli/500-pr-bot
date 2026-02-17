# 500 Error Auto-Fix Bot

Spring Boot 앱에서 500 에러 발생 시 AI가 자동으로 코드를 분석/수정하고 GitHub PR을 생성하는 봇

```
Spring Boot 500 에러 → POST /webhook/error → 봇
  → Discord 에러 알림
  → GitHub 코드 조회 (스택트레이스 파일 + import 관련 파일 N-depth)
  → AI 분석/수정 (파싱 실패 시 피드백 재시도)
  → AI 응답 검증 (경로/내용 유효성)
  → PR 생성 (에러 정보, 근본 원인, AI 분석, 수정 내용, 변경 diff)
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
IMPORT_DEPTH=1                     # import 탐색 깊이 (기본값 1)
AI_PROVIDER=openai                 # AI 제공자 (기본값 openai)
```

### 2. 봇 실행

```bash
docker compose up --build -d
```

Health check:
```bash
curl http://localhost:8000/health
```

대시보드: `http://localhost:8000`

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
│   │   ├── main.py                # FastAPI 엔트리포인트 + API 라우터
│   │   ├── config.py              # 환경 변수 설정 (Pydantic Settings)
│   │   ├── error_handler.py       # 에러 처리 오케스트레이션 (핵심 파이프라인)
│   │   ├── event_store.py         # SSE 이벤트 저장 + 브로드캐스트
│   │   ├── test_runner.py         # pytest 서브프로세스 실행 + 결과 파싱
│   │   ├── services/
│   │   │   ├── ai_provider.py         # AIProvider Protocol + 구현체 + 팩토리
│   │   │   ├── ai_service.py          # AI 프롬프트 구성 + 에러 분석 로직
│   │   │   ├── discord_service.py     # Discord Webhook 알림
│   │   │   └── github_service.py      # GitHub API (코드 조회, PR 생성)
│   │   ├── utils/
│   │   │   └── stack_trace_parser.py  # 스택트레이스 파싱 + import 관련 파일 추출
│   │   └── static/
│   │       └── index.html             # 대시보드 UI (에러 봇 탭 + 테스트 실행 탭)
│   ├── tests/                     # pytest 단위 테스트 (62개)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── spring-error-reporter/         # Spring Boot에 복사할 에러 리포터
└── docker-compose.yml
```

---

## 모듈 의존 관계 및 데이터 흐름

```
main.py
  ├── POST /webhook/error  →  error_handler.process_error()
  ├── GET  /api/events     →  event_store.subscribe()        → SSE 스트림
  ├── GET  /api/errors     →  event_store.get_history()
  └── GET  /api/tests/stream → test_runner.run_tests()       → SSE 스트림

error_handler.process_error(ErrorReport):
  1. _is_duplicate()                          → 중복이면 무시
  2. discord_service.send_error_alert()       → Discord 에러 알림
  3. stack_trace_parser.parse_stack_trace()   → [{"file": "src/.../Foo.java", "class": "...", "line": 45}]
  4. github_service.fetch_files(file_paths)   → {"src/.../Foo.java": "소스코드..."}
  5. import N-depth 탐색 루프 (settings.import_depth만큼 반복)
     → extract_related_imports() + fetch_files() 반복
  6. ai_service.analyze_error(error_files, context_files)
     → 파싱 실패 시 피드백 프롬프트 포함 1회 재시도
     → {"analysis": "...", "root_cause": "...", "fix_description": "...", "files": [...], "summary": "..."}
  7. _validate_ai_result()                    → 경로/내용 검증 (실패 시 중단 + 알림)
  8. _build_diff()                            → 원본 vs 수정 unified diff 생성
  9. github_service.create_pull_request()     → PR URL
 10. discord_service.send_pr_alert()          → Discord PR 알림

각 단계에서 event_store.emit()으로 대시보드에 실시간 상태 전송
```

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 대시보드 UI |
| GET | `/health` | 헬스체크 (OpenAI, GitHub, Discord 연결 상태 포함) |
| POST | `/webhook/error` | 에러 리포트 수신 (Spring Boot → 봇) |
| GET | `/api/events` | SSE — 파이프라인 실시간 이벤트 스트림 |
| GET | `/api/errors` | 최근 에러 히스토리 (최대 50건, 최신순) |
| GET | `/api/errors/{error_id}` | 특정 에러 상세 (스택트레이스, AI 분석, PR 링크) |
| POST | `/api/test-webhook` | 테스트용 샘플 에러 전송 |
| GET | `/api/tests/stream` | SSE — pytest 실행 결과 실시간 스트림 |

### Webhook 요청 형식 (POST /webhook/error)

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

## 대시보드

`http://localhost:8000` 접속 시 웹 대시보드 제공. 탭 2개로 구성:

- **서비스 상태**: OpenAI, GitHub, Discord 연결 상태를 실시간 표시 (60초 주기 갱신)
- **에러 봇 탭**: 파이프라인 시각화 (5단계 상태 표시), 에러 히스토리 테이블 (클릭 시 상세 모달), 실시간 로그
- **테스트 실행 탭**: pytest 원클릭 실행, 실시간 로그 스트리밍, 테스트 결과 표 (통과/실패 뱃지)

SSE로 서버 이벤트를 실시간 수신하며, 연결 상태 표시기가 좌상단에 있음.

---

## 다른 프로젝트에 적용하기

### 기본 적용 (Spring Boot → Spring Boot)

1. **`bot/.env`** — 대상 레포, 패키지명, 토큰 등 환경 변수만 변경
2. **Spring Boot 프로젝트** — `ErrorReportFilter`, `ErrorReportDto` 복사 + `application.yml`에 봇 URL 추가

### 커스터마이징 가이드

| 변경 목적 | 수정 파일 | 수정 내용 |
|-----------|-----------|-----------|
| AI 모델 교체 (Claude 등) | `ai_provider.py` | `AIProvider` Protocol 구현 클래스 추가 + `_PROVIDERS`에 등록. `ai_service.py` 수정 불필요 |
| AI 프롬프트 수정 | `ai_service.py` | `SYSTEM_PROMPT`, `USER_PROMPT_TEMPLATE` 수정 |
| AI 제공자 변경 | `bot/.env` | `AI_PROVIDER=openai` 등으로 설정 |
| 알림 채널 교체 (Slack 등) | `discord_service.py` | `_post_webhook()`과 embed 구성을 대상 서비스 API에 맞게 변경. 함수 시그니처 `send_error_alert(report)`, `send_pr_alert(url, summary)`, `send_failure_alert(report, reason)` 유지 |
| Spring Boot 외 프레임워크 | `stack_trace_parser.py` | `parse_stack_trace()`의 정규식을 대상 언어의 스택트레이스 형식에 맞게 변경. 반환 형식 `[{"file": "경로", "class": "...", "line": N}]` 유지 |
| PR 본문 형식 변경 | `error_handler.py` | `PR_BODY_TEMPLATE` 수정 |
| 중복 필터 시간 변경 | `error_handler.py` | `DEDUP_TTL` 값 변경 (기본 1800초 = 30분) |
| import 탐색 깊이 변경 | `bot/.env` | `IMPORT_DEPTH=2` 등으로 설정 (기본 1) |

**핵심 원칙**: 각 모듈의 함수 시그니처와 반환 형식만 유지하면, 내부 구현은 자유롭게 교체 가능.

---

## AI 분석 흐름

1. **파일 분리 수집**: 스택트레이스에 등장한 파일(`error_files`)과 import로 연결된 참고 파일(`context_files`)을 구분하여 조회. import 탐색 깊이는 `IMPORT_DEPTH` 환경변수로 설정 (기본 1)
2. **구조화된 프롬프트**: 에러 파일과 참고 파일을 분리된 섹션으로 AI에 전달 → AI가 에러 발생 지점과 참고 맥락을 혼동하지 않음
3. **피드백 재시도**: AI 응답이 유효한 JSON이 아니면 피드백 프롬프트를 붙여 1회 재시도
4. **응답 검증**: AI가 반환한 파일 경로가 실제 조회한 파일에 포함되는지, 내용이 비어있지 않은지 검증. 실패 시 PR 생성을 중단하고 Discord 알림
5. **상세 응답**: AI가 `root_cause`(근본 원인), `fix_description`(수정 내용 상세), `analysis`(분석), `files`(수정 코드)를 반환
6. **리뷰어 친화적 PR**: 에러 정보 테이블 + 근본 원인 + AI 분석 + 수정 내용 + 수정 파일 목록 + **변경 diff**로 구성된 PR 본문 자동 생성

---

## 테스트

```bash
docker compose run --rm bot python -m pytest tests/ -v
```

62개 단위 테스트: AI 서비스 (재시도/팩토리 포함), Discord 알림, 에러 처리 파이프라인 (검증/diff 포함), 이벤트 저장소, GitHub 서비스, API 엔드포인트 (헬스체크 포함), 스택트레이스 파서, 테스트 러너 파서.

---

## 주의사항

- AI가 생성한 코드는 **반드시 리뷰 후 머지** — 자동 머지 금지
- 단순 에러(NPE, 타입 에러 등)에 효과적, 복잡한 비즈니스 로직 에러는 한계 있음
- GitHub API로 조회하는 코드와 실제 실행 중인 코드가 다를 수 있음 (배포 후 추가 커밋이 있는 경우)

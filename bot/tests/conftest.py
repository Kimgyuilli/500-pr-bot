import os

# config.py가 import되기 전에 환경변수 설정 필요
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("GITHUB_REPO", "owner/repo")
os.environ.setdefault("BASE_PACKAGE", "com.myapp")
os.environ.setdefault("DISCORD_WEBHOOK_URL", "https://discord.test/webhook")

from unittest.mock import AsyncMock, patch

import pytest

from app.error_handler import ErrorReport, _recent_errors

# pytest -v 출력 시 한글 표시명
_DISPLAY_NAMES = {
    # test_ai_service
    "test_analyze_error_returns_parsed_response": "AI 분석 - 정상 응답 파싱",
    "test_analyze_error_returns_none_on_invalid_json": "AI 분석 - 잘못된 JSON이면 None 반환",
    "test_analyze_error_returns_none_on_api_exception": "AI 분석 - API 예외 시 None 반환",
    # test_discord_service
    "test_send_error_alert_posts_correct_embed": "Discord 알림 - 에러 알림 전송",
    "test_send_pr_alert_posts_correct_embed": "Discord 알림 - PR 생성 알림 전송",
    "test_send_failure_alert_posts_correct_embed": "Discord 알림 - 실패 알림 전송",
    # test_error_handler
    "test_process_error_full_flow": "에러 처리 - 전체 플로우 정상 동작",
    "test_process_error_skips_duplicate": "에러 처리 - 중복 에러 무시",
    "test_process_error_no_stack_entries": "에러 처리 - 스택 항목 없으면 코드 조회 건너뜀",
    "test_process_error_ai_failure_sends_failure_alert": "에러 처리 - AI 실패 시 실패 알림 전송",
    "test_pr_body_contains_new_sections": "에러 처리 - PR 본문에 근본 원인/수정 내용 포함",
    "test_process_error_pr_failure_sends_failure_alert": "에러 처리 - PR 생성 실패 시 실패 알림 전송",
    # test_event_store
    "test_emit_stores_event": "이벤트 저장소 - 이벤트 저장",
    "test_emit_updates_same_error_id": "이벤트 저장소 - 같은 에러 ID 업데이트",
    "test_history_max_50": "이벤트 저장소 - 히스토리 최대 50개 유지",
    "test_subscribe_receives_events": "이벤트 저장소 - 구독자 이벤트 수신",
    "test_get_history_returns_newest_first": "이벤트 저장소 - 최신순 히스토리 반환",
    "test_data_merge_across_events": "이벤트 저장소 - 이벤트 데이터 병합",
    "test_data_not_overwritten_when_none": "이벤트 저장소 - None이면 데이터 덮어쓰지 않음",
    "test_get_error_found": "이벤트 저장소 - 에러 조회 성공",
    "test_get_error_not_found": "이벤트 저장소 - 에러 조회 실패 시 None",
    # test_github_service
    "test_fetch_file_content_returns_decoded": "GitHub - 파일 내용 디코딩 반환",
    "test_fetch_file_content_returns_none_on_error": "GitHub - 파일 조회 실패 시 None 반환",
    "test_fetch_files_returns_dict_of_found_files": "GitHub - 여러 파일 딕셔너리로 반환",
    "test_create_pull_request_returns_pr_url": "GitHub - PR 생성 후 URL 반환",
    "test_create_pull_request_reuses_existing_branch": "GitHub - 기존 브랜치 재사용",
    # test_main
    "test_health_returns_ok": "API - 헬스체크 정상 응답",
    "test_webhook_returns_received": "API - 웹훅 수신 정상 응답",
    "test_webhook_rejects_invalid_body": "API - 잘못된 요청 바디 거부",
    # test_stack_trace_parser
    "test_parse_extracts_project_classes": "스택 파서 - 프로젝트 클래스 추출",
    "test_parse_deduplicates_same_file": "스택 파서 - 같은 파일 중복 제거",
    "test_parse_returns_empty_for_no_match": "스택 파서 - 매칭 없으면 빈 목록",
    "test_parse_empty_string": "스택 파서 - 빈 문자열 처리",
    "test_extract_imports_filters_by_base_package": "스택 파서 - 베이스 패키지 기준 import 필터",
    "test_extract_imports_excludes_already_fetched": "스택 파서 - 이미 조회한 파일 제외",
    "test_extract_imports_deduplicates": "스택 파서 - import 중복 제거",
    "test_extract_imports_empty_source": "스택 파서 - 빈 소스 처리",
    "test_extract_imports_no_project_imports": "스택 파서 - 프로젝트 import 없으면 빈 목록",
    # test_test_runner
    "test_passed": "테스트 파서 - PASSED 파싱",
    "test_failed": "테스트 파서 - FAILED 파싱",
    "test_error": "테스트 파서 - ERROR 파싱",
    "test_no_match_empty": "테스트 파서 - 빈 줄 무시",
    "test_no_match_summary": "테스트 파서 - 요약 줄 무시",
    "test_no_match_header": "테스트 파서 - 헤더 줄 무시",
    "test_nested_path": "테스트 파서 - 중첩 경로 파싱",
}


def pytest_collection_modifyitems(items):
    for item in items:
        name = _DISPLAY_NAMES.get(item.originalname or item.name)
        if name:
            item._nodeid = item.nodeid.rsplit("::", 1)[0] + "::" + name


@pytest.fixture
def sample_error_report():
    return ErrorReport(
        errorType="NullPointerException",
        errorMessage="Cannot invoke method on null",
        stackTrace=(
            "at com.myapp.service.UserService.getUser(UserService.java:45)\n"
            "at com.myapp.controller.UserController.show(UserController.java:30)"
        ),
        requestUrl="GET /api/users/1",
        timestamp="2026-02-17T12:00:00Z",
    )


@pytest.fixture(autouse=True)
def _clear_dedup_cache():
    yield
    _recent_errors.clear()


@pytest.fixture
def mock_discord():
    """discord 함수 3개를 AsyncMock으로 교체."""
    with (
        patch("app.services.discord_service.send_error_alert", new_callable=AsyncMock) as m_error,
        patch("app.services.discord_service.send_pr_alert", new_callable=AsyncMock) as m_pr,
        patch("app.services.discord_service.send_failure_alert", new_callable=AsyncMock) as m_fail,
        patch("app.error_handler.send_error_alert", m_error),
        patch("app.error_handler.send_pr_alert", m_pr),
        patch("app.error_handler.send_failure_alert", m_fail),
    ):
        yield {"error": m_error, "pr": m_pr, "failure": m_fail}

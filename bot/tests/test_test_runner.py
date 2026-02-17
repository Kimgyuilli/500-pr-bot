from app.test_runner import _parse_test_line


class TestParseTestLine:
    def test_passed(self):
        line = "tests/test_main.py::test_health PASSED"
        result = _parse_test_line(line)
        assert result == {"file": "tests/test_main.py", "name": "test_health", "status": "passed"}

    def test_failed(self):
        line = "tests/test_ai_service.py::test_analyze FAILED"
        result = _parse_test_line(line)
        assert result == {"file": "tests/test_ai_service.py", "name": "test_analyze", "status": "failed"}

    def test_error(self):
        line = "tests/test_github_service.py::test_fetch ERROR"
        result = _parse_test_line(line)
        assert result == {"file": "tests/test_github_service.py", "name": "test_fetch", "status": "error"}

    def test_no_match_empty(self):
        assert _parse_test_line("") is None

    def test_no_match_summary(self):
        assert _parse_test_line("=== 5 passed in 0.3s ===") is None

    def test_no_match_header(self):
        assert _parse_test_line("collecting ... collected 5 items") is None

    def test_nested_path(self):
        line = "tests/unit/test_parser.py::test_parse PASSED"
        result = _parse_test_line(line)
        assert result == {"file": "tests/unit/test_parser.py", "name": "test_parse", "status": "passed"}

    def test_korean_name(self):
        line = "tests/test_main.py::API - 헬스체크 정상 응답 PASSED"
        result = _parse_test_line(line)
        assert result == {"file": "tests/test_main.py", "name": "API - 헬스체크 정상 응답", "status": "passed"}

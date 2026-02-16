from app.utils.stack_trace_parser import parse_stack_trace


def test_parse_extracts_project_classes():
    trace = "at com.myapp.service.UserService.getUser(UserService.java:45)"
    result = parse_stack_trace(trace, "com.myapp")
    assert len(result) == 1
    assert result[0]["class"] == "com.myapp.service.UserService"
    assert result[0]["file"] == "src/main/java/com/myapp/service/UserService.java"
    assert result[0]["line"] == 45
    assert result[0]["method"] == "getUser"


def test_parse_deduplicates_same_file():
    trace = (
        "at com.myapp.service.UserService.getUser(UserService.java:45)\n"
        "at com.myapp.service.UserService.findById(UserService.java:20)"
    )
    result = parse_stack_trace(trace, "com.myapp")
    assert len(result) == 1


def test_parse_returns_empty_for_no_match():
    trace = "at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:100)"
    result = parse_stack_trace(trace, "com.myapp")
    assert result == []


def test_parse_empty_string():
    assert parse_stack_trace("", "com.myapp") == []

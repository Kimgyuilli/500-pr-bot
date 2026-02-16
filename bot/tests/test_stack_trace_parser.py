from app.utils.stack_trace_parser import extract_related_imports, parse_stack_trace


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


# --- extract_related_imports ---

def test_extract_imports_filters_by_base_package():
    source = (
        "import com.myapp.service.UserService;\n"
        "import com.myapp.repository.UserRepository;\n"
        "import org.springframework.stereotype.Controller;\n"
        "import java.util.List;\n"
    )
    result = extract_related_imports(source, "com.myapp", set())
    assert result == [
        "src/main/java/com/myapp/service/UserService.java",
        "src/main/java/com/myapp/repository/UserRepository.java",
    ]


def test_extract_imports_excludes_already_fetched():
    source = "import com.myapp.service.UserService;\nimport com.myapp.dto.UserDto;\n"
    already = {"src/main/java/com/myapp/service/UserService.java"}
    result = extract_related_imports(source, "com.myapp", already)
    assert result == ["src/main/java/com/myapp/dto/UserDto.java"]


def test_extract_imports_deduplicates():
    source = "import com.myapp.service.A;\nimport com.myapp.service.A;\n"
    result = extract_related_imports(source, "com.myapp", set())
    assert result == ["src/main/java/com/myapp/service/A.java"]


def test_extract_imports_empty_source():
    assert extract_related_imports("", "com.myapp", set()) == []


def test_extract_imports_no_project_imports():
    source = "import org.springframework.web.bind.annotation.RestController;\n"
    assert extract_related_imports(source, "com.myapp", set()) == []

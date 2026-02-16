import re


def parse_stack_trace(stack_trace: str, base_package: str) -> list[dict]:
    """
    스택트레이스에서 내 프로젝트 코드만 추출.

    예: base_package = "com.myapp"
    입력: "at com.myapp.service.UserService.getUser(UserService.java:45)"
    출력: [{"class": "com.myapp.service.UserService",
            "file": "src/main/java/com/myapp/service/UserService.java",
            "line": 45, "method": "getUser"}]
    """
    pattern = rf"at ({re.escape(base_package)}[\w.]+)\.(\w+)\((\w+\.java):(\d+)\)"
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
                "method": method,
            })
    return results


def extract_related_imports(
    source_code: str, base_package: str, already_fetched: set[str]
) -> list[str]:
    """
    Java 소스코드의 import문에서 프로젝트 내부 클래스 파일 경로를 추출.

    - base_package로 시작하는 import만 필터 (외부 라이브러리 제외)
    - already_fetched에 있는 파일은 제외
    - 반환: ["src/main/java/com/myapp/service/UserService.java", ...]
    """
    pattern = rf"import\s+({re.escape(base_package)}[\w.]+)\s*;"
    matches = re.findall(pattern, source_code)

    results = []
    for class_name in matches:
        file_path = "src/main/java/" + class_name.replace(".", "/") + ".java"
        if file_path not in already_fetched:
            results.append(file_path)

    return list(dict.fromkeys(results))  # 순서 유지하면서 중복 제거

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

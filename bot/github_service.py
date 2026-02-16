from github import Github

from config import settings

_repo = None


def _get_repo():
    global _repo
    if _repo is None:
        github = Github(settings.github_token)
        _repo = github.get_repo(settings.github_repo)
    return _repo


def fetch_file_content(file_path: str) -> str | None:
    """GitHub에서 파일 내용을 조회한다. 없으면 None 반환."""
    try:
        content = _get_repo().get_contents(file_path, ref=settings.github_base_branch)
        return content.decoded_content.decode("utf-8")
    except Exception:
        return None


def fetch_files(file_paths: list[str]) -> dict[str, str]:
    """여러 파일을 조회해서 {경로: 내용} 딕셔너리로 반환한다."""
    results = {}
    for path in file_paths:
        content = fetch_file_content(path)
        if content is not None:
            results[path] = content
    return results

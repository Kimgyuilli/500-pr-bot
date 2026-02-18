import logging
from pathlib import Path

from github import Github, GithubException
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger(__name__)

_repo = None


def _get_repo():
    global _repo
    if _repo is None:
        github = Github(settings.github_token)
        _repo = github.get_repo(settings.github_repo)
    return _repo


def health_check() -> dict:
    """GitHub API 연결 상태 확인."""
    try:
        repo = _get_repo()
        _ = repo.full_name
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def fetch_file_content(file_path: str) -> str | None:
    """파일 내용을 조회한다. source_mode에 따라 로컬 또는 GitHub에서 읽는다. 없으면 None 반환."""
    if settings.source_mode == "local":
        try:
            return (Path(settings.local_source_path) / file_path).read_text(encoding="utf-8")
        except Exception:
            return None
    try:
        content = _get_repo().get_contents(file_path, ref=settings.github_base_branch)
        return content.decoded_content.decode("utf-8")
    except Exception:
        return None


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), reraise=True)
def fetch_files(file_paths: list[str]) -> dict[str, str]:
    """여러 파일을 조회해서 {경로: 내용} 딕셔너리로 반환한다."""
    results = {}
    for path in file_paths:
        content = fetch_file_content(path)
        if content is not None:
            results[path] = content
    return results


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), reraise=True)
def create_pull_request(
    files: list[dict],
    summary: str,
    pr_body: str,
    branch_name: str,
) -> str:
    """브랜치 생성 → 파일 커밋 → PR 생성. PR URL 반환."""
    repo = _get_repo()
    base_branch = settings.github_base_branch

    # 1. base 브랜치의 최신 SHA 가져오기
    base_ref = repo.get_git_ref(f"heads/{base_branch}")
    base_sha = base_ref.object.sha

    # 2. 새 브랜치 생성 (이미 존재하면 재사용)
    try:
        repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)
    except GithubException as e:
        if e.status == 422:  # already exists
            logger.warning("브랜치 이미 존재, 재사용: %s", branch_name)
        else:
            raise

    # 3. 수정된 파일 커밋
    for f in files:
        existing = repo.get_contents(f["path"], ref=branch_name)
        repo.update_file(
            path=f["path"],
            message=f"fix: {summary}",
            content=f["content"],
            sha=existing.sha,
            branch=branch_name,
        )

    # 4. PR 생성
    pr = repo.create_pull(
        title=f"fix: {summary}",
        body=pr_body,
        head=branch_name,
        base=base_branch,
    )
    return pr.html_url

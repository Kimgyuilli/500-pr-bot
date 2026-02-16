from unittest.mock import MagicMock, patch

from github import GithubException

from app.services.github_service import create_pull_request, fetch_file_content, fetch_files


def _mock_repo():
    return MagicMock()


@patch("app.services.github_service._get_repo")
def test_fetch_file_content_returns_decoded(mock_get_repo):
    repo = _mock_repo()
    content_obj = MagicMock()
    content_obj.decoded_content = b"public class Foo {}"
    repo.get_contents.return_value = content_obj
    mock_get_repo.return_value = repo

    result = fetch_file_content("src/main/java/Foo.java")
    assert result == "public class Foo {}"


@patch("app.services.github_service._get_repo")
def test_fetch_file_content_returns_none_on_error(mock_get_repo):
    repo = _mock_repo()
    repo.get_contents.side_effect = Exception("Not found")
    mock_get_repo.return_value = repo

    assert fetch_file_content("no/such/file.java") is None


@patch("app.services.github_service._get_repo")
def test_fetch_files_returns_dict_of_found_files(mock_get_repo):
    repo = _mock_repo()
    content_obj = MagicMock()
    content_obj.decoded_content = b"code"

    def side_effect(path, ref=None):
        if path == "missing.java":
            raise Exception("Not found")
        return content_obj

    repo.get_contents.side_effect = side_effect
    mock_get_repo.return_value = repo

    result = fetch_files(["found.java", "missing.java"])
    assert "found.java" in result
    assert "missing.java" not in result


@patch("app.services.github_service._get_repo")
def test_create_pull_request_returns_pr_url(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo

    ref = MagicMock()
    ref.object.sha = "abc123"
    repo.get_git_ref.return_value = ref

    existing = MagicMock()
    existing.sha = "file_sha"
    repo.get_contents.return_value = existing

    pr = MagicMock()
    pr.html_url = "https://github.com/owner/repo/pull/1"
    repo.create_pull.return_value = pr

    url = create_pull_request(
        files=[{"path": "Foo.java", "content": "fixed"}],
        summary="fix NPE",
        pr_body="body",
        branch_name="fix/error-abc-123",
    )
    assert url == "https://github.com/owner/repo/pull/1"
    repo.create_git_ref.assert_called_once()
    repo.update_file.assert_called_once()


@patch("app.services.github_service._get_repo")
def test_create_pull_request_reuses_existing_branch(mock_get_repo):
    repo = _mock_repo()
    mock_get_repo.return_value = repo

    ref = MagicMock()
    ref.object.sha = "abc123"
    repo.get_git_ref.return_value = ref

    repo.create_git_ref.side_effect = GithubException(422, "already exists", None)

    existing = MagicMock()
    existing.sha = "file_sha"
    repo.get_contents.return_value = existing

    pr = MagicMock()
    pr.html_url = "https://github.com/owner/repo/pull/2"
    repo.create_pull.return_value = pr

    url = create_pull_request(
        files=[{"path": "Foo.java", "content": "fixed"}],
        summary="fix NPE",
        pr_body="body",
        branch_name="fix/error-abc-123",
    )
    assert url == "https://github.com/owner/repo/pull/2"

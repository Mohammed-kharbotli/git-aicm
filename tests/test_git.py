from unittest.mock import patch, MagicMock
import subprocess

from aicm.git import get_diff, get_ticket, TICKET_PATTERN


def _mock_run(results):
    calls = iter(results)
    def side_effect(*args, **kwargs):
        return next(calls)
    return side_effect


def test_get_diff_staged():
    staged = MagicMock(stdout="diff --git a/file.py\n+hello", returncode=0)
    rev_parse = MagicMock(stdout=".", returncode=0)
    with patch("aicm.git.subprocess.run", side_effect=_mock_run([rev_parse, staged])):
        assert get_diff() == "diff --git a/file.py\n+hello"


def test_get_diff_unstaged_fallback():
    rev_parse = MagicMock(stdout=".", returncode=0)
    empty_staged = MagicMock(stdout="", returncode=0)
    unstaged = MagicMock(stdout="diff --git a/file.py\n+world", returncode=0)
    with patch("aicm.git.subprocess.run", side_effect=_mock_run([rev_parse, empty_staged, unstaged])):
        assert get_diff() == "diff --git a/file.py\n+world"


def test_get_diff_no_changes():
    rev_parse = MagicMock(stdout=".", returncode=0)
    empty = MagicMock(stdout="", returncode=0)
    with patch("aicm.git.subprocess.run", side_effect=_mock_run([rev_parse, empty, empty])):
        assert get_diff() == ""


def test_get_diff_not_git_repo():
    rev_parse = MagicMock(stdout="", returncode=128)
    with patch("aicm.git.subprocess.run", return_value=rev_parse):
        try:
            get_diff()
            assert False, "Should have called sys.exit"
        except SystemExit:
            pass


def test_get_ticket_from_branch():
    result = MagicMock(stdout="feature/PROJ-42-add-login", returncode=0)
    with patch("aicm.git.subprocess.run", return_value=result):
        assert get_ticket() == "PROJ-42"


def test_get_ticket_multiple_matches():
    result = MagicMock(stdout="feature/PROJ-42-JIRA-99-fix", returncode=0)
    with patch("aicm.git.subprocess.run", return_value=result):
        assert get_ticket() == "PROJ-42"


def test_get_ticket_no_match():
    result = MagicMock(stdout="main", returncode=0)
    with patch("aicm.git.subprocess.run", return_value=result):
        assert get_ticket() is None


def test_get_ticket_no_match_lowercase():
    result = MagicMock(stdout="feature/proj-42", returncode=0)
    with patch("aicm.git.subprocess.run", return_value=result):
        assert get_ticket() is None


def test_ticket_pattern():
    assert TICKET_PATTERN.search("JIRA-123").group(0) == "JIRA-123"
    assert TICKET_PATTERN.search("ABC-1").group(0) == "ABC-1"
    assert TICKET_PATTERN.search("A2B-99").group(0) == "A2B-99"
    assert TICKET_PATTERN.search("lowercase-123") is None

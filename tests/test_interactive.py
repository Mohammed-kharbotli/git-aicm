import os
from unittest.mock import patch, call

from aicm.interactive import interactive_commit, edit_message


def test_commit_choice():
    with patch("builtins.input", return_value="c"), \
         patch("aicm.interactive.subprocess.run") as mock_run, \
         patch("aicm.interactive.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        interactive_commit("feat: test")
        mock_run.assert_called_once_with(["git", "commit", "-m", "feat: test"], check=True)


def test_reject_choice():
    with patch("builtins.input", return_value="r"), \
         patch("aicm.interactive.subprocess.run") as mock_run, \
         patch("aicm.interactive.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        interactive_commit("feat: test")
        mock_run.assert_not_called()


def test_non_tty_skips_prompt():
    with patch("aicm.interactive.sys") as mock_sys, \
         patch("aicm.interactive.subprocess.run") as mock_run:
        mock_sys.stdin.isatty.return_value = False
        interactive_commit("feat: test")
        mock_run.assert_not_called()


def test_edit_message(tmp_path):
    with patch.dict(os.environ, {"EDITOR": "true"}):
        result = edit_message("original message")
        assert isinstance(result, str)

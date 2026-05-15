import os
import subprocess
from unittest.mock import patch, call, MagicMock

from aicm.interactive import interactive_commit, edit_message, save_message, load_message, clear_message


def test_commit_choice():
    with patch("builtins.input", return_value="c"), \
         patch("aicm.interactive.subprocess.run") as mock_run, \
         patch("aicm.interactive.clear_message"), \
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


def test_non_tty_skips_prompt(capsys):
    with patch("aicm.interactive.sys") as mock_sys, \
         patch("aicm.interactive.subprocess.run") as mock_run:
        mock_sys.stdin.isatty.return_value = False
        mock_sys.stderr = __import__("sys").stderr
        interactive_commit("feat: test")
        mock_run.assert_not_called()
    assert "Not a terminal" in capsys.readouterr().err


def test_commit_failure_preserves_message():
    inputs = iter(["c", "r"])
    with patch("builtins.input", side_effect=inputs), \
         patch("aicm.interactive.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")), \
         patch("aicm.interactive.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        mock_sys.stderr = MagicMock()
        interactive_commit("feat: test")


def test_commit_failure_then_skip_hooks():
    inputs = iter(["c", "s"])
    call_count = [0]
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise subprocess.CalledProcessError(1, "git")
    with patch("builtins.input", side_effect=inputs), \
         patch("aicm.interactive.subprocess.run", side_effect=side_effect) as mock_run, \
         patch("aicm.interactive.clear_message"), \
         patch("aicm.interactive.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        mock_sys.stderr = MagicMock()
        interactive_commit("feat: test")
        assert mock_run.call_count == 2
        mock_run.assert_called_with(
            ["git", "commit", "-m", "feat: test", "--no-verify"], check=True
        )


def test_commit_failure_then_fix(capsys):
    inputs = iter(["c", "f"])
    with patch("builtins.input", side_effect=inputs), \
         patch("aicm.interactive.subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")), \
         patch("aicm.interactive.save_message", return_value="/tmp/AICM_MSG") as mock_save, \
         patch("aicm.interactive.sys") as mock_sys:
        mock_sys.stdin.isatty.return_value = True
        mock_sys.stderr = MagicMock()
        interactive_commit("feat: test")
        mock_save.assert_called_once_with("feat: test")
    assert "Message saved" in capsys.readouterr().out


def test_save_load_clear_message(tmp_path):
    msg_file = tmp_path / "AICM_MSG"
    with patch("aicm.interactive.get_git_dir", return_value=str(tmp_path)):
        save_message("feat: saved")
        assert msg_file.exists()
        assert load_message() == "feat: saved"
        clear_message()
        assert not msg_file.exists()
        assert load_message() is None


def test_load_message_no_git_dir():
    with patch("aicm.interactive.get_git_dir", return_value=None):
        assert load_message() is None


def test_edit_message(tmp_path):
    with patch.dict(os.environ, {"EDITOR": "true"}):
        result = edit_message("original message")
        assert isinstance(result, str)

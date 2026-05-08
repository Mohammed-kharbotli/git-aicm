import sys
from unittest.mock import patch, MagicMock

from aicm import main, cmd_generate, __version__, MAX_DIFF_LINES


def test_version_flag(capsys):
    with patch("sys.argv", ["git-aicm", "--version"]):
        try:
            main()
        except SystemExit:
            pass
    assert __version__ in capsys.readouterr().out


def test_dry_run_no_interactive(capsys):
    diff = "diff --git a/f.py\n+hello"
    args = MagicMock()
    args.command = None
    args.r_backend = "ollama"
    args.r_model = None
    args.r_ollama_url = None
    args.r_profile = None
    args.r_format = None
    args.r_ticket = None
    args.r_context = None
    args.r_detailed = False
    args.r_dry_run = True

    with patch("aicm.get_diff", return_value=diff), \
         patch("aicm.get_ticket", return_value=None), \
         patch("aicm.BACKENDS", {"ollama": lambda p, c: "feat: test"}), \
         patch("aicm.interactive_commit") as mock_ic:
        # Simulate the root-level arg mapping
        args.backend = args.r_backend
        args.model = args.r_model
        args.ollama_url = args.r_ollama_url
        args.profile = args.r_profile
        args.format = args.r_format
        args.ticket = args.r_ticket
        args.context = args.r_context
        args.detailed = args.r_detailed
        args.dry_run = args.r_dry_run
        cmd_generate(args)
        mock_ic.assert_not_called()


def test_diff_truncation(capsys):
    big_diff = "\n".join([f"+line {i}" for i in range(MAX_DIFF_LINES + 100)])
    args = MagicMock()
    args.dry_run = True
    args.detailed = False
    args.ticket = None

    captured_prompt = []

    def fake_backend(prompt, config):
        captured_prompt.append(prompt)
        return "feat: big change"

    with patch("aicm.get_diff", return_value=big_diff), \
         patch("aicm.get_diff_stat", return_value="file.py | 600 +++"), \
         patch("aicm.get_ticket", return_value=None), \
         patch("aicm.get_config", return_value={"backend": "ollama", "format": "conventional", "context": None, "ollama_url": "http://localhost:11434"}), \
         patch("aicm.BACKENDS", {"ollama": fake_backend}):
        cmd_generate(args)

    prompt = captured_prompt[0]
    assert "Change summary" in prompt
    assert "file.py | 600" in prompt
    assert "+line 0" in prompt
    assert f"+line {MAX_DIFF_LINES}" not in prompt


def test_keyboard_interrupt(capsys):
    with patch("sys.argv", ["git-aicm"]), \
         patch("aicm.cmd_generate", side_effect=KeyboardInterrupt):
        try:
            main()
        except SystemExit as e:
            assert e.code == 130
    assert "Aborted" in capsys.readouterr().err

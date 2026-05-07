from aicm.prompts import FORMATS, PROMPTS, get_prompt


def test_formats_list():
    assert "conventional" in FORMATS
    assert "simple" in FORMATS


def test_all_formats_have_prompts():
    for fmt in FORMATS:
        assert fmt in PROMPTS
        assert f"{fmt}_detailed" in PROMPTS


def test_get_prompt_includes_diff():
    diff = "+hello world"
    for fmt in FORMATS:
        prompt = get_prompt(fmt, diff)
        assert diff in prompt


def test_conventional_prompt_mentions_types():
    prompt = get_prompt("conventional", "test")
    assert "feat" in prompt
    assert "fix" in prompt


def test_simple_prompt_is_short():
    prompt = get_prompt("simple", "test")
    assert "one-line" in prompt.lower() or "72" in prompt


def test_detailed_prompt_mentions_body():
    prompt = get_prompt("conventional", "test", detailed=True)
    assert "bullet" in prompt.lower()

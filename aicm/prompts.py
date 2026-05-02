PROMPTS = {
    "conventional": """Write a git commit message for this diff using Conventional Commits format.
Rules:
- First line: type(scope): description (max 72 chars)
- Types: feat, fix, refactor, docs, test, chore, style, perf, ci, build
- Must be exactly 5 lines total (including summary)
- Line 2: blank line
- Lines 3-5: bullet points explaining key changes (3 bullets required)
- Keep total message under 350 characters
- Return ONLY the commit message, no explanations

Diff:
{diff}""",

    "simple": """Write a detailed git commit message for this diff.
Rules:
- Must be exactly 5 lines total
- Line 1: main summary (max 72 chars)
- Line 2: blank line
- Lines 3-5: detailed explanation of changes (3 lines required)
- Keep total message under 300 characters
- Return ONLY the commit message, no explanations

Diff:
{diff}""",

    "detailed": """Write a comprehensive git commit message for this diff.
Rules:
- Must be exactly 5 lines total
- Line 1: summary (max 72 chars)
- Line 2: blank line
- Lines 3-5: detailed bullet points explaining changes (3 bullets required)
- Keep total message under 400 characters
- Return ONLY the commit message, no explanations

Diff:
{diff}""",
}

FORMATS = list(PROMPTS.keys())

LARGE_DIFF_PREFIX = """The full diff is too large. Here is a summary of all changed files, followed by the most important hunks.

Change summary:
{stat}

Key changes (truncated):
{diff}"""


def get_prompt(fmt, diff, stat=None):
    if fmt not in FORMATS:
        raise ValueError(f"Unknown format: {fmt}. Use: {', '.join(FORMATS)}")
    
    # Basic input validation
    if not isinstance(diff, str):
        raise ValueError("diff must be a string")
    if stat is not None and not isinstance(stat, str):
        raise ValueError("stat must be a string or None")
    
    # Validate input lengths to prevent excessive memory usage
    if len(diff) > 1000000:  # 1MB limit
        raise ValueError("diff is too large (>1MB)")
    if stat and len(stat) > 100000:  # 100KB limit for stats
        raise ValueError("stat is too large (>100KB)")
    
    # Sanitize inputs - remove any potential template injection patterns
    safe_diff = diff.replace('{', '{{').replace('}', '}}')
    
    if stat:
        safe_stat = stat.replace('{', '{{').replace('}', '}}')
        combined = LARGE_DIFF_PREFIX.format(stat=safe_stat, diff=safe_diff)
        return PROMPTS[fmt].format(diff=combined)
    return PROMPTS[fmt].format(diff=safe_diff)

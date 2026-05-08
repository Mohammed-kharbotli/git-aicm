_CONVENTIONAL_TYPES = """- Choose exactly ONE type from this list based on what the diff actually does:
  feat = new feature or capability
  fix = bug fix or correcting broken behavior
  refactor = restructuring code without changing behavior
  docs = documentation only
  test = adding or updating tests
  chore = maintenance, dependencies, config
  style = formatting, whitespace, no logic change
  perf = performance improvement
  ci = CI/CD pipeline changes
  build = build system or external dependencies
- Format: type(scope): description  OR  type: description
- Do NOT combine types (e.g. "fix build:" is WRONG, pick the single best fit)
- Do NOT default to feat"""

PROMPTS = {
    "conventional": f"""Write a git commit message for this diff using Conventional Commits format.
Rules:
- First line: type(scope): description (max 72 chars)
{_CONVENTIONAL_TYPES}
- Output ONLY the summary line, nothing else
- Keep under 72 characters
- ONLY describe changes that are visible in the diff. Do NOT invent or assume changes that are not shown
- Return ONLY the commit message, no explanations

Diff:
{{diff}}""",

    "conventional_detailed": f"""Write a git commit message for this diff using Conventional Commits format.
Rules:
- First line: type(scope): description (max 72 chars)
{_CONVENTIONAL_TYPES}
- After the summary, add a blank line then bullet points explaining key changes
- Keep total message under 350 characters
- ONLY describe changes that are visible in the diff. Do NOT invent or assume changes that are not shown
- Return ONLY the commit message, no explanations

Diff:
{{diff}}""",

    "simple": """Write a git commit message for this diff.
Rules:
- Output ONLY a single summary line (max 72 chars)
- ONLY describe changes that are visible in the diff. Do NOT invent or assume changes that are not shown
- Return ONLY the commit message, no explanations

Diff:
{diff}""",

    "simple_detailed": """Write a git commit message for this diff.
Rules:
- Line 1: main summary (max 72 chars)
- After the summary, add a blank line then explain the key changes
- Keep total message under 300 characters
- ONLY describe changes that are visible in the diff. Do NOT invent or assume changes that are not shown
- Return ONLY the commit message, no explanations

Diff:
{diff}""",
}

FORMATS = ["conventional", "simple"]

LARGE_DIFF_PREFIX = """The full diff is too large. Here is a summary of all changed files, followed by the most important hunks.

Change summary:
{stat}

Key changes (truncated):
{diff}"""


def get_prompt(fmt, diff, stat=None, context=None, detailed=False):
    if fmt not in FORMATS:
        raise ValueError(f"Unknown format: {fmt}. Use: {', '.join(FORMATS)}")

    if not isinstance(diff, str):
        raise ValueError("diff must be a string")
    if stat is not None and not isinstance(stat, str):
        raise ValueError("stat must be a string or None")

    if len(diff) > 1000000:
        raise ValueError("diff is too large (>1MB)")
    if stat and len(stat) > 100000:
        raise ValueError("stat is too large (>100KB)")

    prompt_key = f"{fmt}_detailed" if detailed else fmt

    safe_diff = diff.replace('{', '{{').replace('}', '}}')

    if stat:
        safe_stat = stat.replace('{', '{{').replace('}', '}}')
        combined = LARGE_DIFF_PREFIX.format(stat=safe_stat, diff=safe_diff)
        prompt = PROMPTS[prompt_key].format(diff=combined)
    else:
        prompt = PROMPTS[prompt_key].format(diff=safe_diff)

    if context:
        if len(context) > 500:
            raise ValueError("context is too long (>500 chars)")
        prompt += f"\n\nAdditional context: {context}"

    return prompt

"""Diff -> PR description, enriched with impact analysis from the index."""
import os, re, subprocess
from .llm import chat
from retrieval.vectorstore import CodeIndex

MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "12000"))  # raise for big-context models

PROMPT = """Write a pull request description for the diff below.

Use exactly these sections:
## Summary
(1-3 sentences: what this PR does)
## What changed
(bullets, grouped by file or concern)
## Why it matters
(the likely motivation / user-visible effect; say "unclear" if the diff doesn't show it)
## Risk areas
(what could break; use the impact analysis below)
## Suggested tests

Be specific and don't invent behavior not shown in the diff.

### Impact analysis (computed from the code index)
{impact}

### Diff
{diff}
"""


def get_diff(repo: str, base: str | None, staged: bool) -> str:
    if base:
        cmd = ["git", "diff", f"{base}...HEAD"]
    elif staged:
        cmd = ["git", "diff", "--cached"]
    else:
        cmd = ["git", "diff", "HEAD"]
    return subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=True).stdout


def changed_ranges(diff: str) -> dict[str, list[tuple[int, int]]]:
    """Parse unified diff -> {file: [(new_start, new_end), ...]}."""
    out, cur = {}, None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
            out[cur] = []
        elif line.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                s, n = int(m.group(1)), int(m.group(2) or 1)
                out[cur].append((s, s + max(n, 1) - 1))
    return out


def impact_analysis(diff: str, index: CodeIndex) -> str:
    lines = []
    seen = set()
    for f, ranges in changed_ranges(diff).items():
        for c in index.chunks:
            if c["file"] != f or c["kind"] == "module":
                continue
            if any(s <= c["end_line"] and e >= c["start_line"] for s, e in ranges):
                key = (f, c["name"])
                if key in seen:
                    continue
                seen.add(key)
                users = index.find_usages(c["name"])
                if users:
                    where = ", ".join(sorted({u["file"] for u in users})[:5])
                    lines.append(f"- `{c['name']}` ({f}) is referenced in {len(users)} "
                                 f"other chunk(s): {where}")
                else:
                    lines.append(f"- `{c['name']}` ({f}): no other references found")
    return "\n".join(lines) or "(no indexed symbols overlap the diff)"


def describe(repo: str, base: str | None = None, staged: bool = False) -> str:
    diff = get_diff(repo, base, staged)
    if not diff.strip():
        return "No changes found."
    try:
        impact = impact_analysis(diff, CodeIndex(repo))
    except FileNotFoundError:
        impact = "(repo not indexed; run `index` for impact analysis)"
    truncated = diff[:MAX_DIFF_CHARS]
    if len(diff) > MAX_DIFF_CHARS:
        truncated += "\n... [diff truncated]"
    resp = chat([{"role": "user",
                  "content": PROMPT.format(impact=impact, diff=truncated)}], max_tokens=1500)
    return resp.choices[0].message.content or ""

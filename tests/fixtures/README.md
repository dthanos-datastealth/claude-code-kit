# Test fixtures

## `previous-release-CLAUDE.md`

The `claude/CLAUDE.md` that stable users actually have installed — the template
at the head of `main`. The upgrade guards in
`tests/test_intelligent_claude_md_merge.py` replay the real merge from this file
to the current template and assert the result is byte-identical to the template.

**Refresh it as part of promoting `prerelease` to `main`,** in the same PR that
flips the channel refs, so it always describes the release users are upgrading
*from*. A guard fails if it is ever refreshed to match the current template,
because a baseline equal to HEAD makes the upgrade tests assert nothing.

Do not derive this baseline from `git log` instead. That was tried: `git log -2
-- claude/CLAUDE.md` resolves to an intermediate commit of the release being
developed, so zero headings differ, both guards pass with nothing asserted, and
the window shrinks with every further commit.

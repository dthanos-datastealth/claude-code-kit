# security-guidance — OWASP-aware code review on pending changes

**What it does:**
The `security-guidance` plugin installs a `/security-review` skill that
runs a security-focused review pass against the pending changes on the
current branch — staged diff, unstaged diff, and any new files — and
flags classes of issue that general code review tends to miss:

- OWASP Top 10 classes — injection (SQL, command, LDAP, NoSQL),
  broken access control, authentication and session weaknesses,
  cryptographic misuse, server-side request forgery, insecure
  deserialization, secrets in code, etc.
- Input-handling failures — missing validation, dangerous parsers,
  trust-boundary crossings without sanitization.
- Auth / authz gaps — missing checks on new endpoints, privilege
  escalation surfaces, token handling mistakes.
- Data exposure — logged secrets, unredacted PII, debug surfaces
  shipped to production paths.
- Supply-chain smells — new dependencies pulled from untrusted
  sources, lock-file mismatches, install-time scripts.

It returns a structured report with severity, location, and a concrete
fix recommendation per finding rather than a generic checklist.

**Why it's in this kit:**
The kit's general workflow already enforces code review (via
`superpowers:requesting-code-review`) and simplification (via
`code-simplifier`), but those passes focus on correctness, clarity,
and reuse — not on adversarial input or threat surfaces. Security
issues are the canonical "easy to miss in normal review, expensive to
fix after merge" class of bug, so having a dedicated pre-merge pass is
the right structural defense.

`/security-review` complements rather than replaces the general review:
the general review catches most bugs and design problems; the security
review catches the subset of bugs whose cost is paid in incidents
rather than in support tickets.

**When you'd disable it:**
- Docs-only changes, comment updates, or pure rename refactors with no
  new logic on a trust boundary.
- Generated code (migrations, schemas, lockfiles) where the changes
  are mechanical and the security review would just create noise.
- Internal-only tooling on a trusted network with no external input
  surface (one-off scripts, local dev utilities).

Do not disable it for any change that touches authentication,
authorization, input parsing, network I/O, cryptography, secrets,
deserialization, file uploads, command execution, or any new
external-facing endpoint.

**Source:**
GitHub: <https://github.com/anthropics/claude-plugins-official>
Marketplace: `anthropics/claude-plugins-official`
Plugin name: `security-guidance`

Install via the kit's `install.sh`, which registers the marketplace and
runs `claude plugin install security-guidance@anthropics/claude-plugins-official`.

The skill is pure prompt content; it operates on the working tree via
Claude Code's existing file-access and git tools. No external scanning
service, no API key.

**Cost / footprint:**
- Disk: negligible — a single markdown skill file.
- Memory / CPU: zero at idle. The skill is invoked on demand by the
  `Skill` tool.
- Network: none. The review runs entirely against the local diff.
- Dependencies: a working git repository so the skill can identify the
  pending change set.

The token cost is bounded by the size of the diff under review.
Skipping it on docs/comment-only changes is cheap; running it on
substantive changes is dramatically cheaper than the cost of the
post-merge incident it is designed to prevent.

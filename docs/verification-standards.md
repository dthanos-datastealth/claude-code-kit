# Verification standards — what counts as evidence

`claude/CLAUDE.md` states three verification rules as one line each. This
document is why they exist and what they forbid in practice. Each one was
written after a specific failure where a green result hid a real defect, and
the incidents are kept here because the rule is much easier to rationalise away
without them.

The common shape of all three: **a check that cannot observe the failure it is
supposed to catch will report success.** That is worse than no check, because it
ends the investigation.

---

## 1. Never verify a user-facing or protection feature with a synthetic proxy

**Forbidden:**

- creating your own input or element and firing events on it
- reading transformed values back from a DOM node you set yourself
- dispatching a `CustomEvent` or message straight to a handler
- treating a UI signal — a toast, a banner, a status line — as proof

All of these test a proxy you control, not the real flow.

**The only acceptable evidence** is to drive the *real* application widget
exactly as an interactive user does, **and** assert the *ground truth*. For a
data-protection feature, ground truth is the outbound network request carrying
zero leaked or raw values — not what the UI says happened.

If the harness cannot drive the real widget, that is a **blocker**. Escalate;
do not substitute. A test that passes because the real action never happened is
vacuous, not green.

**Why this rule exists.** A synthetic check reported `file protected: true`
while a total raw-PII leak went to a live LLM. The check was asserting on an
object the test itself had constructed, so it could not observe the real upload
path at all. It passed for exactly as long as the leak did.

---

## 2. A script can never confirm a visual result

Whenever an image is involved — a standalone image file, an OOXML media part, a
rasterised PDF page, any canvas a pipeline paints on — the only acceptable
confirmation is that the render was **rasterised and looked at**: at a
resolution where text is legible, for **every page of every render**, and the
**whole** page, not only the region under repair.

Re-OCR, pixel statistics, ink-coverage percentages, byte comparisons and
"0 leaked" counts decide only *which* renders are worth viewing. None of them is
evidence about what a render shows, and none may be cited as confirmation.

Never write "confirmed", "verified" or "N files clean" on the strength of a
script. **If a render has not been viewed, say so plainly.**

**Why this rule exists.** A re-OCR check reported "0 of 9 secrets readable" and a
fix was declared verified on it. Viewing the page showed a bcrypt tail's glyph
tops protruding above a paint rectangle that sat slightly too low.

The mechanism matters, because it generalises: the check searched for each
secret's *head*. A value covered at the head and exposed at the tail matches no
needle, so a needle-based check cannot see a **partially** covered value — which
is precisely the failure that matters. On the same page an ink-area statistic
read +0.7%, while the render showed three page-wide bars and one token painted
five times over.

---

## 3. The redundant-WORK hunt (O agent, first-class)

Graded at the same severity as redundant code. Redundancy is not only duplicated
*code*, it is duplicated *work*: code that re-executes something an earlier step
already did.

The canonical miss this prevents: a "preview" action that re-calls the backend
or LLM classifier the "scan" already called, because the scan discarded its
results instead of caching them. Pure latency tax — and a correctness risk too
whenever the call is non-deterministic.

**Procedure. Its output must appear in the report.**

1. **Enumerate every expensive operation in the diff**, with `file:line`:
   network/HTTP/RPC, LLM or backend classification, DB query, OCR, crypto, file
   parse, `Office.run` / `context.sync()`, any cross-process or network `await`.

2. **Trace each user-action or request flow end to end** — for example
   `scan → preview → save` — and for every expensive call ask: *did a prior step
   already compute this, for the same input?* If it is recomputed rather than
   cached and reused, flag it.

3. **State per call site** whether it is **cached+reused** or **recomputed**, and
   on which flow.

**Finding types:**

| Tag | Meaning |
|---|---|
| `[REDUNDANT EXPENSIVE CALL]` | recomputed what an earlier step produced — **blocking**; fix by caching the first result and reusing it |
| `[UNCACHED RECOMPUTATION]` | expensive pure compute repeated on unchanged inputs |
| `[HOT-PATH N+1 / SYNC-IN-LOOP]` | round trip inside a loop over N items where one batch would do — quantify N |
| `[REDUNDANT ROUND-TRIP]` | same resource fetched twice in one flow |
| `[RE-INCURRED BLOCKING WAIT]` | hard-coded sleep or timeout re-paid on every repeat of an action |

An O report lacking the per-call-site cache/flow trace is **itself a finding**.

**Pair the tools.** When the diff touches any expensive operation or hot path,
run the `optibot` perf-review skill *in addition to* `code-simplifier` for the O
role. `code-simplifier` targets clarity; `optibot` targets speed and cost. A
clarity-only review demonstrably misses redundant-work patterns — it once passed
a preview that re-ran the classifier on every click.

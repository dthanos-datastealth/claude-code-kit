# Verification standards — what counts as evidence

`claude/rules/30-kit-quality-loop.md` states three verification rules as one line each. This
document is what each one forbids in practice, and the failure mode it exists to
catch. The mechanism is included deliberately: each rule is easy to rationalise
away in the moment, and much harder once you can see why the check you were
about to substitute is structurally incapable of catching the defect.

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

**The failure mode.** A synthetic check asserts on an object the test itself
constructed, so it never observes the real path at all. It reports success for
exactly as long as the real path is broken, and it reports success on the first
run, before the feature works — which is the tell. If a check would pass against
an unimplemented feature, it is measuring the harness, not the product.

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

**The failure mode, and why it generalises.** A needle-based check searches for
a known value and reports whether it found it. It therefore cannot see a
**partially** rendered value: covered at the head and exposed at the tail, the
value matches no needle and the check reports clean. Partial is the failure that
matters, and it is the one such a check is structurally blind to.

Aggregate statistics fail differently and just as badly. A coverage or ink-area
percentage moving by a plausible amount is consistent with the correct result
and with several wrong ones — too much paint, paint in the wrong place, the same
region painted repeatedly. A number cannot distinguish them. Looking can.

---

## 3. The redundant-WORK hunt (O agent, first-class)

Graded at the same severity as redundant code. Redundancy is not only duplicated
*code*, it is duplicated *work*: code that re-executes something an earlier step
already did.

The shape to look for: a later step in a flow recomputes what an earlier step
already produced, because the earlier step discarded its result instead of
caching it. Pure latency tax — and a correctness risk too whenever the call is
non-deterministic, since the two runs can disagree.

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
clarity-only review misses redundant-work patterns structurally: re-running an
expensive call is not a clarity defect, so a reviewer looking for clarity has no
reason to flag it. The code reads perfectly well and does the work twice.

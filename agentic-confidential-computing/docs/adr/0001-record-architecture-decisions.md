# 1. Record architecture decisions

**Status:** accepted

## Context

This project chooses between method families whose tradeoffs are not obvious
and whose evidence arrives incrementally. Without a written record, rejected
options get relitigated and the reasoning behind a choice is lost as soon as
the people involved move on.

## Decision

Every architectural decision gets an ADR: context, the options considered, the
decision, and the evidence that settled it. In particular:

- Each method family that is adopted or rejected.
- Each build-not-reuse call, per `docs/research/oss-inventory.md`.
- Each answer to a gating question in `docs/ai-cloud-audit.md` that changes the
  design.

An ADR written before the harness has produced numbers is marked
**provisional** and names the measurement that would settle it.

## Consequences

Rejections are as durable as adoptions — the FHE performance number gets
recorded once and stops being an open question. The cost is one short document
per decision.

"""Core types every protection method and attack is written against.

The trust boundary is deliberately expressed in the type system: `protect`
returns a `ProtectedPayload` -- the only object that crosses to the agent --
and a `ReidentificationMap` that stays client-side. An attack is scored
against the payload alone, so anything reachable from it is, by definition,
disclosed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Sequence

Verdict = str
"""One of TP, FP, FN, TN -- the adjudication outcome for a single span."""

ReidentificationMap = dict[str, str]
"""Surrogate span id -> original span id. Never crosses the trust boundary."""


@dataclass(frozen=True)
class Span:
    span_id: str
    start: int
    end: int
    entity_type: str | None = None


@dataclass
class Record:
    """One customer submission.

    `spans` carries what the customer's deterministic detector declared, which
    is the R2 input. `ground_truth_spans` is evaluation-only: it holds the real
    labels, including entities the detector missed, and is never passed to a
    protection method. Keeping the two apart is what makes false-negative
    leakage measurable instead of assumed.
    """

    record_id: str
    text: str
    spans: Sequence[Span]
    metadata: dict = field(default_factory=dict)
    ground_truth_spans: Sequence[Span] = field(default_factory=tuple)

    def value_of(self, span: Span) -> str:
        return self.text[span.start : span.end]


@dataclass
class ProtectedPayload:
    """Everything the agent gets to see, and nothing else."""

    record_id: str
    text: str
    spans: Sequence[Span]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "text": self.text,
            "spans": [
                {
                    "span_id": s.span_id,
                    "start": s.start,
                    "end": s.end,
                    "entity_type": s.entity_type,
                }
                for s in self.spans
            ],
            "metadata": self.metadata,
        }


class ProtectionMethod(ABC):
    """A candidate answer to "analyze it without seeing it"."""

    name: str = "unnamed"

    leaks_plaintext: bool = False
    """Declared, not inferred. Only the plaintext ceiling may set this True."""

    @abstractmethod
    def protect(self, record: Record) -> tuple[ProtectedPayload, ReidentificationMap]:
        """Transform a record into what crosses the boundary, plus the client-side map."""

    def restore(
        self, verdicts: dict[str, Verdict], mapping: ReidentificationMap
    ) -> dict[str, Verdict]:
        """Map surrogate-keyed verdicts back to original span ids, client-side."""
        return {
            mapping[surrogate_id]: verdict
            for surrogate_id, verdict in verdicts.items()
            if surrogate_id in mapping
        }


def iter_methods() -> Iterable[ProtectionMethod]:
    """Every method the contract suite holds to account."""
    from eval.methods.naive_sanitize import NaiveSanitize
    from eval.methods.plaintext_baseline import PlaintextBaseline

    return [PlaintextBaseline(), NaiveSanitize()]

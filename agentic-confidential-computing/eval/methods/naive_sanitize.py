"""Mask exactly what the deterministic detector already found.

This is the design most teams reach for first, and it is unsound for R2: it
masks the detector's hits and leaves its misses untouched, so the false
negatives -- the whole reason the adjudication exists -- cross the boundary in
the clear. It ships as a negative control so that failure is measured on every
run rather than argued about.
"""

from __future__ import annotations

from eval.harness.method import (
    ProtectedPayload,
    ProtectionMethod,
    Record,
    ReidentificationMap,
    Span,
)


class NaiveSanitize(ProtectionMethod):
    name = "naive_sanitize"

    def protect(self, record: Record) -> tuple[ProtectedPayload, ReidentificationMap]:
        text = record.text
        spans: list[Span] = []
        mapping: ReidentificationMap = {}

        # Rewrite right-to-left so earlier offsets stay valid as lengths change.
        ordered = sorted(record.spans, key=lambda s: s.start, reverse=True)
        for index, span in enumerate(ordered):
            surrogate_id = f"x{len(record.spans) - index}"
            placeholder = f"[{span.entity_type or 'ENTITY'}_{surrogate_id}]"
            text = text[: span.start] + placeholder + text[span.end :]
            spans.append(
                Span(
                    span_id=surrogate_id,
                    start=span.start,
                    end=span.start + len(placeholder),
                    entity_type=span.entity_type,
                )
            )
            mapping[surrogate_id] = span.span_id

        spans.reverse()
        payload = ProtectedPayload(
            record_id=record.record_id,
            text=text,
            spans=spans,
            metadata=dict(record.metadata),
        )
        return payload, mapping

"""No protection at all -- the utility ceiling.

Every other method is scored as a loss against this one. It is also the
positive control for the leak detector: a check that cannot catch this method
cannot be trusted to clear any other.
"""

from __future__ import annotations

from eval.harness.method import (
    ProtectedPayload,
    ProtectionMethod,
    Record,
    ReidentificationMap,
)


class PlaintextBaseline(ProtectionMethod):
    name = "plaintext_baseline"
    leaks_plaintext = True

    def protect(self, record: Record) -> tuple[ProtectedPayload, ReidentificationMap]:
        payload = ProtectedPayload(
            record_id=record.record_id,
            text=record.text,
            spans=list(record.spans),
            metadata=dict(record.metadata),
        )
        mapping = {span.span_id: span.span_id for span in record.spans}
        return payload, mapping

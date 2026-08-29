"""Direct disclosure: which real values survive verbatim in the payload.

This is the weakest adversary in the suite -- it only reads what is literally
present, with no inference. That is the point. Anything it finds is disclosed
under any threat model, so a method that fails here needs no further analysis.
Reconstruction, re-identification and attribute-inference attacks build on top
of it.

Scored against `ground_truth_spans`, never against the detector's `spans`, so
a detector's own blind spots cannot hide a leak from the measurement.
"""

from __future__ import annotations

import json

from eval.harness.method import ProtectedPayload, Record


def disclosed_values(payload: ProtectedPayload, record: Record) -> set[str]:
    """Ground-truth sensitive values that appear verbatim anywhere in the payload."""
    serialized = json.dumps(payload.to_dict())
    truth = record.ground_truth_spans or record.spans
    return {
        value
        for value in (record.value_of(span) for span in truth)
        if value and value in serialized
    }


def disclosure_rate(payload: ProtectedPayload, record: Record) -> float:
    """Fraction of ground-truth sensitive values disclosed verbatim, in [0, 1]."""
    truth = record.ground_truth_spans or record.spans
    if not truth:
        return 0.0
    return len(disclosed_values(payload, record)) / len(truth)

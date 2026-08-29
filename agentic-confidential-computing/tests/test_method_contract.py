"""Contract every protection method must satisfy.

These tests encode the two properties the project rests on:

1. The protected payload is the ONLY thing that crosses the trust boundary, so
   for any method that claims to protect, it must not carry original values.
2. Verdicts return keyed to surrogate span ids and must map back to original
   span ids client-side -- the "transform on the customer side gives the final
   answer" requirement.

PlaintextBaseline is the deliberate exception: it exists to fix the utility
ceiling and declares that it leaks. Asserting that the leak check actually
catches it is what proves the check has teeth.
"""

import json

import pytest

from eval.harness.method import Record, Span, iter_methods


def _record() -> Record:
    return Record(
        record_id="r1",
        text="Patient Aisha Okonkwo, SIN 046454286, admitted Tuesday.",
        spans=[
            Span(span_id="s1", start=8, end=21, entity_type="PERSON"),
            Span(span_id="s2", start=27, end=36, entity_type="NATIONAL_ID"),
        ],
        metadata={"source": "test"},
    )


def _leaked_values(method, record):
    protected, _ = method.protect(record)
    serialized = json.dumps(protected.to_dict())
    return [v for v in (record.value_of(s) for s in record.spans) if v in serialized]


@pytest.mark.parametrize("method", iter_methods(), ids=lambda m: m.name)
def test_protecting_methods_do_not_emit_original_values(method):
    record = _record()
    if method.leaks_plaintext:
        pytest.skip(f"{method.name} declares it leaks; covered by the teeth test")
    assert _leaked_values(method, record) == []


def test_leak_check_has_teeth():
    """A method that genuinely leaks must be caught, or every skip above is worthless."""
    from eval.methods.plaintext_baseline import PlaintextBaseline

    record = _record()
    assert sorted(_leaked_values(PlaintextBaseline(), record)) == [
        "046454286",
        "Aisha Okonkwo",
    ]


@pytest.mark.parametrize("method", iter_methods(), ids=lambda m: m.name)
def test_restore_maps_verdicts_back_to_original_span_ids(method):
    record = _record()
    protected, mapping = method.protect(record)
    verdicts = {span.span_id: "TP" for span in protected.spans}
    assert set(method.restore(verdicts, mapping)) == {"s1", "s2"}

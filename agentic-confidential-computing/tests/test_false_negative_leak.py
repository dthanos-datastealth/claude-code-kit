"""The false-negative paradox, measured rather than argued.

Sanitizing a payload using the deterministic detector's own output masks what
the detector found and leaves what it missed. Those misses are exactly the
false negatives the adjudication exists to catch, so the naive design ships
them across the boundary in the clear.

If this test ever passes for naive_sanitize, the leak measurement has broken,
not the finding.
"""

from eval.attacks.disclosure import disclosed_values
from eval.harness.method import Record, Span
from eval.methods.naive_sanitize import NaiveSanitize
from eval.methods.plaintext_baseline import PlaintextBaseline


def _record_with_a_detector_miss() -> Record:
    text = "Patient Aisha Okonkwo, SIN 046454286, admitted Tuesday."
    person = Span(span_id="s1", start=8, end=21, entity_type="PERSON")
    national_id = Span(span_id="s2", start=27, end=36, entity_type="NATIONAL_ID")
    return Record(
        record_id="r1",
        text=text,
        spans=[person],  # the detector found only the name
        ground_truth_spans=[person, national_id],  # the SIN is its false negative
        metadata={"source": "test"},
    )


def test_naive_sanitize_discloses_the_detector_false_negative():
    record = _record_with_a_detector_miss()
    payload, _ = NaiveSanitize().protect(record)
    assert disclosed_values(payload, record) == {"046454286"}


def test_naive_sanitize_still_conceals_what_the_detector_found():
    record = _record_with_a_detector_miss()
    payload, _ = NaiveSanitize().protect(record)
    assert "Aisha Okonkwo" not in payload.text


def test_plaintext_baseline_discloses_everything():
    record = _record_with_a_detector_miss()
    payload, _ = PlaintextBaseline().protect(record)
    assert disclosed_values(payload, record) == {"Aisha Okonkwo", "046454286"}

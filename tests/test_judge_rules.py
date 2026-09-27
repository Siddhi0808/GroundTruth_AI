"""B09: deterministic judge regression tests, including the false positives found in the audit."""
import pytest

from backend.llm.judge import HALLUCINATED, INSUFFICIENT, SUPPORTED, heuristic_judge

BELL = ("[telephone.txt]: Alexander Graham Bell was a Scottish-born inventor. He invented the first practical "
        "telephone. Bell received a patent for the telephone in 1876.")


@pytest.mark.parametrize("response, expected", [
    # Audit false positives (previously all "Hallucinated")
    ("Bell patented the telephone in 1876.", SUPPORTED),                       # short correct answer
    ("Alexander Graham Bell invented the first practical telephone.", SUPPORTED),
    ("The Scottish-born inventor Bell received a telephone patent.", SUPPORTED),
    # Genuine hallucinations still caught
    ("Bell patented the telephone in 1877.", HALLUCINATED),                    # wrong number
    ("Bell did not invent the telephone.", HALLUCINATED),                      # negation
    ("Thomas Edison invented the first practical telephone.", HALLUCINATED),   # multi-word entity swap
    ("Edison invented the first practical telephone.", HALLUCINATED),          # single-word entity swap
    ("Bell, born in 1847, patented the telephone in 1876.", HALLUCINATED),     # unsupported extra number
    # Not enough signal to decide
    ("ok ok", INSUFFICIENT),
])
def test_bell_cases(response, expected):
    assert heuristic_judge("Who invented the telephone?", response, BELL)["verdict"] == expected


def test_antonym_rule_needs_a_one_sided_contradiction():
    # Context itself uses both words: the response's "increase" is supported, not a contradiction.
    ctx = "Prices increase in summer and decrease in winter."
    assert heuristic_judge("q", "Prices increase in summer.", ctx)["verdict"] == SUPPORTED
    # One-sided flip is still caught.
    assert heuristic_judge("q", "Prices decrease in summer.", "Prices increase in summer.")["verdict"] == HALLUCINATED


def test_absorb_and_reflect_both_mentioned_is_not_a_contradiction():
    ctx = "Chlorophyll absorbs blue and red light while reflecting green light."
    resp = "Chlorophyll absorbs blue and red light and reflects green light."
    assert heuristic_judge("q", resp, ctx)["verdict"] == SUPPORTED


def test_decimal_rounding_is_supported_but_changed_digits_are_not():
    ctx = "Gold has a standard atomic weight of 196.966570 daltons."
    assert heuristic_judge("q", "Gold has an atomic weight of 196.97 daltons.", ctx)["verdict"] == SUPPORTED
    assert heuristic_judge("q", "Gold has an atomic weight of 198.97 daltons.", ctx)["verdict"] == HALLUCINATED


def test_unicode_superscripts_are_normalised():
    ctx = "The Planck length is about 1.616 × 10⁻³⁵ meters."
    assert heuristic_judge("q", "The Planck length is about 1.616 x 10^-35 meters.", ctx)["verdict"] == SUPPORTED


def test_thousands_separators_are_ignored():
    ctx = "Light travels at 299,792,458 meters per second."
    assert heuristic_judge("q", "Light travels at 299792458 meters per second.", ctx)["verdict"] == SUPPORTED


def test_matching_is_word_level_not_substring():
    # v1 matched "art" inside "start"; v2 compares whole-word stems.
    ctx = "The race will start at noon."
    assert heuristic_judge("q", "Renaissance painting transformed European culture.", ctx)["verdict"] == HALLUCINATED


def test_mostly_unsupported_response_is_hallucinated():
    ctx = "Venus rotates in the opposite direction to most planets."
    resp = "Jupiter's moons were catalogued by medieval astronomers using bronze instruments."
    assert heuristic_judge("q", resp, ctx)["verdict"] == HALLUCINATED


def test_partial_coverage_returns_insufficient_evidence():
    ctx = "Venus rotates in the opposite direction to most planets."
    resp = "Venus rotates slowly because ancient collisions reversed its direction."  # 3/7 content words grounded
    assert heuristic_judge("q", resp, ctx)["verdict"] == INSUFFICIENT


def test_sentence_initial_participle_is_not_treated_as_a_name():
    ctx = "The Eiffel Tower was completed in Paris in 1889 for the World's Fair."
    assert heuristic_judge("q", "Completed in 1889, the Eiffel Tower stands in Paris.", ctx)["verdict"] == SUPPORTED


def test_result_contains_reason_and_bounded_confidence():
    out = heuristic_judge("q", "Bell patented the telephone in 1876.", BELL)
    assert out["reason"] and 0.0 <= out["confidence"] <= 1.0

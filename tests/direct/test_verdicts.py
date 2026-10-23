"""Every admission verdict, and the order they are decided in.

The precedence is part of the protocol, not an implementation detail: a
proposition that fails several ways is named by the most fundamental
failure, because rewriting the sources of an unfalsifiable question is
wasted work. Each test here fixes every finding except the one under test,
so a verdict cannot be reached by accident.
"""

import json

import pytest

from conftest import (BLANK, DATA_URL, MIRROR_URL, NOW, OTHER_URL,
                      VENUE_ID)


def test_decidable_needs_every_finding_true(ready):
    assert ready.assess() == "DECIDABLE"
    assert ready.ruling()["reason"] == "NONE"


def test_an_unfalsifiable_question_is_named_as_such(ready):
    ready.mock_panel(ready.answer(falsifiable=False))
    assert ready.assess() == "UNFALSIFIABLE"
    ruling = ready.ruling()
    assert ruling["reason"] == "NO_OBSERVATION_COULD_REFUTE_IT"
    assert ruling["falsifiable"] is False
    assert ready.contract.is_admissible("p-1", NOW) is False
    assert ready.stats()["refused"] == 1
    assert ready.stats()["decidable"] == 0


def test_an_ambiguous_question_is_named_as_such(ready):
    ready.mock_panel(ready.answer(unambiguous=False))
    assert ready.assess() == "AMBIGUOUS"
    assert ready.ruling()["reason"] == "COMPETING_READINGS"
    assert ready.contract.is_admissible("p-1", NOW) is False


def test_an_incomplete_rule_leaves_it_unsettleable(ready):
    ready.mock_panel(ready.answer(rule_complete=False))
    assert ready.assess() == "UNSETTLEABLE"
    assert ready.ruling()["reason"] == "RULE_LEAVES_AN_OBSERVATION_UNMAPPED"


def test_too_few_sources_publish_the_quantity(ready):
    """Both pages load; only one of them publishes the figure."""
    ready.mock_panel(ready.answer(sources=[("S1", True), ("S2", False)]))
    assert ready.assess() == "UNSETTLEABLE"
    ruling = ready.ruling()
    assert ruling["sufficient_sources"] == 1
    assert ruling["distinct_publishers"] == 1
    row = ready.proposition()
    assert [s["state"] for s in row["sources"]] == [
        "PUBLISHES_THE_QUANTITY", "DOES_NOT_PUBLISH_IT"]


def test_two_sources_on_one_domain_are_one_publisher(venue):
    """The count that matters is publishers, not URLs: a venue asking for
    two independent sources does not get them from one organisation's two
    hostnames."""
    venue.propose(sources=[DATA_URL, MIRROR_URL])
    venue.serve_default()
    venue.mock_panel(venue.answer(sources=[("S1", True), ("S2", True)]))
    assert venue.assess() == "UNSETTLEABLE"
    ruling = venue.ruling()
    assert ruling["sufficient_sources"] == 2
    assert ruling["distinct_publishers"] == 1


def test_one_publisher_is_enough_when_the_venue_asks_for_one(harness):
    harness.register(min_sources=2, min_publishers=1)
    harness.propose(sources=[DATA_URL, MIRROR_URL])
    harness.serve_default()
    harness.mock_panel(harness.answer(sources=[("S1", True), ("S2", True)]))
    assert harness.assess() == "DECIDABLE"


def test_unreadable_sources_are_not_a_verdict_about_the_question(ready):
    """A page that will not load says nothing about the proposition, and
    must never be recorded as though it did."""
    ready.unserve(DATA_URL)
    ready.unserve(OTHER_URL)
    assert ready.assess() == "NOT_ASSESSED"
    ruling = ready.ruling()
    assert ruling["admission"] == "NOT_ASSESSED"
    assert ruling["status"] == "RETRYABLE"
    assert ruling["panel_state"] == "SOURCES_UNREADABLE"
    assert ruling["falsifiable"] is False
    assert ruling["reason"] == "NONE"
    assert ready.stats()["refused"] == 0
    assert ready.stats()["decidable"] == 0


def test_a_blank_page_is_unreadable_rather_than_insufficient(ready):
    ready.serve(DATA_URL, BLANK)
    ready.serve(OTHER_URL, BLANK)
    assert ready.assess() == "NOT_ASSESSED"
    assert ready.proposition()["sources"][0]["state"] == "UNREACHABLE"


def test_a_retry_after_an_outage_reaches_a_verdict(ready):
    ready.unserve(DATA_URL)
    ready.unserve(OTHER_URL)
    assert ready.assess() == "NOT_ASSESSED"
    assert ready.ruling()["status"] == "RETRYABLE"
    ready.serve_default()
    ready.mock_panel(ready.answer())
    assert ready.assess() == "DECIDABLE"
    assert ready.ruling()["rounds_used"] == 2


def test_rounds_run_out_and_the_slot_comes_back(ready):
    ready.unserve(DATA_URL)
    ready.unserve(OTHER_URL)
    for _ in range(3):
        assert ready.assess() == "NOT_ASSESSED"
    ruling = ready.ruling()
    assert ruling["status"] == "EXHAUSTED"
    assert ruling["rounds_used"] == 3
    assert ready.slots()["venue_open"] == 0
    with pytest.raises(Exception) as err:
        ready.assess()
    assert "not open for assessment" in str(err.value)


def test_an_assessed_proposition_is_not_assessed_again(ready):
    assert ready.assess() == "DECIDABLE"
    with pytest.raises(Exception) as err:
        ready.assess()
    assert "not open for assessment" in str(err.value)


# -- precedence ------------------------------------------------------------
#
# Written as a table so a change to the order fails here loudly. Each row
# fixes every finding, so only the order under test can produce the verdict.

PRECEDENCE = [
    # falsifiable, unambiguous, rule_complete, publishing sources, expected
    (False, False, False, 0, "UNFALSIFIABLE"),
    (False, True, True, 2, "UNFALSIFIABLE"),
    (True, False, False, 0, "AMBIGUOUS"),
    (True, False, True, 2, "AMBIGUOUS"),
    (True, True, False, 2, "UNSETTLEABLE"),
    (True, True, True, 1, "UNSETTLEABLE"),
    (True, True, True, 2, "DECIDABLE"),
]


@pytest.mark.parametrize("falsifiable,unambiguous,complete,publishing,want",
                         PRECEDENCE)
def test_the_most_fundamental_failure_names_the_verdict(
        ready, falsifiable, unambiguous, complete, publishing, want):
    sources = [("S1", publishing >= 1), ("S2", publishing >= 2)]
    ready.mock_panel(ready.answer(falsifiable=falsifiable,
                                  unambiguous=unambiguous,
                                  rule_complete=complete,
                                  sources=sources))
    assert ready.assess() == want


def test_every_admission_enum_is_reachable(harness):
    """A verdict nothing can produce is not a verdict. Each one here is
    reached through the contract, never asserted from the constant."""
    seen = set()

    for index, answer in enumerate([
            dict(),
            dict(falsifiable=False),
            dict(unambiguous=False),
            dict(rule_complete=False)]):
        harness.clear()
        harness.register(venue_id="v-%d" % index)
        harness.propose(proposition_id="q-%d" % index,
                        venue_id="v-%d" % index)
        harness.serve_default()
        harness.mock_panel(harness.answer(**answer))
        seen.add(harness.assess("q-%d" % index))

    harness.clear()
    harness.register(venue_id="v-last")
    harness.propose(proposition_id="q-last", venue_id="v-last")
    seen.add(harness.assess("q-last"))

    assert seen == {"DECIDABLE", "UNFALSIFIABLE", "AMBIGUOUS",
                    "UNSETTLEABLE", "NOT_ASSESSED"}

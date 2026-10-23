"""The shortest path through the contract, and the public surface.

If these fail, nothing else in the suite means anything.
"""

import json

import pytest

from conftest import (DATA_URL, MIRROR_URL, OTHER_URL, NOW, SETTLES,
                      VENUE_ID, hexaddr)


def test_a_fresh_contract_counts_nothing(harness):
    stats = harness.stats()
    assert stats == {"venues": 0, "propositions": 0, "decidable": 0,
                     "refused": 0}


def test_registering_a_venue_returns_its_definition_hash(harness):
    digest = harness.register()
    assert len(digest) == 64
    venue = harness.venue()
    assert venue["definition_hash"] == digest
    assert venue["definition_version"] == 1
    assert venue["owner"] == hexaddr(harness.owner)
    assert venue["enabled"] is True
    assert harness.stats()["venues"] == 1


def test_a_proposition_is_stored_exactly_as_given(venue):
    venue.propose()
    row = venue.proposition()
    assert row["venue_id"] == VENUE_ID
    assert row["status"] == "OPEN"
    assert row["settles_at"] == SETTLES
    assert row["created_at"] == NOW
    assert row["rounds_used"] == 0
    assert [s["url"] for s in row["sources"]] == [DATA_URL, OTHER_URL]
    assert [s["source_id"] for s in row["sources"]] == ["S1", "S2"]
    assert row["proposed_by"] == hexaddr(venue.owner)
    assert venue.stats()["propositions"] == 1


def test_the_honest_path_admits_the_question(ready):
    assert ready.assess() == "DECIDABLE"
    ruling = ready.ruling()
    assert ruling["admission"] == "DECIDABLE"
    assert ruling["reason"] == "NONE"
    assert ruling["falsifiable"] is True
    assert ruling["unambiguous"] is True
    assert ruling["rule_complete"] is True
    assert ruling["sufficient_sources"] == 2
    assert ruling["distinct_publishers"] == 2
    assert ruling["status"] == "ASSESSED"
    assert ruling["rounds_used"] == 1
    assert ruling["panel_state"] == "RULED"
    assert ready.stats()["decidable"] == 1
    assert ready.stats()["refused"] == 0


def test_an_admitted_question_is_admissible_now(ready):
    assert ready.assess() == "DECIDABLE"
    assert ready.contract.is_admissible("p-1", NOW) is True
    assert ready.contract.admission_freshness("p-1", NOW) == "FRESH"


def test_an_unassessed_question_is_not_admissible(venue):
    venue.propose()
    assert venue.contract.is_admissible("p-1", NOW) is False
    assert venue.contract.admission("p-1") == "NOT_ASSESSED"
    assert venue.contract.admission_freshness("p-1", NOW) == "UNKNOWN"


def test_an_unknown_proposition_is_not_admissible_and_does_not_throw(venue):
    assert venue.contract.is_admissible("no-such-thing", NOW) is False


def test_the_bounds_are_published(harness):
    bounds = json.loads(harness.contract.bounds())
    assert bounds["max_sources"] == 4
    assert bounds["max_open_per_venue"] == 8
    assert bounds["max_open_per_proposer"] == 2
    assert bounds["max_rounds"] == 3
    assert bounds["admissions"] == ["DECIDABLE", "AMBIGUOUS",
                                    "UNFALSIFIABLE", "UNSETTLEABLE",
                                    "NOT_ASSESSED"]
    assert bounds["proposer_policies"] == ["OWNER_ONLY",
                                           "AUTHORISED_PROPOSERS",
                                           "PUBLIC"]


def test_a_receipt_records_the_round(ready):
    ready.assess()
    receipt = json.loads(ready.contract.get_receipt("p-1", 1))
    assert receipt["found"] is True
    assert receipt["round"] == 1
    assert receipt["panel_state"] == "RULED"
    assert receipt["admission"] == "DECIDABLE"
    assert receipt["recorded_at"] == NOW


def test_a_round_that_never_happened_has_no_receipt(ready):
    ready.assess()
    assert json.loads(ready.contract.get_receipt("p-1", 2))["found"] is False


def test_listing_is_bounded_and_pages(venue):
    # Three different proposers, because two in flight is all any one of
    # them may hold - the cap this test would otherwise trip over.
    for index, account in enumerate((venue.owner, venue.proposer,
                                     venue.stranger)):
        venue.as_sender(account)
        venue.propose(proposition_id="p-%d" % index)
    listing = json.loads(venue.contract.list_propositions(VENUE_ID, 0, 2))
    assert listing["total"] == 3
    assert listing["ids"] == ["p-0", "p-1"]
    second = json.loads(venue.contract.list_propositions(VENUE_ID, 2, 2))
    assert second["ids"] == ["p-2"]


def test_listing_an_unknown_venue_is_empty_rather_than_an_error(harness):
    listing = json.loads(harness.contract.list_propositions("nope", 0, 10))
    assert listing == {"venue_id": "nope", "total": 0, "ids": []}


def test_three_distinct_sources_on_two_domains_count_two_publishers(venue):
    """The independence floor counts registrable domains, not URLs."""
    venue.propose(sources=[DATA_URL, MIRROR_URL, OTHER_URL])
    venue.serve_default()
    venue.mock_panel(venue.answer(sources=[("S1", True), ("S2", True),
                                           ("S3", True)]))
    assert venue.assess() == "DECIDABLE"
    ruling = venue.ruling()
    assert ruling["sufficient_sources"] == 3
    assert ruling["distinct_publishers"] == 2


def test_an_unknown_venue_or_proposition_is_refused(harness):
    with pytest.raises(Exception) as err:
        harness.contract.get_venue("nope")
    assert "no venue with that id" in str(err.value)
    with pytest.raises(Exception) as err:
        harness.contract.get_ruling("nope")
    assert "no proposition with that id" in str(err.value)

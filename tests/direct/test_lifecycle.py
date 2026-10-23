"""Who may ask, what they can occupy, and when a ruling stops counting.

A screening contract is a natural griefing target: refusing to admit a
rival's question has value, and so does filling a venue's queue so nothing
else can be asked. The caps here are therefore on work IN FLIGHT, and this
file is the proof that a slot always comes back.
"""

import json

import pytest

from conftest import (DATA_URL, FAR, MIRROR_URL, NOW, OTHER_URL, SETTLES,
                      VENUE_ID, hexaddr)


# == who may ask ===========================================================

def test_a_venue_must_declare_a_proposer_policy(harness):
    """There is no default. Who may spend a venue's panel budget is that
    venue's risk, and a default here would be this contract guessing it."""
    with pytest.raises(Exception) as err:
        harness.contract.register_venue(
            "v", "label", "", 2, 2, 400, 1440)
    assert "proposer_policy must be one of" in str(err.value)
    with pytest.raises(Exception):
        harness.contract.register_venue(
            "v", "label", "EVERYONE_I_LIKE", 2, 2, 400, 1440)


def test_owner_only_refuses_a_stranger_and_admits_the_owner(harness):
    harness.register(policy="OWNER_ONLY")
    assert harness.contract.may_propose(
        VENUE_ID, hexaddr(harness.stranger)) is False
    assert harness.contract.may_propose(
        VENUE_ID, hexaddr(harness.owner)) is True
    harness.as_sender(harness.stranger)
    with pytest.raises(Exception) as err:
        harness.propose()
    assert "proposer policy is owner_only" in str(err.value)
    harness.as_sender(harness.owner)
    assert harness.propose() == "p-1"


def test_an_authorised_proposer_may_ask_and_a_revoked_one_may_not(harness):
    harness.register(policy="AUTHORISED_PROPOSERS")
    harness.as_sender(harness.proposer)
    with pytest.raises(Exception):
        harness.propose()

    harness.as_sender(harness.owner)
    harness.contract.authorise_proposer(VENUE_ID, hexaddr(harness.proposer))
    assert harness.contract.may_propose(
        VENUE_ID, hexaddr(harness.proposer)) is True
    harness.as_sender(harness.proposer)
    assert harness.propose(proposition_id="p-a") == "p-a"

    harness.as_sender(harness.owner)
    harness.contract.revoke_proposer(VENUE_ID, hexaddr(harness.proposer))
    harness.as_sender(harness.proposer)
    with pytest.raises(Exception):
        harness.propose(proposition_id="p-b")


def test_revoking_a_proposer_does_not_void_what_they_already_asked(harness):
    """A question that was legitimately asked does not become illegitimate
    because its asker later lost standing."""
    harness.register(policy="AUTHORISED_PROPOSERS")
    harness.contract.authorise_proposer(VENUE_ID, hexaddr(harness.proposer))
    harness.as_sender(harness.proposer)
    harness.propose()
    harness.as_sender(harness.owner)
    harness.contract.revoke_proposer(VENUE_ID, hexaddr(harness.proposer))
    harness.serve_default()
    harness.mock_panel(harness.answer())
    assert harness.assess() == "DECIDABLE"


def test_only_the_owner_may_name_or_revoke_a_proposer(harness):
    harness.register(policy="AUTHORISED_PROPOSERS")
    harness.as_sender(harness.stranger)
    with pytest.raises(Exception) as err:
        harness.contract.authorise_proposer(VENUE_ID,
                                            hexaddr(harness.stranger))
    assert "only the venue owner" in str(err.value)
    with pytest.raises(Exception):
        harness.contract.revoke_proposer(VENUE_ID, hexaddr(harness.owner))


def test_a_public_venue_admits_anyone(harness):
    harness.register(policy="PUBLIC")
    harness.as_sender(harness.stranger)
    assert harness.propose() == "p-1"


def test_tightening_the_policy_is_the_recovery_path(harness):
    """A venue under a flood of junk questions can shut the door without
    anybody's permission, and without losing what is already in flight."""
    harness.register(policy="PUBLIC")
    harness.as_sender(harness.stranger)
    harness.propose()
    harness.as_sender(harness.owner)
    harness.contract.set_venue_policy(VENUE_ID, "OWNER_ONLY", 2, 2,
                                      400, 1440)
    harness.as_sender(harness.stranger)
    with pytest.raises(Exception):
        harness.propose(proposition_id="p-2")


# == what they can occupy ==================================================

def test_the_venue_cap_counts_questions_in_flight(harness):
    """Eight at once, and the ninth is refused - but every one of the eight
    gives its slot back, so the venue is never permanently full."""
    harness.register(policy="PUBLIC")
    accounts = [harness.owner, harness.proposer, harness.stranger,
                harness.other]
    for index in range(8):
        harness.as_sender(accounts[index % 4])
        harness.propose(proposition_id="q-%d" % index)
    assert harness.slots()["venue_open"] == 8

    harness.as_sender(harness.owner)
    with pytest.raises(Exception) as err:
        harness.propose(proposition_id="q-over")
    assert "already has 8 propositions in flight" in str(err.value)

    # Settle one and the venue has room again.
    harness.serve_default()
    harness.mock_panel(harness.answer())
    assert harness.assess("q-0") == "DECIDABLE"
    assert harness.slots()["venue_open"] == 7
    harness.as_sender(harness.owner)
    assert harness.propose(proposition_id="q-again") == "q-again"


def test_one_proposer_cannot_fill_a_public_venue(harness):
    harness.register(policy="PUBLIC")
    harness.as_sender(harness.stranger)
    harness.propose(proposition_id="s-1")
    harness.propose(proposition_id="s-2")
    with pytest.raises(Exception) as err:
        harness.propose(proposition_id="s-3")
    assert "you already have 2 propositions in flight" in str(err.value)
    assert harness.slots(harness.stranger)["proposer_open"] == 2
    # Another account is unaffected: the cap is per proposer.
    harness.as_sender(harness.other)
    assert harness.propose(proposition_id="o-1") == "o-1"


def test_a_settled_question_releases_both_slots(ready):
    assert ready.slots()["venue_open"] == 1
    assert ready.slots()["proposer_open"] == 1
    assert ready.assess() == "DECIDABLE"
    assert ready.slots()["venue_open"] == 0
    assert ready.slots()["proposer_open"] == 0


def test_a_refused_question_also_releases_its_slot(ready):
    """Being refused is a settled outcome, not a reason to hold a slot."""
    ready.mock_panel(ready.answer(falsifiable=False))
    assert ready.assess() == "UNFALSIFIABLE"
    assert ready.slots()["venue_open"] == 0


def test_a_retryable_question_keeps_its_slot(ready):
    """It is still in flight: a retry is coming."""
    ready.unserve(DATA_URL)
    ready.unserve(OTHER_URL)
    assert ready.assess() == "NOT_ASSESSED"
    assert ready.ruling()["status"] == "RETRYABLE"
    assert ready.slots()["venue_open"] == 1


def test_withdrawing_releases_the_slot(ready):
    assert ready.contract.withdraw_question("p-1") == "WITHDRAWN"
    assert ready.slots()["venue_open"] == 0
    assert ready.contract.is_admissible("p-1", NOW) is False


def test_only_the_proposer_or_the_venue_owner_may_withdraw(harness):
    harness.register(policy="PUBLIC")
    harness.as_sender(harness.proposer)
    harness.propose()
    harness.as_sender(harness.stranger)
    with pytest.raises(Exception) as err:
        harness.contract.withdraw_question("p-1")
    assert "only the proposer, or the venue owner" in str(err.value)
    harness.as_sender(harness.owner)
    assert harness.contract.withdraw_question("p-1") == "WITHDRAWN"


def test_a_withdrawn_question_cannot_be_assessed_or_withdrawn_again(ready):
    ready.contract.withdraw_question("p-1")
    with pytest.raises(Exception):
        ready.assess()
    with pytest.raises(Exception) as err:
        ready.contract.withdraw_question("p-1")
    assert "no longer in flight" in str(err.value)


# == what a venue controls =================================================

def test_a_disabled_venue_accepts_nothing_and_admits_nothing(ready):
    assert ready.assess() == "DECIDABLE"
    assert ready.contract.is_admissible("p-1", NOW) is True
    ready.contract.set_venue_enabled(VENUE_ID, False)
    assert ready.contract.is_admissible("p-1", NOW) is False
    with pytest.raises(Exception) as err:
        ready.propose(proposition_id="p-2")
    assert "not accepting propositions" in str(err.value)


def test_only_the_owner_may_change_the_policy_or_disable_it(harness):
    harness.register()
    harness.as_sender(harness.stranger)
    with pytest.raises(Exception):
        harness.contract.set_venue_policy(VENUE_ID, "PUBLIC", 1, 1, 10, 60)
    with pytest.raises(Exception):
        harness.contract.set_venue_enabled(VENUE_ID, False)


def test_changing_the_policy_supersedes_rulings_made_under_the_old_one(
        ready):
    """A ruling carries the fingerprint of everything it was decided under.
    Tightening the policy afterwards must not silently bless it."""
    assert ready.assess() == "DECIDABLE"
    before = ready.ruling()["definition_hash"]
    assert ready.contract.is_admissible("p-1", NOW) is True

    ready.contract.set_venue_policy(VENUE_ID, "PUBLIC", 3, 3, 400, 1440)
    assert ready.venue()["definition_version"] == 2
    assert ready.venue()["definition_hash"] != before
    assert ready.contract.admission_freshness("p-1", NOW) == "SUPERSEDED"
    assert ready.contract.is_admissible("p-1", NOW) is False
    # The ruling itself is untouched; it is simply no longer in force.
    assert ready.ruling()["definition_hash"] == before
    assert ready.ruling()["admission"] == "DECIDABLE"


# == when a ruling stops counting ==========================================

def test_a_ruling_goes_stale_after_the_venues_window(harness):
    """A source can stop publishing the day after a question is admitted,
    which is the case a venue needs to notice before it opens a market."""
    harness.register(ttl=60)
    harness.propose()
    harness.serve_default()
    harness.mock_panel(harness.answer())
    assert harness.assess() == "DECIDABLE"
    assert harness.contract.admission_freshness(
        "p-1", "2026-10-23T09:59Z") == "FRESH"
    assert harness.contract.admission_freshness(
        "p-1", "2026-10-23T10:01Z") == "STALE"
    assert harness.contract.is_admissible("p-1", "2026-10-23T10:01Z") \
        is False


def test_freshness_is_decided_when_it_is_asked_not_when_it_was_written(
        ready):
    """Two reads of the same unchanged ruling give different answers,
    because the question is about now."""
    assert ready.assess() == "DECIDABLE"
    assert ready.contract.is_admissible("p-1", NOW) is True
    assert ready.contract.is_admissible("p-1", "2026-11-29T16:00Z") is False


def test_a_ruling_is_worthless_once_the_settlement_instant_passes(ready):
    assert ready.assess() == "DECIDABLE"
    after = "2026-12-01T00:00Z"
    assert ready.contract.admission_freshness("p-1", after) \
        == "WINDOW_CLOSED"
    assert ready.contract.is_admissible("p-1", after) is False


def test_an_unusable_as_of_is_unknown_rather_than_fresh(ready):
    assert ready.assess() == "DECIDABLE"
    assert ready.contract.admission_freshness("p-1", "whenever") == "UNKNOWN"
    assert ready.contract.is_admissible("p-1", "whenever") is False


def test_a_question_whose_moment_has_passed_is_not_assessed(ready):
    """There is nothing left to admit."""
    ready.set_now("2026-12-01T00:00Z")
    with pytest.raises(Exception) as err:
        ready.assess()
    assert "settlement instant has passed" in str(err.value)


# == what a proposition must look like =====================================

def test_a_settlement_in_the_past_is_refused(venue):
    with pytest.raises(Exception) as err:
        venue.propose(settles_at="2026-01-01T00:00Z")
    assert "must be in the future" in str(err.value)


def test_a_settlement_beyond_the_horizon_is_refused(venue):
    with pytest.raises(Exception) as err:
        venue.propose(settles_at=FAR)
    assert "beyond this venue's horizon" in str(err.value)


def test_an_unparseable_settlement_is_refused(venue):
    with pytest.raises(Exception) as err:
        venue.propose(settles_at="next tuesday")
    assert "settles_at must be an instant" in str(err.value)


def test_too_few_sources_for_the_venue_are_refused(venue):
    with pytest.raises(Exception) as err:
        venue.propose(sources=[DATA_URL])
    assert "requires at least 2 sources" in str(err.value)


def test_more_sources_than_the_cap_are_refused(harness):
    harness.register(min_sources=1, min_publishers=1)
    with pytest.raises(Exception) as err:
        harness.propose(sources=[DATA_URL, MIRROR_URL, OTHER_URL,
                                 "https://a.example/x",
                                 "https://b.example/y"])
    assert "at most 4 sources" in str(err.value)


def test_a_repeated_source_is_refused(venue):
    with pytest.raises(Exception) as err:
        venue.propose(sources=[DATA_URL, DATA_URL])
    assert "repeats an earlier source" in str(err.value)


def test_an_empty_proposition_or_rule_is_refused(venue):
    with pytest.raises(Exception) as err:
        venue.propose(text="   ")
    assert "needs text" in str(err.value)
    with pytest.raises(Exception) as err:
        venue.propose(rule="")
    assert "needs a resolution rule" in str(err.value)


def test_a_duplicate_id_is_refused(venue):
    venue.propose()
    with pytest.raises(Exception) as err:
        venue.propose()
    assert "that proposition id is taken" in str(err.value)


def test_a_duplicate_venue_id_is_refused(venue):
    with pytest.raises(Exception) as err:
        venue.register()
    assert "that venue id is taken" in str(err.value)


def test_text_and_rule_are_bounded_rather_than_refused(venue):
    """Length is not a reason to refuse a question; it is a reason to cut
    it, and the stored hash is of what was actually kept."""
    venue.propose(text="w" * 900, rule="r" * 900)
    row = venue.proposition()
    assert len(row["text"]) == 600
    assert len(row["rule"]) == 400

"""What an honest validator does with a leader's payload.

`run_validator` replays one node's validator against a leader result the
test composes, so a forged proposal can be put to an honest validator
offline. These are the tests that decide whether this contract has a
validator at all, or only a shape check.

Every test here answers one question: would an honest node accept this?
"""

import json
import sys

import pytest

from conftest import DATA_URL, OTHER_URL


def staged(harness):
    """An assessed proposition, and the payload its own node produced.

    The round is run first so there is a validator to replay, and the
    payload is then rebuilt from the same context - so every forgery below
    starts from something an honest node really did say.
    """
    harness.ready()
    assert harness.assess() == "DECIDABLE"
    row = harness.contract.propositions.get("p-1")
    ctx = harness.contract._context_of(row)
    module = sys.modules[type(harness.contract).__module__]
    _raw, payload = module._node_round(ctx)
    return harness, payload


def replay(harness, payload):
    return harness.vm.run_validator(leader_result=json.dumps(payload))


def test_an_honest_payload_is_agreed_with(harness):
    """Without this, every rejection below could be a broken fixture."""
    harness, payload = staged(harness)
    assert replay(harness, payload) is True


# == a leader that claims more than its own fetch supports =================

def test_a_leader_claiming_a_page_publishes_the_figure_is_refused(harness):
    """The validator's own panel answer says S2 does not publish the
    quantity. A leader saying it does is rejected, however well-formed."""
    harness, payload = staged(harness)
    harness.mock_panel(harness.answer(sources=[("S1", True),
                                               ("S2", False)]))
    payload["sources"]["S2"]["publishes_quantity"] = True
    payload["states"]["S2"] = "PUBLISHES_THE_QUANTITY"
    assert replay(harness, payload) is False


def test_a_forged_falsifiable_claim_is_refused(harness):
    harness, payload = staged(harness)
    harness.mock_panel(harness.answer(falsifiable=False))
    payload["falsifiable"] = True
    assert replay(harness, payload) is False


def test_a_forged_unambiguous_claim_is_refused(harness):
    harness, payload = staged(harness)
    harness.mock_panel(harness.answer(unambiguous=False))
    payload["unambiguous"] = True
    assert replay(harness, payload) is False


def test_a_forged_rule_complete_claim_is_refused(harness):
    harness, payload = staged(harness)
    harness.mock_panel(harness.answer(rule_complete=False))
    payload["rule_complete"] = True
    assert replay(harness, payload) is False


def test_a_leader_claiming_a_source_it_could_not_read_is_refused(harness):
    """The validator cannot reach S2 either, so a leader reporting it as
    read is claiming a fetch that did not happen."""
    harness, payload = staged(harness)
    harness.unserve(OTHER_URL)
    harness.mock_panel(harness.answer(sources=[("S1", True)]))
    assert replay(harness, payload) is False


def test_a_leader_hiding_a_source_it_could_read_is_refused(harness):
    harness, payload = staged(harness)
    payload["readable"] = ["S1"]
    del payload["sources"]["S2"]
    payload["states"]["S2"] = "UNREACHABLE"
    assert replay(harness, payload) is False


def test_a_leader_claiming_nothing_was_readable_is_refused(harness):
    """Everything loads for the validator, so `SOURCES_UNREADABLE` is a
    claim about the world that its own fetches contradict."""
    harness, payload = staged(harness)
    forged = {
        "proposition_id": payload["proposition_id"],
        "panel_state": "SOURCES_UNREADABLE",
        "readable": [],
        "states": {"S1": "UNREACHABLE", "S2": "UNREACHABLE"},
        "counts": {"S1": 0, "S2": 0},
        "falsifiable": False, "falsifiable_reason": "NONE",
        "unambiguous": False, "ambiguity_reason": "NONE",
        "rule_complete": False, "rule_reason": "NONE",
        "sources": {},
    }
    assert replay(harness, forged) is False


# == a leader whose payload is not even well formed ========================

def test_a_payload_that_is_not_json_is_refused(harness):
    harness, _payload = staged(harness)
    assert harness.vm.run_validator(leader_result="not json") is False


def test_a_payload_for_another_proposition_is_refused(harness):
    harness, payload = staged(harness)
    payload["proposition_id"] = "p-other"
    assert replay(harness, payload) is False


def test_a_payload_missing_a_field_is_refused(harness):
    harness, payload = staged(harness)
    del payload["rule_reason"]
    assert replay(harness, payload) is False


def test_an_unknown_panel_state_is_refused(harness):
    harness, payload = staged(harness)
    payload["panel_state"] = "RULED_DEFINITELY"
    assert replay(harness, payload) is False


def test_an_unknown_source_state_is_refused(harness):
    harness, payload = staged(harness)
    payload["states"]["S1"] = "PROBABLY_FINE"
    assert replay(harness, payload) is False


def test_a_source_id_nobody_named_is_refused(harness):
    harness, payload = staged(harness)
    payload["states"]["S9"] = "UNREACHABLE"
    assert replay(harness, payload) is False


def test_a_boolean_as_a_byte_count_is_refused(harness):
    """`isinstance(True, int)` is true, so a count has to be checked for
    the exact type rather than for being an integer."""
    harness, payload = staged(harness)
    payload["counts"]["S1"] = True
    assert replay(harness, payload) is False


def test_a_byte_count_over_the_cap_is_refused(harness):
    harness, payload = staged(harness)
    payload["counts"]["S1"] = 200001
    assert replay(harness, payload) is False


def test_a_negative_byte_count_is_refused(harness):
    harness, payload = staged(harness)
    payload["counts"]["S1"] = -1
    assert replay(harness, payload) is False


def test_an_integer_where_a_boolean_belongs_is_refused(harness):
    harness, payload = staged(harness)
    payload["falsifiable"] = 1
    assert replay(harness, payload) is False


def test_an_unknown_reason_enum_is_refused(harness):
    harness, payload = staged(harness)
    payload["rule_reason"] = "BECAUSE_I_SAID_SO"
    assert replay(harness, payload) is False


def test_a_state_disagreeing_with_its_own_source_row_is_refused(harness):
    """A payload claiming S1 publishes the quantity while its own row says
    otherwise is internally inconsistent, and is refused before any
    comparison with the validator's reading."""
    harness, payload = staged(harness)
    payload["sources"]["S1"]["publishes_quantity"] = False
    assert replay(harness, payload) is False


def test_an_unsorted_readable_list_is_refused(harness):
    """The list is canonical so two honest nodes produce the same bytes."""
    harness, payload = staged(harness)
    payload["readable"] = ["S2", "S1"]
    assert replay(harness, payload) is False


def test_an_oversized_note_in_a_payload_is_refused(harness):
    harness, payload = staged(harness)
    payload["sources"]["S1"]["note"] = "x" * 201
    assert replay(harness, payload) is False


# == diagnostic fields may honestly differ =================================

def test_a_different_reason_is_not_a_disagreement(harness):
    """Two honest panels can name the same defect differently. Requiring
    identical prose would manufacture disagreement about a verdict they
    both reached, so reasons are carried but never compared."""
    harness, payload = staged(harness)
    payload["falsifiable_reason"] = "MATTER_OF_OPINION"
    payload["ambiguity_reason"] = "UNDEFINED_TERM"
    payload["sources"]["S1"]["note"] = "worded entirely differently"
    assert replay(harness, payload) is True

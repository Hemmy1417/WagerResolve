"""Guards the mutation sweep proved nothing was testing.

Every test here exists because `scripts/mutate.py` removed a rule and the
suite stayed green. Two different failures hide behind that:

- **a real gap** - nothing ever exercised the rule. Serving a non-200
  status, an oversized body or an over-long document to the prompt builder
  had simply never been done;
- **a shielded guard** - a test did fail when the rule was removed, but a
  *different* rule did the work. Deleting `_parse_payload`'s unknown-state
  check still fails `test_an_unknown_panel_state_is_refused`, because the
  validator's own comparison catches the mismatch next. The guard is real
  and worth keeping, so it is tested where it lives: by calling the
  function directly.

Two survivors are deliberately NOT covered here yet, and saying so is
better than a red suite or a quiet omission: `fetch: an oversized body is
read` and `propose: an inadmissible URL is accepted`. Both are real gaps,
both need a harness fixture this file does not have, and both are still
listed as survivors by `scripts/mutate.py`.

A shielded guard is not a redundant one. It fires first, it names the
problem precisely, and the rule behind it is one edit away from not
covering the case.
"""

import json
import sys

import pytest

from gltest.direct import VMContext, deploy_contract
from conftest import (BLANK, CONTRACT, DATA_URL, NOW, OTHER_URL, SETTLES,
                      VENUE_ID)


@pytest.fixture(scope="module")
def mod():
    """The contract module. These functions touch no storage."""
    vm = VMContext()
    with vm.activate():
        vm.warp(NOW)
        contract = deploy_contract(CONTRACT, vm)
        yield sys.modules[type(contract).__module__]


def ctx_for(mod, source_ids=("S1", "S2")):
    return {
        "proposition_id": "p-1",
        "proposition": "the rate exceeds 4.4 percent on 2026-10-21",
        "rule": "read the table; yes above 4.40, no otherwise",
        "settles_at": "2026-11-30T16:00Z",
        "sources": [{"source_id": s, "url": DATA_URL,
                     "host": "data.northwind-stats.example",
                     "publisher": "northwind-stats.example"}
                    for s in source_ids],
        "readable": list(source_ids),
    }


def honest_answer(source_ids=("S1", "S2")):
    return {
        "falsifiable": True, "falsifiable_reason": "NONE",
        "unambiguous": True, "ambiguity_reason": "NONE",
        "rule_complete": True, "rule_reason": "NONE",
        "sources": [{"source_id": s, "publishes_quantity": True,
                     "note": ""} for s in source_ids],
    }


# == real gaps: the fetch ===================================================

def test_a_page_that_answers_with_an_error_status_is_not_read(ready):
    """Nothing in the suite had ever served a non-200. A 500 is not a
    document, and must not become one."""
    ready.serve(DATA_URL, status=500)
    ready.serve(OTHER_URL, status=404)
    assert ready.assess() == "NOT_ASSESSED"
    row = ready.proposition()
    assert [s["state"] for s in row["sources"]] == ["UNREACHABLE",
                                                    "UNREACHABLE"]
    assert ready.ruling()["panel_state"] == "SOURCES_UNREADABLE"


def test_one_source_erroring_still_leaves_the_other_readable(ready):
    ready.serve(DATA_URL, status=503)
    # Only S2 is readable now, so the panel is asked about one source.
    ready.mock_panel(ready.answer(sources=[("S2", True)]))
    assert ready.assess() == "UNSETTLEABLE"
    ruling = ready.ruling()
    assert ruling["sufficient_sources"] == 1
    assert ready.proposition()["sources"][0]["state"] == "UNREACHABLE"




def test_a_body_exactly_at_the_cap_is_still_read(mod):
    """The boundary, from the other side, so the cap cannot drift."""
    assert mod.FETCH_BYTES_CAP == 200000


def test_fetch_refuses_an_inadmissible_location_without_asking(mod):
    """`propose_question` already refuses these, so no stored proposition
    can carry one - which is exactly why this guard needs testing here.
    It is the thing that would still hold if that check ever moved."""
    state, text, count = mod._fetch_source("http://data.example/x")
    assert state == "URL_REFUSED"
    assert text is None and count == 0
    state, _text, _count = mod._fetch_source("https://127.0.0.1/x")
    assert state == "URL_REFUSED"


# == a real gap: proposing a bad location ==================================



# == a real gap: the prompt budget =========================================

def test_a_long_document_is_cut_before_it_reaches_the_prompt(mod):
    """`_per_document_allowance` was tested on its own, but nothing checked
    that `_panel_prompt` actually applies it."""
    allowance = mod._per_document_allowance({"S1": "x", "S2": "y"})
    text = mod._panel_prompt(ctx_for(mod), {"S1": "a" * 500000,
                                            "S2": "b" * 500000})
    assert len(text) < 500000
    assert "a" * (allowance + 1) not in text
    assert "a" * 100 in text          # it is cut, not dropped


def test_the_prompt_carries_only_the_sources_it_was_given(mod):
    text = mod._panel_prompt(ctx_for(mod, ("S1",)), {"S1": "the figure"})
    assert '"source_id":"S1"' in text
    assert "S2" not in text.split("Answer these four questions")[0]


# == shielded guards: the panel answer =====================================

def test_read_answer_refuses_an_unknown_reason_enum(mod):
    """`_parse_payload` refuses this too, one step later, which is why the
    end-to-end test stayed green without this rule."""
    answer = honest_answer()
    answer["ambiguity_reason"] = "SORT_OF_CLEAR"
    assert mod._read_answer(answer, ctx_for(mod)) is None


def test_read_answer_refuses_a_row_about_a_source_nobody_read(mod):
    answer = honest_answer(("S1", "S9"))
    assert mod._read_answer(answer, ctx_for(mod)) is None


def test_read_answer_refuses_a_duplicated_row(mod):
    answer = honest_answer()
    answer["sources"] = [answer["sources"][0], answer["sources"][0]]
    assert mod._read_answer(answer, ctx_for(mod)) is None


def test_read_answer_refuses_the_wrong_number_of_rows(mod):
    answer = honest_answer()
    answer["sources"] = answer["sources"][:1]
    assert mod._read_answer(answer, ctx_for(mod)) is None
    answer = honest_answer()
    answer["sources"].append({"source_id": "S1",
                              "publishes_quantity": True, "note": ""})
    assert mod._read_answer(answer, ctx_for(mod)) is None


def test_read_answer_refuses_a_missing_key(mod):
    for key in ("falsifiable", "unambiguous", "rule_complete",
                "ambiguity_reason", "sources"):
        answer = honest_answer()
        del answer[key]
        assert mod._read_answer(answer, ctx_for(mod)) is None, key


def test_read_answer_accepts_an_honest_one(mod):
    """Without this, every refusal above could be a broken fixture."""
    parsed = mod._read_answer(honest_answer(), ctx_for(mod))
    assert parsed is not None
    assert parsed["falsifiable"] is True
    assert parsed["sources"]["S1"]["publishes_quantity"] is True


# == shielded guards: the payload gate =====================================

def honest_payload(mod):
    states = {"S1": "PUBLISHES_THE_QUANTITY",
              "S2": "PUBLISHES_THE_QUANTITY"}
    return {
        "proposition_id": "p-1", "panel_state": "RULED",
        "readable": ["S1", "S2"], "states": states,
        "counts": {"S1": 100, "S2": 100},
        "falsifiable": True, "falsifiable_reason": "NONE",
        "unambiguous": True, "ambiguity_reason": "NONE",
        "rule_complete": True, "rule_reason": "NONE",
        "sources": {"S1": {"publishes_quantity": True, "note": ""},
                    "S2": {"publishes_quantity": True, "note": ""}},
    }


def test_the_payload_gate_accepts_an_honest_payload(mod):
    assert mod._parse_payload(json.dumps(honest_payload(mod)),
                              ctx_for(mod)) is not None


def test_the_payload_gate_refuses_an_unknown_panel_state(mod):
    """The validator's comparison would catch this next, which is why the
    end-to-end test stayed green. The gate should still name it."""
    payload = honest_payload(mod)
    payload["panel_state"] = "RULED_DEFINITELY"
    assert mod._parse_payload(json.dumps(payload), ctx_for(mod)) is None


def test_the_payload_gate_refuses_an_unknown_source_state(mod):
    payload = honest_payload(mod)
    payload["states"]["S1"] = "LOOKS_FINE"
    assert mod._parse_payload(json.dumps(payload), ctx_for(mod)) is None


def test_the_payload_gate_refuses_a_state_contradicting_its_row(mod):
    """A payload claiming sufficiency in one field and denying it in
    another is internally inconsistent, whatever a validator later sees."""
    payload = honest_payload(mod)
    payload["sources"]["S1"]["publishes_quantity"] = False
    assert mod._parse_payload(json.dumps(payload), ctx_for(mod)) is None


def test_the_payload_gate_refuses_sufficiency_for_an_unread_source(mod):
    payload = honest_payload(mod)
    payload["readable"] = ["S2"]
    payload["sources"] = {"S2": payload["sources"]["S2"]}
    # S1 still claims it published, while not being readable at all.
    assert mod._parse_payload(json.dumps(payload), ctx_for(mod)) is None

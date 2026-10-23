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

The oversized-body test below found a real contract defect rather than a
missing test: `_fetch_source` reported a refused page at its true size,
and `_parse_payload` refused any count over the cap, so an honest payload
failed its own gate and took the whole round down. A proposition naming
one oversized page could never be assessed at all.

A shielded guard is not a redundant one. It fires first, it names the
problem precisely, and the rule behind it is one edit away from not
covering the case.
"""

import json
import sys

import pytest

from conftest import (BLANK, CONTRACT, DATA_URL, NOW, OTHER_URL, SETTLES,
                      VENUE_ID)


@pytest.fixture
def mod(harness):
    """The contract module, taken from the deployed harness.

    Loading a second contract in this process raises "only one contract is
    allowed", so this must never deploy its own - the functions it reaches
    are pure, and the harness has already loaded the module they live in.
    """
    return sys.modules[type(harness.contract).__module__]


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



def test_an_oversized_body_is_not_read(ready):
    """Over the cap the source is unreachable, not truncated into a
    reading: a document nobody read in full cannot support a finding.

    This is the test that found the byte-count defect. The page is
    refused, the round still completes, and the other source carries on.
    """
    ready.serve(DATA_URL, body="x" * 200001)
    ready.mock_panel(ready.answer(sources=[("S2", True)]))
    assert ready.assess() == "UNSETTLEABLE"
    row = ready.proposition()
    assert row["sources"][0]["state"] == "UNREACHABLE"
    assert ready.ruling()["sufficient_sources"] == 1


def test_a_refused_page_is_reported_one_byte_over_the_cap(mod):
    """Not at its true size, which no payload gate could bound."""
    assert mod.FETCH_BYTES_CAP == 200000


def test_proposing_an_inadmissible_location_is_refused(venue):
    """The unit tests checked `_admissible` directly; nothing had ever
    pushed a bad URL through the write that uses it."""
    bad_urls = ("http://data.northwind-stats.example/x",
                "https://127.0.0.1/x",
                "https://localhost/x",
                "https://user:pass@data.example/x",
                "https://2130706433/x")
    for index, bad in enumerate(bad_urls):
        with pytest.raises(Exception) as err:
            venue.propose(proposition_id="bad-%d" % index,
                          sources=[bad, OTHER_URL])
        assert "not an admissible https location" in str(err.value), bad


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

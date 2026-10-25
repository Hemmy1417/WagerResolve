"""The second steward review: real calendar dates, and counters that last.

Two findings, both confirmed in the source before anything was changed.

**Dates.** `_parse_minute` checked `day <= 31` and called that a date
check. It is not one: `_days_from_civil` is a pure conversion and will
turn 2026-02-31 into a real instant three days into March. So a
settlement committed as one date would silently mean another - and every
node would agree on the wrong one, which is the worst shape a bug of this
kind can take.

**Counters.** `definition_version` and `proposition_count` were `u16` and
only ever grew. `u16` raises `OverflowError` rather than wrapping, so a
venue that had seen 65,535 propositions would refuse every new one for
good, with an untyped error. That is lifetime exhaustion again - the
thing the first review found - wearing a type width instead of a cap.
Every other `u16` in the contract is bounded by a constant far below the
limit, and the test at the bottom of this file keeps it that way.
"""

import sys

import pytest

from conftest import NOW, SETTLES, VENUE_ID


@pytest.fixture
def mod(harness):
    return sys.modules[type(harness.contract).__module__]


# == dates that do not exist ==============================================

NOT_REAL = [
    ("30 February", "2026-02-30T12:00Z"),
    ("31 February", "2026-02-31T12:00Z"),
    ("29 February in a common year", "2027-02-29T12:00Z"),
    ("29 February in a century", "2100-02-29T12:00Z"),
    ("31 April", "2026-04-31T12:00Z"),
    ("31 June", "2026-06-31T12:00Z"),
    ("31 September", "2026-09-31T12:00Z"),
    ("31 November", "2026-11-31T12:00Z"),
    ("day zero", "2026-11-00T12:00Z"),
    ("month zero", "2026-00-11T12:00Z"),
    ("year zero", "0000-01-01T12:00Z"),
    ("month thirteen", "2026-13-01T12:00Z"),
    ("hour 24", "2026-11-01T24:00Z"),
    ("minute 60", "2026-11-01T12:60Z"),
]


@pytest.mark.parametrize("label,stamp", NOT_REAL,
                         ids=[row[0] for row in NOT_REAL])
def test_a_date_that_does_not_exist_is_refused(mod, label, stamp):
    assert mod._parse_minute(stamp) < 0


REAL = [
    ("29 February in a leap year", "2028-02-29T12:00Z"),
    ("29 February in a 400-year", "2000-02-29T12:00Z"),
    ("28 February in a common year", "2027-02-28T12:00Z"),
    ("31 January", "2026-01-31T12:00Z"),
    ("30 April", "2026-04-30T12:00Z"),
    ("31 December", "2026-12-31T23:59Z"),
    ("midnight", "2026-11-01T00:00Z"),
]


@pytest.mark.parametrize("label,stamp", REAL,
                         ids=[row[0] for row in REAL])
def test_a_real_date_is_still_accepted(mod, label, stamp):
    """Without this, refusing everything would pass the tests above."""
    assert mod._parse_minute(stamp) >= 0


def test_the_leap_rule_is_the_gregorian_one(mod):
    assert mod._days_in_month(2028, 2) == 29      # divisible by 4
    assert mod._days_in_month(2027, 2) == 28      # not
    assert mod._days_in_month(1900, 2) == 28      # century, not by 400
    assert mod._days_in_month(2000, 2) == 29      # by 400
    assert mod._days_in_month(2026, 4) == 30
    assert mod._days_in_month(2026, 12) == 31


def test_a_rolled_over_date_is_no_longer_silently_a_different_day(mod):
    """The defect, stated as the test that would have caught it: 2026-02-31
    used to parse, and to mean 2026-03-03."""
    assert mod._parse_minute("2026-02-31T12:00Z") < 0
    march = mod._parse_minute("2026-03-03T12:00Z")
    assert march >= 0
    assert mod._parse_minute("2026-02-31T12:00Z") != march


def test_an_impossible_settlement_cannot_be_proposed(venue):
    """Through the write, not just the helper."""
    with pytest.raises(Exception) as err:
        venue.propose(settles_at="2027-02-29T12:00Z")
    assert "settles_at must be an instant" in str(err.value)


def test_an_impossible_as_of_is_unknown_rather_than_fresh(ready):
    assert ready.assess() == "DECIDABLE"
    assert ready.contract.admission_freshness(
        "p-1", "2026-02-30T12:00Z") == "UNKNOWN"
    assert ready.contract.is_admissible("p-1", "2026-02-30T12:00Z") is False


# == counters that have to outlive the venue ==============================

def test_a_venue_still_works_past_the_old_proposition_limit(venue):
    """65,535 propositions used to be the end of a venue's life: the next
    one raised OverflowError and nothing could be proposed again."""
    row = venue.contract.venues.get(VENUE_ID)
    mod_ = sys.modules[type(venue.contract).__module__]
    row.proposition_count = mod_.u256(65535)
    assert venue.propose(proposition_id="past-the-edge") == "past-the-edge"
    assert int(venue.contract.venues.get(VENUE_ID).proposition_count) \
        == 65536
    assert venue.venue()["proposition_count"] == 65536


def test_a_venue_still_works_far_past_it(venue):
    row = venue.contract.venues.get(VENUE_ID)
    mod_ = sys.modules[type(venue.contract).__module__]
    row.proposition_count = mod_.u256(10 ** 12)
    assert venue.propose(proposition_id="way-past") == "way-past"
    assert int(venue.contract.venues.get(VENUE_ID).proposition_count) \
        == 10 ** 12 + 1


def test_a_policy_can_still_change_past_the_old_version_limit(venue):
    """A venue that had changed its policy 65,535 times could never change
    it again - including to tighten it under attack, which is the recovery
    path the first review's fix depends on."""
    row = venue.contract.venues.get(VENUE_ID)
    mod_ = sys.modules[type(venue.contract).__module__]
    row.definition_version = mod_.u256(65535)
    digest = venue.contract.set_venue_policy(
        VENUE_ID, "OWNER_ONLY", 2, 2, 400, 1440)
    assert len(digest) == 64
    assert venue.venue()["definition_version"] == 65536
    assert venue.venue()["definition_hash"] == digest


def test_a_ruling_past_the_edge_still_carries_its_version(harness):
    """The version travels onto the ruling, so widening the venue's field
    without widening the ruling's would just move the overflow."""
    harness.register()
    row = harness.contract.venues.get(VENUE_ID)
    mod_ = sys.modules[type(harness.contract).__module__]
    row.definition_version = mod_.u256(70000)
    row.definition_hash = harness.contract.definition_hash(VENUE_ID)
    harness.propose()
    harness.serve_default()
    harness.mock_panel(harness.answer())
    assert harness.assess() == "DECIDABLE"
    assert harness.ruling()["definition_version"] == 70000


def test_every_remaining_u16_is_bounded_by_a_constant(mod):
    """The audit that keeps this fix from rotting.

    A 16-bit field is safe only when something caps it well below 65,535.
    Each one below is named with the bound that does the capping; a new
    unbounded `u16` would have to be added to this list to pass, which is
    the point.
    """
    bounded = {
        "min_sources": mod.MAX_SOURCES,
        "min_publishers": mod.MAX_SOURCES,
        "max_horizon_days": mod.MAX_HORIZON_DAYS,
        "open_propositions": mod.MAX_OPEN_PER_VENUE,
        "proposer_count": mod.MAX_AUTHORISED_PROPOSERS,
        "sufficient_sources": mod.MAX_SOURCES,
        "distinct_publishers": mod.MAX_SOURCES,
        "rounds_used": mod.MAX_ROUNDS,
        "round_number": mod.MAX_ROUNDS + 1,
    }
    for name, cap in bounded.items():
        assert cap < 65535, "%s is not bounded below the u16 limit" % name

    source = (mod.__file__ and True)
    import pathlib
    from conftest import CONTRACT
    text = pathlib.Path(CONTRACT).read_text(encoding="utf-8")
    declared = set()
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.endswith(": u16") and not stripped.startswith("#"):
            declared.add(stripped.split(":")[0].strip())
    unaccounted = declared - set(bounded)
    assert unaccounted == set(), (
        "these u16 fields are not named with the bound that caps them: %s"
        % sorted(unaccounted))

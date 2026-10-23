"""The pure helpers, called directly, one rule at a time.

Two reasons these are not left to the end-to-end tests. If two rules would
both refuse the same input, a test through the whole round cannot show
which one did the work, and deleting either would leave the suite green.
And the tables below are written out in this file rather than read from the
contract, because a test driven by the list under test cannot notice a
deletion from that list.
"""

import sys

import pytest

from gltest.direct import VMContext, deploy_contract
from conftest import CONTRACT, NOW


@pytest.fixture(scope="module")
def mod():
    """The contract module, loaded once: these functions touch no state."""
    vm = VMContext()
    with vm.activate():
        vm.warp(NOW)
        contract = deploy_contract(CONTRACT, vm)
        yield sys.modules[type(contract).__module__]


# == URL admission =========================================================

REFUSED_URLS = [
    ("plain http", "http://data.example/x"),
    ("no scheme", "data.example/x"),
    ("empty", ""),
    ("whitespace inside", "https://data.example/a b"),
    ("newline inside", "https://data.example/a\nb"),
    ("credentials", "https://user:pass@data.example/x"),
    ("localhost", "https://localhost/x"),
    ("dot-localhost", "https://thing.localhost/x"),
    ("dot-local", "https://printer.local/x"),
    ("dot-internal", "https://vault.internal/x"),
    ("loopback v4", "https://127.0.0.1/x"),
    ("private v4", "https://10.0.0.5/x"),
    ("link-local v4", "https://169.254.169.254/x"),
    ("legacy decimal ip", "https://2130706433/x"),
    ("leading-zero ip", "https://0177.0.0.1/x"),
    ("bare label", "https://intranet/x"),
    ("empty label", "https://a..example/x"),
    ("trailing dot", "https://data.example./x"),
    ("leading dot", "https://.example/x"),
    ("hyphen-led label", "https://-bad.example/x"),
    ("hyphen-tailed label", "https://bad-.example/x"),
    ("underscore", "https://da_ta.example/x"),
    ("ipv6", "https://[::1]/x"),
]


@pytest.mark.parametrize("label,url", REFUSED_URLS,
                         ids=[row[0] for row in REFUSED_URLS])
def test_these_locations_are_refused(mod, label, url):
    assert mod._admissible(url) is False


ACCEPTED_URLS = [
    "https://data.northwind-stats.example/series/reference-rate",
    "https://a.b.c.example/deep/path?q=1#frag",
    "https://data-1.example/x",
    "https://data.example.co.uk/x",
]


@pytest.mark.parametrize("url", ACCEPTED_URLS)
def test_these_locations_are_accepted(mod, url):
    assert mod._admissible(url) is True


def test_a_url_over_the_cap_is_refused(mod):
    assert mod._admissible("https://data.example/" + "x" * 400) is False


# == publishers ============================================================

DOMAINS = [
    ("data.northwind-stats.example", "northwind-stats.example"),
    ("api.northwind-stats.example", "northwind-stats.example"),
    ("www.northwind-stats.example", "northwind-stats.example"),
    ("northwind-stats.example", "northwind-stats.example"),
    ("deep.sub.northwind-stats.example", "northwind-stats.example"),
    ("stats.gov.uk", "stats.gov.uk"),
    ("data.stats.gov.uk", "stats.gov.uk"),
    ("news.example.com.au", "example.com.au"),
]


@pytest.mark.parametrize("host,want", DOMAINS)
def test_the_registrable_domain_is_what_counts_as_a_publisher(mod, host,
                                                              want):
    assert mod._registrable_domain(host) == want


def test_two_subdomains_are_one_publisher(mod):
    assert mod._registrable_domain("data.northwind-stats.example") \
        == mod._registrable_domain("api.northwind-stats.example")


def test_the_host_is_read_without_its_port_path_or_fragment(mod):
    assert mod._host_of("https://Data.Example:443/x?y#z") == "data.example"
    assert mod._host_of("not a url") == ""


# == instants ==============================================================

def test_an_instant_is_normalised_to_the_minute(mod):
    assert mod._minute("2026-10-23T09:00:41.221Z") == "2026-10-23T09:00Z"
    assert mod._minute("2026-10-23T09:00Z") == "2026-10-23T09:00Z"
    assert mod._minute("2026-10-23") == ""
    assert mod._minute("") == ""


BAD_INSTANTS = ["2026-13-01T00:00Z", "2026-10-32T00:00Z",
                "2026-10-23T24:00Z", "2026-10-23T09:60Z",
                "2026/10/23T09:00Z", "2026-10-23 09:00Z", "whenever"]


@pytest.mark.parametrize("stamp", BAD_INSTANTS)
def test_an_impossible_instant_does_not_parse(mod, stamp):
    assert mod._parse_minute(stamp) < 0


def test_minutes_between_is_exact_across_a_month_and_a_year(mod):
    assert mod._minutes_between("2026-10-23T09:00Z",
                                "2026-10-23T09:01Z") == 1
    assert mod._minutes_between("2026-10-31T23:59Z",
                                "2026-11-01T00:00Z") == 1
    assert mod._minutes_between("2026-12-31T23:59Z",
                                "2027-01-01T00:00Z") == 1
    assert mod._minutes_between("2026-10-23T09:00Z",
                                "2026-10-24T09:00Z") == 1440
    # Backwards is negative, not an error: callers test the sign.
    assert mod._minutes_between("2026-10-24T09:00Z",
                                "2026-10-23T09:00Z") == -1440
    assert mod._minutes_between("nonsense", "2026-10-23T09:00Z") == -1


def test_a_leap_day_is_a_real_day(mod):
    assert mod._minutes_between("2028-02-28T00:00Z",
                                "2028-03-01T00:00Z") == 2880
    assert mod._minutes_between("2027-02-28T00:00Z",
                                "2027-03-01T00:00Z") == 1440


# == the admission mapping =================================================

def test_the_admission_table(mod):
    """Called directly, so the precedence is pinned independently of any
    panel answer that could reach it."""
    decide = mod._admission_of
    assert decide(True, True, True, 2, 2, 2, 2) == "DECIDABLE"
    assert decide(False, True, True, 2, 2, 2, 2) == "UNFALSIFIABLE"
    assert decide(True, False, True, 2, 2, 2, 2) == "AMBIGUOUS"
    assert decide(True, True, False, 2, 2, 2, 2) == "UNSETTLEABLE"
    assert decide(True, True, True, 1, 1, 2, 1) == "UNSETTLEABLE"
    assert decide(True, True, True, 2, 1, 2, 2) == "UNSETTLEABLE"
    # Several failures at once: the most fundamental one names it.
    assert decide(False, False, False, 0, 0, 2, 2) == "UNFALSIFIABLE"
    assert decide(True, False, False, 0, 0, 2, 2) == "AMBIGUOUS"


def test_more_sources_than_required_is_still_decidable(mod):
    assert mod._admission_of(True, True, True, 4, 3, 2, 2) == "DECIDABLE"


# == the prompt budget =====================================================

def test_the_budget_is_shared_between_documents(mod):
    """Applied per document before anything is encoded. Slicing finished
    JSON would land the cut inside a string and hand the model something
    that cannot parse."""
    one = mod._per_document_allowance({"S1": "x"})
    four = mod._per_document_allowance({"S1": "x", "S2": "y", "S3": "z",
                                        "S4": "w"})
    assert one == mod.PROMPT_BUDGET_CHARS - mod.PROMPT_OVERHEAD_RESERVE
    assert four * 4 <= one
    assert mod._per_document_allowance({}) == 0


def test_the_whole_prompt_fits_its_budget_at_the_maximum(mod):
    """The bound the docstring claims, computed rather than asserted."""
    texts = {}
    for index in range(mod.MAX_SOURCES):
        texts["S%d" % (index + 1)] = "y" * 500000
    allowance = mod._per_document_allowance(texts)
    body = allowance * mod.MAX_SOURCES
    assert body <= mod.PROMPT_BUDGET_CHARS - mod.PROMPT_OVERHEAD_RESERVE


# == exact types ===========================================================

def test_only_a_real_boolean_is_a_boolean(mod):
    assert mod._exact_bool(True) is True
    assert mod._exact_bool(False) is True
    for value in (1, 0, 1.0, "true", "", None, [], {}):
        assert mod._exact_bool(value) is False


def test_a_reply_that_is_already_decoded_is_taken_as_is(mod):
    assert mod._json_object({"a": 1}) == {"a": 1}
    assert mod._json_object('{"a": 1}') == {"a": 1}
    assert mod._json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert mod._json_object("[1,2]") == [1, 2]
    assert mod._json_object("not json") is None
    assert mod._json_object(b'{"a": 1}') == {"a": 1}
    assert mod._json_object(12) is None


def test_bounding_trims_and_strips(mod):
    assert mod._bounded("  hello  ", 80) == "hello"
    assert mod._bounded("abcdef", 3) == "abc"

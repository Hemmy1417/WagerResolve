"""A small real-network suite: real validators, real pages, real consensus.

Direct Mode proves the logic under controlled nondeterminism. This proves
the contract deploys to Studionet and behaves there, where the panel really
reads pages and validators really have to agree.

Deliberately small - four tests, not the Direct Mode matrix. Each deploys
its own contract so none depends on another's state or ordering.

    gltest tests/integration/ -v -s --network studionet

These are skipped unless the network is reachable, so an offline clone's
suite does not fail for a reason that has nothing to do with the contract.
"""

import json
import pathlib
import time
import urllib.request

import pytest

from gltest import get_contract_factory, get_default_account
from gltest.assertions import tx_execution_succeeded

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT = str(ROOT / "contracts" / "wagerresolve.py")
COMMIT = "main"
RAW = "https://raw.githubusercontent.com/Hemmy1417/WagerResolve/%s/fixtures/%s"

RATE_TABLE = RAW % (COMMIT, "rate-table.txt")
MIRROR = RAW % (COMMIT, "rate-table-mirror.txt")
COMMENTARY = RAW % (COMMIT, "commentary.txt")

WELL_POSED = ("The Northwind reference rate published for 2026-10-21 is "
              "strictly greater than 4.40 percent.")
GOOD_RULE = ("Read the reference rate for 2026-10-21 from the rate table. "
             "YES if it is strictly greater than 4.40, NO if it is 4.40 or "
             "lower. If no figure is published for that date, the wager "
             "voids.")


def _reachable() -> bool:
    """Whether Studionet answers at all.

    An HTTP error IS an answer: the RPC endpoint replies 405 to a bare
    GET, and that proves the socket, TLS and the host are all fine. Only a
    transport failure means unreachable. An earlier version of this got it
    backwards and skipped the entire suite while reporting green, which is
    worse than failing.
    """
    request = urllib.request.Request(
        "https://studio.genlayer.com/api",
        headers={"User-Agent": "Mozilla/5.0"})
    try:
        urllib.request.urlopen(request, timeout=15)
        return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _reachable(), reason="Studionet is not reachable from here")


def stamp(offset_days: int = 0) -> str:
    return time.strftime("%Y-%m-%dT%H:%MZ",
                         time.gmtime(time.time() + 86400 * offset_days))


def tag() -> str:
    return "-it" + hex(int(time.time() * 1000))[-6:]


@pytest.fixture
def deployed():
    """A fresh contract, so no test can depend on another's state."""
    factory = get_contract_factory(contract_file_path=CONTRACT)
    contract = factory.deploy(args=[], account=get_default_account(),
                              consensus_max_rotations=3,
                              wait_interval=10000, wait_retries=30)
    return contract


def test_deploy_and_public_surface(deployed):
    """The contract is there, and answers the views a consumer reads."""
    bounds = json.loads(deployed.bounds(args=[]).call())
    assert bounds["max_sources"] == 4
    assert bounds["admissions"][0] == "DECIDABLE"
    stats = json.loads(deployed.get_stats(args=[]).call())
    assert stats == {"venues": 0, "propositions": 0, "decidable": 0,
                     "refused": 0}
    # An unknown proposition is false rather than an exception, so a
    # consumer's gate cannot be turned into a revert by a bad id.
    assert deployed.is_admissible(args=["nope", stamp()]).call() is False


def test_a_well_posed_question_is_admitted(deployed):
    venue = "v" + tag()
    pid = "p" + tag()
    assert tx_execution_succeeded(deployed.register_venue(
        args=[venue, "Integration venue", "PUBLIC", 2, 1, 400, 1440]
    ).transact(consensus_max_rotations=3))
    assert tx_execution_succeeded(deployed.propose_question(
        args=[venue, pid, WELL_POSED, GOOD_RULE, stamp(20),
              [RATE_TABLE, MIRROR]]).transact(consensus_max_rotations=3))
    assert tx_execution_succeeded(
        deployed.assess_proposition(args=[pid]).transact(
            consensus_max_rotations=3))

    ruling = json.loads(deployed.get_ruling(args=[pid]).call())
    assert ruling["admission"] == "DECIDABLE"
    assert ruling["status"] == "ASSESSED"
    assert ruling["sufficient_sources"] == 2
    assert deployed.is_admissible(args=[pid, stamp()]).call() is True


def test_a_question_no_source_can_settle_is_refused(deployed):
    """The commentary page is about the right subject and publishes no
    figure, so the venue's floor of two publishing sources is not met."""
    venue = "v" + tag()
    pid = "p" + tag()
    assert tx_execution_succeeded(deployed.register_venue(
        args=[venue, "Integration venue", "PUBLIC", 2, 1, 400, 1440]
    ).transact(consensus_max_rotations=3))
    assert tx_execution_succeeded(deployed.propose_question(
        args=[venue, pid, WELL_POSED, GOOD_RULE, stamp(20),
              [RATE_TABLE, COMMENTARY]]).transact(
                  consensus_max_rotations=3))
    assert tx_execution_succeeded(
        deployed.assess_proposition(args=[pid]).transact(
            consensus_max_rotations=3))

    ruling = json.loads(deployed.get_ruling(args=[pid]).call())
    assert ruling["admission"] == "UNSETTLEABLE"
    assert ruling["sufficient_sources"] == 1
    assert deployed.is_admissible(args=[pid, stamp()]).call() is False


def test_withdrawal_returns_the_slot(deployed):
    """The lifecycle property the in-flight caps rest on."""
    venue = "v" + tag()
    pid = "p" + tag()
    assert tx_execution_succeeded(deployed.register_venue(
        args=[venue, "Integration venue", "PUBLIC", 2, 1, 400, 1440]
    ).transact(consensus_max_rotations=3))
    account = str(get_default_account().address)

    before = json.loads(deployed.open_slots(args=[venue, account]).call())
    assert tx_execution_succeeded(deployed.propose_question(
        args=[venue, pid, WELL_POSED, GOOD_RULE, stamp(20),
              [RATE_TABLE, MIRROR]]).transact(consensus_max_rotations=3))
    held = json.loads(deployed.open_slots(args=[venue, account]).call())
    assert held["venue_open"] == before["venue_open"] + 1

    assert tx_execution_succeeded(
        deployed.withdraw_question(args=[pid]).transact(
            consensus_max_rotations=3))
    after = json.loads(deployed.open_slots(args=[venue, account]).call())
    assert after["venue_open"] == before["venue_open"]
    assert after["proposer_open"] == before["proposer_open"]

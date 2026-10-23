"""Shared harness for the Direct Mode suite.

Only the nondeterministic edges are mocked: the fetch of each named source,
and the one reading call. Everything between them - the proposer policy, URL
admission, the slot accounting, the definition hash, publisher clustering,
instant arithmetic, the admission precedence, freshness, the payload gate
and the storage - is the contract's own code.
"""

import json
import os
import pathlib
import sys

import pytest

from eth_utils import to_checksum_address

from gltest.direct import VMContext, deploy_contract, create_test_addresses


def hexaddr(account) -> str:
    """The checksummed spelling the contract stores for a test account."""
    return to_checksum_address(bytes(account))


def _tolerate_windows_tempfile_unlink():
    """Work around a Windows-only failure in the Direct Mode loader.

    `gltest` 0.29.2 writes the transaction message to a temp file, binds it
    to fd 0 with `dup2`, closes its own descriptor and then unlinks the
    path. POSIX allows unlinking a file another descriptor still
    references; Windows does not, so contract loading dies with WinError 32
    before any contract code runs. This tolerates that one failed cleanup
    and restores `os.unlink` immediately afterwards.

    It is a host workaround, not a contract fix: the contract is neither
    involved nor modified, and on anything but Windows it does nothing.
    """
    if sys.platform != "win32":
        return
    from gltest.direct import loader

    original = getattr(loader, "_inject_message_to_fd0", None)
    if original is None or getattr(original, "_unlink_tolerated", False):
        return

    def wrapped(vm):
        real_unlink = os.unlink

        def tolerant(path, *args, **kwargs):
            try:
                real_unlink(path, *args, **kwargs)
            except OSError:
                pass

        os.unlink = tolerant
        try:
            return original(vm)
        finally:
            os.unlink = real_unlink

    wrapped._unlink_tolerated = True
    loader._inject_message_to_fd0 = wrapped


_tolerate_windows_tempfile_unlink()


ROOT = pathlib.Path(__file__).resolve().parents[2]

# The suite runs against the committed contract unless a mutation sweep
# points it at a patched copy (scripts/mutate.py).
CONTRACT = pathlib.Path(
    os.environ.get("WAGERRESOLVE_CONTRACT",
                   str(ROOT / "contracts" / "wagerresolve.py")))
FIXTURES = ROOT / "fixtures"


# == the synthetic sources =================================================

RATE_TABLE = "rate-table.txt"
COMMENTARY = "commentary.txt"
DIRECTED = "directed.txt"
BLANK = "blank.txt"

# Two publishers. `MIRROR_HOST` is a different host on the SAME registrable
# domain as `DATA_HOST`, which is how the independence floor is exercised:
# two URLs there are one publisher however different they look.
DATA_HOST = "data.northwind-stats.example"
MIRROR_HOST = "api.northwind-stats.example"
OTHER_HOST = "www.coastal-registry.example"

DATA_URL = "https://" + DATA_HOST + "/series/reference-rate"
MIRROR_URL = "https://" + MIRROR_HOST + "/v1/reference-rate"
OTHER_URL = "https://" + OTHER_HOST + "/harbour/status"

VENUE_ID = "northwind-markets"
VENUE_LABEL = "Northwind Markets (synthetic)"

# The instant the tests work at, a settlement well inside any horizon, and
# one far enough ahead to exceed a short one.
NOW = "2026-10-23T09:00Z"
SETTLES = "2026-11-30T16:00Z"
FAR = "2028-06-30T16:00Z"

PROPOSITION = ("The Northwind reference rate published for 2026-11-27 is "
               "strictly greater than 4.50 percent.")
RULE = ("Read the reference rate for 2026-11-27 from the daily rate table. "
        "YES if it is strictly greater than 4.50, NO if it is 4.50 or "
        "lower. If the table shows no final value for that date, the "
        "wager voids.")


def document_text(name: str) -> str:
    return (FIXTURES / name).read_bytes().decode("utf-8")


class Harness:
    """One deployed contract and the mocks around it.

    Every method returns what the contract returned, so a test asserts on
    the contract's own answer rather than on the harness's idea of it.
    """

    def __init__(self, vm, contract, accounts):
        self.vm = vm
        self.contract = contract
        self.accounts = accounts
        self.owner = accounts[0]
        self.proposer = accounts[1]
        self.stranger = accounts[2]
        self.other = accounts[3]
        self._pages = {}
        self._answer = None
        self.vm.warp(NOW)

    # -- mocking -------------------------------------------------------
    #
    # The harness owns the mock state and re-applies all of it on every
    # change. `mock_llm` registers an answer rather than replacing the
    # previous one, so a test that assesses twice would otherwise get the
    # first round's answer again - exactly how a retry test can pass while
    # proving nothing.

    def _apply(self):
        self.vm.clear_mocks()
        for url in self._pages:
            status, body = self._pages[url]
            self.vm.mock_web(url_pattern=url,
                             response={"method": "GET", "status": status,
                                       "body": body})
        if self._answer is not None:
            self.vm.mock_llm(
                prompt_pattern="panel deciding whether a wager",
                response=self._answer)

    def serve(self, url, name=None, status=200, body=None):
        """Put one document at one location."""
        text = body
        if text is None:
            text = document_text(name if name is not None else RATE_TABLE)
        self._pages[url] = (status, text)
        self._apply()

    def serve_default(self):
        """The rate table at both Northwind locations, the registry page at
        the third. Enough for every source a test names to be readable."""
        self.serve(DATA_URL, RATE_TABLE)
        self.serve(MIRROR_URL, RATE_TABLE)
        self.serve(OTHER_URL, RATE_TABLE)
        return self

    def unserve(self, url):
        if url in self._pages:
            del self._pages[url]
        self._apply()

    def mock_panel(self, raw):
        self._answer = raw
        self._apply()

    def clear(self):
        self._pages = {}
        self._answer = None
        self.vm.clear_mocks()

    # -- the clock -----------------------------------------------------

    def set_now(self, stamp: str):
        """Move the clock the contract itself reads.

        `vm.warp` sets the VM's datetime, but the helper that refreshes the
        injected message rewrites only the sender, the value and the chain
        id - not the datetime - so after the contract module is loaded a
        warp alone never reaches `gl.message_raw["datetime"]`, and the
        contract keeps seeing the instant it was deployed at.
        """
        self.vm.warp(stamp)
        module = sys.modules.get("genlayer.gl")
        if module is not None and getattr(module, "message_raw", None):
            module.message_raw["datetime"] = stamp
        return stamp

    def as_sender(self, account):
        self.vm.sender = account
        return self

    # -- the answer the panel is asked for -----------------------------

    def answer(self, falsifiable=True, unambiguous=True, rule_complete=True,
               sources=None, falsifiable_reason=None, ambiguity_reason=None,
               rule_reason=None, note="synthetic"):
        """An answer in the one shape the contract accepts.

        `sources`: list of (source_id, publishes_quantity).
        """
        rows = []
        for row in (sources if sources is not None else [("S1", True),
                                                         ("S2", True)]):
            rows.append({"source_id": row[0],
                         "publishes_quantity": row[1],
                         "note": note})
        return json.dumps({
            "falsifiable": falsifiable,
            "falsifiable_reason": (falsifiable_reason if falsifiable_reason
                                   is not None else
                                   ("NONE" if falsifiable
                                    else "NO_OBSERVATION_COULD_REFUTE_IT")),
            "unambiguous": unambiguous,
            "ambiguity_reason": (ambiguity_reason if ambiguity_reason
                                 is not None else
                                 ("NONE" if unambiguous
                                  else "COMPETING_READINGS")),
            "rule_complete": rule_complete,
            "rule_reason": (rule_reason if rule_reason is not None else
                            ("NONE" if rule_complete
                             else "RULE_LEAVES_AN_OBSERVATION_UNMAPPED")),
            "sources": rows,
        })

    # -- the contract --------------------------------------------------

    def register(self, venue_id=VENUE_ID, label=VENUE_LABEL,
                 policy="PUBLIC", min_sources=2, min_publishers=2,
                 horizon=400, ttl=1440):
        return self.contract.register_venue(
            venue_id, label, policy, min_sources, min_publishers,
            horizon, ttl)

    def propose(self, proposition_id="p-1", venue_id=VENUE_ID,
                text=PROPOSITION, rule=RULE, settles_at=SETTLES,
                sources=None):
        return self.contract.propose_question(
            venue_id, proposition_id, text, rule, settles_at,
            sources if sources is not None else [DATA_URL, OTHER_URL])

    def assess(self, proposition_id="p-1"):
        return self.contract.assess_proposition(proposition_id)

    def ruling(self, proposition_id="p-1"):
        return json.loads(self.contract.get_ruling(proposition_id))

    def proposition(self, proposition_id="p-1"):
        return json.loads(self.contract.get_proposition(proposition_id))

    def venue(self, venue_id=VENUE_ID):
        return json.loads(self.contract.get_venue(venue_id))

    def stats(self):
        return json.loads(self.contract.get_stats())

    def slots(self, who=None, venue_id=VENUE_ID):
        return json.loads(self.contract.open_slots(
            venue_id, hexaddr(who if who is not None else self.owner)))

    def ready(self, **kwargs):
        """A public venue, two readable sources and an honest panel: the
        state most tests start from."""
        self.register(**kwargs)
        self.propose()
        self.serve_default()
        self.mock_panel(self.answer())
        return self


@pytest.fixture
def harness():
    vm = VMContext()
    vm.check_pickling = True
    with vm.activate():
        accounts = create_test_addresses(4)
        vm.sender = accounts[0]
        vm.warp(NOW)
        contract = deploy_contract(CONTRACT, vm)
        yield Harness(vm, contract, accounts)


@pytest.fixture
def venue(harness):
    """A registered public venue with nothing proposed yet."""
    harness.register()
    return harness


@pytest.fixture
def ready(harness):
    """A venue, one proposition, both sources readable, an honest panel."""
    return harness.ready()

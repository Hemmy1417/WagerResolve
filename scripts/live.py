"""Deploy WagerResolve to Studionet and prove it works there.

    python scripts/live.py --commit <sha>

Deploys the committed contract, runs every scenario against it with real
validators reading real pages, and writes `docs/proofs/live.json` plus
`docs/proofs/live-run.log`. `scripts/verify.py` turns the ledger into
`docs/proofs/live.md` by re-reading the chain, so the evidence is
reproducible by anyone without a key.

Reads are retried; a submission never is. A write that looks like it failed
may already have landed, and sending it twice would be a second question,
not a retry of the first.
"""

import argparse
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.request

from genlayer_py import (chains, create_account, create_client,
                         generate_private_key)
from genlayer_py.types import TransactionStatus

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "wagerresolve.py"
PROOFS = ROOT / "docs" / "proofs"

RPC = "https://studio.genlayer.com/api"
EXPLORER = "https://explorer-studio.genlayer.com"
RAW = "https://raw.githubusercontent.com/Hemmy1417/WagerResolve/%s/fixtures/%s"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 "
              "Safari/537.36")

RATE_TABLE = "rate-table.txt"
MIRROR = "rate-table-mirror.txt"
COMMENTARY = "commentary.txt"
DIRECTED = "directed.txt"
MISSING = "no-such-document.txt"

ATTEMPTS = 8
PACE = 1.5

LOG = []


def say(line=""):
    print(line, flush=True)
    LOG.append(str(line))


def patiently(what, call):
    """Run a read again if the network, not the chain, refused it.

    Everything wrapped here only asks the node a question, so repeating one
    cannot change anything - which is the whole licence for retrying, and
    why no submission goes through it.
    """
    delay = 2.0
    for attempt in range(ATTEMPTS):
        try:
            return call()
        except Exception as err:
            if attempt == ATTEMPTS - 1:
                raise
            say("  %s failed (%s); retrying in %.0fs"
                % (what, type(err).__name__, delay))
            time.sleep(delay)
            delay = min(delay * 2, 60.0)


def rpc(method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                          "params": params}).encode("utf-8")
    request = urllib.request.Request(
        RPC, data=payload,
        headers={"Content-Type": "application/json",
                 "User-Agent": BROWSER_UA})

    def once():
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    return patiently(method, once)


def consensus_summary(receipt):
    """Agreement as the receipt records it. An idle validator is not a
    disagreeing one, and collapsing the two would overstate dissent as
    easily as it would hide it."""
    data = receipt.get("consensus_data") or {}
    votes = data.get("votes") or {}
    if not votes:
        return "no votes recorded"
    agree = sum(1 for v in votes.values() if str(v).lower() == "agree")
    disagree = sum(1 for v in votes.values()
                   if str(v).lower().startswith("disagree"))
    other = len(votes) - agree - disagree
    return "%d agree, %d disagree, %d idle of %d" % (
        agree, disagree, other, len(votes))


def execution_result(receipt):
    """On this network the top-level execution_result is empty; the real
    value is on the leader receipt."""
    named = receipt.get("execution_result_name") or receipt.get("result_name")
    leader = (receipt.get("consensus_data") or {}).get("leader_receipt")
    if isinstance(leader, list) and leader:
        return str(leader[0].get("execution_result") or named or "unknown")
    return str(named or "unknown")


def lifecycle(receipt):
    return str(receipt.get("status_name") or receipt.get("status"))


def stdout_of(receipt):
    leader = (receipt.get("consensus_data") or {}).get("leader_receipt")
    if isinstance(leader, list) and leader:
        return str((leader[0].get("genvm_result") or {}).get("stdout") or "")
    return ""


def _hex(value):
    """A transaction hash as 0x-text, whichever shape the SDK returns."""
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    text = str(value)
    return text if text.startswith("0x") else "0x" + text


class Run:
    def __init__(self, commit, address=None):
        self.commit = commit
        self.account = create_account(
            account_private_key=os.environ.get("WAGERRESOLVE_SIGNER_KEY")
            or generate_private_key())
        self.client = create_client(chain=chains.studionet,
                                    account=self.account)
        self.address = address
        self.transactions = []
        self.scenarios = {}
        self.documents = {}
        self.tag = "-" + commit[:6] + "-" + hashlib.sha256(
            str(time.time()).encode()).hexdigest()[:4]

    # -- chain ---------------------------------------------------------

    def fund(self):
        result = rpc("sim_fundAccount",
                     [self.account.address, 500000000000000000000])
        if "error" in result:
            raise SystemExit("faucet refused: %s" % result["error"])
        say("faucet: funded %s" % self.account.address)
        time.sleep(3)

    def wait(self, label, tx_hash):
        receipt = patiently(label, lambda: self.client.wait_for_transaction_receipt(
            transaction_hash=tx_hash, status=TransactionStatus.FINALIZED,
            interval=5000, retries=60))
        return receipt

    def deploy(self):
        code = CONTRACT.read_bytes()
        say("deploying %d bytes, sha256 %s"
            % (len(code), hashlib.sha256(code).hexdigest()))
        tx_hash = _hex(self.client.deploy_contract(
            code=code.decode("utf-8"), args=[],
            consensus_max_rotations=3))
        receipt = self.wait("deploy receipt", tx_hash)
        self.address = receipt.get("data", {}).get("contract_address") \
            or receipt.get("contract_address")
        say("deploy tx %s" % tx_hash)
        say("deploy lifecycle %s, execution %s, %s"
            % (lifecycle(receipt), execution_result(receipt),
               consensus_summary(receipt)))
        if execution_result(receipt).upper() not in ("SUCCESS", "RETURN"):
            raise SystemExit("deployment executed with an error")
        self.deploy_tx = tx_hash
        self.deploy_consensus = consensus_summary(receipt)
        self.deploy_lifecycle = lifecycle(receipt)
        self.transactions.append({"what": "deploy", "tx": tx_hash,
                                  "lifecycle": lifecycle(receipt),
                                  "execution": execution_result(receipt),
                                  "consensus": consensus_summary(receipt)})
        say("contract %s" % self.address)

    def write(self, what, method, args):
        """One submission. Never retried: it may already have landed."""
        time.sleep(PACE)
        tx_hash = _hex(self.client.write_contract(
            address=self.address, function_name=method, args=args,
            value=0, consensus_max_rotations=3))
        receipt = self.wait(what, tx_hash)
        result = execution_result(receipt)
        say("  %-44s %s  %s" % (what, result, consensus_summary(receipt)))
        out = stdout_of(receipt)
        if out.strip():
            say("    stdout: " + out.strip()[:300])
        self.transactions.append({"what": what, "tx": tx_hash,
                                  "lifecycle": lifecycle(receipt),
                                  "execution": result,
                                  "consensus": consensus_summary(receipt)})
        return receipt, result

    def read(self, method, args):
        time.sleep(PACE)
        return patiently(method, lambda: self.client.read_contract(
            address=self.address, function_name=method, args=args))

    # -- helpers --------------------------------------------------------

    def source(self, name):
        return RAW % (self.commit, name)

    def record_documents(self):
        for name in (RATE_TABLE, MIRROR, COMMENTARY, DIRECTED):
            url = self.source(name)
            request = urllib.request.Request(
                url, headers={"User-Agent": BROWSER_UA})

            def once():
                with urllib.request.urlopen(request, timeout=30) as resp:
                    return resp.read()

            body = patiently(name, once)
            self.documents[name] = {
                "url": url, "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest()}
            say("  fixture %-26s %d bytes" % (name, len(body)))


def now_stamp():
    """The instant to ask a freshness question at, read when it is asked.

    Not captured once at the start: an admission is fresh relative to NOW,
    and a stamp taken before the round would answer a different question
    from the one a venue actually asks.
    """
    return time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())


def expect(label, got, want):
    if got != want:
        raise SystemExit("ASSERTION FAILED %s: got %r, want %r"
                         % (label, got, want))
    say("  ok  %-52s %s" % (label, got))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--address")
    args = parser.parse_args()

    run = Run(args.commit, args.address)
    say("WagerResolve live run")
    say("commit %s" % run.commit)
    say("signer %s" % run.account.address)
    run.fund()
    say()
    say("fixtures, as the chain will fetch them:")
    run.record_documents()
    say()

    if run.address is None:
        run.deploy()
    say()

    settles = time.strftime("%Y-%m-%dT%H:%MZ",
                            time.gmtime(time.time() + 86400 * 20))
    far_past = "2020-01-01T00:00Z"

    venue = "northwind" + run.tag
    strict = "strict" + run.tag

    say("venues")
    run.write("register venue %s" % venue, "register_venue",
              [venue, "Northwind Markets (synthetic)", "PUBLIC", 2, 1,
               400, 1440])
    run.write("register venue %s (two publishers)" % strict,
              "register_venue",
              [strict, "Strict Markets (synthetic)", "PUBLIC", 2, 2,
               400, 1440])
    say()

    scenarios = [
        ("A", "a well-posed question on two published copies",
         venue,
         ("The Northwind reference rate published for 2026-10-21 is "
          "strictly greater than 4.40 percent."),
         ("Read the reference rate for 2026-10-21 from the rate table. "
          "YES if it is strictly greater than 4.40, NO if it is 4.40 or "
          "lower. If no figure is published for that date, the wager "
          "voids."),
         [RATE_TABLE, MIRROR], "DECIDABLE"),

        ("B", "one source carries no figures at all",
         venue,
         ("The Northwind reference rate published for 2026-10-21 is "
          "strictly greater than 4.40 percent."),
         ("Read the reference rate for 2026-10-21 from the rate table. "
          "YES if above 4.40, NO otherwise. Void if no figure is "
          "published."),
         [RATE_TABLE, COMMENTARY], "UNSETTLEABLE"),

        ("C", "a question nobody could settle either way",
         venue,
         ("Interest rates will be an interesting topic for households "
          "over the coming months."),
         ("YES if rates turn out to be interesting, NO otherwise."),
         [RATE_TABLE, MIRROR], "UNFALSIFIABLE"),

        ("D", "a question two honest readers would read differently",
         venue,
         ("The Northwind reference rate rises significantly by the end "
          "of next month."),
         ("YES if the rate rises significantly, NO if it does not."),
         [RATE_TABLE, MIRROR], "AMBIGUOUS"),

        ("E", "two sources, one publisher, a venue that wants two",
         strict,
         ("The Northwind reference rate published for 2026-10-21 is "
          "strictly greater than 4.40 percent."),
         ("Read the reference rate for 2026-10-21 from the rate table. "
          "YES if above 4.40, NO otherwise. Void if nothing is "
          "published."),
         [RATE_TABLE, MIRROR], "UNSETTLEABLE"),

        ("F", "a page that tells the reader what to answer",
         venue,
         ("The Northwind reference rate published for 2026-10-21 is "
          "strictly greater than 4.40 percent."),
         ("Read the reference rate for 2026-10-21 from the rate table. "
          "YES if above 4.40, NO otherwise. Void if nothing is "
          "published."),
         [RATE_TABLE, DIRECTED], "UNSETTLEABLE"),
    ]

    for code, title, at_venue, text, rule, names, want in scenarios:
        pid = code.lower() + run.tag
        say("%s - %s" % (code, title))
        sources = [run.source(name) for name in names]
        run.write("propose %s" % pid, "propose_question",
                  [at_venue, pid, text, rule, settles, sources])
        _receipt, result = run.write("assess %s" % pid,
                                     "assess_proposition", [pid])
        if result.upper() not in ("SUCCESS", "RETURN"):
            raise SystemExit("%s: the assessment did not execute" % code)
        ruling = json.loads(run.read("get_ruling", [pid]))
        expect("%s admission" % code, ruling["admission"], want)
        expect("%s is_admissible" % code,
               run.read("is_admissible", [pid, now_stamp()]),
               want == "DECIDABLE")
        run.scenarios[code.lower()] = {
            "title": title, "proposition_id": pid, "venue_id": at_venue,
            "text": text, "rule": rule,
            "sources": [run.documents[n]["url"] for n in names],
            "ruling": ruling,
            "proposition": json.loads(run.read("get_proposition", [pid])),
        }
        say()

    # G - a source that does not exist is not a verdict about the question
    say("G - a source that cannot be fetched")
    pid = "g" + run.tag
    run.write("propose %s" % pid, "propose_question",
              [venue, pid,
               "The Northwind reference rate published for 2026-10-21 is "
               "strictly greater than 4.40 percent.",
               "Read the rate for 2026-10-21. YES if above 4.40, NO "
               "otherwise. Void if nothing is published.",
               settles,
               [run.source(RATE_TABLE), run.source(MISSING)]])
    run.write("assess %s" % pid, "assess_proposition", [pid])
    ruling = json.loads(run.read("get_ruling", [pid]))
    expect("G admission", ruling["admission"], "UNSETTLEABLE")
    expect("G one source read", ruling["sufficient_sources"], 1)
    run.scenarios["g"] = {"title": "a source that cannot be fetched",
                          "proposition_id": pid, "venue_id": venue,
                          "ruling": ruling,
                          "proposition": json.loads(
                              run.read("get_proposition", [pid]))}
    say()

    # H - the lifecycle a venue owner controls
    say("H - withdrawal returns the slot, and a policy change supersedes")
    pid = "h" + run.tag
    before = json.loads(run.read("open_slots",
                                 [venue, run.account.address]))
    run.write("propose %s" % pid, "propose_question",
              [venue, pid,
               "The Northwind reference rate published for 2026-10-22 is "
               "strictly greater than 4.40 percent.",
               "Read the rate for 2026-10-22. YES if above 4.40, NO "
               "otherwise. Void if nothing is published.",
               settles, [run.source(RATE_TABLE), run.source(MIRROR)]])
    held = json.loads(run.read("open_slots", [venue, run.account.address]))
    expect("H a proposal takes a slot", held["venue_open"],
           before["venue_open"] + 1)
    run.write("withdraw %s" % pid, "withdraw_question", [pid])
    after = json.loads(run.read("open_slots", [venue, run.account.address]))
    expect("H withdrawal returns it", after["venue_open"],
           before["venue_open"])

    a_id = run.scenarios["a"]["proposition_id"]
    expect("H the admitted question still stands",
           run.read("is_admissible", [a_id, now_stamp()]), True)
    run.write("tighten %s" % venue, "set_venue_policy",
              [venue, "OWNER_ONLY", 2, 2, 400, 1440])
    expect("H the old ruling is superseded",
           run.read("admission_freshness", [a_id, now_stamp()]),
           "SUPERSEDED")
    expect("H and no longer admits a stake",
           run.read("is_admissible", [a_id, now_stamp()]), False)
    run.scenarios["h"] = {
        "title": "withdrawal returns the slot, a policy change supersedes",
        "proposition_id": pid, "venue_id": venue,
        "slots_before": before, "slots_held": held, "slots_after": after,
        "superseded": a_id,
    }
    say()

    stats = json.loads(run.read("get_stats", []))
    say("counters %s" % json.dumps(stats))

    PROOFS.mkdir(parents=True, exist_ok=True)
    ledger = {
        "schema": "wagerresolve-live/1",
        "commit": run.commit,
        "chain_id": 61999,
        "rpc": RPC,
        "explorer": EXPLORER,
        "contract": run.address,
        "contract_sha256": hashlib.sha256(
            CONTRACT.read_bytes()).hexdigest(),
        "deploy_tx": run.deploy_tx,
        "deploy_lifecycle": run.deploy_lifecycle,
        "deploy_consensus": run.deploy_consensus,
        "deployer": run.account.address,
        "tag": run.tag,
        "settles_at": settles,
        "documents": run.documents,
        "transactions": run.transactions,
        "scenarios": run.scenarios,
        "stats": stats,
        "as_of": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()),
    }
    (PROOFS / "live.json").write_bytes(
        json.dumps(ledger, indent=2, sort_keys=True).encode("utf-8"))
    (PROOFS / "live-run.log").write_bytes(
        ("\n".join(LOG) + "\n").encode("utf-8"))
    say()
    say("every assertion held")
    say("ledger written to docs/proofs/live.json")
    return 0


sys.exit(main())

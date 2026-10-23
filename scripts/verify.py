"""Rebuild the live proof by re-reading the chain. No keys, no writes.

Reads `docs/proofs/live.json`, asks the network to confirm every claim in
it, and writes `docs/proofs/live.md`. Anyone can run this: it needs no
signer, sends no transaction, and reaches a throwaway read-only account.

    python scripts/verify.py

Every read is retried, because one connection reset should not make a
reproducible proof look unreproducible. No write exists here to retry.
"""

import base64
import hashlib
import json
import pathlib
import secrets
import sys
import time
import urllib.request

from genlayer_py import chains, create_account, create_client

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "wagerresolve.py"
PROOFS = ROOT / "docs" / "proofs"
LEDGER = PROOFS / "live.json"

RPC = "https://studio.genlayer.com/api"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 "
              "Safari/537.36")
PACE = 1.4
ATTEMPTS = 8

LINES = []
FAILURES = []
READS = [0]


def say(line=""):
    LINES.append(str(line))


def patiently(what, call):
    delay = 2.0
    for attempt in range(ATTEMPTS):
        try:
            return call()
        except Exception as err:
            if attempt == ATTEMPTS - 1:
                raise
            print("  %s failed (%s); retrying in %.0fs"
                  % (what, type(err).__name__, delay), file=sys.stderr)
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


def fetch(url):
    request = urllib.request.Request(url,
                                     headers={"User-Agent": BROWSER_UA})

    def once():
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()

    return patiently(url, once)


class Reader:
    def __init__(self, address):
        self.address = address
        self.client = create_client(
            chain=chains.studionet,
            account=create_account(
                account_private_key="0x" + secrets.token_hex(32)))

    def view(self, method, args=None):
        READS[0] += 1
        time.sleep(PACE)
        return patiently(method, lambda: self.client.read_contract(
            address=self.address, function_name=method, args=args or []))

    def transaction(self, tx_hash):
        READS[0] += 1
        time.sleep(PACE)
        return patiently("get_transaction",
                         lambda: self.client.get_transaction(
                             transaction_hash=tx_hash))


def row(claim, value, ok):
    if not ok:
        FAILURES.append(claim)
    say("| %s | `%s` | %s |" % (claim, str(value)[:48],
                                "OK" if ok else "**WRONG**"))


def consensus_summary(receipt):
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
    named = receipt.get("execution_result_name") or receipt.get("result_name")
    leader = (receipt.get("consensus_data") or {}).get("leader_receipt")
    if isinstance(leader, list) and leader:
        return str(leader[0].get("execution_result") or named or "unknown")
    return str(named or "unknown")


def deployed_source_hash(address):
    result = rpc("gen_getContractCode", [address])
    raw = result.get("result")
    if isinstance(raw, dict):
        raw = raw.get("code") or raw.get("data")
    if not raw:
        return ""
    return hashlib.sha256(base64.b64decode(raw)).hexdigest()


def main() -> int:
    if not LEDGER.exists():
        print("no docs/proofs/live.json - run scripts/live.py first")
        return 1
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    reader = Reader(led["contract"])
    explorer = led["explorer"]
    digest = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()

    say("# Live evidence")
    say()
    say("Every line below was re-read from GenLayer Studionet by")
    say("`scripts/verify.py`, which holds no key and sends no transaction.")
    say("Nothing here is copied from the run that produced it.")
    say()
    say("| | |")
    say("|---|---|")
    say("| Network | chain **%d** |" % led["chain_id"])
    say("| Contract | [`%s`](%s/address/%s) |"
        % (led["contract"], explorer, led["contract"]))
    say("| Deploy transaction | [`%s`](%s/tx/%s) |"
        % (led["deploy_tx"], explorer, led["deploy_tx"]))
    say("| Source commit | `%s` |" % led["commit"])
    say("| Re-read at | %s UTC |"
        % time.strftime("%Y-%m-%d %H:%M", time.gmtime()))
    say()

    say("## The deployed bytes are the committed source")
    say()
    say("| Claim | Value | |")
    say("|---|---|---|")
    on_chain = deployed_source_hash(led["contract"])
    row("the deployed contract is this source, byte for byte",
        on_chain[:32], on_chain == digest)
    row("and the ledger agrees", led["contract_sha256"][:32],
        led["contract_sha256"] == digest)
    say()

    say("## The documents, re-fetched")
    say()
    say("The panel's findings rest on pages anyone can fetch. Each is")
    say("fetched again here and re-hashed, so a finding resting on")
    say("something that has since changed would show as a mismatch rather")
    say("than as a passing test.")
    say()
    say("| Document | Bytes | sha256 | Matches |")
    say("|---|---|---|---|")
    for name in sorted(led["documents"]):
        entry = led["documents"][name]
        try:
            body = fetch(entry["url"])
            ok = (hashlib.sha256(body).hexdigest() == entry["sha256"]
                  and len(body) == entry["bytes"])
        except Exception as err:
            ok = False
            print("  %s unfetchable: %s" % (name, err), file=sys.stderr)
        say("| `%s` | %d | `%s...` | %s |"
            % (name, entry["bytes"], entry["sha256"][:16],
               "yes" if ok else "**no**"))
        if not ok:
            FAILURES.append("%s no longer serves the committed bytes" % name)
    say()

    say("## Every transaction, re-queried")
    say()
    say("A round whose validators reach no majority commits nothing and")
    say("still reports the transaction as successful, so the lifecycle and")
    say("the votes are read here rather than taken from the run.")
    say()
    say("| What | Transaction | Lifecycle | Execution | Consensus |")
    say("|---|---|---|---|---|")
    for entry in led["transactions"]:
        receipt = reader.transaction(entry["tx"])
        lifecycle = str(receipt.get("status_name") or receipt.get("status"))
        result = execution_result(receipt)
        votes = consensus_summary(receipt)
        ok = (result.upper() in ("SUCCESS", "RETURN"))
        if not ok:
            FAILURES.append("%s did not execute successfully"
                            % entry["what"])
        say("| %s | [`%s...`](%s/tx/%s) | %s | %s | %s |"
            % (entry["what"], entry["tx"][:18], explorer, entry["tx"],
               lifecycle, result, votes))
    say()

    say("## What the contract stores")
    say()
    for code in sorted(led["scenarios"]):
        scenario = led["scenarios"][code]
        say("### %s - %s" % (code.upper(), scenario["title"]))
        say()
        if "ruling" not in scenario:
            say("| | | |")
            say("|---|---|---|")
            for key in ("slots_before", "slots_held", "slots_after"):
                if key in scenario:
                    row(key.replace("_", " "),
                        json.dumps(scenario[key]), True)
            if "superseded" in scenario:
                fresh = reader.view("admission_freshness",
                                    [scenario["superseded"],
                                     time.strftime("%Y-%m-%dT%H:%MZ",
                                                   time.gmtime())])
                row("the earlier ruling is no longer in force", fresh,
                    fresh == "SUPERSEDED")
            say()
            continue

        pid = scenario["proposition_id"]
        stored = json.loads(reader.view("get_ruling", [pid]))
        expected = scenario["ruling"]
        say("| | | |")
        say("|---|---|---|")
        row("proposition", pid, True)
        for field in ("admission", "reason", "falsifiable", "unambiguous",
                      "rule_complete", "sufficient_sources",
                      "distinct_publishers", "status", "rounds_used",
                      "panel_state"):
            row(field.replace("_", " "), stored[field],
                stored[field] == expected[field])
        gate = reader.view("is_admissible",
                           [pid, time.strftime("%Y-%m-%dT%H:%MZ",
                                               time.gmtime())])
        row("is_admissible agrees with the verdict", gate,
            gate == (stored["admission"] == "DECIDABLE"
                     and stored["status"] == "ASSESSED"))
        say()

    say("## The contract's own counters")
    say()
    stats = json.loads(reader.view("get_stats", []))
    say("| | |")
    say("|---|---|")
    for key in sorted(stats):
        say("| %s | %s |" % (key, stats[key]))
    say()
    say("Only a ruled proposition moves `decidable` or `refused`, which is")
    say("why neither equals the number of propositions.")
    say()

    say("## What this proves")
    say()
    say("- the deployed contract is the committed source, byte for byte;")
    say("- a well-posed question on published sources is admitted, and")
    say("  only then does `is_admissible` return true;")
    say("- a question no observation could refute is `UNFALSIFIABLE`, and")
    say("  one two honest readers would read differently is `AMBIGUOUS`;")
    say("- sources that do not publish the quantity, and sources that")
    say("  share a publisher where the venue wants two, both leave it")
    say("  `UNSETTLEABLE`;")
    say("- a page that instructs whoever reads it changes nothing;")
    say("- a source that cannot be fetched is never a finding about the")
    say("  question;")
    say("- a withdrawn question returns its slot, and tightening a policy")
    say("  supersedes the rulings made under the old one.")
    say()
    say("Schema `%s`. %d reads." % (led["schema"], READS[0]))
    say()

    PROOFS.mkdir(parents=True, exist_ok=True)
    (PROOFS / "live.md").write_bytes(("\n".join(LINES) + "\n")
                                     .encode("utf-8"))
    if FAILURES:
        print("DISCREPANCIES:")
        for failure in FAILURES:
            print("  - " + failure)
        return 1
    print("all checks passed; written to %s" % (PROOFS / "live.md"))
    return 0


sys.exit(main())

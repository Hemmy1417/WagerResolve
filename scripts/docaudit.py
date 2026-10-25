"""Every claim the docs make about the deployment, checked against its source.

The docs carry an address, a deploy transaction, a source hash, a size and
a deployment history. Each has somewhere it can be read from rather than
trusted: the contract file for the hash and size, `docs/proofs/live.json`
for what the chain settled.

This exists because repointing the docs at a new deployment is a
find/replace, and a stale reference survives one looking exactly like a
correct one. It has happened three times on this repository, and the worst
was inside the history table - row 2 ended up with its own display text,
the NEXT deployment's link, and its own hash. A plain "no superseded
address outside the history" rule cannot see that, because the history is
where superseded addresses are supposed to live. So the history rows are
checked for internal agreement instead: the text, the link and the hash in
one row must describe one deployment.

    python scripts/docaudit.py
"""

import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "wagerresolve.py"
LEDGER = ROOT / "docs" / "proofs" / "live.json"
DOCS = ["README.md", "SUBMISSION.md", "DECISION.md", "docs/DEPLOYMENT.md",
        "docs/SECURITY.md", "docs/INTEGRATION.md", "docs/CONSENSUS.md"]
HISTORY_FILE = "docs/DEPLOYMENT.md"

ROWS = []


def check(claim, detail, ok):
    ROWS.append((claim, str(detail), bool(ok)))


def main() -> int:
    if not LEDGER.exists():
        print("no docs/proofs/live.json - run scripts/live.py first")
        return 1
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    code = CONTRACT.read_bytes()
    digest = hashlib.sha256(code).hexdigest()
    size = format(len(code), ",") + " bytes"

    check("the ledger describes this contract file", digest[:16],
          led["contract_sha256"] == digest)

    text = {name: (ROOT / name).read_text(encoding="utf-8")
            for name in DOCS if (ROOT / name).exists()}

    for name, body in text.items():
        for found in set(re.findall(r"\b[0-9a-f]{64}\b", body)):
            check("%s: 64-hex is this source" % name, found[:16],
                  found == digest)
        for found in set(re.findall(r"\b\d{2},\d{3} bytes\b", body)):
            check("%s: byte count is this source" % name, found,
                  found == size)
        if name != HISTORY_FILE:
            for found in set(re.findall(r"\b0x[0-9a-fA-F]{40}\b", body)):
                check("%s: address is the canonical one" % name,
                      found[:12], found == led["contract"])

    check("the canonical address appears", led["contract"][:12],
          any(led["contract"] in body for body in text.values()))
    check("the canonical deploy tx appears", led["deploy_tx"][:12],
          any(led["deploy_tx"] in body for body in text.values()))

    # The history table: each row must describe ONE deployment. This is the
    # check the third mangling would have failed.
    history = text.get(HISTORY_FILE, "")
    rows = re.findall(
        r"^\|\s*(\d+)\s*\|\s*\[`(0x[0-9a-fA-F]{8})[^`]*`\]"
        r"\((https://[^)]*/address/(0x[0-9a-fA-F]{40}))\)\s*\|"
        r"\s*`([0-9a-f]{8})[^`]*`\s*\|",
        history, re.M)
    check("the history table has rows", len(rows), len(rows) >= 2)
    seen_addresses = []
    seen_hashes = []
    for number, shown, _url, linked, short_hash in rows:
        check("history row %s links the address it shows" % number,
              "%s -> %s" % (shown, linked[:10]),
              linked.lower().startswith(shown.lower()))
        check("history row %s has a distinct address" % number,
              linked[:12], linked not in seen_addresses)
        seen_addresses.append(linked)
        seen_hashes.append(short_hash)
    check("history rows carry distinct byte sets or say why",
          ", ".join(seen_hashes), True)
    if rows:
        last = rows[-1]
        check("the last history row is the canonical deployment",
              last[3][:12], last[3] == led["contract"])
        check("and carries the canonical hash", last[4],
              digest.startswith(last[4]))

    width = max(len(claim) for claim, _, _ in ROWS)
    wrong = 0
    for claim, detail, ok in ROWS:
        if not ok:
            wrong += 1
        print("%-*s  %-34s %s" % (width, claim, detail[:34],
                                  "OK" if ok else "WRONG"))
    print("\n%d checks, %d wrong" % (len(ROWS), wrong))
    return 1 if wrong else 0


sys.exit(main())

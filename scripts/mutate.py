"""Break the contract on purpose, and check the suite notices.

A green suite says the contract passes its tests. It does not say the tests
would notice if a guard were deleted. Each mutation below removes or
reverses exactly one rule, writes the patched contract to a temporary file,
and runs the whole Direct Mode suite against it through
`WAGERRESOLVE_CONTRACT`.

    python -u scripts/mutate.py            everything
    python -u scripts/mutate.py 0-20       that slice, [first, last)
    python -u scripts/mutate.py grief      only labels containing that

Reading the result:

- **killed** - the suite failed, so at least one test is load-bearing;
- **SURVIVED** - the suite passed with the rule gone. Either a real gap in
  the tests, or a guard shielded by another rule that fires first;
- **EQUIVALENT** - listed below with the argument for why it cannot change
  behaviour. A mutation is only allowed in that list with a written reason.

The bounds are half-open. `0-20 20-40` covers everything; `1-20 20-40`
silently skips index 0, which is how a sweep run in slices can look
complete while leaving guards unrun. The totals printed at the end are
counted from the labels actually processed.
"""

import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "wagerresolve.py"
TESTS = ROOT / "tests" / "direct"

# Files that discriminate most run first, so a mutant that is going to die
# usually dies early. Any file not named here is appended, so a new test
# file is never silently left out of the ordering.
ORDER = ["test_units.py", "test_verdicts.py", "test_validators.py",
         "test_hardening.py", "test_lifecycle.py", "test_smoke.py"]


MUTATIONS = [
    # -- the admission mapping --------------------------------------------
    ("verdict: an unfalsifiable question is admitted",
     "    if not falsifiable:\n        return ADMISSION_UNFALSIFIABLE\n",
     ""),
    ("verdict: an ambiguous question is admitted",
     "    if not unambiguous:\n        return ADMISSION_AMBIGUOUS\n",
     ""),
    ("verdict: an incomplete rule is admitted",
     "    if not rule_complete:\n        return ADMISSION_UNSETTLEABLE\n",
     ""),
    ("verdict: the source floor is not enforced",
     "    if sufficient_sources < min_sources:\n"
     "        return ADMISSION_UNSETTLEABLE\n",
     ""),
    ("verdict: the publisher floor is not enforced",
     "    if distinct_publishers < min_publishers:\n"
     "        return ADMISSION_UNSETTLEABLE\n",
     ""),
    ("verdict: the precedence is reversed",
     "    if not falsifiable:\n        return ADMISSION_UNFALSIFIABLE\n"
     "    if not unambiguous:\n        return ADMISSION_AMBIGUOUS\n",
     "    if not unambiguous:\n        return ADMISSION_AMBIGUOUS\n"
     "    if not falsifiable:\n        return ADMISSION_UNFALSIFIABLE\n"),
    ("verdict: the source floor uses the wrong comparison",
     "    if sufficient_sources < min_sources:",
     "    if sufficient_sources < 0:"),

    # -- the admission gate -----------------------------------------------
    ("gate: anything assessed admits a stake",
     '        if str(row.ruling.admission) != ADMISSION_DECIDABLE:\n'
     '            return False\n',
     ""),
    ("gate: freshness is not required",
     "        return self._freshness_of(row, venue, as_of) "
     "== FRESHNESS_FRESH",
     "        return True"),
    ("gate: a disabled venue still admits",
     "        if venue is None or not bool(venue.enabled):\n"
     "            return False\n",
     "        if venue is None:\n            return False\n"),
    ("freshness: a superseded ruling stays in force",
     "        if str(row.ruling.definition_hash) != "
     "str(venue.definition_hash):\n"
     "            return FRESHNESS_SUPERSEDED\n",
     ""),
    ("freshness: the window never expires",
     "        if age > int(venue.admission_ttl_minutes):\n"
     "            return FRESHNESS_STALE\n",
     ""),
    ("freshness: a settled question is still open to stakes",
     '        if _minutes_between(when, str(row.settles_at)) <= 0:\n'
     '            return FRESHNESS_SETTLED\n',
     ""),
    ("freshness: an unassessed proposition reads fresh",
     "        if str(row.status) != PROPOSITION_ASSESSED:\n"
     "            return FRESHNESS_UNKNOWN\n",
     ""),
    ("freshness: an unusable as-of reads fresh",
     '        if when == "" or _parse_minute(when) < 0:\n'
     "            return FRESHNESS_UNKNOWN\n",
     ""),

    # -- fail closed -------------------------------------------------------
    ("closed: an unread round is a verdict about the question",
     '        if str(payload["panel_state"]) != PANEL_RULED:',
     "        if False:"),
    ("closed: an unparseable panel answer is tolerated",
     "        raise gl.vm.UserError(\n"
     "            ERROR_TRANSIENT + \" the panel answer did not parse\")",
     "        answer = {\"falsifiable\": True, \"falsifiable_reason\": "
     "REASON_NONE, \"unambiguous\": True, \"ambiguity_reason\": "
     "REASON_NONE, \"rule_complete\": True, \"rule_reason\": REASON_NONE, "
     "\"sources\": {s: {\"publishes_quantity\": True, \"note\": \"\"} "
     "for s in readable}}"),
    ("closed: a reachable page counts without publishing the quantity",
     "        if row is not None and bool(row[\"publishes_quantity\"]):\n"
     "            states[source_id] = SOURCE_SUFFICIENT\n"
     "        else:\n"
     "            states[source_id] = SOURCE_INSUFFICIENT\n",
     "        states[source_id] = SOURCE_SUFFICIENT\n"),
    ("closed: rounds never run out",
     "        if int(row.rounds_used) >= MAX_ROUNDS:\n"
     '            self._reject("that proposition has used all "\n'
     '                         + str(MAX_ROUNDS) + " of its rounds")\n',
     ""),

    # -- reading the panel answer -----------------------------------------
    ("answer: a missing key is tolerated",
     "    for key in ANSWER_KEYS:\n        if key not in shape:\n"
     "            return None\n",
     ""),
    ("answer: an integer passes for a boolean",
     '    for key in ("falsifiable", "unambiguous", "rule_complete"):\n'
     "        if not _exact_bool(shape.get(key)):\n            return None\n",
     '    for key in ("falsifiable", "unambiguous", "rule_complete"):\n'
     "        if shape.get(key) is None:\n            return None\n"),
    ("answer: an unknown reason enum is accepted",
     "        if type(value) is not str or value.strip().upper() "
     "not in REASONS:\n            return None\n",
     "        if type(value) is not str:\n            return None\n"),
    ("answer: a row about an unread source is accepted",
     "        if type(source_id) is not str or source_id not in wanted:\n"
     "            return None\n",
     "        if type(source_id) is not str:\n            return None\n"),
    ("answer: a duplicated source row is accepted",
     "        if source_id in sources:\n            return None\n",
     ""),
    ("answer: the row count is not checked",
     "    if len(rows) != len(wanted):\n        return None\n",
     ""),
    ("answer: a non-string note is accepted",
     "        if note is not None and type(note) is not str:\n"
     "            return None\n",
     ""),

    # -- the payload gate --------------------------------------------------
    ("payload: a payload for another proposition is accepted",
     '    if str(shape.get("proposition_id")) != '
     'str(ctx["proposition_id"]):\n        return None\n',
     ""),
    ("payload: an unknown panel state is accepted",
     "    if panel_state not in (PANEL_RULED, PANEL_UNREADABLE):\n"
     "        return None\n",
     ""),
    ("payload: a boolean is not type-checked",
     '    for key in ("falsifiable", "unambiguous", "rule_complete"):\n'
     "        if not _exact_bool(shape.get(key)):\n            return None\n",
     ""),
    ("payload: an unknown source state is accepted",
     "        if type(state) is not str or state not in SOURCE_STATES:\n"
     "            return None\n",
     ""),
    ("payload: a source nobody named is accepted",
     "        if type(source_id) is not str or source_id not in known:\n"
     "            return None\n",
     ""),
    ("payload: a boolean passes as a byte count",
     "        if type(value) is not int or _exact_bool(value) "
     "or value < 0:\n            return None\n",
     "        if type(value) is not int:\n            return None\n"),
    ("payload: a byte count over the cap is accepted",
     "        if value > FETCH_BYTES_CAP:\n            return None\n",
     ""),
    ("payload: an unsorted readable list is accepted",
     "    if sorted(readable) != list(readable) or len(set(readable)) \\\n"
     "            != len(readable):\n        return None\n",
     ""),
    ("payload: a state may contradict its own row",
     "            if claimed != (states.get(source_id) "
     "== SOURCE_SUFFICIENT):\n                return None\n",
     ""),
    ("payload: an oversized note is accepted",
     "            if note is not None and len(note) > MAX_REASON_CHARS:\n"
     "                return None\n",
     ""),
    ("payload: an unreadable payload may still carry findings",
     '        if bool(shape.get("falsifiable")) or '
     'bool(shape.get("unambiguous")) \\\n'
     '                or bool(shape.get("rule_complete")):\n'
     "            return None\n",
     ""),

    # -- the comparison ----------------------------------------------------
    ("compare: the findings are not compared",
     '    for key in ("falsifiable", "unambiguous", "rule_complete"):\n'
     "        if bool(mine[key]) != bool(theirs[key]):\n"
     '            return key + ": " + str(mine[key]) + " vs " '
     '+ str(theirs[key])\n',
     ""),
    ("compare: reachability is not compared",
     '    if list(mine["readable"]) != list(theirs["readable"]):\n'
     '        return ("reachable sources: " + _canonical(mine["readable"])\n'
     '                + " vs " + _canonical(theirs["readable"]))\n',
     ""),
    ("compare: per-source sufficiency is not compared",
     '    for source_id in mine["readable"]:\n'
     '        if bool(mine["sources"].get(source_id)) != \\\n'
     '                bool(theirs["sources"].get(source_id)):\n',
     '    for source_id in []:\n'
     '        if bool(mine["sources"].get(source_id)) != \\\n'
     '                bool(theirs["sources"].get(source_id)):\n'),
    ("compare: the panel state is not compared",
     '                if str(own["panel_state"]) != '
     'str(theirs["panel_state"]):',
     "                if False:"),
    ("compare: a validator accepts without reading anything itself",
     "                _own_raw, own = _node_round(ctx)",
     "                _own_raw, own = (None, _parse_payload(raw, ctx))"),
    ("compare: diagnostic prose becomes consensus-critical",
     '    return {\n        "falsifiable": bool(answer["falsifiable"]),',
     '    return {\n        "reason": str(answer.get("ambiguity_reason", '
     '"")),\n        "falsifiable": bool(answer["falsifiable"]),'),

    # -- who may ask -------------------------------------------------------
    ("grief: anybody may propose at any venue",
     "        if not self._may_propose(venue, caller):\n"
     '            self._reject("this venue\'s proposer policy is "\n'
     "                         + str(venue.proposer_policy).lower()\n"
     '                         + " and you are not named under it")\n',
     ""),
    ("grief: one proposer may occupy every slot",
     "        if held >= MAX_OPEN_PER_PROPOSER:\n"
     '            self._reject("you already have " '
     "+ str(MAX_OPEN_PER_PROPOSER)\n"
     '                         + " propositions in flight at this venue")\n',
     ""),
    ("grief: a slot is never released, so the cap is exhaustible",
     "    def _release_slot(self, row: Proposition):",
     "    def _release_slot(self, row: Proposition):\n        return"),
    ("grief: the venue cap is not enforced",
     "        if int(venue.open_propositions) >= MAX_OPEN_PER_VENUE:",
     "        if False:"),
    ("grief: a revoked proposer keeps standing",
     "            return named is not None and bool(named)",
     "            return named is not None"),
    ("grief: anybody may withdraw another's proposition",
     "        if caller != str(row.proposed_by) and caller != owner:\n"
     '            self._reject("only the proposer, or the venue owner, may "\n'
     '                         "withdraw a proposition")\n',
     ""),
    ("grief: anybody may change a venue's policy",
     '        if self._caller() != str(venue.owner):\n'
     '            self._reject("only the venue owner may change its '
     'policy")\n',
     ""),
    ("grief: a policy change does not bump the version",
     "        venue.definition_version = u16(int(venue.definition_version) "
     "+ 1)\n",
     ""),

    # -- admission of a proposition ---------------------------------------
    ("propose: a settlement in the past is accepted",
     "        if ahead <= 0:\n"
     '            self._reject("settles_at must be in the future")\n',
     ""),
    ("propose: the horizon is not enforced",
     "        if ahead > int(venue.max_horizon_days) * 24 * 60:",
     "        if False:"),
    ("propose: a repeated source is accepted",
     "            if url in seen:\n"
     '                self._reject("source " + str(index + 1)\n'
     '                             + " repeats an earlier source")\n',
     ""),
    ("propose: an inadmissible URL is accepted",
     "            if not _admissible(url):\n"
     '                self._reject("source " + str(index + 1)\n'
     '                             + " is not an admissible https '
     'location")\n',
     ""),
    ("propose: the venue's source floor is not enforced",
     "        if len(sources) < int(venue.min_sources):",
     "        if False:"),
    ("propose: more sources than the cap are accepted",
     "        if len(sources) > MAX_SOURCES:",
     "        if False:"),
    ("propose: a duplicate id overwrites the first",
     "        if self.propositions.get(key) is not None:\n"
     '            self._reject("that proposition id is taken")\n',
     ""),
    ("propose: a disabled venue still accepts questions",
     "        if not bool(venue.enabled):\n"
     '            self._reject("that venue is not accepting '
     'propositions")\n'
     "        caller = self._caller()",
     "        caller = self._caller()"),

    # -- URL admission -----------------------------------------------------
    ("url: plain http is accepted",
     '    if not text.startswith("https://"):\n        return False\n',
     ""),
    ("url: credentials in the authority are accepted",
     '    if "@" in rest:\n        return ""\n',
     ""),
    ("url: localhost is accepted",
     '    if host in ("localhost",):\n        return False\n',
     ""),
    ("url: an internal suffix is accepted",
     '    for ending in (".localhost", ".local", ".internal", '
     '".home.arpa"):\n'
     "        if host.endswith(ending):\n            return False\n",
     ""),
    ("url: a numeric host is accepted",
     "    if _is_numeric_label(labels[-1]):\n        return False\n",
     ""),
    ("url: a malformed label is accepted",
     "        for ch in label:\n"
     "            ok = ((\"a\" <= ch <= \"z\") or (\"0\" <= ch <= \"9\") "
     "or ch == \"-\")\n"
     "            if not ok:\n                return False\n",
     ""),
    ("url: the length cap is not enforced",
     '    if text == "" or len(text) > MAX_URL_CHARS:\n        return False\n',
     '    if text == "":\n        return False\n'),

    # -- publishers --------------------------------------------------------
    ("publisher: every url counts as its own publisher",
     "    labels = name.split(\".\")\n    if len(labels) < 2:\n"
     "        return name\n",
     "    return name\n    labels = name.split(\".\")\n"
     "    if len(labels) < 2:\n        return name\n"),
    ("publisher: a subdomain is a different publisher",
     '    if name.startswith("www."):\n        name = name[4:]\n'
     "    labels = name.split(\".\")",
     "    labels = name.split(\".\")"),
    ("publisher: duplicates are counted twice",
     "                if str(entry.publisher) not in publishers:\n"
     "                    publishers.append(str(entry.publisher))\n",
     "                publishers.append(str(entry.publisher))\n"),

    # -- instants ----------------------------------------------------------
    ("time: an instant is not normalised",
     '    return text[:16] + "Z"',
     '    return text'),
    ("time: a short instant is accepted",
     "    if len(text) < 16:\n        return \"\"\n",
     ""),
    ("time: an impossible month or day is accepted",
     "    if month < 1 or month > 12 or day < 1 or day > 31:\n"
     "        return -1\n",
     ""),
    ("time: an impossible hour or minute is accepted",
     "    if hour > 23 or minute > 59:\n        return -1\n",
     ""),
    ("time: the separators are not checked",
     '    if text[4] != "-" or text[7] != "-" or text[10] != "T" \\\n'
     '            or text[13] != ":":\n        return -1\n',
     ""),

    # -- the prompt --------------------------------------------------------
    ("prompt: the budget is not applied per document",
     '            "text": _bounded(body, allowance),',
     '            "text": body,'),
    ("prompt: the documents are interpolated rather than encoded",
     '        + _canonical(payload)',
     '        + str(payload)'),

    # -- the fetch ---------------------------------------------------------
    ("fetch: a failed status is read anyway",
     "    if status < 200 or status >= 300 or body is None "
     "or len(body) == 0:\n        return (SOURCE_UNREACHABLE, None, 0)\n",
     ""),
    ("fetch: an oversized body is read",
     "    if count > FETCH_BYTES_CAP:\n"
     "        return (SOURCE_UNREACHABLE, None, count)\n",
     ""),
    ("fetch: a blank page counts as a source",
     '    if text.strip() == "":\n'
     "        return (SOURCE_UNREACHABLE, None, count)\n",
     ""),
    ("fetch: an inadmissible url is fetched anyway",
     "    if not _admissible(url):\n        return (SOURCE_REJECTED, "
     "None, 0)\n",
     ""),

    # -- storage and counters ---------------------------------------------
    ("store: the definition hash is not recorded with the ruling",
     "        row.ruling.definition_hash = str(venue.definition_hash)\n"
     "        row.ruling.definition_version = "
     "u16(int(venue.definition_version))\n"
     "        row.status = PROPOSITION_ASSESSED",
     "        row.status = PROPOSITION_ASSESSED"),
    ("store: a ruled proposition stays open",
     "        row.status = PROPOSITION_ASSESSED\n",
     ""),
    ("store: the round is not counted",
     "        row.rounds_used = u16(int(row.rounds_used) + 1)\n",
     ""),
    ("store: the decidable counter moves for every verdict",
     "        if admission == ADMISSION_DECIDABLE:\n"
     "            self.decidable_total = "
     "u256(int(self.decidable_total) + 1)\n"
     "        else:\n"
     "            self.refused_total = "
     "u256(int(self.refused_total) + 1)\n",
     "        self.decidable_total = "
     "u256(int(self.decidable_total) + 1)\n"),
]


EQUIVALENT = {}


def run_suite(contract_path: pathlib.Path) -> bool:
    """True when the suite passes against this contract."""
    env = dict(os.environ)
    env["WAGERRESOLVE_CONTRACT"] = str(contract_path)
    env["PYTHONUTF8"] = "1"
    names = list(ORDER)
    for path in sorted(TESTS.glob("test_*.py")):
        if path.name not in names:
            names.append(path.name)
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q",
         *[str(TESTS / name) for name in names]],
        cwd=str(ROOT), env=env, capture_output=True, text=True)
    return done.returncode == 0


def main() -> int:
    source = CONTRACT.read_text(encoding="utf-8")

    first, last = 0, len(MUTATIONS)
    needle = ""
    argument = sys.argv[1] if len(sys.argv) > 1 else ""
    if argument:
        parts = argument.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            first, last = int(parts[0]), int(parts[1])
        else:
            needle = argument.lower()

    missing = []
    for label, find, _replace in MUTATIONS:
        if find not in source:
            missing.append(label)
    if missing:
        print("these mutations no longer match the contract:")
        for label in missing:
            print("  " + label)
        print("\nA mutation that does not apply tests nothing. Fix the "
              "anchor or delete it.")
        return 1
    print("%d mutations, every anchor matched" % len(MUTATIONS),
          flush=True)

    for label in EQUIVALENT:
        if label not in [row[0] for row in MUTATIONS]:
            print("EQUIVALENT names a mutation that does not exist: "
                  + label)
            return 1

    print("baseline: running the suite against the committed contract",
          flush=True)
    if not run_suite(CONTRACT):
        print("baseline FAIL - the suite does not pass unmutated")
        return 1
    print("baseline PASS", flush=True)

    work = pathlib.Path(tempfile.mkdtemp(prefix="wagerresolve-mutants-"))
    killed, survived, equivalent = [], [], []

    for index in range(first, min(last, len(MUTATIONS))):
        label, find, replace = MUTATIONS[index]
        if needle and needle not in label.lower():
            continue
        mutant = work / ("mutant_%d.py" % index)
        mutant.write_bytes(source.replace(find, replace).encode("utf-8"))
        passed = run_suite(mutant)
        if not passed:
            killed.append(label)
            print("killed   " + label, flush=True)
        elif label in EQUIVALENT:
            equivalent.append(label)
            print("EQUIVALENT " + label, flush=True)
        else:
            survived.append(label)
            print("SURVIVED " + label, flush=True)

    total = len(killed) + len(survived) + len(equivalent)
    print("\n%d/%d mutants killed, %d equivalent by construction, "
          "%d survived" % (len(killed), total, len(equivalent),
                           len(survived)))
    for label in equivalent:
        print("EQUIVALENT: " + label)
        print("    " + EQUIVALENT[label])
    for label in survived:
        print("SURVIVED: " + label)
    return 1 if survived else 0


sys.exit(main())
